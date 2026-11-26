import { useEffect } from "react";
import {
  REAGENTS, useLab, type ApparatusSlot, type AdditionOrder,
} from "./lab";
// 写实 2D 器材：tikz-chemlab 编译输出物（assets/apparatus/，逐资产署名见 ASSETS.csv）。
// ?url 导入让 Vite 在 dev 与 Docker build 都把 SVG 拷入产物，前端只经静态资源取用。
import beakerSvg from "../../../assets/apparatus/beaker_250ml.svg?url";
import cylinderSvg from "../../../assets/apparatus/graduated-cylinder.svg?url";
import dropperSvg from "../../../assets/apparatus/dropper.svg?url";

/** apparatus_id → 写实资产 URL（与 apparatus 卡 asset 字段同源，单一事实源）。 */
const APPARATUS_ASSET: Record<string, string> = {
  beaker_250ml: beakerSvg,
  graduated_cylinder_100ml: cylinderSvg,
  dropper: dropperSvg,
};

/**
 * 写实器材呈现：<img> 为出版级主视觉；液体色以半透明层叠加在容器下半部
 * （表现近似，不进化学事实层；精确的指示剂混色/温升/飞溅由 VesselView 的 PixiJS 层负责）。
 */
function ApparatusSvg({ apparatusId, liquid }: { apparatusId: string; liquid: string | null }) {
  const src = APPARATUS_ASSET[apparatusId];
  if (!src) return null;
  return (
    <span className="apparatus-art" role="img" aria-label="写实器材">
      <img src={src} alt="" />
      {liquid && <span className="apparatus-art__liquid" style={{ background: liquid }} aria-hidden="true" />}
    </span>
  );
}

const ORDER_LABEL: Record<AdditionOrder, string> = {
  acid_into_water: "酸入水（正确）",
  water_into_acid: "水入浓酸（错误）",
};

export default function LabBench() {
  const {
    slots, selectedReagent, selectedVolume_L, additionOrder, wsStatus, loading,
    setSelectedReagent, setSelectedVolume, setAdditionOrder, placeApparatus,
    pourInto, clearBench, connectWs,
  } = useLab();

  useEffect(() => connectWs(), [connectWs]);

  return (
    <section className="panel panel--bench" aria-label="实验台装置建造">
      <div className="panel__head">
        <div>
          <h2>实验台 · 装置建造</h2>
          <p className="muted tiny">取药品 → 选器材 → 倾倒；WS 现象通道 {wsStatus}</p>
        </div>
        <button type="button" onClick={clearBench} disabled={loading}>清空</button>
      </div>

      <div className="bench-grid">
        <div className="bench-rack">
          <h3>药品架</h3>
          <div className="reagent-list">
            {REAGENTS.map((r) => (
              <button
                key={r.compound_id} type="button"
                className={selectedReagent === r.compound_id ? "reagent reagent--active" : "reagent"}
                onClick={() => setSelectedReagent(r.compound_id)}
              >
                {r.label}{r.hazard ? " ⚠" : ""}
              </button>
            ))}
          </div>
          <div className="pour-controls">
            <label>取用量 <span className="mono">{selectedVolume_L.toFixed(2)} L</span></label>
            <input
              type="range" min={0.05} max={1} step={0.05}
              value={selectedVolume_L}
              onChange={(e) => setSelectedVolume(Number(e.target.value))}
              aria-label="取用体积"
            />
            <label>加入顺序</label>
            <select value={additionOrder} onChange={(e) => setAdditionOrder(e.target.value as AdditionOrder)}>
              <option value="acid_into_water">{ORDER_LABEL.acid_into_water}</option>
              <option value="water_into_acid">{ORDER_LABEL.water_into_acid}</option>
            </select>
          </div>
          <h3>器材架</h3>
          <div className="apparatus-palette">
            <button type="button" onClick={() => placeApparatus("beaker_250ml", "烧杯 250 mL")}>+ 烧杯</button>
            <button type="button" onClick={() => placeApparatus("graduated_cylinder_100ml", "量筒 100 mL")}>+ 量筒</button>
            <button type="button" onClick={() => placeApparatus("dropper", "胶头滴管")}>+ 滴管</button>
          </div>
        </div>

        <div className="bench-stage">
          {slots.map((slot) => (
            <BenchSlot key={slot.slot_id} slot={slot} onPour={() => void pourInto(slot.slot_id)} loading={loading} />
          ))}
        </div>
      </div>
    </section>
  );
}

function BenchSlot({ slot, onPour, loading }: { slot: ApparatusSlot; onPour: () => void; loading: boolean }) {
  const reagentIds = slot.contents.map((c) => c.compound_id);
  const liquid = reagentIds.includes("sulfuric_acid_conc") ? "#d9c27a"
    : reagentIds.includes("phenolphthalein") ? "#f2b8c6"
    : reagentIds.includes("naoh") || reagentIds.includes("koh") ? "#cfe3d8"
    : reagentIds.includes("hcl") ? "#e8dfc9" : null;
  const totalVolume = slot.contents.reduce((s, c) => s + c.volume_L, 0);
  return (
    <div className="bench-slot">
      <ApparatusSvg apparatusId={slot.apparatus_id} liquid={liquid} />
      <div className="bench-slot__meta">
        <strong>{slot.label}</strong>
        <span className="muted tiny">{slot.contents.length ? reagentIds.join(" + ") : "空"}</span>
        <span className="mono tiny">Σ {totalVolume.toFixed(2)} L</span>
      </div>
      <button type="button" onClick={onPour} disabled={loading}>倾倒 →</button>
    </div>
  );
}
