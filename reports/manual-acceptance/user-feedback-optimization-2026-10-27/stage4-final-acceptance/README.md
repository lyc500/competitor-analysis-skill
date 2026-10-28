# 第 4 阶段：来源访问准备与最终验收

本目录是 2026-10-27 的新验收运行，不覆盖旧报告。来源访问与素材下载使用当时已有的 Chrome“用户1”会话；正式报告由同一通用 CLI 从结构化输入生成，HTML 未手工修改。

## 结果边界

- 场景 A 在 UI Notes、Refero 当前可见范围得到 14 个可审核候选，9 张通过目标页和机械质量审核，5 张因设置页、内容详情、他人主页或抽屉状态与宽泛“我的页”目标不符而拒绝。
- 场景 B 使用 6 张通过审核的竞品图和 1 张用户测试归档的虎牙现状图。现状图仅是明确输入基线，不计入竞品数量。
- 通用设置页验证使用同一张 Refero Duolingo 图片：在场景 A 中因页面角色不符被拒绝，在“设置页”任务中被接受。该验证只证明流程通用，不承担完整设置页研究。
- 这是新来源访问与新证据链运行。豆包爱学、多邻国、酷狗及 Refero 首批候选来自本次可见列表；哔哩哔哩、拼多多、斗鱼使用历史候选 ID 作为查找种子，但本次重新打开真实详情和原图并下载、审核，标记为“种子复查”，不冒充首次发现。原始图片哈希和尺寸见 `raw-asset-manifest.json`。
- UI Notes、Refero、Mobbin 都是已有账号会话但受订阅范围限制；PTTRNS 新标签需要登录。限制未实质阻断本批覆盖，因此没有询问用户 A/B，也没有执行新的登录或拒绝登录流程。真实“登录后复查并恢复”和真实“用户选择公开继续”仍未触发；状态流只由契约/夹具验证，不能写成第三方网站实测通过。

## 正式产物

| 场景 | 结构化输入 | 审核素材 | 最终报告 |
| --- | --- | --- | --- |
| A：一句话搜集 | `scenario-a-my-pages/input/` | `scenario-a-my-pages/stage3c/reviewed_materials.json` | `scenario-a-my-pages/report/report.html` |
| B：虎牙改版目标 | `scenario-b-redesign/input/` | `scenario-b-redesign/stage3c/reviewed_materials.json` | `scenario-b-redesign/report/report.html` |
| 设置页小验证 | `generic-settings-validation/input/` | `generic-settings-validation/stage3c/reviewed_materials.json` | `generic-settings-validation/report/report.html` |

每个场景都依次运行来源登记、Stage 3C 逐图审核和正式 Stage 4。9 条实际命令、stdout、stderr 与退出码保存在 `actual-command-log.json`。`build_acceptance_inputs.py` 可确定性重建验收输入；`run_acceptance.py` 可重新执行正式链路；`verify_reproducibility.py` 从保存的审核素材、分类和分析重新生成到临时目录，并把逐文件 SHA-256 比较写入 `reproducibility.json`。

## 来源访问证据

- `source-access-observation.json`：真实浏览器会话、标签 ID、六项能力、认证状态、访问边界、可见范围与覆盖影响。
- `source-access-observation.md`：为什么本批没有阻塞并请求 A/B 选择。
- `raw-assets/` 与 `raw-asset-manifest.json`：真实来源详情页下载的 14 张图片、尺寸与 SHA-256。
- 各场景 `input/sources-input.json`：`access_preparation`、来源尝试、候选、50 条容量契约和本次决定。
- 各场景 `stage2/sources.json`：正式入口规范化后的同一记录；可保存后再次校验。

来源网站认证状态与截图内 App 登录状态独立保存。报告把来源能力和候选过程放在默认折叠的“来源与筛选说明”，把未登录、抽屉和历史版本等影响理解的素材状态留在卡片短标。

## 浏览器与人工验收

`browser_acceptance.py` 使用本地 Playwright Chromium 打开三份新报告，检查图片真实加载、详情/现状/来源默认关闭、综合小结为最后模块、键盘放大与 Escape 关闭、1440/390 无横向溢出，并保存：

- `browser-evidence/browser-validation.json`
- `browser-evidence/scenario-a-my-pages-desktop.png`
- `browser-evidence/scenario-a-my-pages-mobile.png`
- `browser-evidence/scenario-b-redesign-desktop.png`
- `browser-evidence/scenario-b-redesign-mobile.png`
- `browser-evidence/generic-settings-validation-desktop.png`
- `browser-evidence/generic-settings-validation-mobile.png`

桌面几何实测：场景 A 的 2＋3 同排，下一行 2＋1＋1；场景 B 的 2＋2 同排，第三个 2 张组整体换行。移动端全部按单列顺序连续显示。完整人工逐图与结论复核见 `manual-analysis-review.md`。

## 验收资料分类

- **文档检查**：SKILL、README、来源访问契约、报告内容契约、任务书、STATUS。
- **契约/夹具测试**：预检、一次性选择、公开继续、登录后同会话复查、订阅仍受限、会话过期、网络异常、恢复分区、B1 字段传递。
- **历史重放**：Stage 1–3 目录，仅证明旧素材上的结构、分析和布局回归；本目录没有把它们当作新来源证据。
- **真实搜集**：`source-access-observation.*`、`raw-assets/`、来源/候选/截图链。
- **人工语义审核**：各场景 `semantic-reviews.json`、`analysis.json` 和 `manual-analysis-review.md`。
- **本地真实浏览器验收**：`browser-evidence/`。

逐项结果与证据位置见 `acceptance-matrix.md`。测试总数只证明机械回归，分析质量结论来自逐图人工复核。

最终执行结果见 `test-results.md`：全量 175 项自动化通过，三场景 9 条正式命令通过，三份报告浏览器验收通过，三份报告从保存输入逐文件精确再生成。Skill 规则的独立压力复测也确认候选容量、停止检查点和访问准备后的 fallback 顺序已补齐。
