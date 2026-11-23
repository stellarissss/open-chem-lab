import { useEffect } from "react";
import type { SpeciationTimeline } from "@st/protocol";
import { SYSTEM_LABELS, useLab, type ScanSystem } from "./lab";

interface Props {
  timeline: SpeciationTimeline | null;
}

/** pH 曲线：直接取 timeline.curves 中 species=ph 的数据点，不自造数值。 */
function PhCurve({ timeline, frameIndex }: Props & { frameIndex: number }) {
  const curve = timeline?.curves?.find((c) => c.species === "ph");
  const points = curve?.points ?? [];
  if (points.length < 2) return <p className="muted">暂无 pH 曲线。</p>;

  const phs = points.map((p) => p[1]);
  const lo = Math.min(...phs);
  const hi = Math.max(...phs);
  const span = hi - lo || 1;
  const W = 320;
  const H = 96;
  const x = (i: number) => (i / (points.length - 1)) * W;
  const y = (ph: number) => H - ((ph - lo) / span) * H;
  const path = points.map((p, i) => `${i === 0 ? "M" : "L"}${x(i).toFixed(1)},${y(p[1]).toFixed(1)}`).join(" ");
  const cx = x(Math.min(frameIndex, points.length - 1));
  const cy = y(points[Math.min(frameIndex, points.length - 1)]?.[1] ?? 0);

  return (
    <svg className="ph-curve" viewBox={`0 0 ${W} ${H}`} role="img" aria-label="pH 随滴定进程变化曲线">
      <path d={path} fill="none" stroke="#2f6b4f" strokeWidth={2} vectorEffect="non-scaling-stroke" />
      <line x1={cx} y1={0} x2={cx} y2={H} stroke="#b8860b" strokeDasharray="3 3" />
      <circle cx={cx} cy={cy} r={4} fill="#b8860b" />
    </svg>
  );
}

/** 时间轴回放：关键帧定位 + 曲线；回放只读缓存的时间轴，不重复求解。 */
export default function Timeline({ timeline }: Props) {
  const { system, frameIndex, playing, setSystem, setFrame, togglePlay } = useLab();
  const total = timeline?.keyframes.length ?? 0;

  useEffect(() => {
    if (!playing || total === 0) return;
    const id = window.setInterval(() => {
      const { frameIndex: cur, setFrame: set } = useLab.getState();
      if (cur + 1 >= total) {
        useLab.getState().togglePlay();
        return;
      }
      set(cur + 1);
    }, 900);
    return () => window.clearInterval(id);
  }, [playing, total, setFrame]);

  return (
    <section className="panel panel--timeline" aria-label="时间轴回放">
      <div className="panel__head">
        <h2>时间轴回放</h2>
        <span className="muted">{total} 关键帧 · 稳态复用不重复求解</span>
      </div>

      <div className="system-tabs" role="tablist" aria-label="滴定体系">
        {(Object.keys(SYSTEM_LABELS) as ScanSystem[]).map((key) => (
          <button
            key={key}
            type="button"
            role="tab"
            aria-selected={system === key}
            className={system === key ? "tab tab--active" : "tab"}
            onClick={() => setSystem(key)}
          >
            {SYSTEM_LABELS[key]}
          </button>
        ))}
      </div>

      <PhCurve timeline={timeline} frameIndex={frameIndex} />

      <div className="scrubber">
        <button type="button" onClick={togglePlay} disabled={total === 0}>
          {playing ? "暂停" : "回放"}
        </button>
        <input
          type="range"
          min={0}
          max={Math.max(0, total - 1)}
          value={frameIndex}
          disabled={total === 0}
          onChange={(e) => setFrame(Number(e.target.value))}
          aria-label="关键帧位置"
        />
        <span className="num mono">{total ? `${frameIndex + 1}/${total}` : "—"}</span>
      </div>
      <p className="muted tiny">
        回放刻度为仿真相对时间（每帧 1s），只服务观察节奏，不代表真实反应速率。
      </p>
    </section>
  );
}
