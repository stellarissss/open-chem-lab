import { useEffect, useState } from "react";
import { useHealth } from "./health";
import SpeciesPanel from "./SpeciesPanel";
import Timeline from "./Timeline";
import LabBench from "./LabBench";
import VesselView from "./VesselView";
import { fromSnapshot, SYSTEM_LABELS, useLab } from "./lab";
import type { PhenomenonDirective } from "@st/protocol";
import "./style.css";

/** 最小直接求解入口：演示 gateway 物种读取接口，配比走已签核中和体系。 */
const PRESETS = [
  { label: "0.1M HCl", substances: [{ compound_id: "hcl", concentration_mol_L: 0.1, volume_L: 1.0 }] },
  {
    label: "等体积中和",
    substances: [
      { compound_id: "hcl", concentration_mol_L: 0.1, volume_L: 0.5 },
      { compound_id: "naoh", concentration_mol_L: 0.1, volume_L: 0.5 },
    ],
  },
  {
    label: "弱酸+强碱",
    substances: [
      { compound_id: "acetic_acid", concentration_mol_L: 0.1, volume_L: 0.5 },
      { compound_id: "naoh", concentration_mol_L: 0.1, volume_L: 0.5 },
    ],
  },
];

export default function App() {
  const { status, version, protocol, uptimeMs, checkedAt, refresh } = useHealth();
  const {
    system, timeline, frameIndex, live, heat, error, loading,
    phenomenonSource, wsDirectives,
    loadTimeline, solveLive, clearLive, solveHeat,
  } = useLab();
  const [preset, setPreset] = useState(1);

  useEffect(() => {
    void refresh();
    const id = window.setInterval(() => void refresh(), 5000);
    return () => window.clearInterval(id);
  }, [refresh]);

  useEffect(() => {
    void loadTimeline(system);
  }, [loadTimeline, system]);

  const frame = timeline?.keyframes[frameIndex];
  const panelData = live ?? (frame ? fromSnapshot(frame.speciation, frame.container_id) : null);

  // 现象来源优先级：live 倾倒结果 > WS 实时推送 > 时间轴回放帧 > 热效应结果。
  // 三者都喂给同一 VesselView 渲染管线（st.phenomenon.v1 指令驱动）。
  const frameDirectives: PhenomenonDirective[] =
    (frame?.speciation as { phenomena?: PhenomenonDirective[] } | undefined)?.phenomena ?? [];
  let directives: PhenomenonDirective[];
  let solvable: boolean;
  if (phenomenonSource === "live" && heat) {
    directives = heat.directives ?? [];
    solvable = heat.outcome === "solved";
  } else if (live && phenomenonSource !== "ws") {
    directives = live.phenomena ?? [];
    solvable = live.outcome === "solved";
  } else if (phenomenonSource === "ws" && wsDirectives.length) {
    directives = wsDirectives;
    solvable = true;
  } else {
    directives = frameDirectives;
    solvable = (panelData?.outcome ?? "") === "solved";
  }

  const label = status === "ok" ? "后端已连接" : status === "error" ? "后端不可用" : "检测中…";

  return (
    <div className="shell">
      <header className="topbar">
        <span className="brand">ST Crucible · 实验台</span>
        <span className={`badge badge--${status}`}>● {label}</span>
      </header>

      <main className="stage">
        <div className="stage__left">
          <LabBench />
          <VesselView directives={directives} solvable={solvable}
            label={phenomenonSource === "timeline" ? "时间轴复现" : phenomenonSource === "ws" ? "WS 实时" : "实验台容器"} />
          <Timeline timeline={timeline} />
          <SpeciesPanel
            data={panelData}
            systemLabel={live ? "单容器求解" : SYSTEM_LABELS[system]}
            loading={loading}
            error={error}
            timestamp={panelData?.timestampMs ?? null}
          />
        </div>

        <aside className="inspector" aria-label="状态面板">
          <h2>系统状态</h2>
          <dl>
            <dt>服务版本</dt><dd>{version}</dd>
            <dt>协议</dt><dd>{protocol}</dd>
            <dt>运行时长</dt><dd>{uptimeMs == null ? "—" : `${(uptimeMs / 1000).toFixed(0)}s`}</dd>
            <dt>最近检测</dt><dd>{checkedAt == null ? "—" : new Date(checkedAt).toLocaleTimeString()}</dd>
          </dl>

          <h2>单容器求解</h2>
          <p className="muted tiny">经 gateway 求解，不直连求解库。</p>
          <select value={preset} onChange={(e) => setPreset(Number(e.target.value))} aria-label="预设配比">
            {PRESETS.map((p, i) => <option key={p.label} value={i}>{p.label}</option>)}
          </select>
          <div className="inspector__actions">
            <button type="button" onClick={() => void solveLive(PRESETS[preset]?.substances ?? [])} disabled={loading}>
              求解
            </button>
            <button type="button" onClick={clearLive} disabled={!live}>回到回放</button>
          </div>

          <h2>错误操作后果</h2>
          <p className="muted tiny">浓硫酸稀释：水入酸飞溅 / 酸入水温升。见解剖面板指令溯源。</p>
          <div className="inspector__actions">
            <button type="button" onClick={() => void solveHeat("water_into_acid")} disabled={loading}>
              水入浓酸
            </button>
            <button type="button" onClick={() => void solveHeat("acid_into_water")} disabled={loading}>
              浓酸入水
            </button>
          </div>
          {heat && heat.outcome === "solved" && (
            <div className={`heat-card ${heat.splash_risk ? "heat-card--splash" : ""}`}>
              <div>ΔT <strong>{heat.delta_T_K?.toFixed(2)} K</strong> · 终温 {heat.final_temperature_K?.toFixed(2)} K</div>
              {heat.splash_risk
                ? <div className="heat-card__warn">⚠ 界面闪沸 · 酸液飞溅（错误操作）</div>
                : <div className="heat-card__ok">✓ 热量分散 · 无飞溅（正确操作）</div>}
              <div className="muted tiny">派生指令：{heat.directives.map((d) => d.type).join(", ") || "无"}</div>
            </div>
          )}
        </aside>
      </main>

      <footer className="footer">
        现实操作勿模仿 · 数值零错红线 · LGPL-3.0 · 时间轴为仿真相对刻度
      </footer>
    </div>
  );
}
