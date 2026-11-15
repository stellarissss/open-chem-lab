# -*- coding: utf-8 -*-
"""M0 最小测试 02（v2 · 单位修正）：phreeqpython 作为电解质/水溶液平衡主引擎的可行性。

覆盖：中性盐 pH、官方 CaCl2+NaHCO3 用例（pH / 电导率 / 饱和度指数 / 物种浓度 /
元素总量）、加料重算、沉淀溶解、溶液混合运算——逐条对应项目核心需求
「真实物质任意组合 + 隐藏化学态 + 事件唤醒重算 + 沉淀与溶解」。

⚠️ 单位说明（本版修复点）：
  add_solution_simple() 的输入单位为 **mmol**（phreeqpython 官方源码确认）。
  早期版本误按 mol 传入 1.0/1000，导致官方用例仅 1/5 PASS、混合/加料数值错位。
  本版统一传 mmol（CaCl2=1.0, NaHCO3=2.0, NaOH=0.5），与官方示例一致。

期望值来自 phreeqpython 官方示例与独立解析基准，不由被测库自证。
输出：phreeq_result.json（与本脚本同目录，运行时请 cd 到本目录）。
"""
import json, time
from phreeqpython import PhreeqPython

R = {'cases': []}

def rec(case, exp, got, unit, tol, ms, note=''):
    try:
        err = abs(float(got) - float(exp)); ok = err <= tol
    except Exception:
        err, ok = None, False
    R['cases'].append(dict(case=case, expected=exp, got=got, unit=unit,
                           abs_err=err, tol=tol, pass_=ok,
                           ms=round(ms, 3), note=note))
    print(f"  [{'PASS' if ok else 'FAIL'}] {case:24s} exp={exp} got={got} err={err} {ms:.2f}ms {note}")

pp = PhreeqPython()

print('=== 1. 中性盐 pH（显式 mol/kgw，电荷平衡） ===')
t0 = time.perf_counter()
s0 = pp.add_solution({'units': 'mol/kgw', 'Na': 0.05, 'Cl': 0.05})
ms = (time.perf_counter() - t0) * 1000
rec('0.05M NaCl pH', 7.0, round(s0.pH, 2), 'pH', 0.15, ms, '中性盐')

print('\n=== 2. 官方示例 CaCl2 1 mmol + NaHCO3 2 mmol（mmol 单位） ===')
t0 = time.perf_counter()
s = pp.add_solution_simple({'CaCl2': 1.0, 'NaHCO3': 2.0})
ms = (time.perf_counter() - t0) * 1000
print(f'  pH={s.pH:.3f} sc={s.sc:.2f} SI(Calcite)={s.si("Calcite"):.3f} '
      f'HCO3-={float(s.species.get("HCO3-", 0)):.6f} 总 Cl={s.total("Cl", units="mol"):.6f}')
rec('官方示例 pH',          8.12,    round(s.pH, 3),                          'pH',       0.02,   ms, 'CaCl2+NaHCO3 (mmol)')
rec('官方示例 sc',          427.32,  round(s.sc, 2),                          'uS/cm',    1.0,    0,  '电导率')
rec('官方示例 SI(Calcite)', 0.38,    round(s.si('Calcite'), 3),                'SI',       0.02,   0,  '饱和度指数')
rec('官方示例 HCO3-',       0.0019,  round(float(s.species.get('HCO3-', 0)), 6), 'mol/kgw', 0.0001, 0,  '物种浓度')
rec('官方示例 总 Cl',       0.002,   round(s.total('Cl', units='mol'), 6),     'mol',      1e-5,   0,  '元素总量')

print('\n=== 3. 加料重算 / 沉淀溶解（对应「加一滴酸平衡怎么移动」） ===')
t0 = time.perf_counter()
s2 = pp.add_solution_simple({'CaCl2': 1.0, 'NaHCO3': 2.0})
s2.add('NaOH', 0.5)
ph1 = s2.pH
s2.desaturate('Calcite')
ca = s2.total('Ca', units='mol')
ms = (time.perf_counter() - t0) * 1000
print(f'  加 NaOH 后 pH={ph1:.3f}（官方 9.47）; desaturate 后总 Ca={ca:.6f} mol')
rec('加 NaOH 后 pH',      9.47,     round(ph1, 3), 'pH',  0.02,  ms, '加料/事件唤醒重算')
rec('desaturate 后总 Ca', 0.000497, round(ca, 6),  'mol', 1e-5,  0,  '沉淀溶解')

print('\n=== 4. 溶液混合运算（对应「真实物质任意组合」核心玩法） ===')
t0 = time.perf_counter()
a = pp.add_solution_simple({'NaCl': 1.0})
b = pp.add_solution_simple({'KCl': 1.0})
c = a * 0.5 + b * 0.5
ms = (time.perf_counter() - t0) * 1000
print(f'  50/50 混合后总 K={c.total("K", units="mol"):.6f} mol（官方期望 0.0005）')
rec('50/50 混合总 K', 0.0005, round(c.total('K', units='mol'), 6), 'mol', 1e-5, ms, '溶液混合运算')

print('\n=== 汇总 ===')
ok = sum(1 for x in R['cases'] if x['pass_'])
print(f"  {ok}/{len(R['cases'])} PASS")
R['note'] = 'add_solution_simple 默认单位 mmol（官方源码确认）；此前 1/5 系误用 mol 所致'
R['summary'] = {'pass': ok, 'total': len(R['cases'])}
# 直接依赖数：PyPI JSON API 元数据（2026-11-15 快照），非运行时测量
R['deps'] = {'phreeqpython': 3, 'chempy': 46, 'cantera': 6}
with open('phreeq_result.json', 'w', encoding='utf-8') as f:
    json.dump(R, f, ensure_ascii=False, indent=2)
print('  已存 phreeq_result.json')
