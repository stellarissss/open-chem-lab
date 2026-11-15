---
name: 内容 / 真实反应参数贡献
about: 提交或精校一条真实反应参数、器材、课标知识点映射
labels: content
---

> **严格只做真实库**：不接受虚构物质、用户自制物质、自定义规则、MOD 或规则包工坊（台账 5.4 / 6.4）。

## 内容类型

- [ ] 真实反应参数（`content/rules/`）
- [ ] 真实物质 / 器材（`content/`）
- [ ] 课标知识点映射 / 多版本教材标注（`content/curriculum/`，长线）
- [ ] 黄金用例（`content/golden-cases/`）

## 参数草案（若为反应参数）

```yaml
id:
confidence:          # verified / extracted（仅 verified 进沙盒）
source:              # NIST / CRC / IUPAC / 课标附录 / 开放教材，必填
applicability:       # 温度 / 浓度 / 溶剂 / 离子强度 / pH 范围
equilibrium:         # Ka / Kb / Ksp / E0 / deltaG（定量，非近似）
kinetics:            # 速率模型 / 活化能（如适用）
numerics:            # rtol / atol / stiffness:auto / significance:auto
reactants / products / stoichiometry:
effects:             # 现象指令，非渲染代码
safety:
```

## 依据

<!-- 权威源、实验条件、现象描述的可核验来源；不复制商业产品文案 -->

## 检查

- [ ] 为**真实物质与真实反应**，有权威源与适用条件
- [ ] 计量守恒；与现有体系无「同一反应物集合 + 条件桶」冲突
- [ ] 反应方向、产物、平衡趋势、pH / 浓度数值准确（**数值零错**）
- [ ] 已完成 **AI 独立对拍（独立解析解 + ChemPy / Cantera / phreeqpython）+ 用户人工签核**；黄金用例同时校验 `sane` / `success`，并排除 PHREEQC `-999` 哨兵值
- [ ] 未整段复制 ORD 描述文本（CC-BY-SA 边界；ORD 数据仅存独立仓）
- [ ] 已在 `golden-cases/` 补断言
- [ ] 不把未核实猜测标为 `verified`
