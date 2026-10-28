# 第 2 阶段：历史素材分析重放

日期：2026-10-27

本目录使用 2026-10-26 两个真实用户场景已经接受的截图，重新执行逐图观察、横向比较、分类和报告分析。它是**历史素材分析重放**：没有重新访问第三方来源，没有重新检查 UI 数据库登录态，也不把历史截图描述为当前最新版。

## 场景与结果

| 场景 | 结构化输入 | 正式输出 | 覆盖 |
| --- | --- | --- | --- |
| 一句话搜集国内外 App“我的”页 | [classification-plan.json](one-sentence-my-pages/classification-plan.json)、[analysis.json](one-sentence-my-pages/analysis.json) | [report.html](one-sentence-my-pages/generated/report.html)、[report_data.json](one-sentence-my-pages/generated/report_data.json) | 20 个产品、26 张竞品图、7 组；没有现状模块 |
| 虎牙“我的”页改版参考 | [classification-plan.json](detailed-my-page-redesign/classification-plan.json)、[analysis.json](detailed-my-page-redesign/analysis.json) | [report.html](detailed-my-page-redesign/generated/report.html)、[report_data.json](detailed-my-page-redesign/generated/report_data.json) | 9 个竞品、10 张竞品图、4 组；1 张现状图另计 |

两份分析均为 `schema_version: 2`，保存逐图事实、证据边界、横向比较、设计判断、建议、适用条件、限制和最终 Claim 引用。`quality_review.review_type=agent_self_review` 且 `independent=false`，只证明执行了交付前自查，不是独立质量验证。

## 关键修正

- 一句话场景改以页面主任务和可见设计机制分类。原“未登录的完整个人中心”兜底组被删除，登录态改为逐图标签。
- 迅雷按下载、云盘、文件统计与容量管理归入“媒体与文件库”，不再与订单、电商页面同组。
- 不背单词两张截图只显示会员、虚拟资产、装备与个性化设置，拆入“学习资产与个性化设置”，不再用未出现的学习进度解释该组。
- Target 在一句话场景属于交易与消费权益；在详细场景单列“会员收益与奖励结果”，不再与任务动作和进度等价。
- 自己的账户/个人中心、公开主页、首屏、子页、滚动下段和已打开抽屉均保留不同标签或组边界。
- 虎牙现状图标出会员与功能入口区、任务中心区、游戏与更多服务区；可见事实、用户目标和设计推断分开保存，并分别关联竞品结论。
- 头部、分类副标题、单卡分析和结尾小结均由结构化 v2 输入生成。详细前后对照见 [before-after.md](before-after.md)。

## 可重复生成

`build_inputs.py` 记录本轮历史素材的人工分析输入生成过程，只用于验收留痕，不是生产分类器，也不包含关键词或固定产品规则。正式报告由通用 CLI 生成：

```bash
python3 -B reports/manual-acceptance/user-feedback-optimization-2026-10-27/stage2-analysis-replay/build_inputs.py

python3 -B -m competitor_analysis_skill \
  --report-data-file reports/manual-acceptance/user-feedback-optimization-2026-10-27/stage1-replay/one-sentence-my-pages/generated/report_data.json \
  --classification-plan-file reports/manual-acceptance/user-feedback-optimization-2026-10-27/stage2-analysis-replay/one-sentence-my-pages/classification-plan.json \
  --analysis-file reports/manual-acceptance/user-feedback-optimization-2026-10-27/stage2-analysis-replay/one-sentence-my-pages/analysis.json \
  --output reports/manual-acceptance/user-feedback-optimization-2026-10-27/stage2-analysis-replay/one-sentence-my-pages/generated

python3 -B -m competitor_analysis_skill \
  --report-data-file reports/manual-acceptance/user-feedback-optimization-2026-10-27/stage1-replay/detailed-my-page-redesign/generated/report_data.json \
  --classification-plan-file reports/manual-acceptance/user-feedback-optimization-2026-10-27/stage2-analysis-replay/detailed-my-page-redesign/classification-plan.json \
  --analysis-file reports/manual-acceptance/user-feedback-optimization-2026-10-27/stage2-analysis-replay/detailed-my-page-redesign/analysis.json \
  --output reports/manual-acceptance/user-feedback-optimization-2026-10-27/stage2-analysis-replay/detailed-my-page-redesign/generated
```

## 浏览器验收

运行 `verify_render.py` 的本地 Chromium 检查，结果保存在 [verification.json](evidence/rendered/verification.json)。两份报告的图片均可加载和放大；卡片详情、来源说明和现状默认关闭；综合小结是最后一个主要模块；1440px 与 390px 视口均无横向溢出。

渲染证据：

- [一句话场景桌面长图](evidence/rendered/one-sentence-my-pages-desktop.png)
- [详细场景桌面长图](evidence/rendered/detailed-my-page-redesign-desktop.png)
- [详细场景展开后的现状分析](evidence/rendered/detailed-my-page-redesign-current.png)

旧归档与第 1 阶段产物没有被覆盖。本阶段没有实施小分类并排（R3）或正式采集前登录预检与会话恢复（R8）。

## 自动化与可复现性

- 分析、分类和正式入口定向测试 37 项通过；全量 153 项通过，0 failure/error/skip。全量运行保留既有 socket `ResourceWarning` 与一次测试服务器 BrokenPipe 日志。
- 从相同 Stage 1 快照和本目录两份结构化输入重放到独立 `/tmp` 目录后，`classification.json`、`report_data.json`、`report.html` 和全部 assets 与验收目录逐字节一致。
- 2026-10-26 旧真实用户测试归档的 90 个文件与实施前 SHA-256 清单完全一致。
- Chromium 验收结果见 `verification.json`：一句话场景 26 张图/7 组，详细场景 10 张竞品图/4 组加 1 张独立现状图；桌面与 390px 窄屏均无横向溢出。
