import { useEffect, useRef, useState } from "react";
import { Application, Container, Graphics } from "pixi.js";
import { initView, transformDirectives, viewBackend, type Appearance } from "@st/wasm-view";
import type { PhenomenonDirective } from "@st/protocol";

interface Props {
  /** 当前容器要呈现的现象指令（live / ws / timeline 同源）。 */
  directives: PhenomenonDirective[];
  /** 是否有定量解：无解不出象。 */
  solvable: boolean;
  label?: string;
}

const VW = 360;
const VH = 260;
const VESSEL_X = 110;
const VESSEL_W = 140;
const VESSEL_TOP = 50;
const VESSEL_BOTTOM = 220;
const VESSEL_H = VESSEL_BOTTOM - VESSEL_TOP;

/** PixiJS 容器绘制层：只认表现参数（st.appearance.v1），与求解完全解耦。 */
export default function VesselView({ directives, solvable, label }: Props) {
  const hostRef = useRef<HTMLDivElement | null>(null);
  const appRef = useRef<Application | null>(null);
  const layerRef = useRef<Container | null>(null);
  const appearanceRef = useRef<Appearance | null>(null);
  const splashRef = useRef<{ born: number; intensity: number } | null>(null);
  const [backend, setBackend] = useState<"wasm" | "ts" | "init">("init");

  // 变换器初始化一次（WASM 优先，失败降级 TS）。
  useEffect(() => {
    let cancelled = false;
    void initView().then((r) => { if (!cancelled) setBackend(r.backend); });
    return () => { cancelled = true; };
  }, []);

  // 指令变化 → 纯同步变换为表现参数（不触发任何求解）。
  useEffect(() => {
    appearanceRef.current = solvable && directives.length
      ? transformDirectives(directives)
      : null;
    if (directives.some((d) => d.type === "splash") && solvable) {
      const s = directives.find((d) => d.type === "splash");
      splashRef.current = { born: performance.now(), intensity: s?.intensity ?? 0.5 };
    } else {
      splashRef.current = null;
    }
  }, [directives, solvable]);

  // PixiJS 应用初始化（固定 60fps 帧循环，与求解异步请求互不阻塞）。
  useEffect(() => {
    const host = hostRef.current;
    if (!host) return;
    let disposed = false;
    const app = new Application();
    appRef.current = app;

    void app.init({
      width: VW, height: VH, backgroundAlpha: 0, antialias: true,
      resolution: Math.min(window.devicePixelRatio || 1, 2), autoDensity: true,
    }).then(() => {
      if (disposed) { app.destroy(true); return; }
      host.appendChild(app.canvas);
      const layer = new Container();
      layerRef.current = layer;
      app.stage.addChild(layer);

      // 帧循环只做绘制：读 appearanceRef，不调用求解、不发起请求。
      app.ticker.add(() => {
        const g = layer.getChildAt(0) as Graphics | undefined;
        if (!g) return;
        g.clear();
        drawVessel(g, appearanceRef.current, splashRef.current, performance.now());
      });
      const g = new Graphics();
      layer.addChild(g);
    }).catch(() => {
      // 图形后端不可用时保留 DOM 说明，不影响其余面板。
    });

    return () => {
      disposed = true;
      layerRef.current = null;
      appRef.current = null;
      if (app.renderer) app.destroy(true, { children: true });
    };
  }, []);

  return (
    <section className="panel panel--vessel" aria-label="容器内现象">
      <div className="panel__head">
        <div>
          <h2>容器内现象</h2>
          <p className="muted tiny">{label ?? "实验台"} · 表现由 st.phenomenon.v1 指令驱动</p>
        </div>
        <span className="mono tiny" title="表现参数变换后端">渲染:{backend === "init" ? "…" : backend}</span>
      </div>
      <div ref={hostRef} className="vessel-host" />
      {!solvable && <p className="muted tiny">当前无定量解：不出象（诚实降级）。</p>}
    </section>
  );
}

/** 纯绘制：容器轮廓 + 液体（wasm-view 颜色）+ 温升/飞溅效果。 */
function drawVessel(
  g: Graphics,
  appearance: Appearance | null,
  splash: { born: number; intensity: number } | null,
  now: number,
): void {
  // 容器（简笔：玻璃烧杯轮廓）。
  g.rect(VESSEL_X, VESSEL_TOP, VESSEL_W, VESSEL_H).stroke({ width: 2, color: 0x5b6b63 });
  g.moveTo(VESSEL_X - 8, VESSEL_TOP).lineTo(VESSEL_X + 8, VESSEL_TOP).stroke({ width: 2, color: 0x5b6b63 });
  g.moveTo(VESSEL_X + VESSEL_W - 8, VESSEL_TOP).lineTo(VESSEL_X + VESSEL_W + 8, VESSEL_TOP)
    .stroke({ width: 2, color: 0x5b6b63 });

  if (!appearance) return;

  const [r, gr, b, a] = appearance.liquid.rgba;
  // PixiJS 颜色为 0xRRGGBB（alpha 走 fill.alpha），勿把 alpha 拼进 32 位色值导致溢出负数。
  const rgb = (Math.round(r) << 16) | (Math.round(gr) << 8) | Math.round(b);
  const fillH = VESSEL_H * 0.42;
  const fillY = VESSEL_BOTTOM - fillH;
  if (a > 0) {
    g.rect(VESSEL_X + 2, fillY, VESSEL_W - 4, fillH - 2).fill({ color: rgb, alpha: 0.85 * a });
    g.rect(VESSEL_X + 2, fillY, VESSEL_W - 4, 3).fill({ color: 0xffffff, alpha: 0.35 });
  }

  for (const eff of appearance.effects) {
    if (eff.type === "temperature_change") {
      const heat = Math.min(1, eff.intensity);
      const color = eff.hot ? 0xd9534f : 0x4a90d9;
      for (let i = 0; i < 3; i++) {
        const x = VESSEL_X + VESSEL_W / 2 + (i - 1) * 18;
        g.circle(x, fillY - 8 - heat * 6, 2 + heat * 2)
          .fill({ color, alpha: 0.25 + heat * 0.4 });
      }
    }
  }

  // 飞溅：由 splash 指令的 intensity 驱动，短时动画（表现近似，不进事实层）。
  const sp = splash;
  if (sp) {
    const age = (now - sp.born) / 700;
    if (age < 1) {
      const rise = age * 40 * (0.6 + sp.intensity);
      for (let i = 0; i < 6; i++) {
        const dx = (i - 2.5) * 9 * (0.7 + sp.intensity);
        const x = VESSEL_X + VESSEL_W / 2 + dx;
        const y = VESSEL_BOTTOM - 12 - rise + (i % 2) * 6;
        g.circle(x, y, 2.5 + sp.intensity * 2).fill({ color: 0xd9534f, alpha: 1 - age });
      }
    }
  }
}
