# 第 3 阶段：信息层级与布局重放

日期：2026-10-27

本目录使用第 2 阶段已经复核的两组历史截图、分析和分类，重新生成通用报告并验收信息层级、分类块并排、折叠和图片交互。它是**历史素材布局重放**：没有访问第三方来源，没有重新检查来源登录态，也不把历史截图描述为当前最新版。

## 场景与报告

| 场景 | 报告 | 覆盖 |
| --- | --- | --- |
| 一句话搜集国内外 App“我的”页 | [report.html](one-sentence-my-pages/generated/report.html) | 20 个产品、26 张竞品图、7 组；无现状模块 |
| 虎牙“我的”页改版参考 | [report.html](detailed-my-page-redesign/generated/report.html) | 9 个竞品、10 张竞品图、4 组；1 张现状图另计 |

验证脚本逐项比较了 Stage 2 与 Stage 3 的 `analysis`、完整 `groups` 和 assets：分析相等、组名/成员/理由/审核依据相等，26/11 个图片文件逐字节相等。Stage 3 只为详细场景增加两个显式展示状态：腾讯视频 `annotation_status=original_annotated`，哔哩哔哩 `version_status=historical_version`；它们只控制“原图带标注”“历史版本”短标，不改变分类或结论。

## 通用能力验收

- 主卡默认只显示产品名、平台/地区、关键状态短标、截图和参考重点；详细需求场景再显示一条简洁借鉴。
- 页面角色、路径、交互/渲染状态、完整分析条件和限制、版本日期、来源 URL、证据链及审核说明都保留在默认关闭的“页面详情”。来源 URL 可点击，离线图片仍从独立 `assets/` 加载。
- 一句话场景实测学习资产 2＋创作身份 2 同排、账户设置 1＋账户下段 1 同排；媒体文件 2 后的 10 张交易组整体换到下一行。
- 详细场景首个 5 张大组独占一行，后续 2＋1＋2 三组同排。各组保留独立标题、副标题、上边界和顺序。
- 自动化另覆盖单组 1/2/3/5/6/20 张、2＋2、3＋2、4＋2、21/45 张与多组独立展开。视口切换不重置已展开数量，素材 ID 顺序不变。
- 现状与来源默认关闭；无现状时不输出模块。竞品分析小结是最后主要模块。重大覆盖缺口只显示一句短提示，完整统计留在来源折叠区。
- 竞品图和现状图均支持点击或键盘 Enter 放大；Escape 与关闭按钮可关闭，详情开关不会触发放大。

## 重新生成

`build_inputs.py` 从 Stage 2 分类输入派生本轮显示状态，只用于验收留痕，不是生产分类器。报告仍由通用 CLI 生成：

```bash
python3 -B reports/manual-acceptance/user-feedback-optimization-2026-10-27/stage3-layout-replay/build_inputs.py

python3 -B -m competitor_analysis_skill \
  --report-data-file reports/manual-acceptance/user-feedback-optimization-2026-10-27/stage2-analysis-replay/one-sentence-my-pages/generated/report_data.json \
  --classification-plan-file reports/manual-acceptance/user-feedback-optimization-2026-10-27/stage3-layout-replay/one-sentence-my-pages/classification-plan.json \
  --output reports/manual-acceptance/user-feedback-optimization-2026-10-27/stage3-layout-replay/one-sentence-my-pages/generated

python3 -B -m competitor_analysis_skill \
  --report-data-file reports/manual-acceptance/user-feedback-optimization-2026-10-27/stage2-analysis-replay/detailed-my-page-redesign/generated/report_data.json \
  --classification-plan-file reports/manual-acceptance/user-feedback-optimization-2026-10-27/stage3-layout-replay/detailed-my-page-redesign/classification-plan.json \
  --output reports/manual-acceptance/user-feedback-optimization-2026-10-27/stage3-layout-replay/detailed-my-page-redesign/generated
```

## 验证证据

[verification.json](evidence/rendered/verification.json) 记录实际 DOM、几何、折叠、图片加载、键盘放大、模块顺序和 1440/390 无溢出结果。

- [一句话场景桌面长图](evidence/rendered/one-sentence-my-pages-desktop.png)
- [一句话场景移动首屏](evidence/rendered/one-sentence-my-pages-mobile.png)
- [详细场景桌面长图](evidence/rendered/detailed-my-page-redesign-desktop.png)
- [详细场景移动首屏](evidence/rendered/detailed-my-page-redesign-mobile.png)
- [详细场景现状模块展开](evidence/rendered/detailed-current-expanded.png)

全量自动化 159 项通过，0 failure/error/skip；运行保留既有 socket `ResourceWarning` 与一次测试服务器 BrokenPipe 日志。旧归档与 Stage 1/2 产物没有被覆盖。本阶段没有实施 R8/B1 来源预检和会话恢复。
