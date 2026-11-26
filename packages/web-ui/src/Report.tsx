import type { LabReport, Operation, SourceAnchor } from "@st/protocol";

/** 只读实验报告视图（spec-006）：只展示 solver-worker 汇编、gateway 代理转发的产物，不在表现层加工数值。 */
const KIND_LABEL: Record<Operation["kind"], string> = {
  place_apparatus: "取用器材",
  pour: "倾倒",
  set_order: "加入顺序",
  solve: "求解",
  heat: "热效应",
};

const SOURCE_KIND_LABEL: Record<SourceAnchor["kind"], string> = {
  solver: "求解出口",
  timeline: "时间轴",
  ruleset: "规则集",
  authoritative_db: "权威源",
  crosscheck: "独立对拍",
  computed: "计算",
};

const OUTCOME_LABEL: Record<string, string> = {
  solved: "定量解",
  no_significant_change: "无明显变化（覆盖外）",
  degraded: "诚实降级",
};

export default function Report({ report, onClose }: { report: LabReport; onClose: () => void }) {
  const sources = new Map(report.sources.map((s) => [s.source_id, s]));
  const refLabel = (id: string) => {
    const s = sources.get(id);
    return s ? `${SOURCE_KIND_LABEL[s.kind]} · ${s.ref}` : id;
  };
  const summary = report.outcome_summary;

  return (
    <section className="report" aria-label="实验报告">
      <header className="report__head">
        <div>
          <h2>实验报告</h2>
          <p className="muted tiny">
            report_id {report.report_id} · 规则集 {report.ruleset_version} · 数值原样取自求解与时间轴，不加工
          </p>
        </div>
        <button type="button" onClick={onClose} aria-label="关闭报告">关闭</button>
      </header>

      <div className="report__summary">
        <span>出口汇总：</span>
        <span className="report__tag">定量解 {summary.solved}</span>
        <span className="report__tag">无明显变化 {summary.no_significant_change}</span>
        <span className={`report__tag ${summary.degraded ? "report__tag--warn" : ""}`}>
          降级 {summary.degraded}
        </span>
        <span>共 {summary.total} 项快照</span>
      </div>

      <div className="report__grid">
        <div className="report__block">
          <h3>① 操作序列</h3>
          <ol className="report__ops">
            {report.operations.map((op) => (
              <li key={op.seq}>
                <strong>{KIND_LABEL[op.kind]}</strong>
                <span className="muted tiny">
                  {op.container_id}
                  {op.apparatus_id ? ` · ${op.apparatus_id}` : ""}
                  {op.compound_id ? ` · ${op.compound_id}` : ""}
                  {op.volume_L != null ? ` · ${op.volume_L} L` : ""}
                  {op.addition_order ? ` · ${op.addition_order}` : ""}
                </span>
              </li>
            ))}
            {report.operations.length === 0 && <li className="muted">无操作记录</li>}
          </ol>
        </div>

        <div className="report__block">
          <h3>② 物种快照</h3>
          {report.snapshots.map((snap, i) => (
            <div key={`${snap.container_id}-${i}`} className="report__snap">
              <div className="report__snap-head">
                <span className={`report__outcome report__outcome--${snap.outcome}`}>
                  {OUTCOME_LABEL[snap.outcome] ?? snap.outcome}
                </span>
                <span className="muted tiny">{snap.container_id}</span>
              </div>
              {snap.ph != null && <div>pH <strong>{snap.ph}</strong></div>}
              {snap.ionic_strength != null && <div>离子强度 <strong>{snap.ionic_strength}</strong></div>}
              {snap.temperature_K != null && <div>温度 <strong>{snap.temperature_K} K</strong></div>}
              {snap.confidence != null && <div className="muted tiny">置信度 {snap.confidence}</div>}
              {snap.reason && <div className="report__reason">原因：{snap.reason}</div>}
              <table className="report__species">
                <thead><tr><th>物种</th><th>浓度 mol/L</th></tr></thead>
                <tbody>
                  {(snap.species ?? []).map((s) => (
                    <tr key={s.name}><td>{s.name}</td><td>{s.concentration_mol_l}</td></tr>
                  ))}
                </tbody>
              </table>
              <div className="muted tiny">来源：{refLabel(snap.source_ref)}</div>
            </div>
          ))}
        </div>

        <div className="report__block">
          <h3>③ 曲线</h3>
          {report.curves.map((curve, i) => (
            <div key={`${curve.species}-${i}`} className="report__curve">
              <div className="report__curve-head">
                <strong>{curve.species}</strong>
                <span className="muted tiny">{curve.points.length} 点 · {refLabel(curve.source_ref)}</span>
              </div>
              <Sparkline points={curve.points} />
            </div>
          ))}
          {report.curves.length === 0 && <p className="muted">无曲线</p>}
        </div>

        <div className="report__block">
          <h3>④ 反应式</h3>
          <ul className="report__rxns">
            {report.reactions.map((rxn) => (
              <li key={rxn.rule_id}>
                <code>{rxn.equation}</code>
                <span className="muted tiny">
                  {rxn.rule_id}{rxn.confidence_level ? ` · ${rxn.confidence_level}` : ""}
                  {" · "}{refLabel(rxn.source_ref)}
                </span>
              </li>
            ))}
            {report.reactions.length === 0 && <li className="muted">当前出口无可引用反应式</li>}
          </ul>
        </div>
      </div>

      <div className="report__block">
        <h3>⑤ 来源锚点</h3>
        <ul className="report__sources">
          {report.sources.map((s) => (
            <li key={s.source_id}>
              <strong>{SOURCE_KIND_LABEL[s.kind]}</strong>
              <span className="muted tiny">{s.ref}</span>
              {s.sha256 && <code className="report__hash">{s.sha256}</code>}
              {s.snapshot_date && <span className="muted tiny">快照 {s.snapshot_date}</span>}
              {s.note && <span className="muted tiny">{s.note}</span>}
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}

/** 只读迷你曲线：纯 SVG 折线，不插值、不改写数值，仅按点映射坐标。 */
function Sparkline({ points }: { points: [number, number][] }) {
  if (points.length < 2) return <div className="muted tiny">数据点不足</div>;
  const xs = points.map((p) => p[0]);
  const ys = points.map((p) => p[1]);
  const minX = Math.min(...xs), maxX = Math.max(...xs);
  const minY = Math.min(...ys), maxY = Math.max(...ys);
  const spanX = maxX - minX || 1, spanY = maxY - minY || 1;
  const W = 100, H = 30;
  const d = points.map((p, i) => {
    const x = ((p[0] - minX) / spanX) * W;
    const y = H - ((p[1] - minY) / spanY) * H;
    return `${i === 0 ? "M" : "L"}${x.toFixed(2)},${y.toFixed(2)}`;
  }).join(" ");
  return (
    <svg className="report__spark" viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="none" aria-hidden="true">
      <path d={d} fill="none" stroke="#2f6b4f" strokeWidth="1" />
    </svg>
  );
}
