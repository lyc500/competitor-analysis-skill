# V0.1 审计修正验收记录

日期：2026-10-26
范围：正式入口、证据登记、跨阶段关联、统计、报告交互与自动化回归
结论：工程契约与本地回归通过；本轮不宣称完成真实第三方来源采集验收。

## 本轮核实的历史问题

仅为核实审计问题读取了旧的 `reports/manual-acceptance/v0.1-my-pages-rerun-2/` 产物，没有复用其中的竞品、URL、截图、分类结论或运行记录作为本轮样本。旧产物的来源登记与 captures/reviewed materials 使用的来源 ID 无法形成可靠的一致链路，因此记录为“历史证据缺口”，没有猜测性补写 ID。

## 实施内容

- 正式入口改为结构化 `--task-file` 流程；自然语言位置参数只保留为 `legacy/demo`。
- 来源尝试与候选登记拆分为 `source_attempts`、`candidates`、`candidate_pool` 和 `candidate_limit`。
- 记录查询映射、实际查询、检索模式、发现批次、访问状态、可用性未知值、候选处置和原因。
- 校验来源入口、单屏详情、图片资源三种 URL 角色及其 ID 关联。
- 校验来源尝试 → 候选 → 截图 → 语义审核 → 素材 → 分类 → 报告的引用链；旧格式不伪装成正式证据。
- 报告分开显示来源访问、候选、语义审核、素材流水线、fallback 和覆盖边界统计。
- 每组 5 列、每次 20 张渐进展开保留，并覆盖多组独立展开和窄屏场景。

## 测试证据

| 类型 | 实际命令 | 结果 |
| --- | --- | --- |
| 契约/行为/fixture 回归 | `python3 -m unittest tests.test_skill_contract tests.test_quality tests.test_semantic_review tests.test_report tests.test_source_discovery tests.test_stage1 tests.test_stage2_pipeline tests.test_stage4_pipeline tests.test_classification tests.test_mvp tests.test_acceptance_tasks tests.test_evidence_contract -q` | 106 项通过 |
| 本地 Chromium 与 HTTP | `python3 -m unittest tests.test_browser_report tests.test_capture_workflow -q` | 13 项通过；使用了本地测试页面，不代表第三方来源访问 |
| 全量回归 | `python3 -m unittest discover -s tests -p 'test_*.py' -q` | 119 项通过 |

## 证据边界

- 已执行：Python 契约校验、错误引用行为测试、统计测试、本地 HTTP/真实 Chromium 报告交互和截图链路回归。
- 已执行但仅属离线/fixture：测试图片、测试网页、测试来源登记和静态文档关键词检查。
- 本轮未执行：真实第三方来源搜索、外部 UI 数据库分页/下滑、真实竞品截图逐图人工语义审核、真实外部网络 fallback。
- 因此本目录不能证明任何新一轮真实竞品搜集结果；不能替代正式来源发现和产品验收。
