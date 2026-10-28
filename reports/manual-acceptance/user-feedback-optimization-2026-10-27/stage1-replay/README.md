# 第 1 阶段：两场景历史数据重放

日期：2026-10-27。这里验证通用报告内容契约、正式生成入口与模板能力，**没有执行新的来源搜集、来源登录、截图采集或逐图语义复审**。两份输出的 `generation.mode` 均为 `replay`，`standard_acceptance` 为 `not_assessed`；不能将其称为当前来源或新版正式采集验收。

原始归档保持在 `../../v0.1-user-tests-2026-10-26/`，未覆盖。本目录为新产物：

- `one-sentence-my-pages/analysis.json`：从原归档的需求、素材审核说明和分类记录整理出的结构化分析；不编造用户产品、现状或业务目标。
- `detailed-my-page-redesign/analysis.json`：从原归档需求、定制 HTML、`research/selected-screens.json` 及现状图整理出的结构化分析；现状图另存于 `baseline-assets/`，不进入竞品材料和统计。
- 各场景 `generated/`：只通过同一个通用 CLI 输出的 `report.html`、`report_data.json`、`classification.json` 和独立 `assets/`。
- `evidence/`：真实 Chromium 全页截图和机器可读浏览器验收记录。

这些分析文件是对归档内已有内容的迁移与结构化，不是重新访问来源后得出的新结论。一句话报告仍保留旧分类边界，并在组结论中明确宽泛组需要后续语义复核；它不能作为 R2 分类质量已完成的证据。

## 生成路径核实

| 核实项 | 一句话报告 | 详细需求报告 |
| --- | --- | --- |
| 原归档能由旧通用 `report.py` 完整重建 | 不能。旧 renderer 可重建基本图墙，但与归档 HTML 不同；归档的来源链接/样式等不完全来自当前模板 | 不能。旧 renderer 不消费现状、头部发现、逐图借鉴、限制和综合分析 |
| 一次性实现证据 | 原目录没有生成脚本；归档总 README 明确“一次性生成脚本未复制”，因此无法进一步区分脚本生成与生成后手改 | 同左；不能把定制 HTML 的能力归功于通用入口 |
| 仅存在 HTML 的信息 | 头部呈现和部分文案没有独立分析契约 | 头部结论、现状区块、模块顺序和部分综合表达只在 HTML；逐图 `title/evidence/borrow/avoid` 另见 `research/selected-screens.json` |
| 原 `report_data.json` 是否完整表达最终报告 | 否。主要是 task/materials/classification/fallback，缺结构化报告分析与 generation 标记 | 否。没有现状、头部判断、逐图建议和综合小结，也不读取 `selected-screens.json` |
| 当前通用入口 | 读取旧快照＋本目录 `analysis.json`，校验引用、复制全部素材并确定性生成 | 同一入口；现状作为独立证据复制，统计仍为 9 个竞品/10 张竞品图 |

审计时在内存调用旧 renderer：一句话归档 HTML 为 29,756 bytes，旧通用渲染结果为 32,755 bytes；详细归档为 47,428 bytes，旧通用结果为 14,569 bytes。字节差异本身不判定生成方式，只证明当前归档 HTML 不是由旧正式入口按现有结构直接重建。原目录没有可审计的一次性脚本，故不推测更具体的手工步骤。

第 1 阶段后，最终可见分析全部来自 `analysis.json`，生成快照在 `generated/report_data.json.analysis` 中完整保留；HTML 不再是唯一事实来源。分类审核 reason 仍在 classification，读者 takeaway 单独在 analysis，未复用同一字段。

## 重放命令

```bash
python3 -B -m competitor_analysis_skill \
  --report-data-file reports/manual-acceptance/v0.1-user-tests-2026-10-26/one-sentence-my-pages/report_data.json \
  --analysis-file reports/manual-acceptance/user-feedback-optimization-2026-10-27/stage1-replay/one-sentence-my-pages/analysis.json \
  --output reports/manual-acceptance/user-feedback-optimization-2026-10-27/stage1-replay/one-sentence-my-pages/generated

python3 -B -m competitor_analysis_skill \
  --report-data-file reports/manual-acceptance/v0.1-user-tests-2026-10-26/detailed-my-page-redesign/report_data.json \
  --analysis-file reports/manual-acceptance/user-feedback-optimization-2026-10-27/stage1-replay/detailed-my-page-redesign/analysis.json \
  --output reports/manual-acceptance/user-feedback-optimization-2026-10-27/stage1-replay/detailed-my-page-redesign/generated
```

命令明确输出“重放报告（非新采集验收）”。修改结构化输入并重放会更新 HTML；自动化测试还验证了搬移整个 bundle 后可以只依赖本地快照与 assets 重建，且两次相同输入生成相同 HTML。

## 验收结果

浏览器记录见 [`evidence/verification.json`](evidence/verification.json)：

- 一句话场景：20 个竞品、26 张竞品图、6 组；无现状模块。模块顺序为总览、导航、6 个图墙、来源说明、综合小结。
- 详细场景：9 个竞品、10 张竞品图、3 组，加 1 张独立现状图；现状不计入竞品。模块顺序为总览、导航、现状、3 个图墙、来源说明、综合小结。
- 两份报告的卡片详情和来源说明默认关闭，详细场景的现状也默认关闭；图片全部加载、放大交互通过，1440 与 390 宽度水平溢出均为 0，综合小结是最后一个主要模块。

全量自动化回归：`python3 -B -m unittest discover -s tests -p 'test_*.py' -q`，141 项通过。测试覆盖同一模板的两种输入、有/无现状、现状计数隔离、无效引用、空组引用、兼容缺口、输入变更后重建、图墙、分类唯一性、20 张展开、放大和 bundle 搬移。测试输出仍有既有本地 HTTP/Playwright socket `ResourceWarning`，不影响本次断言结果。

本阶段未完成：R2 的分类语义质量升级、R3 小分类并排、R8 正式采集前登录/访问预检，以及两场景的新来源搜集和重新逐图审核。这些不由历史重放替代。
