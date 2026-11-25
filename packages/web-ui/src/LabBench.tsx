import { useEffect } from "react";
import {
  REAGENTS, useLab, type ApparatusSlot, type AdditionOrder,
} from "./lab";

/** 内联简笔器材图（不落 assets/ 资产文件，署名与出版级资产链不受影响）。 */
function ApparatusSvg({ type, liquid }: { type: string; liquid: string | null }) {
  const body = (
    <>
      {type === "beaker" && (
        <>
          <path d="M20 14 L24 78 Q60 84 96 78 L100 14" fill="#eef3f1" stroke="#5b6b63" strokeWidth="2" />
          <path d="M14 14 L26 14 M94 14 L106 14" stroke="#5b6b63" strokeWidth="2" />
          {[32, 46, 60, 74].map((y) => <path key={y} d={`M26 ${y} L34 ${y}`} stroke="#9aa9a2" strokeWidth="1" />)}
          {liquid && <clipPath id="beaker-clip"><rect x="24" y="48" width="72" height="30" /></clipPath>}
          {liquid && <rect x="24" y="48" width="72" height="30" fill={liquid} clipPath="url(#beaker-clip)" opacity="0.8" />}
        </>
      )}
      {type === "graduated_cylinder" && (
        <>
          <rect x="44" y="10" width="32" height="74" rx="3" fill="#eef3f1" stroke="#5b6b63" strokeWidth="2" />
          <rect x="40" y="84" width="40" height="6" rx="2" fill="#5b6b63" />
          {[22, 34, 46, 58, 70].map((y) => <path key={y} d={`M46 ${y} L58 ${y}`} stroke="#9aa9a2" strokeWidth="1" />)}
          {liquid && <rect x="46" y="46" width="28" height="38" fill={liquid} opacity="0.8" />}
        </>
      )}
      {type === "dropper" && (
        <>
          <rect x="54" y="8" width="12" height="22" rx="5" fill="#8a5a2b" />
          <path d="M54 30 L56 76 Q60 82 64 76 L66 30 Z" fill="#eef3f1" stroke="#5b6b63" strokeWidth="2" />
          {liquid && <path d="M57 52 L63 52 L62 74 L58 74 Z" fill={liquid} opacity="0.8" />}
        </>
      )}
    </>
  );
  return <svg viewBox="0 0 120 96" width="120" height="96" role="img" aria-label="器材示意">{body}</svg>;
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
      <ApparatusSvg type={slot.apparatus_id.split("_")[0] ?? "beaker"} liquid={liquid} />
      <div className="bench-slot__meta">
        <strong>{slot.label}</strong>
        <span className="muted tiny">{slot.contents.length ? reagentIds.join(" + ") : "空"}</span>
        <span className="mono tiny">Σ {totalVolume.toFixed(2)} L</span>
      </div>
      <button type="button" onClick={onPour} disabled={loading}>倾倒 →</button>
    </div>
  );
}
