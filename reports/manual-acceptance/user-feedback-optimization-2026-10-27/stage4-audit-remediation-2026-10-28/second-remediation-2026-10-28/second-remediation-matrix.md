# 第二轮修正矩阵

| 优先级 | 根因 | 修改位置 | 回归与实际验证 | 结果与限制 |
| --- | --- | --- | --- | --- |
| P1 正式旧来源格式绕过 | pipeline 在旧 `sources` 兼容分支中先调用截图执行器，之后才用 `legacy_incomplete` 标记证据缺口 | `competitor_analysis_skill/pipeline.py`、`__main__.py`、`tests/test_capture_workflow.py`、README、SKILL、`docs/SOURCE_ACCESS_CONTRACT.md` | pipeline mock 观察执行器实参；正式 CLI 子进程拒绝；独立 CLI main 探针记录 `executor_calls=0`、无 `captures.json` | 通过。旧格式仍可无采集读取和诊断；任何 `--capture-sources` 都要求正式来源与访问准备 |
| P1 分析底层理由残留越界 | 第一轮只改了部分默认文案，事实、分类理由与综合概括没有作为同一证据链同步复核 | 两场景 `input/analysis.json`、`classification-plan.json`，场景 A `stage3c/reviewed_materials.json`，SKILL、报告内容契约 | 逐图查看 10 张唯一入选源图；正式生成后检查 report_data、classification 与 HTML；浏览器展开来源说明检查分类审核 | 通过。豆包不再称任务对象清楚；Wise 不再含安全/退出；NYT 只作当前下段局部参考；Airbuds 用于身份与个人内容表达 |
| P2 整个 captures 文件缺失不列 ID | 文件不存在分支在读取候选完成列表前只输出通用错误 | `competitor_analysis_skill/pipeline.py`、`tests/test_source_access.py` | 整个文件缺失时稳定列出全部 completed ID；个别记录缺失时只列受影响 ID；两种情况执行器均未运行 | 通过。恢复提示要求保留候选 ID 并显式移回 remaining，不静默重跑全部 |
| P2 Airbuds 综合概括错误 | 综合小结把身份/内容表达误写成关系资料 | 场景 A `analysis.json`、`classification-plan.json` | 原图显示身份、最近播放与收藏；报告小结改为 Duolingo 支持好友关系、Airbuds 支持个人内容表达 | 通过。保留 Airbuds 的具体参考价值，没有推断未显示的关系数据 |

## 已通过能力的保护

检查点恢复、报告正式生成与快照、分类 reason/takeaway 分离、默认折叠、小组并排、移动响应式、独立渐进展开、原比例图片与键盘放大、现状统计隔离、稳定证据引用和综合小结末尾位置均通过全量测试与两份报告的 Chromium 检查。
