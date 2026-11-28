/**
 * benchPhysics.ts — 倾角倾倒的操作物理（008）
 *
 * 职责边界：本模块只做「玩家手势 → 容器倾角 → 流速 → 转移体积」的**操作层物理**，
 * 不碰任何化学数值（pH/浓度/产物一律由 gateway 求解，见 lab.ts）。倾倒体积是操作
 * 产生的物理量，不是预设配比——这是它与旧范式「体积滑条」的本质区别。
 *
 * 物理口径（已裁决，写入 01 §一）：
 * - 倾角 = 指针相对容器中心的方位角（正上方为 0°，向右为正）。
 * - 液面世界水平：表现层容器 rotate(θ)、液面层 rotate(−θ) 抵消（本模块只给角度）。
 * - 临界角：倾斜到液面触及瓶口才流出；填充越满临界角越小（来自容器几何）。
 * - 流速：托里拆利 v=√(2gh) × 开口有效面积 Cd·A，对时间积分得体积；单调、来源可追溯。
 * - 黏度为表现层近似，暂不引入（不虚构物性数值）。
 *
 * 参数 g（重力加速度）、Cd（流量系数）为物理常数、带来源，不进化学事实层、不冒充求解结果。
 */

/** 重力加速度 m/s²（NIST 标准值，物理常数非化学数值）。 */
export const G_M_S2 = 9.80665;
/** 孔口流量系数 Cd（薄壁孔口工程常用近似 0.61，表现层物理近似、标注来源）。 */
export const DISCHARGE_COEFF = 0.61;

/** 器材几何（mm）：来自 apparatus 卡容量与写实 SVG 比例，用于倾角物理。 */
export interface VesselGeometry {
  /** 容器口径（瓶口宽度）mm */
  mouthWidth_mm: number;
  /** 容器有效高度 mm */
  height_mm: number;
  /** 满容量 mL（= cm³），来自 apparatus 卡 capacity_mL */
  capacity_mL: number;
}

/** 容器操作态：填充体积 + 倾角。 */
export interface PourState {
  /** 当前体积 mL */
  volume_mL: number;
  /** 容器倾角（度，正为向右倾） */
  tilt_deg: number;
}

/** 单次倾倒积分结果。 */
export interface PourFlow {
  /** 是否已越过临界角、开始流出 */
  pouring: boolean;
  /** 临界角（度） */
  criticalAngle_deg: number;
  /** 瞬时流速 mL/s */
  flow_mL_s: number;
  /** 本次积分转移体积 mL */
  transferred_mL: number;
  /** 有效液柱高 mm（流速物理输入，供面板溯源） */
  head_mm: number;
}

const RAD = Math.PI / 180;

/**
 * 指针相对容器中心的方位角 → 容器倾角（度）。
 * 约定：指针在容器正上方 = 0°；向右 = 正值；向左 = 负值。
 * 用 atan2(dx, −dy)：正上方 (dx=0, −dy>0)→0°，正右 (dx>0,−dy=0)→+90°。
 */
export function tiltFromPointer(
  centerX: number, centerY: number, pointerX: number, pointerY: number,
  maxTilt_deg = 135,
): number {
  const dx = pointerX - centerX;
  const dy = pointerY - centerY;
  if (dx === 0 && dy === 0) return 0;
  const angle = Math.atan2(dx, -dy) / RAD; // [-180,180]，正上方为 0
  return Math.max(-maxTilt_deg, Math.min(maxTilt_deg, angle));
}

/** 填充率 0..1（体积/容量），夹紧防越界。 */
export function fillRatio(state: PourState, geo: VesselGeometry): number {
  if (geo.capacity_mL <= 0) return 0;
  return Math.max(0, Math.min(1, state.volume_mL / geo.capacity_mL));
}

/**
 * 临界角（度）：倾斜到液面触及瓶口才流出。
 * 世界坐标液面水平；容器倾斜 θ 后倾倒侧液面相对容器壁抬升 ≈ (mouthWidth/2)·tan(θ)。
 * 当抬升量 ≥ 液面到瓶口的余量 (1−fill)·height 时开始溢出：
 *   tan(θc) = (1−fill)·height / (mouthWidth/2)
 * 填充越满（fill→1）θc→0；空杯 θc→大。来自几何、无硬编码角度阈值。
 */
export function criticalAngleDeg(state: PourState, geo: VesselGeometry): number {
  const fill = fillRatio(state, geo);
  const halfMouth = Math.max(geo.mouthWidth_mm / 2, 1e-6);
  const headroom = (1 - fill) * geo.height_mm;
  return Math.atan(headroom / halfMouth) / RAD;
}

/**
 * 有效液柱高 head（mm）：超过临界角后，液面到瓶口的可流出的垂直高差。
 * 简化为随超出临界角的角度单调增长：head = halfMouth·(sinθ − sinθc)。
 * θ 越大、head 越大 → 流速越大（单调性由 sin 在 [-90,90] 保证）。
 */
export function effectiveHeadMm(state: PourState, geo: VesselGeometry): number {
  const thetaC = criticalAngleDeg(state, geo) * RAD;
  const theta = Math.min(Math.abs(state.tilt_deg) * RAD, Math.PI / 2);
  if (theta <= thetaC) return 0;
  const halfMouth = geo.mouthWidth_mm / 2;
  return halfMouth * (Math.sin(theta) - Math.sin(thetaC));
}

/**
 * 托里拆利瞬时流速（mL/s）：v=√(2gh)，Q=Cd·A·v。
 * head_mm→m，开口面积取瓶口宽 × 等效缝宽（随倾角增大）mm²→m²，Q(m³/s)→mL/s。
 * 缝宽用 head 与口径的较小者近似（液面越高开口越充分），保证单调且不为负。
 */
export function flowRate(state: PourState, geo: VesselGeometry): number {
  const head_mm = effectiveHeadMm(state, geo);
  if (head_mm <= 0) return 0;
  const head_m = head_mm / 1000;
  const v = Math.sqrt(2 * G_M_S2 * head_m); // m/s
  const aperture_mm = Math.min(head_mm, geo.mouthWidth_mm);
  const area_m2 = (geo.mouthWidth_mm * aperture_mm) * 1e-6; // mm² → m²
  const q_m3_s = DISCHARGE_COEFF * area_m2 * v;
  return q_m3_s * 1e6; // m³/s → mL/s
}

/**
 * 对一次操作帧积分转移体积（mL）。dt 来自真实指针帧间隔，非预设。
 * 转移量不会超过源容器现有体积（物理约束）。
 */
export function integratePour(
  state: PourState, geo: VesselGeometry, dt_s: number,
): PourFlow {
  const thetaC = criticalAngleDeg(state, geo);
  const flow = flowRate(state, geo);
  const dt = Math.max(0, Math.min(dt_s, 0.1)); // 单帧上限 100ms，防卡顿导致跳变
  const transferred = Math.min(state.volume_mL, flow * dt);
  return {
    pouring: flow > 0,
    criticalAngle_deg: thetaC,
    flow_mL_s: flow,
    transferred_mL: transferred,
    head_mm: effectiveHeadMm(state, geo),
  };
}

/**
 * 液面层抵消角度（度）：容器旋转 tilt 时液面层旋转 −tilt 保持世界水平。
 * 表现层据此设 CSS transform，液面相对容器壁呈真实倾斜。
 */
export function liquidCounterRotation(tilt_deg: number): number {
  return -tilt_deg;
}
