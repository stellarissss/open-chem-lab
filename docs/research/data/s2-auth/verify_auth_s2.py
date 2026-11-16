#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
阶段二补充规划 · 权威源/缓存源门禁（可运行，非占位）

用法：cd docs/research/data/s2-auth && python3 verify_auth_s2.py
退出码 0 = 全通过；非 0 = 打印 FAIL 明细（每条含校验点）。

与 verify_m0_s2.py 分工：本脚本校验「本轮权威源/缓存源产物 + E1–E16 口径落地」；
verify_m0_s2.py 校验 M0 求解/对拍归档。两者互不替代，均接入 docs.yml。
阶段二不写产品代码（docs/12 第一节），本脚本只校验归档数据与仓库静态口径。
"""
import json, os, re

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


def rload(rel):
    p = os.path.join(REPO, rel)
    if not os.path.exists(p):
        return ''
    with open(p, encoding='utf-8', errors='replace') as f:
        return f.read()


# ---- A. 三组实测结果自洽（对应 E13）----
snap = jload('auth_snapshot_result.json')
ck(snap['summary']['status'] == 'PASS' and snap['summary']['pass'] == snap['summary']['total'] == 4,
   'auth_snapshot 应 4/4 PASS')
ck(snap['summary']['wateq4f_materialized'] >= 500, 'wateq4f 物化条目应 ≥500')
ck(all(c['pass_'] for c in snap['cases']), 'auth_snapshot 存在 FAIL case')
ck(len(snap['summary']['materialized_checksum']) == 64, '物化层校验和应为 sha256 64 位')

eps = jload('auth_endpoints_result.json')
ck(eps['summary']['status'] == 'PASS' and eps['summary']['pass'] == eps['summary']['total'] == 5,
   'auth_endpoints 应 5/5 PASS')
ck(eps['parsed_sample'].get('MolecularFormula') == 'C2H6O', 'PubChem 应解析出乙醇 C2H6O')
atct = next(e for e in eps['endpoints'] if e['id'] == 'atct_api')
ck(atct['http_code'] in (403, 429, 503, 200), 'ATcT 受限端点应如实记录（403 等）')

key = jload('auth_cachekey_result.json')
ck(key['summary']['status'] == 'PASS' and key['summary']['pass'] == key['summary']['total'] == 5,
   'auth_cachekey 应 5/5 PASS')
ck(len(key['snapshot_record']['sha256']) == 64, '快照记录应含 sha256')
ck(all(k in key['snapshot_record'] for k in ('endpoint', 'license', 'snapshot_date', 'sha256')),
   '快照记录缺四要素')

idx = jload('INDEX.json')
ck(idx['total'] == {'pass': 14, 'total': 14}, 'INDEX 总计应 14/14')
for pair in idx['pairs']:
    ck(os.path.exists(os.path.join(HERE, pair['script'])), f"缺脚本 {pair['script']}")
    ck(os.path.exists(os.path.join(HERE, pair['result'])), f"缺结果 {pair['result']}")

# ---- B. E14 门禁脚本接入 CI ----
ci = rload('.github/workflows/docs.yml')
ck('verify_auth_s2.py' in ci, 'docs.yml 应接入 verify_auth_s2.py')

# ---- C. 新交付物存在性（E16）----
ck(os.path.exists(os.path.join(REPO, 'docs/research/05-权威数据源与缓存可行性核验.md')),
   '缺 research/05 报告')
ck(os.path.exists(os.path.join(REPO, 'docs/adr/ADR-0010-权威数据供应链与缓存分层.md')),
   '缺 ADR-0010')
docs_readme = rload('docs/README.md')
ck('05-权威数据源' in docs_readme, 'docs/README.md 索引缺 research/05')

# ---- D. 许可证红线（E6 / E7）：Burcat 仅作禁用说明，不得正面推荐 ----
def burcat_lines(text):
    return [ln for ln in text.splitlines() if re.search(r'Burcat', ln, re.I)]

for rel in ('CREDITS.md', 'docs/research/05-权威数据源与缓存可行性核验.md'):
    txt = rload(rel)
    for ln in burcat_lines(txt):
        # 每处 Burcat 必须同时落入禁用/红线语境
        ck(bool(re.search(r'禁用|红线|弃用|替代|JANAF|禁|FORBIDDEN|不纳入|不进', ln, re.I)),
           f'{rel} 的 Burcat 行缺禁用语境: {ln[:80]}')

all_md = ''
for root, dirs, files in os.walk(REPO):
    dirs[:] = [d for d in dirs if d not in ('.git', 'node_modules')]
    for fn in files:
        if fn.endswith('.md'):
            try:
                all_md += rload(os.path.relpath(os.path.join(root, fn), REPO))
            except Exception:
                pass
# 仅禁止「正面采用 AGPL 作主链/主许可证」；"不纳入主链""直接失败""严格不兼容"等禁止性表述不算违规
agpl_violations = []
for ln in all_md.splitlines():
    if not re.search(r'AGPL', ln, re.I):
        continue
    positive = re.search(r'(采用|改用|选用|换用|作为)\s*AGPL|AGPL\s*(作为|为主|为主许可证|主链)', ln, re.I)
    negated = re.search(r'不|禁|失败|隔离|不兼容|FORBIDDEN|excluded', ln, re.I)
    if positive and not negated:
        agpl_violations.append(ln)
ck(not agpl_violations, f'不得正面采用 AGPL 作主链: {agpl_violations[:1]}')

# ---- E. 隔离仓与供应链口径（E11 / E12）----
gitignore = rload('.gitignore')
ck('data-thirdparty/' in gitignore, '.gitignore 应含 data-thirdparty/（E12 统一隔离仓）')
security = rload('SECURITY.md')
ck('运行时零网络依赖' in security or '构建期' in security,
   'SECURITY.md 应体现 E11 构建期固化/运行时零依赖')
ck('仅构建期' in security or '仅内容生产期' in security or '构建期离线' in security,
   'SECURITY.md 的 PubChem 口径应改为仅构建期')

# ---- F. 主线索措辞清理（9.6.0 L0：4 处「中学体系」易混淆措辞）----
for rel in ('CREDITS.md', 'docs/research/02-开源生态全景与选型.md', 'docs/10-完整规划与风险登记册.md'):
    ck('真实中学体系' not in rload(rel), f'{rel} 仍有「真实中学体系」残留措辞')

# ---- G. 台账 E1–E16 固定完整性 ----
ledger = rload('docs/11-问题与决策台账.md')
for eid in ['E13', 'E14', 'E15', 'E16']:
    ck(f'**{eid}**' in ledger, f'台账缺 {eid} 固定记录')
ck('E1–E16' in ledger, '台账应标注 E1–E16 全部固定')

# ---- 输出 ----
if FAILS:
    print(f'FAIL {len(FAILS)}/{CHECKS}:')
    for m in FAILS:
        print('  -', m)
    raise SystemExit(1)
print(f'PASS {CHECKS}/{CHECKS}（权威源/缓存源门禁全绿）')
