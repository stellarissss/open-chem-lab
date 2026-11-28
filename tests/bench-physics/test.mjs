/**
 * 倾角倾倒操作物理单测（008 验收 3/4）。
 * 用 tsx 直接导入 web-ui 的纯函数模块，验证物理口径可判定、无硬编码。
 * 运行：packages/gateway/node_modules/.bin/tsx tests/bench-physics/test.mjs
 */
import assert from "node:assert/strict";
import {
  G_M_S2, DISCHARGE_COEFF, tiltFromPointer, criticalAngleDeg, effectiveHeadMm,
  flowRate, integratePour, liquidCounterRotation, fillRatio,
} from "../../packages/web-ui/src/benchPhysics.ts";

const beaker = { mouthWidth_mm: 78, height_mm: 95, capacity_mL: 250 };
const state = (volume_mL, tilt_deg) => ({ volume_mL, tilt_deg });

let passed = 0;
const ok = (cond, msg) => { assert.ok(cond, msg); passed += 1; };

// 1. 液面世界水平：容器转 θ，液面层 −θ 抵消
ok(liquidCounterRotation(30) === -30, "液面反向旋转 = −容器倾角");
ok(liquidCounterRotation(-45) === 45, "负倾角反向正确");
ok(liquidCounterRotation(0) === 0, "零倾角液面不变");

// 2. 方位角→倾角：正上 0°、右 +90°、左 −90°
ok(Math.abs(tiltFromPointer(100, 100, 100, 50)) < 1e-9, "正上方指针→0°");
ok(Math.abs(tiltFromPointer(100, 100, 150, 100) - 90) < 1e-9, "正右→+90°");
ok(Math.abs(tiltFromPointer(100, 100, 50, 100) + 90) < 1e-9, "正左→−90°");
ok(Math.abs(tiltFromPointer(100, 100, 150, 150) - 135) < 1e-9, "右下→+135°");
ok(tiltFromPointer(100, 100, 100, 100) === 0, "零位移→0°无 NaN");

// 3. 临界角：填充越满越小（越易流出），来自几何、无硬编码角度阈值
const half = state(125, 0);      // 半满
const full = state(250, 0);      // 满
const empty = state(1, 0);       // 近空
ok(criticalAngleDeg(full, beaker) < criticalAngleDeg(half, beaker),
   "满杯临界角 < 半杯临界角");
ok(criticalAngleDeg(half, beaker) < criticalAngleDeg(empty, beaker),
   "半杯临界角 < 近空临界角");
ok(criticalAngleDeg(full, beaker) < 1e-9, "满杯临界角≈0（一倾即流）");

// 4. 托里拆利流速：单调随倾角增长，未过临界角为 0
const thetaC = criticalAngleDeg(half, beaker);
ok(flowRate(state(125, 0), beaker) === 0, "未倾斜无流速");
ok(flowRate(state(125, thetaC - 5), beaker) === 0, "未过临界角无流速");
const f1 = flowRate(state(125, thetaC + 10), beaker);
const f2 = flowRate(state(125, thetaC + 30), beaker);
const f3 = flowRate(state(125, thetaC + 60), beaker);
ok(f1 > 0 && f2 > f1 && f3 > f2, "流速随倾角单调递增");
ok(effectiveHeadMm(state(125, thetaC + 30), beaker) > 0, "过临界角液柱高>0");

// 5. 积分转移量：>0、随 dt 增长、不超过现有体积、物理常数带来源值
const flow = integratePour(state(125, thetaC + 30), beaker, 0.05);
ok(flow.pouring === true && flow.transferred_mL > 0, "过临界角积分出正转移量");
ok(flow.transferred_mL <= 125, "转移量不超过现有体积");
const smaller = integratePour(state(125, thetaC + 30), beaker, 0.01);
ok(flow.transferred_mL > smaller.transferred_mL, "转移量随积分时长增长");
ok(integratePour(state(125, 0), beaker, 1).transferred_mL === 0, "未倾倒零转移");
ok(Math.abs(G_M_S2 - 9.80665) < 1e-9, "重力加速度=NIST标准值");
ok(Math.abs(DISCHARGE_COEFF - 0.61) < 1e-9, "流量系数=工程近似值");

// 6. 体积归一：填充率 = 体积/容量，夹紧 0..1
ok(Math.abs(fillRatio(state(125, 0), beaker) - 0.5) < 1e-9, "半满填充率=0.5");
ok(fillRatio(state(500, 0), beaker) === 1, "超容量夹紧为1");
ok(fillRatio(state(-5, 0), beaker) === 0, "负体积夹紧为0");

console.log(`[bench-physics] 通过 ${passed} 项断言：液面水平/方位角/临界角/托里拆利/积分守恒/无预设值`);
