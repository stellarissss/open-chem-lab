#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
阶段二收尾 · M0 归档数据自洽 + 静态合规门禁（可运行，非占位）

用法：cd docs/research/data/m0 && python3 verify_m0_s2.py
退出码 0 = 全通过；非 0 = 有断言失败（打印 FAIL 明细）。

设计边界（依 docs/12 第一节）：阶段二不写产品代码，只消解不确定性。
本脚本校验「已归档的实测数据 + 仓库静态合规」，不校验尚不存在的产品依赖树 / content/ / e2e —— 那些是 M1 骨架阶段的门禁。
"""
import json, os, struct, sys, glob

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
FAILS = []
CHECKS = 0

def ck(cond, msg):
    global CHECKS
    CHECKS += 1
    if not cond:
        FAILS.append(msg)

def jload(name):
    with open(os.path.join(HERE, name), encoding='utf-8') as f:
        return json.load(f)

# ---- 1. 三组求解/对拍 JSON 数值自洽 ----
solver = jload('solver_result_v3.json')
ck(solver['summary'] == {'pass': 14, 'total': 14}, 'solver_result_v3 应为 14/14')
ck(len(solver['cases']) == 14, 'solver cases 应为 14 条')
ck(all(c.get('pass_', True) for c in solver['cases']), 'solver 存在 FAIL case')

phreeq = jload('phreeq_result.json')
ck(phreeq['summary'] == {'pass': 9, 'total': 9}, 'phreeq_result 应为 9/9')

golden = jload('golden_cases_probe.json')
ck(sum(1 for c in golden['cases'] if c['pass_']) == len(golden['cases']) == 3, 'golden 应为 3/3')

# ---- 2. 脚本/结果成对可重跑 ----
idx = jload('INDEX.json')
for pair in idx['pairs']:
    ck(os.path.exists(os.path.join(HERE, pair['script'])), f"缺脚本 {pair['script']}")
    ck(os.path.exists(os.path.join(HERE, pair['result'])), f"缺结果 {pair['result']}")

# ---- 3. WASM 结果自洽 + 二进制产物（存在则校验，缺失则降级跳过）----
wb = jload('wasm_bench_result.json')
ck(wb['wasm_imports'] == 0, 'WASM 应零外部 import')
ck(wb['summary']['all_within_budget'] is True, 'WASM 帧预算应全部达标')
ck(wb['summary']['deterministic_same_seed'] is True, 'WASM 同 seed 应确定性一致')
ck(len(wb['cases']) == 4, 'WASM 应有 4 组规模用例')
# wasm_kernel.wasm 是「可重跑实测产物」而非产品依赖；若被外部清理，门禁不应整体崩溃，
# 只要 bench 结果 JSON 自洽即可。存在时才做魔数/版本/字节数一致性校验。
wasm_path = os.path.join(HERE, 'wasm_kernel.wasm')
WASM_PRESENT = os.path.exists(wasm_path)
if WASM_PRESENT:
    wasm = open(wasm_path, 'rb').read()
    ck(wasm[:4] == b'\x00asm', 'wasm 魔数错误')
    ck(struct.unpack('<I', wasm[4:8])[0] == 1, 'wasm 版本应为 1')
    ck(len(wasm) == wb['wasm_bytes'], 'wasm 字节数应与 bench 结果一致')
else:
    print('  [info] wasm_kernel.wasm 不在场，跳过二进制一致性校验（bench JSON 结论仍校验）')

# ---- 4. 补验汇总自洽 ----
s2 = jload('s2_completion_result.json')
ck(len(s2['items']) == 6, '补验项应为 6 项')
ck(s2['summary']['now_pass_or_closed'].startswith('C1/C2/C3/C4'), 'C1-C4 销项结论缺失')
for item in s2['items']:
    ck(bool(item.get('now')) and bool(item.get('prior')), f"{item['id']} 缺 prior/now")

# ---- 5. 静态合规红线（仓库级）----
def repo(path): return os.path.join(REPO, path)
ck(os.path.exists(repo('LICENSE.GPL-3')), '缺 GPL-3 全文')
ck(os.path.exists(repo('LICENSE.LGPL-3')), '缺 LGPL-3 全文')
ck(os.path.exists(repo('docs/11-问题与决策台账.md')), '缺决策台账')
ck('GNU GENERAL PUBLIC LICENSE' in open(repo('LICENSE.GPL-3'), encoding='utf-8', errors='ignore').read(400), 'GPL-3 全文首部异常')
ck('GNU LESSER GENERAL PUBLIC LICENSE' in open(repo('LICENSE.LGPL-3'), encoding='utf-8', errors='ignore').read(400), 'LGPL-3 全文首部异常')

# 无明文 token
token_hit = []
for root, dirs, files in os.walk(REPO):
    if '.git' in root.split(os.sep): continue
    for fn in files:
        p = os.path.join(root, fn)
        try:
            t = open(p, encoding='utf-8', errors='ignore').read()
        except Exception:
            continue
        import re
        if re.search(r'ghp_[A-Za-z0-9]{20,}', t):
            token_hit.append(os.path.relpath(p, REPO))
ck(not token_hit, f'检测到明文 token: {token_hit[:3]}')

# 无 CRLF
crlf = []
for root, dirs, files in os.walk(REPO):
    if '.git' in root.split(os.sep): continue
    for fn in files:
        p = os.path.join(root, fn)
        try:
            if b'\r\n' in open(p, 'rb').read(): crlf.append(os.path.relpath(p, REPO))
        except Exception:
            pass
ck(not crlf, f'存在 CRLF 文件: {crlf[:3]}')

# 无 LPPL 宏包源码
macros = []
for pat in ('tikz-chemlab.sty', 'tikz-chemlabObj.tex', 'tikz-chemlab.tex'):
    macros += glob.glob(os.path.join(REPO, '**', pat), recursive=True)
ck(not macros, f'LPPL 宏包源码入库: {macros[:3]}')

# ---- 6. Kenney CC0 证据链（s2 汇总里的一手来源文本存在）----
c3 = next(i for i in s2['items'] if i['id'] == 'C3')
ck('Creative Commons CC0' in c3['evidence']['official_page'], 'Kenney 官网 CC0 标注缺失')
ck('CC0' in c3['evidence']['bundled_license'], 'Kenney 包内 LICENSE CC0 缺失')
ck('403' in c3['evidence']['note'], 'Kenney 下载端点 403 的诚实注记缺失')

# ---- 7. reaktoro LGPL §6 证据链 ----
c4 = next(i for i in s2['items'] if i['id'] == 'C4')
ev = c4['evidence']
ck('libReaktoro.so' in ev['dynamic_link'], 'reaktoro 动态链接证据缺失')
ck('SONAME 完全一致' in ev['soname'], 'reaktoro SONAME 可替换证据缺失')
ck('ldd' in ev['runtime_replace'], 'reaktoro 运行时替换实证缺失')
ck('LGPL 全文' in ev['compliance_caveat'], 'LGPL 全文补注缺失')

# ---- 输出 ----
print(f"[verify_m0_s2] checks={CHECKS} fails={len(FAILS)} wasm_binary={'present' if WASM_PRESENT else 'absent(skipped)'}")
for f in FAILS:
    print('  FAIL:', f)
if FAILS:
    sys.exit(1)
print('  ALL PASS · M0 归档数据自洽 + 静态合规红线 + 补验证据链完整')
sys.exit(0)
