# 项目当前状态

更新时间：2026-09-07
当前阶段：V0.1 第二轮 Stage 5A——真实端到端验收准备完成，等待独立复验

## 阶段 1 本轮已完成

- [x] 增加 `task_contract.py`，校验任务字段、任务状态、竞品来源和规划策略。
- [x] 需求任务改为包含 `raw_request`、`assumptions`、`task_status`、`planning_strategy` 等字段。
- [x] 用户指定竞品优先保留并标记 `user_specified`；Agent 补充项标记 `agent_planned`；fixture 仅显式启用。
- [x] 更新 `SKILL.md`，明确 Agent 语义理解与 Python 确定性处理边界。
- [x] 新增阶段 1 测试和验收记录 `docs/acceptance/V0.1_STAGE1_ACCEPTANCE.md`。

## 阶段 1 当前限制

- 当前 Python 输入适配仅覆盖阶段 1 验收所需的明确短语，不是通用自然语言理解模型。
- Stage 1：关闭。
- Stage 2：关闭。
- Stage 3A：关闭。
- Stage 3B：关闭。
- Stage 3C：关闭。
- Stage 4：关闭并通过独立验收。

## 本轮已完成

- [x] 建立 `competitor_analysis_skill/` 最小 Skill 实现与根目录 `SKILL.md` 入口说明。
- [x] 实现结构化任务、竞品规划、公开来源候选、浏览器截图、Agent Review handoff、Agent Classification Plan 校验和 HTML 报告。
- [x] 将内置候选目录与公开来源采集器解耦；候选仅作为输入、测试和 fallback。
- [x] HTML 截图点击放大，无法确认页面图片时显示 `needs_manual_capture` 占位。

## 明确区分

### 已实现并验证的代码能力

- Skill 入口说明、Python 模块入口和 CLI 参数。
- 需求解析、候选规划与候选/采集器解耦。
- 公开来源采集器、图片基础质量筛选、失败状态记录。
- 统一素材 JSON；Agent 根据实际 collected 素材生成 Classification Plan，Python 校验计划并稳定生成分组、HTML 报告和放大交互。

### 已通过自动化测试的能力

- 需求解析、图片机械质量筛选、Classification Plan 契约与稳定分组；Python 不根据 `product_type`、`notes` 或关键词推断页面结构。
- 公开采集器独立边界。
- JSON/HTML 产物生成和放大交互标记。
- `python3 -m unittest discover -s tests -v`：81 项通过（含阶段 1/2/3A/3B/3C 回归、Stage 4 补正、真实 Chromium 测试和 Stage 5A Task Contract 检查）。

### 因当前网络环境无法真实验证的在线采集能力

- 访问百度、小红书、淘宝、Google、Bing、Amazon、YouTube、Pinterest 并取得可确认的真实页面图片。
- 在线图片的真实性、清晰度、完整性和页面版本质量。
- 指定首轮任务在线模式已执行并生成 8 个素材记录，但 8 条均为 `collection_status: needs_manual_capture`，不能描述为公开来源采集已完成。

### fallback / 内置候选能力

- `catalog.py` 的 8 个候选仅用于首轮输入和离线结构测试。
- `--offline` 产物标记 `provenance: builtin_candidate`，不是在线采集成功。
- 在线访问失败的产物标记 `provenance: online` 与 `needs_manual_capture`，表示尝试了在线采集但失败，不是 fallback 图片。

## 阶段 2 已实现并通过独立验收

- `--task-file` 正式入口支持 `--materials-file` 素材输入；任务竞品不被覆盖。
- 统一素材契约、来源枚举校验、报告目录内路径标准化和外部文件复制。
- Pillow 真实解码、完整性、扩展名/格式一致性、尺寸、文件大小、SHA-256 与完全重复识别。
- `semantic_status` 与 `quality_status` 分离；只有两者均 accepted 且路径有效才为 `collected`。
- `og:image`/`twitter:image` 候选保持 `web_candidate` 与 `pending`。

## 阶段 3A 已实现并通过独立验收

- 新增独立 Source Candidate 契约、URL 标准化、稳定 ID、同竞品去重和 `sources.json` 持久化。
- 正式入口支持 `--task-file + --sources-file`；候选只保持 `candidate_status=pending`，不进入素材或截图流程。
- Agent 负责发现公开来源 URL，Python 不访问 URL、不搜索互联网、不下载图片。

## 阶段 3B 已实现并通过独立验收

- 新增真实 Playwright Chromium 浏览器截图、动态等待、截图元数据、机械质量检查和 `captures.json`（Playwright 1.60.0，Chromium 148.0.7778.96）。
- 增加 public-only DNS/IP 防护、重定向防护、HTTP/超时/空白渲染失败记录；截图不进入 Material、分类或报告图墙。
- 阶段 3B 已通过独立验收；其截图现由阶段 3C 的 Agent Review handoff 审核后进入统一 Material 流程。

## 阶段 3C 已实现并通过独立验收

- [x] Agent Semantic Review Contract：由 Agent 提供产品身份、目标页面、主体完整性和素材类型判断，Python 只校验契约一致性。
- [x] Browser Capture → Material：captured 截图必须逐条审核，并重新通过阶段 2 机械质量校验。
- [x] 用户上传 handoff 与 device/manual capture handoff：两类来源均需同一套 Agent Review。
- [x] `reviewed_materials.json`、`fallback_requests.json` 和 open/resolved 回退状态。
- [x] semantic + mechanical 双门槛 collected；Stage 3C 结果不进入现有分类和 HTML 报告。

## Stage 4 已关闭并通过独立验收

- [x] collected-only 报告输入与 Agent Classification Plan 契约校验。
- [x] 动态分类、多维 Agent labels、`classification.json` 和 `report_data.json`。
- [x] HTML 图墙、点击放大、unavailable/fallback 清单和自包含 `assets/`。
- [x] 真实 Chromium 报告交互与移动 viewport 测试。
- [x] Stage 4 资产目标改用 Material ID 的确定性 SHA-256 摘要文件名，并防御性拒绝目标路径逃逸。
- [x] 恢复 Stage 2 `--materials-file` collected 正式流程兼容；非 Stage 4 分支不要求 Classification Plan，也未恢复关键词分类 heuristic。
- [x] 校验 fallback open/resolved 与 collected Material 事实一致性。
- [x] 真实移动报告目录后，由 Chromium 验证主图和放大图均可加载。

## Stage 5A 已准备完成，等待独立复验

- [x] 保存 Task A / B 的确定性用户输入与本次 Agent 生成的 Task Contract；竞品清单不写入 production catalog、planner 或 Python 固定映射。
- [x] Task A 使用 `agent_only`，覆盖国内与海外搜索结果页；Task B 保留四个用户指定直播产品并使用 `mixed` 补充代表性竞品。
- [x] 新增 Task / Planning Contract 与防固定目录回归测试，不使用 mock、假公网截图或假 collected Material 冒充真实 E2E。
- [x] 建立 Stage 5B / 5C 真实产物目录与运行记录规范，不创建空的成功产物。
- [x] 建立 V0.1 MVP Acceptance Report 骨架并写明后续硬门槛。

## 尚未实现

- 完整真实公网竞品 E2E 验收。
- iPhone 镜像自动化。
- 复杂竞品分析、Dashboard 和轻量设计洞察。

## 当前最大问题

浏览器截图与结构化 Agent Review handoff 已跑通，但尚未进行真实公网竞品页面端到端验收；未经 Agent Review 和机械质量双重通过的截图仍不能视为有效竞品素材。

## 下一步建议

等待 Stage 5A 独立复验。Stage 5B 尚未执行，Stage 5C 尚未执行，不在 Stage 5A 进行真实公网采集。完整真实公网竞品 E2E 尚未完成，V0.1 MVP 尚未完成，iPhone 镜像自动化仍未实现。Stage 4 已生成 `classification.json`、`report_data.json` 和自包含 HTML 报告，`reviewed_materials.json` 已正式接入 Stage 4 分类与图墙。正式入口为 `--task-file`，自然语言 CLI 仅为 legacy/demo。
