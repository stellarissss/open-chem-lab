# M0 阶段二收尾 · 补验复跑说明

> 本目录所有结果都可由下列命令复现。脚本不进产品构建（依 `docs/12` 第六节）。
> 快照环境：Ubuntu 22.04 / Chrome 144 / Rust 1.93（含 wasm32 target）/ Node 22.13.1 / conda 23.5.2 / Xvfb / zstd。

## 0. 数据自洽 + 静态合规门禁（零外部依赖，最先跑）

```bash
cd docs/research/data/m0 && python3 verify_m0_s2.py
# 期望：[verify_m0_s2] checks=41 fails=0 · ALL PASS
```

## 1. 三组定量求解 / 对拍（需 chempy / phreeqpython / scipy / cantera / pyequion2）

```bash
cd docs/research/data/m0
python3 test_solver_v3.py   # → solver_result_v3.json  14/14
python3 test_phreeq.py      # → phreeq_result.json       9/9
python3 test_golden.py      # → golden_cases_probe.json  3/3
```

## 2. WASM 现象内核（Rust→WASM 编译 + 帧预算）

```bash
# 归档的是源码与产物；复跑需还原成 cargo 工程目录结构：
mkdir -p /tmp/st_wasm/src
cp wasm_kernel_Cargo.toml /tmp/st_wasm/Cargo.toml
cp wasm_kernel_lib.rs      /tmp/st_wasm/src/lib.rs
cp wasm_kernel_harness.mjs /tmp/st_wasm/harness.mjs
cd /tmp/st_wasm
rustup target add wasm32-unknown-unknown          # 建议 RUSTUP_DIST_SERVER=https://rsproxy.cn
cargo build --target wasm32-unknown-unknown --release
node harness.mjs                                  # → wasm_bench_result.json
```

期望：`wasm_imports=0`、4 组规模 `p95_ms` 全部 `< 16.7`、同 seed 确定性一致。

## 3. 真实 WebGL + 3Dmol.js 球棍渲染（Xvfb + SwiftShader）

`webgl_real.html` 与 `mol_render_real.html` 依赖同目录的 `3dmol-min.js`（3Dmol.js 2.5.5，BSD-3-Clause）。
**依项目既有纪律（第三方 bundle 源码不入库，同 tikz-chemlab 只存编译输出物），`3dmol-min.js` 不入库**；复跑时从 npm 取：

```bash
ART=docs/research/data/m0
cp "$(npm root -g)/3dmol/build/3Dmol-min.js" "$ART/3dmol-min.js" 2>/dev/null || \
  curl -s "https://registry.npmjs.org/3dmol/-/3dmol-2.5.5.tgz" -o /tmp/3dmol.tgz && \
  tar -xzf /tmp/3dmol.tgz -C /tmp && cp /tmp/package/build/3Dmol-min.js "$ART/3dmol-min.js"
# 并在两个 HTML 中把 <script src="3dmol-min.js"> 与实际文件名对齐
```

然后：

```bash
ART=$(pwd)   # 需为绝对路径，file:// 才生效
xvfb-run -a -s "-screen 0 1024x768x24" \
  google-chrome --headless=new --no-sandbox \
  --enable-unsafe-swiftshader --use-gl=angle --use-angle=swiftshader \
  --virtual-time-budget=3000 --dump-dom "file://$ART/webgl_real.html" \
  | grep -o '<title>RESULT=[^<]*</title>'
# 期望：WebGL 2.0 / SwiftShader / clearDepth=function / pixelNonBlack=true

xvfb-run -a -s "-screen 0 1024x768x24" \
  google-chrome --headless=new --no-sandbox \
  --enable-unsafe-swiftshader --use-gl=angle --use-angle=swiftshader \
  --virtual-time-budget=5000 --dump-dom "file://$ART/mol_render_real.html" \
  | grep -o '<title>RESULT=[^<]*</title>'
# 期望：hasWebGL=true / atomCount=9 / nonWhitePixels>0 / hasGeometry=true / ok=true
```

> 关键：纯 `--headless` 无 X display 时 SwiftShader 的 Vulkan/XCB 后端 `xcb_connect() failed`，
> 必须 `xvfb-run` 提供真实 display —— 这正是上一轮「clearDepth 为 null」的根因。

## 4. reaktoro LGPL §6 可替换性（conda-forge 单包，绕开 repodata）

```bash
# anaconda.org API 取直链（repodata.json 过大，全通道超时，勿用 conda solve）
curl -s https://api.anaconda.org/package/conda-forge/reaktoro -o /tmp/rk.json
# 取 linux-64/reaktoro-2.13.0-py311h9c93177_3.conda 与 _0 两个构建的 download_url
URL=https://conda.anaconda.org/conda-forge/linux-64/reaktoro-2.13.0-py311h9c93177_3.conda
curl -s "$URL" -o /tmp/rk3.conda
unzip -o -q /tmp/rk3.conda -d /tmp/rk3 && mkdir -p /tmp/rk3/x
tar --zstd -xf /tmp/rk3/pkg-*.tar.zst -C /tmp/rk3/x      # 需 apt install zstd
EXT=/tmp/rk3/x/lib/python3.11/site-packages/reaktoro/reaktoro4py.cpython-311-x86_64-linux-gnu.so
readelf -d "$EXT" | grep -E "NEEDED|RPATH"               # 期望 NEEDED libReaktoro.so + RPATH $ORIGIN/../../..
readelf -d /tmp/rk3/x/lib/libReaktoro.so | grep SONAME     # 期望 SONAME libReaktoro.so（无版本后缀）
# 运行时替换：把 _0 的 libReaktoro.so 覆盖到 lib/ 后
LD_LIBRARY_PATH=/tmp/rk3/x/lib ldd "$EXT" | grep libReaktoro  # 期望解析到替换后的同名库
```

> 合规注记：conda 单包 `info/` 不含 LGPL 全文，`lgpl-link-check` 须自行随附 `LICENSE.LGPL-2.1` 全文。

## 5. Kenney CC0（F3 销项证据）

- 官网页面：`https://kenney.nl/assets/particle-pack`（带浏览器 UA 返回 200；`<td>License</td> → Creative Commons CC0`）
- 包内 LICENSE.txt 原文：第三方镜像 `Calinou/kenney-particle-pack` 仓库根 `LICENSE.txt`（CC0、可商用、署名非强制）
- CC0 官方法典：`https://creativecommons.org/publicdomain/zero/1.0/legalcode.txt`
- 官网签名下载端点 `/download-link/{id}` 返回 403（需会话/人机校验），按技能规范不规避、不硬刷。

## 6. Windows 双平台

见 [`../../../../deploy/README-windows.md`](../../../../deploy/README-windows.md)。Linux 侧已实测；
Windows 实机执行清单交付给用户在本机跑，沙箱无法覆盖，按 `docs/12` 第三节显式标「受限」。

---

**归档文件**：`s2_completion_result.json`（补验结论汇总）、`wasm_bench_result.json`（帧预算原始数据）、
`wasm_kernel.wasm`（编译产物）、`webgl_real.html` / `mol_render_real.html`（渲染探测页）、
`verify_m0_s2.py`（可运行门禁）。脚本与结果配对登记见 `INDEX.json`。
