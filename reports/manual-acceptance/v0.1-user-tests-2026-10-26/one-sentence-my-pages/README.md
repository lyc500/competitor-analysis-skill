# 一句话测试：国内外 App “我的”页截图

## 输入与目标

用户只给出一句话：

> 帮我搜集一下国内外知名 app “我的”页的竞品截图。

任务将“我的”语义映射到国内常用的个人中心/账户页，以及海外来源常见的 `Profile`、`You`、`Me`、`Account`、`My Account`、`My Page` 等命名，并以移动端单屏截图为主要目标。

## 结果

- 最终报告：[`report.html`](./report.html)
- 报告数据：[`report_data.json`](./report_data.json)
- 分类结果：[`classification.json`](./classification.json)
- 报告使用的本地截图：[`assets/`](./assets/)
- 最终报告包含 26 张有效截图，覆盖 20 个产品；国内与海外产品均有收录，具体以 `report_data.json` 为准。

## 过程证据

- 任务结构化输入：[`task.json`](./task.json)
- 来源尝试：[`source-attempts.json`](./source-attempts.json)
- 候选登记：[`candidate-registry.json`](./candidate-registry.json)
- 候选下载与标准化：[`candidates-downloaded.json`](./candidates-downloaded.json)
- 语义审核通过素材：[`accepted.json`](./accepted.json)
- 被拒候选及原因：[`rejected.json`](./rejected.json)
- 分类计划：[`classification-plan.json`](./classification-plan.json)
- 审核后素材登记：[`reviewed_materials.json`](./reviewed_materials.json)
- 来源/查询分组：[`discovery-groups.txt`](./discovery-groups.txt)、[`refero.tsv`](./refero.tsv)、[`selected.tsv`](./selected.tsv)
- 研究备注：[`research-notes.md`](./research-notes.md)

## 边界

这是“一句话测试”的真实结果，不是本轮审计的 fixture。报告 HTML 和本地 `assets/` 可以离线复核；过程记录保留当时的来源、候选和审核结果，但外部来源的当前可访问性不由本归档保证。
