#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""M0 最小测试 01（v3 · 官方 API 对齐）：四体系定量求解 + 数值零错 + 耗时基线。

一级来源（官方仓库源码，2026-11-15 读取）：
  - chempy/tests/test_equilibria.py::test_Equilibria_root_simple
      → Species(name, charge, composition={Z:count})；Kw=1e-14/55.5；init_concs 用 defaultdict
  - examples/NaCl_precipitation.ipynb
      → 沉淀相用 Species(..., phase_idx=1)；Equilibrium 写溶解方向，常数为 Ksp
  - pyequion2 SolutionResult 属性：ph / ionic_strength / concentrations / saturation_indexes

期望值由独立解析解计算（弱酸二次方程、Henderson-Hasselbalch、Ksp 开方），不依赖被测库自证。
"""
import json, math, time, traceback, sys, collections

R = {"date":"2026-11-15", "python":sys.version.split()[0], "cases":[], "stiffness":[], "libs":{}}
def rec(case, lib, exp, got, unit, tol, ms, note=""):
    try: err=abs(float(got)-float(exp)); ok=err<=tol
    except Exception: err,ok=None,False
    R["cases"].append(dict(case=case,lib=lib,expected=exp,got=got,unit=unit,abs_err=err,tol=tol,pass_=ok,ms=round(ms,3),note=note))
    print(f"  [{'PASS' if ok else 'FAIL'}] {case:28s} {lib:12s} exp={exp} got={got} err={err} {ms:.1f}ms {note}")

Kw, Ka, Ksp = 1e-14, 1.75e-5, 1.77e-10
def acid(C,Ka):
    x=(-Ka+math.sqrt(Ka*Ka+4*Ka*C))/2; return -math.log10(x), x/C
def base(C,Kb):
    x=(-Kb+math.sqrt(Kb*Kb+4*Kb*C))/2; return 14+math.log10(x), x/C
ph_a, alpha = acid(0.1,Ka); ph_b,_ = base(0.1,Kw/Ka)
print("=== 独立解析基准（25°C，权威常数） ===")
print(f"  0.1M HAc pH={ph_a:.6f} α={alpha:.6%} | 0.1M NaAc pH={ph_b:.6f} | AgCl饱和[Ag+]={math.sqrt(Ksp):.6e} | 半中和pH={-math.log10(Ka):.6f}")

from chempy.chemistry import Species, Equilibrium
from chempy.equilibria import EqSystem

# 物种组成（原子序数: 个数）——守恒矩阵由此构建
def acid_species(with_NaCl=False):
    s=[Species('H2O',0,composition={1:2,8:1}),
       Species('H+',1,composition={1:1}),
       Species('OH-',-1,composition={1:1,8:1}),
       Species('HAc',0,composition={1:4,6:2,8:2}),
       Species('Ac-',-1,composition={1:3,6:2,8:2})]
    if with_NaCl:
        s += [Species('Na+',1,composition={11:1}), Species('Cl-',-1,composition={17:1})]
    return s
w_auto = lambda: Equilibrium({'H2O':1},{'H+':1,'OH-':1}, Kw/55.5)
hac_dis = lambda: Equilibrium({'HAc':1},{'H+':1,'Ac-':1}, Ka)

# ---- 体系 1：弱酸电离 ----
print("\n=== 体系 1 · 弱酸电离（中和/电离，ChemPy） ===")
try:
    eqsys=EqSystem([w_auto(),hac_dis()], acid_species())
    init=collections.defaultdict(float,{'H2O':55.5,'HAc':0.1})
    t0=time.perf_counter(); x,info,sane=eqsys.root(init); ms=(time.perf_counter()-t0)*1000
    d=eqsys.as_per_substance_dict(x); ph=-math.log10(d['H+'])
    print(f"  sane={sane} success={info.get('success')} pH={ph:.5f} [Ac-]={d['Ac-']:.6f}")
    rec("0.1M 乙酸 pH","ChemPy",round(ph_a,4),round(ph,4),"pH",0.02,ms,"非线性平衡 + 元素守恒")
    rec("0.1M 乙酸电离度","ChemPy",round(alpha,6),round(d['Ac-']/0.1,6),"frac",1e-4,0,"由守恒自动满足")
except Exception as e:
    print("  失败:",e); traceback.print_exc(limit=3); rec("0.1M 乙酸 pH","ChemPy",round(ph_a,4),"ERROR","pH",0.02,0,str(e)[:90])

# ---- 体系 2：水解 ----
print("\n=== 体系 2 · 水解（乙酸钠，ChemPy） ===")
try:
    eqsys=EqSystem([w_auto(),hac_dis()], acid_species(with_NaCl=True))
    init=collections.defaultdict(float,{'H2O':55.5,'Ac-':0.1,'Na+':0.1})
    t0=time.perf_counter(); x,info,sane=eqsys.root(init); ms=(time.perf_counter()-t0)*1000
    d=eqsys.as_per_substance_dict(x); ph=-math.log10(d['H+'])
    print(f"  sane={sane} success={info.get('success')} pH={ph:.5f} [HAc]={d['HAc']:.3e}")
    rec("0.1M 乙酸钠水解 pH","ChemPy",round(ph_b,4),round(ph,4),"pH",0.05,ms,"Ac-+H2O⇌HAc+OH-")
except Exception as e:
    print("  失败:",e); traceback.print_exc(limit=2); rec("0.1M 乙酸钠水解 pH","ChemPy",round(ph_b,4),"ERROR","pH",0.05,0,str(e)[:90])

# ---- 体系 3：中和 / 缓冲 ----
print("\n=== 体系 3 · 中和与缓冲（半中和点，ChemPy） ===")
try:
    eqsys=EqSystem([w_auto(),hac_dis()], acid_species(with_NaCl=True))
    # 0.1M HAc 50mL + 0.05M NaOH 50mL → HAc 0.025 / Ac- 0.025 / Na+ 0.025（半中和）
    init=collections.defaultdict(float,{'H2O':55.5,'HAc':0.025,'Ac-':0.025,'Na+':0.025})
    t0=time.perf_counter(); x,info,sane=eqsys.root(init); ms=(time.perf_counter()-t0)*1000
    d=eqsys.as_per_substance_dict(x); ph=-math.log10(d['H+'])
    print(f"  sane={sane} success={info.get('success')} pH={ph:.5f}（期望 pKa={-math.log10(Ka):.5f}）")
    rec("半中和缓冲 pH=pKa","ChemPy",4.757,round(ph,3),"pH",0.02,ms,"Henderson-Hasselbalch")
except Exception as e:
    print("  失败:",e); traceback.print_exc(limit=2); rec("半中和缓冲 pH","ChemPy",4.757,"ERROR","pH",0.02,0,str(e)[:90])

# ---- 体系 4：沉淀（官方 NaCl notebook 范式） ----
print("\n=== 体系 4 · 沉淀溶解（AgCl，ChemPy） ===")
try:
    Ag=Species('Ag+',1,composition={47:1}); Cl=Species('Cl-',-1,composition={17:1})
    AgCl=Species('AgCl',phase_idx=1,composition={47:1,17:1})
    Na=Species('Na+',1,composition={11:1}); NO3=Species('NO3-',-1,composition={7:1,8:3})
    eq=Equilibrium({'AgCl':1},{'Ag+':1,'Cl-':1},Ksp)   # 溶解方向，常数=Ksp
    eqsys=EqSystem([eq],[Ag,Cl,AgCl,Na,NO3])
    init=collections.defaultdict(float,{'Ag+':0.05,'Cl-':0.05,'Na+':0.05,'NO3-':0.05,'AgCl':0.0})
    t0=time.perf_counter(); x,info,sane=eqsys.root(init); ms=(time.perf_counter()-t0)*1000
    d=eqsys.as_per_substance_dict(x)
    print(f"  sane={sane} success={info.get('success')} [Ag+]={d['Ag+']:.6e} [Cl-]={d['Cl-']:.6e} AgCl(s)={d['AgCl']:.6f}")
    rec("AgCl 饱和 [Ag+]","ChemPy",round(math.sqrt(Ksp),8),round(d['Ag+'],8),"M",2e-6,ms,"Ksp 平衡 + 守恒")
    rec("AgCl 沉淀生成量","ChemPy",0.05,round(d['AgCl'],4),"M",1e-3,0,"等量混合应近完全沉淀")
except Exception as e:
    print("  失败:",e); traceback.print_exc(limit=2); rec("AgCl 沉淀","ChemPy",1.33e-5,"ERROR","M",2e-6,0,str(e)[:90])

# ---- 体系 5：pyequion2 活度 / 离子强度 ----
print("\n=== 体系 5 · 电解质活度与物种分布（pyequion2） ===")
try:
    import pyequion2
    eq=pyequion2.EquilibriumSystem(['Na+','Cl-','H+','OH-'])
    t0=time.perf_counter(); sr,info=eq.solve_equilibrium_mixed_balance(298.15,molal_balance={'Na':0.1,'Cl':0.1}); ms=(time.perf_counter()-t0)*1000
    ph=float(sr.ph); I=float(sr.ionic_strength)
    print(f"  pH={ph:.4f} I={I:.4f} 残差={max(abs(v) for v in info['res']):.2e}")
    rec("0.1M NaCl pH","pyequion2",7.0,round(ph,3),"pH",0.3,ms,"Debye-Hückel 活度")
    rec("0.1M NaCl 离子强度","pyequion2",0.1,round(I,3),"mol/kgw",0.02,0,"I=½Σm·z²")
    # 修复：sr.concentrations 在 pyequion2 中为 dict（键为物种名），不是可切片数组。
    # 早期版本对它做 [:len(eq.solutes)] 触发 "unhashable type: 'slice'"，
    # 使 except 分支误追加一条虚假 FAIL 并制造重复 case。此处兼容 dict / array 两种形态。
    conc = sr.concentrations
    if isinstance(conc, dict):
        items = [(k, round(float(v),6)) for k,v in list(conc.items())[:8]]
    else:
        items = [(k, round(float(v),6)) for k,v in zip(eq.solutes, list(conc)[:len(eq.solutes)])][:8]
    print(f"  物种浓度: {dict(items)}")
except Exception as e:
    print("  失败:",e); traceback.print_exc(limit=2); rec("0.1M NaCl pH","pyequion2",7.0,"ERROR","pH",0.3,0,str(e)[:90])

# ---- 体系 6：刚性 ODE（ADR-0008 / SP-1 核心验证） ----
print("\n=== 体系 6 · 动力学 ODE 与刚性自适应（SciPy） ===")
try:
    from scipy.integrate import solve_ivp
    import numpy as np
    k=0.1; exact=math.exp(-k*10)
    for m in ['RK45','LSODA','BDF','Radau']:
        t0=time.perf_counter(); s=solve_ivp(lambda t,y:[-k*y[0],k*y[0]],[0,10],[1.,0.],method=m,t_eval=np.linspace(0,10,11),rtol=1e-8,atol=1e-10); ms=(time.perf_counter()-t0)*1000
        rec(f"一级动力学 {m}","SciPy",round(exact,6),round(s.y[0][-1],6),"M",1e-5,ms,f"nfev={s.nfev}")
    def stiff(t,y): return [-1e4*y[0]+1e4*y[1], 1e4*y[0]-1e4*y[1]-y[1]]
    for m in ['RK45','LSODA','BDF','Radau']:
        t0=time.perf_counter(); s=solve_ivp(stiff,[0,1],[1.,0.],method=m,rtol=1e-8,atol=1e-10); ms=(time.perf_counter()-t0)*1000
        R['stiffness'].append(dict(method=m,nfev=s.nfev,ms=round(ms,2),success=s.success))
        print(f"  刚性 {m:6s}: nfev={s.nfev:6d} 耗时={ms:8.2f}ms success={s.success}")
except Exception as e: print("  失败:",e); traceback.print_exc(limit=2)

# ---- 体系 7：Cantera / phreeqpython（AI 对拍第二引擎） ----
print("\n=== 体系 7 · Cantera 热力学 / phreeqpython 独立对拍 ===")
try:
    import cantera as ct
    R['libs']['cantera']=ct.__version__
    t0=time.perf_counter(); g=ct.Solution('gri30.yaml'); g.TP=300,ct.one_atm
    g.set_equivalence_ratio(1.0,'CH4:1','O2:2, N2:7.52'); g.equilibrate('HP'); ms=(time.perf_counter()-t0)*1000
    print(f"  Cantera {ct.__version__}: GRI30 {g.n_species} 物种, T_ad={g.T:.1f}K")
    rec("甲烷绝热火焰温度","Cantera",2220,round(g.T,0),"K",150,ms,"GRI30 HP 平衡（量级校验）")
except Exception as e: print("  Cantera 失败:",e)
try:
    from phreeqpython import PhreeqPython
    pp=PhreeqPython(); t0=time.perf_counter(); s=pp.add_solution({'units':'mol/kgw','Na':0.1,'Cl':0.1}); ms=(time.perf_counter()-t0)*1000
    print(f"  phreeqpython: pH={s.pH:.3f} 物种数={len(s.species)}")
    rec("PHREEQC 中性盐 pH","phreeqpython",7.0,round(s.pH,2),"pH",0.3,ms,"独立引擎（AI 对拍候选）")
except Exception as e: print("  phreeqpython 失败:",e)

# ---- 库版本留档 ----
import importlib.metadata as md
for p in ['chempy','pyequion2','cantera','phreeqpython','chemicals','thermo','CoolProp','numpy','scipy','sympy']:
    try: R['libs'][p]=md.version(p)
    except Exception: pass

print("\n=== 汇总 ===")
tot=len(R['cases']); ok=sum(1 for c in R['cases'] if c['pass_'])
print(f"  {ok}/{tot} PASS"); R['summary']={'pass':ok,'total':tot}
with open('solver_result_v3.json','w',encoding='utf-8') as f:
    json.dump(R,f,ensure_ascii=False,indent=2)
print("  已存 solver_result_v3.json（与本脚本同目录）")
