# Stage 5B-R1 Task A 移动端重新验收运行记录

## 执行信息

- 原始需求：`帮我搜集一下海内外热门产品的搜索结果页。`，与上一轮完全一致。
- 执行日期：2026-09-08。
- 执行 Agent：Codex。
- 执行起始 commit：`8b6e477bdd1860e6da5d7502cb77939369af728a`；开始时本地 `HEAD` 与 `origin/main` 一致且工作区 clean。
- Python：3.9.6；Playwright：1.60.0；Pillow：11.3.0。
- Chromium：148.0.7778.96，真实 headless Chromium；未使用 mock。
- 新输出目录：`reports/acceptance/task-a-mobile/`；上一轮 `reports/acceptance/task-a/` 未删除或覆盖。

## Task Contract 与 Agent 规划

Task 保持原始自然语言不变，并显式写入 `target_page = 搜索结果页`、`target_surface = mobile_app`，有效目标平台仅为 iOS/Android。Agent 按移动端信息组织的横向研究价值规划起点读书、LinkedIn 与 WhatsApp，分别覆盖数字阅读的多内容标签、职业检索的筛选决策列表、即时通信的跨实体结果分区；CN 与 Global 均有代表产品。

该竞品清单只保存在本次验收 Task 和报告中，没有写入 production catalog、planner 或 Python 固定映射。Surface 由 Agent 写入 Task，Python 不根据“搜索结果页”、产品类型、URL、图片尺寸或 notes 推断。

## 来源发现与 App Screen 提取

Agent 先用真实 Chromium 打开 UI Notes 与 Refero 的公开页面并检查候选。完整数据库页面只保存为 `evidence/source-*.png`；最终素材通过页面公开展示的单图链接取得 App Screen 原图，并保留来源页面 URL 与 `source_asset_url`。没有绕过登录、付费墙或安全限制。

完整尝试、拒绝和 fallback 记录见 `SOURCE_ATTEMPTS.md`。最终四张素材均来自 Priority 1 `ui_database`，因此三个竞品都未进入 public Web fallback。

## 正式 Python 流程

来源候选先经正式 Source Candidate 契约持久化为 `sources.json`。从数据库提取的 App Screen 及真实来源元数据写入 `captures.json`，Agent 逐张视觉检查后提供 `semantic-reviews.json`，再执行 Stage 3C：

```text
python3 -m competitor_analysis_skill \
  --task-file reports/acceptance/task-a-mobile/task.json \
  --captures-file reports/acceptance/task-a-mobile/captures.json \
  --semantic-reviews-file reports/acceptance/task-a-mobile/semantic-reviews.json \
  --output reports/acceptance/task-a-mobile
```

四张图片随后均由 Pillow 重新完成解码、尺寸、格式、文件大小、SHA-256 和重复检查。Agent 查看 collected 素材后生成 Classification Plan，再执行 Stage 4：

```text
python3 -m competitor_analysis_skill \
  --task-file reports/acceptance/task-a-mobile/task.json \
  --reviewed-materials-file reports/acceptance/task-a-mobile/reviewed_materials.json \
  --classification-plan-file reports/acceptance/task-a-mobile/classification-plan.json \
  --output reports/acceptance/task-a-mobile
```

## 语义与机械结果

| 产品 | 来源 | Screen | Agent Semantic Review | Mechanical Quality | 最终状态 |
| --- | --- | --- | --- | --- | --- |
| 起点读书 | UI Notes | 作品标签搜索结果 | product/page/surface matched；complete；ui_page | accepted，480 × 1039 WebP | collected |
| 起点读书 | UI Notes | 漫画标签搜索结果 | product/page/surface matched；complete；ui_page | accepted，480 × 1039 WebP | collected |
| LinkedIn | Refero | 职位搜索结果 | product/page/surface matched；complete；ui_page | accepted，488 × 1056 JPEG | collected |
| WhatsApp | Refero | 联系人与通话搜索结果 | product/page/surface matched；complete；ui_page | accepted，488 × 1057 JPEG | collected |

结果汇总：4 个有效 Mobile App UI、3 个不同产品；CN 1 个有效产品 / 2 张，Global 2 个有效产品 / 2 张；4 张均来自专业 UI 数据库。三个 fallback request 均为 resolved，没有伪造 user upload 或 device capture。

## Classification 与报告

Agent 根据四张实际 Screen 选择“移动端搜索结果的任务与信息组织方式”作为分类维度，形成“多内容类型分栏结果”“筛选驱动的职业决策列表”“跨通信实体分区结果”三个分组。每个 collected Material 恰好进入一个分组；Python 只校验 Agent Plan，没有恢复关键词 classification heuristic。

Stage 4 输出 `classification.json`、`report_data.json`、`report.html` 和自包含 `assets/`。本轮图墙只含四张 `target_surface = mobile_app`、`target_surface_match = matched`、平台为 iOS 的 collected Material；上一轮 Amazon / 哔哩哔哩 Desktop Web 素材没有进入新报告。

## 真实 Chromium 报告验证

- 本地 HTTP：200。
- `.asset-image`：4。
- 主图 `naturalWidth`：`[480, 480, 488, 488]`。
- 主图 `naturalHeight`：`[1039, 1039, 1056, 1057]`。
- 实际点击第一张起点读书 App Screen 后 `dialog[open]` 成功出现。
- dialog 图片：`naturalWidth = 480`、`naturalHeight = 1039`。
- 资源请求失败：0。
- 证据：`evidence/report-page.png`、`evidence/report-dialog-open.png`。

## 完整验证

提交前执行 `python3 -m unittest discover -s tests -v`、`python3 -m compileall competitor_analysis_skill tests`、验收产物一致性检查和 `git diff --check`。最终测试数字以提交前实际结果为准，不允许 skip 隐藏问题。

## 结论

Stage 5B 首次执行保留为工程 E2E 真实验证成功、产品验收失败的历史证据；失败原因是四张有效素材全部属于 Desktop Web，且没有优先执行专业 UI 数据库来源。

本次 Stage 5B-R1 已达到移动端产品自验收硬门槛，状态为“移动端 Task A 补正执行完成，等待 GPT 独立复验”。Stage 5C 未执行；V0.1 MVP 未完成；iPhone 镜像自动化未实现。
