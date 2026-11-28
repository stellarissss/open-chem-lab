// GENERATED from schemas/container_state.v1.schema.json — DO NOT EDIT. Run pnpm build:types.

/**
 * st.container_state.v1 — 容器实时状态定向推送（008）：gateway 经 WS 按 container_id 定向推送，替换旧 phenomenon 全局广播。状态变化驱动求解的结果流，多容器现象不串扰。数值来自求解、原样转发不加工。
 */
export interface ContainerState {
  schema_version: "st.container_state.v1";
  /**
   * 定向推送键：仅订阅该 container_id 的客户端收到
   */
  container_id: string;
  /**
   * 该容器的 st.solution_speciation.v1 求解结果（原样转发，含三态出口）
   */
  speciation: {};
  /**
   * 该容器派生的 st.phenomenon.v1 现象指令（只含本容器）
   */
  directives: {}[];
  /**
   * 本次求解耗时 ms（反馈真实开销，非虚标）
   */
  solve_latency_ms?: number;
  /**
   * 求解器版本，供缓存失效与证据自证
   */
  solver_version: string;
  /**
   * 规则集版本（可选，与 bench_world 对齐）
   */
  ruleset_version?: string;
}
