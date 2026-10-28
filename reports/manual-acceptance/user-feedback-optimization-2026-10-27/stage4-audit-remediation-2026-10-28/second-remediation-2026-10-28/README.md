# 第二轮定向修正与复验准备

日期：2026-10-28。

本目录记录用户转述的最新独立复验发现及其第二轮修正。仓库中没有该次复验工具的原始输出文件，因此本文不把用户提供的审计文本伪装成独立执行记录。第一轮审计、修正矩阵和历史失败记录保留在上级目录。

本轮关闭四个问题：正式 `--capture-sources` 的旧 `sources` 格式绕过；豆包、Wise、NYT 的底层分类/事实残留；整个 `captures.json` 缺失时不列候选 ID；Airbuds 被概括为关系资料。修正均落在通用执行门禁、结构化分析源或契约中，两份 HTML 只由正式入口重生成。

证据：

- [第二轮修正矩阵](second-remediation-matrix.md)
- [分析前后对照](analysis-before-after.md)
- [旧格式 CLI 负向探针](legacy-cli-negative-probe.json)
- [临时目录重生成一致性](reproducibility.json)
- [浏览器验收结果](browser-validation.json)
- [测试与校验结果](test-results.md)
- [实际命令记录](actual-command-log.json)
- [场景 A 报告](../scenario-a-my-pages/report/report.html)
- [场景 B 报告](../scenario-b-redesign/report/report.html)

R8 的真实“用户选择登录或公开继续—人工认证—同会话复查—恢复采集”仍未发生。本轮只修复旧格式可绕过门禁的实现缺陷；自动化覆盖不能替代未来真实触发链路的证据。
