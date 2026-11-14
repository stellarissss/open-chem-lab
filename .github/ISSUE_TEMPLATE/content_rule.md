---
name: 内容 / 规则贡献
about: 提交或精校一条反应规则、器材、教材实验模板
labels: content
---

## 内容类型

- [ ] 反应规则（`content/rules/`）
- [ ] 物质 / 材质 / 器材（`content/`）
- [ ] 教材实验模板（`content/experiments/`，M3）
- [ ] 黄金用例（`content/golden-cases/`）

## 规则草案（若为规则）

```yaml
id:
confidence:          # verified / extracted / community / ml_guess（仅 verified 进沙盒）
source:              # 教材/文献/ORD dataset_id，必填
conditions:          # 温度/浓度/pH/压强/溶剂/催化剂
reactants / products / stoichiometry:
effects:             # 现象指令，非渲染代码
safety:
```

## 依据

<!-- 教材出处、实验条件、现象描述的可核验来源；不复制商业产品文案 -->

## 检查

- [ ] 计量守恒
- [ ] 与现有规则无「同一 reactants+条件桶」冲突
- [ ] 未整段复制 ORD 描述文本（CC-BY-SA 边界）
- [ ] 已在 `golden-cases/` 补断言（若影响教材实验）
- [ ] 不把未核实猜测标为 `verified`
