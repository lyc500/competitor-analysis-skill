# 项目当前状态

更新时间：2026-09-04
当前阶段：V0.1 第二轮阶段 1——需求理解与竞品规划

## 阶段 1 本轮已完成

- [x] 增加 `task_contract.py`，校验任务字段、任务状态、竞品来源和规划策略。
- [x] 需求任务改为包含 `raw_request`、`assumptions`、`task_status`、`planning_strategy` 等字段。
- [x] 用户指定竞品优先保留并标记 `user_specified`；Agent 补充项标记 `agent_planned`；fixture 仅显式启用。
- [x] 更新 `SKILL.md`，明确 Agent 语义理解与 Python 确定性处理边界。
- [x] 新增阶段 1 测试和验收记录 `docs/acceptance/V0.1_STAGE1_ACCEPTANCE.md`。

## 阶段 1 当前限制

- 当前 Python 输入适配仅覆盖阶段 1 验收所需的明确短语，不是通用自然语言理解模型。
- 尚未开始阶段 2–5：图片质量、浏览器截图、页面语义确认、动态分类和 HTML 优化均保持未实现。

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
- `python3 -m unittest discover -s tests -v`：7 项通过。

### 因当前网络环境无法真实验证的在线采集能力

- 访问百度、小红书、淘宝、Google、Bing、Amazon、YouTube、Pinterest 并取得可确认的真实页面图片。
- 在线图片的真实性、清晰度、完整性和页面版本质量。
- 指定首轮任务在线模式已执行并生成 8 个素材记录，但 8 条均为 `collection_status: needs_manual_capture`，不能描述为公开来源采集已完成。

### fallback / 内置候选能力

- `catalog.py` 的 8 个候选仅用于首轮输入和离线结构测试。
- `--offline` 产物标记 `provenance: builtin_candidate`，不是在线采集成功。
- 在线访问失败的产物标记 `provenance: online` 与 `needs_manual_capture`，表示尝试了在线采集但失败，不是 fallback 图片。

## 尚未实现

- 用户上传截图自动接入。
- iPhone 镜像自动化或人工协作流程。
- 动态网页的真实浏览器截图适配器。
- 复杂竞品分析、Dashboard 和轻量设计洞察。

## 当前最大问题

本轮环境无法解析外部域名，`reports/search-results/report.html` 是完整的缺失状态报告，不是已完成截图搜集的验收样本。动态站点后续通常需要 Playwright、浏览器控制或专门截图服务。

## 下一步建议

在具备公开网络访问能力的执行环境重跑指定任务，并视动态页面情况接入浏览器截图适配器；保持 `online` 与 `builtin_candidate` provenance 区分。
