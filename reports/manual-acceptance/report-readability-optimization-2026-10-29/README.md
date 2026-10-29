# 报告可读性优化验收

本目录验证 2026-10-29 用户标注反馈：报告默认界面减少过程性文字，标题和结论改为直白表达，并把样本覆盖不足变成正式分析契约。两份报告均使用 2026-10-27 已归档素材重放，没有重新采集，也没有把重生成日期描述成素材日期。

## 结果

- 场景 A：9 张历史素材，报告见 [scenario-a-replay/report/report.html](scenario-a-replay/report/report.html)。
- 场景 B：6 张竞品素材＋1 张用户现状图，报告见 [scenario-b-replay/report/report.html](scenario-b-replay/report/report.html)。
- B 场景明确显示“小样本方向参考”；UI Notes 非会员浏览限制、缺少更多会员状态案例和任务入口/详情成对案例保存在折叠的“来源与筛选说明”中。
- 标题只说明研究对象；头部把总判断和关键发现合并为一段“结论”，下面只保留一段“建议”。样本数量、历史重放标记、证据引用、适用条件、限制和分析复核均移入折叠区。
- 正式生成入口从 `analysis.json` 消费 `coverage_assessment`。样本不足时必须记录继续当前样本或补充来源的明确选择；选择补充来源时禁止提前生成正式报告。

## 复现

正式命令和测试结果见 [test-results.md](test-results.md)。同一输入在 `/private/tmp/competitor-analysis-readability-replay/` 重生成后，两份报告目录均与本目录逐文件一致。

## 边界

- 这是历史素材分析重放，只验证报告表达、结构化覆盖评估和生成门槛。
- 没有重新访问 UI Notes，也没有验证购买会员后能增加多少合格素材。
- R8 的真实用户选择、人工认证、同会话复查和恢复采集仍沿用此前待验证状态。
