import { useEffect } from "react";
import { useHealth } from "./health";
import "./style.css";

export default function App() {
  const { status, version, protocol, uptimeMs, checkedAt, refresh } = useHealth();

  useEffect(() => {
    void refresh();
    const id = window.setInterval(() => void refresh(), 5000);
    return () => window.clearInterval(id);
  }, [refresh]);

  const label =
    status === "ok" ? "后端已连接" : status === "error" ? "后端不可用" : "检测中…";

  return (
    <div className="shell">
      <header className="topbar">
        <span className="brand">ST Crucible</span>
        <span className={`badge badge--${status}`}>● {label}</span>
      </header>
      <main className="stage">
        <section className="bench" aria-label="实验台">
          <p className="bench__hint">实验台骨架 · 器材与求解将在后续切片接入</p>
        </section>
        <aside className="inspector" aria-label="状态面板">
          <h2>系统状态</h2>
          <dl>
            <dt>服务版本</dt><dd>{version}</dd>
            <dt>协议</dt><dd>{protocol}</dd>
            <dt>运行时长</dt><dd>{uptimeMs == null ? "—" : `${(uptimeMs / 1000).toFixed(0)}s`}</dd>
            <dt>最近检测</dt><dd>{checkedAt == null ? "—" : new Date(checkedAt).toLocaleTimeString()}</dd>
          </dl>
        </aside>
      </main>
      <footer className="footer">
        现实操作勿模仿 · 数值零错红线 · LGPL-3.0
      </footer>
    </div>
  );
}
