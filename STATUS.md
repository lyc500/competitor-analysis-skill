# 项目当前状态

更新时间：2026-09-07
当前阶段：V0.1 第二轮阶段 3B——独立验收通过

## 阶段 1 本轮已完成

- [x] 增加 `task_contract.py`，校验任务字段、任务状态、竞品来源和规划策略。
- [x] 需求任务改为包含 `raw_request`、`assumptions`、`task_status`、`planning_strategy` 等字段。
- [x] 用户指定竞品优先保留并标记 `user_specified`；Agent 补充项标记 `agent_planned`；fixture 仅显式启用。
- [x] 更新 `SKILL.md`，明确 Agent 语义理解与 Python 确定性处理边界。
- [x] 新增阶段 1 测试和验收记录 `docs/acceptance/V0.1_STAGE1_ACCEPTANCE.md`。

## 阶段 1 当前限制

- 当前 Python 输入适配仅覆盖阶段 1 验收所需的明确短语，不是通用自然语言理解模型。
- 阶段 1：关闭；阶段 2：关闭；阶段 3A：关闭；阶段 3B：关闭并通过独立验收。

## 本轮已完成

- [x] 建立 `competitor_analysis_skill/` 最小 Skill 实现与根目录 `SKILL.md` 入口说明。
- [x] 实现需求解析、候选规划、公开来源采集器、质量筛选、统一素材 JSON、动态分类和 HTML 报告。
- [x] 将内置候选目录与公开来源采集器解耦；候选仅作为输入、测试和 fallback。
- [x] HTML 截图点击放大，无法确认页面图片时显示 `needs_manual_capture` 占位。

## 明确区分

### 已实现并验证的代码能力

- Skill 入口说明、Python 模块入口和 CLI 参数。
- 需求解析、候选规划与候选/采集器解耦。
- 公开来源采集器、图片基础质量筛选、失败状态记录。
- 统一素材 JSON、按素材差异选择地区/产品类型/页面结构模式、HTML 报告和放大脚本。

### 已通过单元测试的能力

- 需求解析、图片质量筛选、页面结构分类和地区分类选择。
- 公开采集器独立边界。
- JSON/HTML 产物生成和放大交互标记。
- `python3 -m unittest discover -s tests -v`：49 项通过（含阶段 1/2/3A 回归与阶段 3B 测试）。

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
- 阶段 3B 已通过独立验收；页面语义审核、用户上传和真机 fallback 仍属于尚未开始的阶段 3C。

## 尚未实现

- 真实公网竞品页面集成验收。
- 页面视觉语义审核、Logo/分享图/营销图排除和 `target_page` 语义确认（阶段 3C）。
- 用户上传、人工截图、iPhone 镜像和真机 fallback（阶段 3C）。
- 阶段 4 动态分类与正式报告修正。
- 复杂竞品分析、Dashboard 和轻量设计洞察。

## 当前最大问题

浏览器截图链路已经跑通，但尚未进行真实公网竞品页面集成验收；浏览器截图也尚未经过页面语义审核，因此不能直接视为有效竞品素材。

## 下一步建议

下一步：阶段 3C——页面语义审核与人工回退。Stage 3C 尚未开始；正式入口为 `--task-file`，自然语言 CLI 仅为 legacy/demo。
