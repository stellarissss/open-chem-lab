import { useEffect, useRef } from "react";
import {
  detectNearby, geometryOf, itemFill, liquidColorOf, liquidRotation,
  pourTick, useLab, type BenchItem,
} from "./lab";

/** 写实 2D 实验台：器材/试剂瓶自由拖放、临近浮动按钮、倾角倾倒（008 核心）。 */
export default function BenchView() {
  const {
    items, reagents, apparatus, mode, nearby, pourSourceId, pourTargetId,
    placeFromRack, startDrag, moveDrag, endDrag, select, beginPour,
    updatePourTilt, endPour, closeItem, clearBench, loadCatalog, connectWs,
  } = useLab();
  const stageRef = useRef<HTMLDivElement | null>(null);
  const rafRef = useRef<number | null>(null);
  const lastTsRef = useRef<number>(0);

  useEffect(() => { void loadCatalog(); }, [loadCatalog]);
  useEffect(() => connectWs(), [connectWs]);

  // 台面指针移动：拖动 / 倾倒两类模式
  const onStageMove = (e: React.PointerEvent<HTMLDivElement>) => {
    const rect = stageRef.current?.getBoundingClientRect();
    if (!rect) return;
    const px = e.clientX - rect.left, py = e.clientY - rect.top;
    const s = useLab.getState();
    if (s.mode === "dragging") s.moveDrag(px, py);
    else if (s.mode === "pouring") s.updatePourTilt(px, py);
  };

  // 倾倒帧循环：按倾角流速积分，把源容器内容按比例转移到目标容器。
  useEffect(() => {
    if (mode !== "pouring" || !pourSourceId || !pourTargetId) {
      if (rafRef.current != null) cancelAnimationFrame(rafRef.current);
      rafRef.current = null;
      return;
    }
    lastTsRef.current = performance.now();
    const frame = (ts: number) => {
      const dt = (ts - lastTsRef.current) / 1000;
      lastTsRef.current = ts;
      const s = useLab.getState();
      if (s.mode !== "pouring" || !s.pourSourceId || !s.pourTargetId) return;
      const src = s.items.find((i) => i.instance_id === s.pourSourceId);
      const dst = s.items.find((i) => i.instance_id === s.pourTargetId);
      if (!src || !dst || src.contents.length === 0) { rafRef.current = requestAnimationFrame(frame); return; }

      const flow = pourTick(
        { volume_mL: src.volume_mL, tilt_deg: src.rotation },
        geometryOf(src), dt,
      );
      if (flow.transferred_mL > 0) {
        const ratio = flow.transferred_mL / src.volume_mL;
        const moved = src.contents.map((c) => ({
          ...c,
          volume_L: c.volume_L * ratio,
        }));
        const remaining = src.contents.map((c) => ({ ...c, volume_L: c.volume_L * (1 - ratio) }));
        useLab.setState({
          items: s.items.map((it) => {
            if (it.instance_id === src.instance_id) {
              return { ...it, volume_mL: it.volume_mL - flow.transferred_mL, contents: remaining };
            }
            if (it.instance_id === dst.instance_id) {
              const merged = mergeContents(it.contents, moved);
              return { ...it, volume_mL: it.volume_mL + flow.transferred_mL, contents: merged };
            }
            return it;
          }),
        });
      }
      rafRef.current = requestAnimationFrame(frame);
    };
    rafRef.current = requestAnimationFrame(frame);
    return () => { if (rafRef.current != null) cancelAnimationFrame(rafRef.current); };
  }, [mode, pourSourceId, pourTargetId]);

  // 计算临近关系（取第一对足够近的容器）
  const nearbyAction = nearby ?? deriveNearby(items);

  return (
    <section className="panel panel--bench" aria-label="自由实验台">
      <div className="panel__head">
        <div>
          <h2>自由实验台</h2>
          <p className="muted tiny">
            从架子拖出器材/试剂 → 靠近另一容器点倾倒图标 → 移动鼠标控制倾角。
            WS {useLab.getState().wsStatus} · 规则集 {useLab.getState().rulesetVersion}
          </p>
        </div>
        <button type="button" onClick={clearBench}>清空台面</button>
      </div>

      <div className="bench-layout">
        <aside className="rack" aria-label="器材与试剂架">
          <h3>试剂架 <span className="muted tiny">ruleset 驱动</span></h3>
          <div className="rack__grid">
            {reagents.map((r) => (
              <button key={r.compound_id} type="button" className="rack__item"
                onClick={() => placeFromRack("reagent", r.compound_id)}
                title={`${r.formula} · ${r.concentration_mol_L} mol/L${r.applicability ? ` · ${r.applicability}` : ""}`}>
                <span className="rack__swatch" style={{ background: hexColor(r.solution_color) }} />
                <span className="rack__label">{r.label}</span>
                <span className="mono tiny">{r.concentration_mol_L} M{r.hazard ? " ⚠" : ""}</span>
              </button>
            ))}
          </div>
          <h3>器材架</h3>
          <div className="rack__grid">
            {apparatus.filter((a) => ["beaker", "graduated_cylinder", "dropper"].includes(a.type)).map((a) => (
              <button key={a.apparatus_id} type="button" className="rack__item"
                onClick={() => placeFromRack("apparatus", a.apparatus_id)}>
                <span className="rack__label">{a.names.zh}</span>
                <span className="mono tiny">{a.capacity_mL ?? "—"} mL</span>
              </button>
            ))}
          </div>
        </aside>

        <div
          ref={stageRef}
          className={`bench-stage ${mode === "pouring" ? "bench-stage--pouring" : ""}`}
          onPointerMove={onStageMove}
          onPointerUp={() => { if (useLab.getState().mode === "dragging") endDrag(); }}
          onPointerLeave={() => { if (useLab.getState().mode === "dragging") endDrag(); }}
        >
          {items.map((item) => (
            <BenchPiece
              key={item.instance_id}
              item={item}
              selected={useLab.getState().selectedId === item.instance_id}
              pouring={item.instance_id === pourSourceId}
              onPointerDown={(e) => {
                e.stopPropagation();
                if (useLab.getState().mode === "pouring") return;
                select(item.instance_id);
                const rect = stageRef.current?.getBoundingClientRect();
                if (rect) startDrag(item.instance_id, e.clientX - rect.left, e.clientY - rect.top);
              }}
              onClose={() => closeItem(item.instance_id)}
            />
          ))}

          {/* 临近交互范式：两容器足够近 → 交界浮动操作按钮（缩略图） */}
          {nearbyAction && mode === "idle" && (
            <button
              type="button"
              className="nearby-action"
              style={{ left: nearbyAction.x, top: nearbyAction.y }}
              title="倾倒：点击进入倾角控制，移动鼠标控制容器倾角"
              onPointerDown={(e) => e.stopPropagation()}
              onClick={() => beginPour(nearbyAction.sourceId, nearbyAction.targetId)}
            >
              <span aria-hidden="true">⤓</span>
              <small>倾倒</small>
            </button>
          )}

          {mode === "pouring" && (
            <div className="pour-hint">
              倾倒中 · 移动鼠标改变倾角（液面保持世界水平） ·
              <button type="button" onClick={() => void endPour()}>结束倾倒并求解</button>
            </div>
          )}
        </div>
      </div>
    </section>
  );
}

/** 合并内容物：同 compound_id 合并体积与浓度加权平均（浓度取物质的量守恒）。 */
function mergeContents(
  base: BenchItem["contents"], moved: BenchItem["contents"],
): BenchItem["contents"] {
  const out = base.map((c) => ({ ...c }));
  for (const m of moved) {
    const found = out.find((c) => c.compound_id === m.compound_id);
    if (found) {
      const n1 = found.concentration_mol_L * found.volume_L;
      const n2 = m.concentration_mol_L * m.volume_L;
      const total = found.volume_L + m.volume_L;
      found.concentration_mol_L = total > 0 ? (n1 + n2) / total : found.concentration_mol_L;
      found.volume_L = total;
    } else {
      out.push({ ...m });
    }
  }
  return out;
}

function deriveNearby(items: BenchItem[]) {
  for (let i = 0; i < items.length; i++) {
    for (let j = i + 1; j < items.length; j++) {
      const action = detectNearby(items[i]!, items[j]!);
      if (action) return action;
    }
  }
  return null;
}

function hexColor(name: string | null): string {
  if (!name || name === "无色") return "rgba(255,255,255,0.7)";
  if (/red|红|pink|粉/.test(name)) return "#e8a0a8";
  if (/yellow|黄/.test(name)) return "#e8d48a";
  return "rgba(210,230,220,0.8)";
}

/** 单件器材：容器旋转 rotate(θ)，液面层反向 rotate(−θ) 保持世界水平（物理裁决）。 */
function BenchPiece({ item, selected, pouring, onPointerDown, onClose }: {
  item: BenchItem;
  selected: boolean;
  pouring: boolean;
  onPointerDown: (e: React.PointerEvent<HTMLDivElement>) => void;
  onClose: () => void;
}) {
  const fill = itemFill(item);
  const liquid = liquidColorOf(item);
  const counterRot = liquidRotation(item);
  return (
    <div
      className={`bench-piece ${selected ? "bench-piece--selected" : ""} ${pouring ? "bench-piece--pouring" : ""}`}
      style={{ left: item.x, top: item.y, width: item.w, height: item.h }}
      onPointerDown={onPointerDown}
      data-instance={item.instance_id}
    >
      <div className="bench-piece__vessel" style={{ transform: `rotate(${item.rotation}deg)` }}>
        <img src={item.asset} alt="" draggable={false} />
        {/* 液面层：反向旋转抵消容器倾角 → 世界坐标水平；clip-path 约束到容器轮廓 */}
        {liquid && fill > 0 && (
          <div
            className="bench-piece__liquid"
            style={{
              height: `${Math.max(6, fill * 78)}%`,
              background: liquid,
              transform: `rotate(${counterRot}deg)`,
              transformOrigin: "center bottom",
            }}
          />
        )}
      </div>
      <div className="bench-piece__meta">
        <span className="bench-piece__label">{item.label}</span>
        {item.volume_mL > 0 && <span className="mono tiny">{item.volume_mL.toFixed(0)} mL</span>}
        <button type="button" className="bench-piece__close" onPointerDown={(e) => e.stopPropagation()} onClick={onClose} title="移走">×</button>
      </div>
    </div>
  );
}
