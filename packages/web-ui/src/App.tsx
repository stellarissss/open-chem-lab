import { useEffect } from "react";
import { useHealth } from "./health";
import SpeciesPanel from "./SpeciesPanel";
import BenchView from "./BenchView";
import VesselView from "./VesselView";
import { useLab } from "./lab";
import type { PhenomenonDirective } from "@st/protocol";
import "./style.css";

/** 自由实验台主界面（008 范式重构）：台面手动操作 + 物种面板 + 现象渲染，无预设按钮/配比/时间轴/报告。 */
export default function App() {
  const { status, version, protocol, uptimeMs, refresh } = useHealth();
  const { selectedPanel, loading, error, opCount, items, selectedId } = useLab();

  useEffect(() => {
    void refresh();
    const id = window.setInterval(() => void refresh(), 5000);
    return () => window.clearInterval(id);
  }, [refresh]);

  const label = status === "ok" ? "后端已连接" : status === "error" ? "后端不可用" : "检测中…";
  const selectedItem = items.find((i) => i.instance_id === selectedId);
  const directives: PhenomenonDirective[] = selectedPanel?.phenomena ?? [];
  const solvable = selectedPanel?.outcome === "solved";

  return (
    <div className="shell">
      <header className="topbar">
        <span className="brand">ST Crucible · 自由实验台</span>
        <span className={`badge badge--${status}`}>● {label}</span>
        <span className="topbar__meta">操作事件 {opCount}</span>
      </header>

      <main className="stage">
        <div className="stage__left">
          <BenchView />
          <VesselView directives={directives} solvable={solvable}
            label={selectedItem ? `容器 ${selectedItem.label}` : "未选中容器"} />
          <SpeciesPanel
            data={selectedPanel}
            systemLabel={selectedItem ? `容器 ${selectedItem.label} · 实时求解` : "点选容器查看"}
            loading={loading}
            error={error}
            timestamp={selectedPanel?.timestampMs ?? null}
          />
        </div>

        <aside className="inspector" aria-label="状态面板">
          <h2>系统状态</h2>
          <dl>
            <dt>服务版本</dt><dd>{version}</dd>
            <dt>现象协议</dt><dd>{protocol}</dd>
            <dt>运行时长</dt><dd>{uptimeMs == null ? "—" : `${(uptimeMs / 1000).toFixed(0)}s`}</dd>
          </dl>

          <h2>玩法说明</h2>
          <ol className="help-list">
            <li>从左侧架子点选试剂瓶/器材，放到台面空位。</li>
            <li>把两个容器拖到足够近，交界处浮现「倾倒」按钮。</li>
            <li>点按钮进入倾角控制，移动鼠标让容器倾斜——倾角越大流得越快，液面始终水平。</li>
            <li>点「结束倾倒并求解」查看物种面板与现象；可继续叠加操作。</li>
          </ol>
          <p className="notice">
            自由探索：没有预设配比、没有固定顺序、没有体积滑条。倒什么、倒多少、什么顺序，全由你的操作决定；后果如实呈现。
          </p>

          <h2>诚实计算</h2>
          <p className="muted tiny">
            所有数值来自实时求解；覆盖外如实返回「无明显变化」，不虚构结论。倾倒体积来自物理积分，不是预设值。
          </p>
        </aside>
      </main>

      <footer className="footer">
        现实操作勿模仿 · 自由探索 · 诚实计算 · LGPL-3.0
      </footer>
    </div>
  );
}
