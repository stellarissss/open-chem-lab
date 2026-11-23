import type { PanelData } from "./lab";

const OUTCOME_LABEL: Record<string, string> = {
  solved: "已求解",
  no_significant_change: "无明显变化",
  degraded: "降级结果",
};

interface Props {
  data: PanelData | null;
  systemLabel: string;
  loading: boolean;
  error: string | null;
  timestamp: number | null;
}

/** 物种面板：定量 + 诚实提示。数值原样呈现，不加工、不美化。 */
export default function SpeciesPanel({ data, systemLabel, loading, error, timestamp }: Props) {
  if (loading && !data) {
    return <section className="panel panel--species"><p className="muted">正在读取求解数据…</p></section>;
  }
  if (error && !data) {
    return <section className="panel panel--species"><p className="error-text">读取失败：{error}</p></section>;
  }
  if (!data) {
    return <section className="panel panel--species"><p className="muted">尚无物种数据。</p></section>;
  }

  const degraded = data.outcome === "degraded";
  const noChange = data.outcome === "no_significant_change";

  return (
    <section className="panel panel--species" aria-label="物种面板">
      <div className="panel__head">
        <div>
          <h2>物种面板</h2>
          <p className="muted">{systemLabel} · 容器 {data.containerId}</p>
        </div>
        <span className={`outcome outcome--${data.outcome}`}>
          {OUTCOME_LABEL[data.outcome] ?? data.outcome}
        </span>
      </div>

      {degraded && (
        <p className="notice notice--warn">
          数值或活度模型超出适用域，此为诚实降级结果
          {data.confidence != null && `（置信度 ${(data.confidence * 100).toFixed(0)}%）`}，
          不作为定量科学结论。
        </p>
      )}
      {noChange && (
        <p className="notice">当前条件下，事实层覆盖范围内无明显变化（合法结论）。</p>
      )}

      <div className="metrics">
        <div className="metric"><span>pH（活度口径）</span><strong>{data.ph.toFixed(4)}</strong></div>
        <div className="metric"><span>离子强度</span><strong>{data.ionicStrength.toFixed(4)}</strong><small>mol/L</small></div>
        <div className="metric"><span>温度</span><strong>{data.temperatureK != null ? data.temperatureK.toFixed(2) : "—"}</strong><small>K</small></div>
        <div className="metric"><span>回放时刻</span><strong>{timestamp != null ? `${(timestamp / 1000).toFixed(0)}s` : "—"}</strong></div>
      </div>

      <h3>物种分布</h3>
      <table className="species-table">
        <thead>
          <tr><th>物种</th><th>浓度 (mol/L)</th><th>活度</th><th>相态</th></tr>
        </thead>
        <tbody>
          {data.species.length === 0 && (
            <tr><td colSpan={4} className="muted">无物种数据（{OUTCOME_LABEL[data.outcome] ?? data.outcome}）</td></tr>
          )}
          {data.species.map((s) => (
            <tr key={s.name}>
              <td className="mono">{s.name}</td>
              <td className="num">{s.concentration.toExponential(4)}</td>
              <td className="num">{s.activity != null ? s.activity.toExponential(4) : "—"}</td>
              <td>{s.phase ?? "aq"}</td>
            </tr>
          ))}
        </tbody>
      </table>

      <h3>隐藏反应 <span className="muted">· 不可见但真实发生</span></h3>
      {data.hiddenReactions.length === 0 ? (
        <p className="muted">本帧无隐藏反应引用。</p>
      ) : (
        <ul className="chips">
          {data.hiddenReactions.map((id) => <li key={id} className="chip mono">{id}</li>)}
        </ul>
      )}

      <h3>现象成因溯源 <span className="muted">· st.phenomenon.v1 trigger</span></h3>
      {data.phenomena.length === 0 ? (
        <p className="muted">本帧未派生现象指令（无定量解时不编造现象）。</p>
      ) : (
        <ul className="trace">
          {data.phenomena.map((d) => (
            <li key={d.directive_id}>
              <span className="mono">{d.type}</span>
              <span className="muted">
                {d.trigger?.observable ?? "—"} · {d.trigger?.derivation ?? "—"}
                {d.physics?.ph != null && ` · pH=${Number(d.physics.ph).toFixed(4)}`}
                {d.physics?.pka != null && ` · pKa=${d.physics.pka}`}
                {d.physics?.indicator_ratio != null && ` · [In⁻]/[HIn]=${Number(d.physics.indicator_ratio).toFixed(3)}`}
                {d.physics?.temperature_K != null && ` · T=${d.physics.temperature_K}K`}
              </span>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
