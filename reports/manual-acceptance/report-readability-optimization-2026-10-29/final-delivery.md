# 报告可读性与样本覆盖固化交付记录

日期：2026-10-29（Asia/Shanghai）

## 通用实现

- 头部只消费 Agent 已归纳的 `overall.statement` 与可选 `overall.recommendation`，分别显示为“结论”“建议”；`key_findings` 只在折叠依据中出现，不再由 renderer 拼接。
- v2 覆盖评估按核心问题保存素材 ID、横向比较 ID、策略、覆盖状态与分原因缺口。标记可比较时至少需要两个不同产品；同一产品重复截图不会增加独立案例数。
- 正式分析的覆盖评估和用户选择必须与当前 `research.question` 一致；样本不足时只有本次用户明确选择可继续或补源，选择补源会阻止报告提前发布。
- v1 只允许显式历史重放。未提供分析仍可生成兼容图墙，但保持 `analysis_status=missing`、`standard_acceptance=not_assessed`，不能作为分析完成。
- SKILL 明确直白表达复核、来源受限后的替代来源、登录/订阅区分、一次汇总选择和检查点续跑。Agent 判断语义质量，Python 只校验结构与门槛。

## 报告

- [场景 A](scenario-a-replay/report/report.html)：9 张历史素材，无用户现状；头部归纳继续内容、身份关系和多业务分区。
- [场景 B](scenario-b-replay/report/report.html)：6 张历史竞品图＋1 张用户现状图；覆盖 limited，任务入口是单案例，订阅限制与发现不足分别记录。
- 两份均为历史素材重放，不是 2026-10-29 新采集。

## 验证

- 全量：`python3 -B -m unittest discover -s tests -p 'test_*.py' -q`，196 项通过，0 failure/error/skip；保留 3 条 socket `ResourceWarning`。
- `PYTHONPYCACHEPREFIX=/private/tmp/competitor-analysis-pycache python3 -m compileall -q competitor_analysis_skill tests`：通过。
- Skill Creator quick validator：`Skill is valid!`。
- `git diff --check`：通过。
- Chromium：1440×1000 与 390×844 下两份报告图片加载、无横向溢出；来源默认折叠；放大与 Escape 关闭通过。截图见 `browser-evidence/`。
- 非个人中心用例：自动化将同一通用流程用于“搜索结果页筛选参考”，确认头部不包含虎牙、会员或任务中心专用文案。
- 历史 v0.1 归档内容哈希汇总：`45dbe272f9bd6e4818e0f3824e965cee49f8d997d6f75d845225f8344f0d95a4`。

## 已知限制

- R8 的真实“用户选择登录或公开继续—人工认证—同会话复查—恢复采集”仍未完整触发。
- UI Notes 购买会员后能增加多少合格素材未验证。
- NYT 截图与 You 标签根层首屏的关系未证实，只作可见下段局部参考。
