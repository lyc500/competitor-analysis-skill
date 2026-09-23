---
name: competitor-analysis
description: 根据自然语言需求搜集竞品页面、筛选公开素材、动态分类并生成可点击放大的 HTML 报告。
---

# 竞品分析 Skill

## 默认产品设计语境与来源顺序

当用户做产品设计竞品 UI 调研且没有明确指定 Desktop/Web 时，Agent 默认把移动端 App UI 作为主要目标，并在结构化 Task 中显式写入 `target_surface: mobile_app` 与 iOS/Android 平台。该判断来自 Agent 对任务语境的理解，不得在 Python 中按“搜索结果页”等关键词推断。

每个竞品按以下顺序发现来源：专业 UI / 设计参考数据库 → 其他公开 Web / 官方公开来源 → 用户上传 → device capture / iPhone 镜像。来源网站运行在 Web 不代表素材属于 Web UI；`source_type`、`source_provider`、`source_url`/`source_asset_url` 与目标素材的 `target_surface`、`platform` 分开记录。UI 数据库中的整站页面不是竞品素材，必须提取可确认产品、页面与 Surface 的完整单张 App Screen；不得绕过登录或付费限制。

## 目标页面、交互阶段与状态先验

开始找素材前，Agent 必须把需求拆成三个互相独立的轴，并在结构化 Task 的假设或研究说明中写清楚本次纳入与排除的范围：

- `page_role / path`：用户要完成什么任务、处于哪条页面路径，例如发现/首页、列表/结果、详情、发布/创建、编辑、设置、确认/成功等。
- `interaction_stage`：用户动作处于什么阶段，例如操作前、输入或编辑中、提交/保存后、操作完成后。
- `render_state`：页面当前如何呈现，例如已加载完整、进行中/加载中、空结果、错误/权限/登录拦截、占位或新手引导。

页面角色、交互阶段和渲染状态不能互相替代。用户要求“发布页”时，首页上的加号只是入口，不等于发布编辑页；要求“详情页”时，列表卡片只是入口，不等于详情页；要求“设置页”时，设置入口所在的个人页也不等于设置页。反过来，如果用户明确要求首页、发现或入口体验，它们就可以作为目标页面，但必须在 Task 中明确写成目标角色。

通用默认状态策略：除非用户明确研究过程态或异常态，优先纳入“已加载、主体完整、可支持横向比较”的页面；默认排除加载中、空态、错误、权限/登录拦截、占位和未完成输入等过渡或异常状态。若用户要求纳入这些状态，必须把每种状态单独记录、单独分类，不能和正常完成态混成一个页面类别，也不能为了补足竞品数量放宽准入。

来源标题、URL、文件名和数据库标签只能作为候选线索，不能替代对截图本身的判断。一个页面上出现目标控件（搜索框、加号、购物车、设置入口等），不代表该截图就是目标页面；必须以页面主任务、主体内容和交互阶段的可见证据为准。

搜索类需求只是上述模型的一个实例，至少区分：

- `search_discovery / input_before`：尚未提交查询的搜索入口，包含搜索框以及热榜、推荐、关注对象等发现内容。
- `autocomplete / typed_not_submitted`：已输入词但尚未提交的联想词或建议列表。
- `search_results / submitted_loaded`：已提交查询且结果内容已经加载，可看到与查询对应的结果、结果 Tab 或筛选结构。
- `search_results / submitted_loading`：已提交查询但仍在加载、骨架屏或空白等待状态。

因此，默认情况下“搜索发现页”只纳入 `search_discovery / input_before`，“搜索结果页”只纳入 `search_results / submitted_loaded`；联想、加载、空态和异常态只有在需求明确包含时才纳入，并分别记录。

## 目标页面准入门

阶段 3C 的语义审核必须按以下顺序逐项回答，并把结论写入 `semantic_reason`：产品身份 → 目标页面角色/路径 → 交互阶段 → 渲染状态 → 目标 Surface / 平台 → 页面主体完整性 → 图片类型 → 视觉可读性。任一关键项不匹配就拒绝该素材，不能因为来源标签或页面上的某个目标控件而强行接收。

特别注意以下反例：

- 上游首页或推荐页中的目标入口，不等于目标工作页；例如搜索框不等于搜索发现页，加号不等于发布/编辑页。
- 列表卡片、Tab、导航入口或快捷操作，不等于对应的详情、结果或设置页面。
- 已输入但未提交、已编辑但未保存、已点击但仍在等待的页面，不等于动作完成后的页面。
- 加载中的 Tab、spinner、骨架屏、大面积空白、错误提示或登录拦截，不等于已加载且主体完整的目标页。
- 一张局部裁切、浏览器壳层、拼接图或无法确认产品身份的图，不等于完整竞品 App Screen。

误匹配素材必须保留明确的 `rejected` 原因，并进入 fallback 规划；不得把它静默移动到其他分组，也不得为了增加竞品数量降低页面准入标准。

## 视觉质量准入门

机械质量校验（尺寸、文件可读性、HTTP 状态等）只是必要条件，不是接受条件。Agent 还必须在报告卡片尺寸和点击放大后的尺寸分别检查：核心文字是否可读、目标控件/导航/表单/内容主体是否清晰、页面是否足以支持横向比较，以及是否被浏览器背景、压缩、裁切或大面积无信息区域严重干扰。

低分辨率、压缩严重、核心内容不可读或几乎只有空白占位的素材应拒绝；只有当用户明确研究空态、加载态或占位态时，才可将这类状态作为单独目标接收。接受素材时，`semantic_reason` 必须同时说明它为什么属于目标路径、处于什么状态，以及哪些可见 UI 证据支撑该判断，不能只写“图片有效”或“URL 可访问”。

## 状态隔离、动态分类与报告布局

分类必须发生在语义准入之后。Agent 根据本次素材实际呈现的页面路径、交互阶段、渲染状态、结果对象、地区、产品类型或设计模式动态生成 Classification Plan；每个 collected Material 必须且只能进入一个分组。至少保留 `path_stage`、`state`、`page_role`、`result_object` 等能解释页面差异的 labels，不能只按产品类型或竞品名称分组。

同一目标页面角色下也要保持交互阶段和渲染状态隔离：操作前、输入/编辑中、提交/保存后、已完成、加载中、空态/错误态/登录态应分别标记；如果某状态不在本次需求范围内，直接排除而不是塞入相邻分组。分类完成后，报告图墙在每个分组内尽量把同类竞品放在同一行，桌面端最多 5 列，只有超过 5 张时才换行；窄屏保持响应式换行。布局不能用来掩盖语义混组，必须先完成准入和分类，再做排版。

## 交付前反例检查

阶段 4 前，Agent 必须对候选和最终素材各做一次反例复核：是否把上游入口当成目标工作页、把相邻页面角色当成目标页面、把操作中或加载态当成完成态、把空态/错误/登录态当成正常内容、把低质量图当成有效素材、把错误产品/平台/页面 Surface 当成目标素材。发现任一问题时，拒绝并触发 fallback，而不是继续生成报告。

最终报告验收至少确认：纳入和排除状态与需求一致；每张图只有一个分组；fallback 原因可追溯；来源 URL 与素材身份对应；同类图墙符合最多 5 列的布局规则；报告卡片和放大视图都能看清支撑分类的 UI 证据。

## 使用入口

正式入口要求 Agent 先完成语义理解和竞品规划，输出结构化任务 JSON，再执行：

```bash
python3 -m competitor_analysis_skill --task-file <task.json> --output reports/<name>
```

公开来源发现的正式 handoff：Agent 根据结构化 Task 使用可用公开搜索/Web 能力发现候选 URL，写入 `sources-file`，再由 Python 校验、标准化、去重并持久化 `sources.json`：

```bash
python3 -m competitor_analysis_skill --task-file <task.json> --sources-file <sources-input.json> --output reports/<name>
```

`sources-file` 只表示公开来源候选，不是截图或素材；当前阶段不会访问 URL、下载图片、截图或将候选标记为 `collected`。Agent 负责来源发现和候选上下文，Python 只负责契约校验与确定性处理。fixture 仅用于测试/demo。

阶段 3B 浏览器工作流在显式 `--capture-sources` 下消费 `sources.json` 并输出独立 `captures.json`。Browser Capture 只证明候选 URL 被真实浏览器加载并截图；截图仍待阶段 3C 语义审核，不会自动成为 `semantic accepted` 或 `collected Material`。

阶段 3C 消费已有截图和 Agent 的结构化视觉审核：

```bash
python3 -m competitor_analysis_skill --task-file <task.json> \
  --captures-file <captures.json> \
  --manual-captures-file <manual-captures.json> \
  --semantic-reviews-file <semantic-reviews.json> \
  --output reports/<name>
```

Agent 必须逐项判断产品身份、目标页面匹配、页面状态、目标 Surface 匹配、页面主体完整性、图片类型和视觉可读性，并提供 `semantic_reason`。移动端 Task 只有 matched/matched/matched/complete/ui_page 才能声明 `semantic_status=accepted`；页面状态纳入范围和视觉质量结论也必须在 `semantic_reason` 中明确说明。Python 只校验 Review Contract，并将 ui_database、browser、user_upload、device_capture 统一交给阶段 2 机械质量复验；它不通过图片尺寸、关键词、文件名、URL、OCR 或图像规则推断语义。输出独立的 `reviewed_materials.json` 与 `fallback_requests.json`，不会提前进入分类或 HTML 报告。

阶段 4 消费 `reviewed_materials.json` 和 Agent 生成的 `classification-plan.json`：Python 只过滤三重状态均通过的 collected Materials、校验分类计划、复制报告所需图片到独立 `assets/`，并生成 `classification.json`、`report_data.json` 和 HTML 报告。分类维度、分组、分组原因和多维 labels 全部来自 Agent；Python 不根据 `product_type`、`notes` 或关键词推断页面结构。无有效素材时输出 `unavailable` 和 fallback 清单。

安装浏览器依赖：

```bash
python3 -m pip install -r requirements.txt
python3 -m playwright install chromium
```

Python 只读取、校验、排序和持久化 Agent 提供的任务，不负责通过关键词或固定名单生成语义判断。自然语言位置参数仅保留为 `legacy/demo` 兼容入口，不代表通用自然语言理解能力。

legacy/demo 兼容入口（不承担通用语义理解）：

```bash
python3 -m competitor_analysis_skill "<自然语言调研需求>" --output reports/<name>
```

输出 `report.html` 和 `materials.json`。HTML 可直接打开，截图可点击放大；无法验证的页面显示 `needs_manual_capture`，不使用替代图片凑数。

## 执行边界

主流程是：Agent 理解需求并生成结构化任务、Python 校验任务契约、保留用户指定竞品并整理计划、公开来源采集、质量筛选、统一素材池、动态分类、报告生成。Agent 必须负责理解真实目标、识别目标页面、提取明确指定产品、规划必要的补充竞品、记录假设，并输出符合 `competitor_analysis_skill/task_contract.py` 的任务；随后才交给 Python。Python 只负责结构校验、状态校验、指定竞品优先排序和持久化，不能通过不断增加关键词或 `if/else` 假装成通用自然语言理解模型。

本阶段不接入 OpenAI API，也不增加模型调用依赖。任务不足以执行时使用 `task_status: needs_clarification`，不进入采集，且不能把该值写入素材 `collection_status`。

`catalog.py` 中的内置候选只允许通过显式 fixture/demo 路径使用，不能作为正式流程的自动 fallback。正式任务中用户指定竞品标记 `planning_source: user_specified`，Agent 补充竞品标记 `planning_source: agent_planned`；只有显式 fixture 任务才使用 `fixture_demo`。在线结果通过素材中的 `provenance: online` 标识；内置离线结果标记为 `builtin_candidate`。

## 扩展规则

新增来源应实现独立采集器并输出统一素材字段，不修改报告消费接口。Agent 根据 collected 素材差异选择地区、产品类型、页面结构或设计模式等维度并生成 Classification Plan；Python 只校验和稳定生成分组，不把任何单一维度作为固定模板。
