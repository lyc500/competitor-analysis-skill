# 独立审计修正与复验（2026-10-28）

> 后续独立复验发现正式旧来源格式仍可绕过访问准备，以及若干底层分析理由残留越界。第一轮记录保留为当时事实；第二轮闭环证据见 [second-remediation-2026-10-28](second-remediation-2026-10-28/README.md)。

本目录针对最近一次“部分通过”独立审计的 3 个 P1 与 2 个 P2 做根因修正。原审计结论和 `stage4-final-acceptance/` 交付保留；本目录是新增修正证据，不把历史失败改写成从未发生。

本轮结论为 **部分通过**：三个 P1 和两个 P2 的可执行代码、结构化分析、正式生成与自动化回归已修正；R8 的真实用户登录／拒绝登录、同会话复查与恢复因当前真实来源没有出现 material 级认证限制而未触发，仍不能标为全面真实通过。

## 修正报告

- [场景 A：一句话搜集“我的”页](scenario-a-my-pages/report/report.html)
- [场景 B：虎牙“我的”页改版参考](scenario-b-redesign/report/report.html)

两份报告均由本目录保存的 Task、reviewed materials、classification plan 和 analysis 通过正式 `--task-file` 入口生成。使用的是 2026-10-27 已归档真实素材，不是 2026-10-28 新采集；没有直接修改生成后的 HTML。

## 证据索引

- [修正矩阵](audit-remediation-matrix.md)
- [分析文案前后对照](analysis-before-after.md)
- [自动化与实际命令结果](test-results.md)
- [结构化命令日志](actual-command-log.json)
- [真实来源访问复验](source-access-revalidation.md) / [JSON](source-access-revalidation.json)
- [报告可复现性](reproducibility.json)
- [浏览器验收 JSON](browser-evidence/browser-validation.json)
- 桌面／移动整页截图：`browser-evidence/*.png`
- [历史用户测试归档只读清单](historical-archive-manifest.json)

## 事实边界

- 自动化已覆盖 `not_required` 绕过、公开继续、登录复查、恢复检查点、阻塞和完成产物损坏。
- 真实 Chrome 已复查 UI Notes、Refero、Mobbin 和 PTTRNS 的当前能力；这不是新候选搜集。
- 当前只有 PTTRNS 匿名限制，且对本批已归档证据影响为 minor，因此未向用户制造一次登录选择。真实登录或公开继续链路仍待未来 material 限制触发。
- Skill quick validator 在 `/tmp` 隔离 venv 中补装 PyYAML 后通过；项目依赖未增加。
- 本轮未 commit、未 push、未安装生效。
