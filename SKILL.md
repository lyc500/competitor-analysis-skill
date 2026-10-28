---
name: competitor-analysis
description: 根据自然语言需求搜集竞品页面、筛选公开素材、动态分类并生成可点击放大的 HTML 报告。
---

# 竞品分析 Skill

## 默认产品设计语境与来源顺序

当用户做产品设计竞品 UI 调研且没有明确指定 Desktop/Web 时，Agent 默认把移动端 App UI 作为主要目标，并在结构化 Task 中显式写入 `target_surface: mobile_app` 与 iOS/Android 平台。该判断来自 Agent 对任务语境的理解，不得在 Python 中按“搜索结果页”等关键词推断。

每个竞品按以下顺序发现来源：专业 UI / 设计参考数据库 → 其他公开 Web / 官方公开来源 → 用户上传 → device capture / iPhone 镜像。来源网站运行在 Web 不代表素材属于 Web UI；`source_type`、`source_provider`、`source_url`/`source_asset_url` 与目标素材的 `target_surface`、`platform` 分开记录。UI 数据库中的整站页面不是竞品素材，必须提取可确认产品、页面与 Surface 的完整单张 App Screen；不得绕过登录或付费限制。

## 海外页面命名映射与来源检索

当需求使用中文页面名称、但需要从海外产品或海外 UI 数据库搜集时，中文名称只能作为页面意图输入，不能直接当作唯一的英文检索词。Agent 必须先建立“页面意图 → 海外常用命名”的映射，再进入海外来源检索；这条规则适用于“我的”页，也适用于发布、搜索、详情、设置、首页等任何页面类型。

映射时不要只做逐字翻译，也不要把所有近义词当成同一个页面。至少生成一组可追溯的查询词：一个规范英文命名、若干产品常用别名、以及来源站点使用的分类/标签命名。原始中文需求、映射后的词族、每个来源实际使用的查询词和发现批次都要保留在候选登记/研究记录中。示例：

- “我的”/“个人中心” → `Profile`、`You`、`Me`、`Account`、`My Account`、`My Page`；其中 `Settings`、`Activity` 等相邻命名只能作为扩展发现词，不能因此自动判定为目标页。
- “账户/账号” → `Account`、`Profile`、`My Account`；若命中设置、登录或账户安全页面，仍按页面主任务单独判断。
- “发布/发帖” → `Create`、`Compose`、`Post`、`Publish`、`New Post`。
- “搜索发现/搜索入口” → `Search`、`Explore`、`Discover`、`Search Home`；必须继续区分输入前发现、联想词、已提交结果和加载状态。
- “详情” → `Details`、`Product Details`、`Post Details`、`Content Details`；列表卡片或入口页不因出现详情文案而自动纳入。

对“我的”这类页面，海外来源至少使用上述 `Profile`、`You`、`Me`、`Account`、`My Page` 词族中的相关变体，并结合来源 taxonomy 检索以下入口：PTTRNS 的 `Profile & Account` 分类（`https://app.pttrns.com/patterns?categories=profile-account`）、Refero 的 page type 15（`https://refero.design/apps/search?page_types%5Bid%5D%5B%5D=15`）、Mobbin 的 `My Account & Profile` screen pattern（`https://mobbin.com/search/apps/ios?content_type=screens&sort=popularity&filter=screenPatterns.My+Account+%26+Profile`）。这些入口是来源和检索线索，不代表页面已经通过语义审核；来源站点整页也不能直接作为竞品素材。

海外来源的正式检索记录至少要包含：原始页面名称、映射词族、来源入口 URL、实际查询词/分类、访问状态（`accessible`、`login_required`、`paywall`、`empty`、`error` 或 `blocked`）、实际看到的结果范围、分页/滚动批次和候选处置结果。来源 URL 或分类命中不等于有效素材；最终仍必须检查产品身份、目标页面角色/路径、交互阶段、渲染状态、目标 Surface/平台、单屏完整性和视觉质量。

若海外来源无法访问、需要登录/订阅、结果为空或只能看到数据库壳页面，不得绕过限制，也不得用固定 catalog、fixture 或历史报告补齐。先按下述访问准备判断限制是否实质影响本次覆盖；不影响时记录范围并继续，影响时完成一次性用户选择。确认公开范围或登录复查结果后，再换用同一来源的其他映射词和入口，并按来源顺序 fallback 到其他公开 Web、用户上传或 device capture。若仍无有效素材，保留 `rejected` / `not_reviewed` 记录并在报告中说明覆盖边界。

## 动态 UI 数据库的浏览器优先访问

UI 数据库的“文本可抓取”和“浏览器可用”是两个独立维度。对于依赖 JavaScript 渲染、登录会话、滚动加载、筛选交互或反爬验证的来源，必须采用浏览器优先策略：文本抓取只用于补充标题、链接和公开元数据，不能作为来源可用性的唯一判断。`文本抓取失败不等于来源不可用`。

每个来源尝试至少分别记录以下状态：

- `web_text_accessible`：文本/源码工具是否能读取页面内容。
- `browser_accessible`：真实浏览器是否能打开并渲染页面。
- `browser_interactive`：是否能完成必要的搜索、筛选、分页/滚动和打开候选。
- `content_available`：是否实际看到足以继续审核的候选内容。
- `access_status`：`accessible`、`login_required`、`paywall`、`empty`、`error` 或 `blocked`，并附实际观察范围和原因。

正式流程先用真实浏览器打开来源入口，等待页面渲染，按映射词族和站点 taxonomy 执行搜索/筛选，持续分页或滚动；若浏览器可交互，就继续候选发现和截图筛选，不因文本工具失败而提前 fallback。浏览器只能证明来源页面或候选可见，不能把数据库整页截图直接当作竞品素材；仍须提取产品明确、单屏完整、目标 Surface/平台匹配的 App Screen，并进入统一语义审核。

只有在浏览器也无法打开、无法完成必要交互、权限边界已按访问准备处理，或实际结果耗尽且没有符合页面准入门的候选时，才进入下一来源或用户上传/device capture fallback。不得绕过验证码、登录墙、订阅或访问控制；如果浏览器能打开但文本工具不能解析，记录为“浏览器可用、文本不可解析”，而不是“来源不可用”。

## 正式搜集前的来源访问准备

理解研究范围后、批量搜集前，Agent 只检查本次实际相关的常用来源，不遍历所有网站。检查必须发生在后续采集使用的浏览器与会话中，优先复用有效会话；不要主动退出、切换账号，或默认另开无登录态环境。每个来源快速验证页面打开、搜索、筛选、详情、完整原图和分页/滚动能力，并分别记录认证状态、访问边界、可见范围和覆盖影响。头像不等于采集能力可用，登录按钮也不等于全部内容不可用；局部可用就记录具体可用操作。

若登录、验证或会话过期实质影响覆盖，一次性向用户汇总：已可用来源、建议登录来源及影响、登录后仍可能存在的订阅范围、不登录继续的覆盖限制。提供“协助登录后继续”与“仅使用当前公开内容继续”。等待必要选择时暂停依赖该选择的采集；用户选择公开内容后，本批不再重复询问同一限制。没有实质影响时直接继续，不为了登录检查阻塞正常搜集，也不承诺登录后一定获得更多合格截图。

用户选择登录后，只走网站正常认证流程。账号选择、扫码、验证码或人工验证由用户完成；不得索取、输出或保存明文密码、验证码、cookie 或会话凭据，不自动购买订阅，也不绕过访问限制。用户完成后，Agent 必须在有效会话实际复查搜索、详情、原图和分页能力，再从已保存检查点继续；已完成的候选、下载和审核不重复计数。同一站点不同标签或会话能力不同时分别记录；会话过期后不能沿用旧的成功状态。

`access_preparation` 与既有来源登记一起保存：`checks` 记录 preflight/recheck、浏览器会话标签和能力；`decision` 记录是否无需选择、等待选择、公开继续或登录继续；`resume` 记录检查点、已完成、待继续和复查引用。Python 校验状态、引用、时间和候选分区，不通过页面文案推断登录。正式 `--capture-sources` 只接受同时包含 `source_attempts`、`candidates`、候选池与 `access_preparation` 的结构化来源登记，并在调用截图执行器前完成校验；旧 `sources` 列表只能离线读取、诊断或历史重放，不能触发实际采集。详细字段见 [来源访问准备契约](docs/SOURCE_ACCESS_CONTRACT.md)。来源网站认证状态与截图内目标 App 的 `login_state` 必须分开记录。

当前有效检查仍有 material 级 `login_required`、`security_verification` 或 `session_expired` 时，不能用 `not_required` 绕过一次性用户选择；历史检查曾受限但当前同会话复查已恢复时，以当前检查为准。正式截图从检查点构造执行集合：有效 `completed_candidate_ids` 只保留，不重复截图；只有 `remaining_candidate_ids` 中当前能力可用的候选交给截图执行器；`blocked` 不执行。完成项产物缺失或损坏时记录受影响候选并要求保留 ID、移回 remaining，不重置候选池或静默重跑全部。`captures.json.capture_execution` 保存计划、实际执行、跳过候选及原因。

## 开放式需求的高召回候选发现

当用户没有给出完整竞品名单，或明确要求“更多/热门/国内外/继续补充”时，先建立候选池，再进行准入筛选；竞品数量不设 3–5 个的小范围上限，但正式候选池最多 50 个。50 个是容量上限，不是应凑足的目标数量；若候选超过 50 个，按目标页面相关性、地区/产品类型覆盖、页面匹配度、素材质量和来源可追溯性排序保留，并在候选登记中记录截断原因。只有通过语义审核和质量审核的素材才进入最终报告，不能为了接近 50 个而放宽页面准入标准。

候选发现的停止条件必须与容量分开判断。未满 50 条时不能机械地“补满”后停止；达到 50 条后也不无限继续。Agent 根据研究问题的关键地区、代表性产品、设计问题和有效样本是否仍有实质缺口，以及新候选是否可能替换低价值候选，决定继续或停止。用户有明确截止时间或执行时间不足时，可以在保存已发现候选、未审核/截断处置、当前来源范围、剩余覆盖缺口和下一步补充方向后交付；不得把因时间或容量主动停止写成“来源耗尽”或“完整覆盖”。

发现阶段必须使用目标页面的语义同义词和产品类型扩展查询。对支持多种检索入口的 UI 数据库，至少组合两种可用模式（例如标签搜图、OCR 搜图、App 搜索或站内关键词）；每种模式都要记录查询词、检索模式、来源、分页/滚动批次和候选排名。搜索结果必须持续分页或下滑，直到连续两批没有新增且有意义的产品，或来源已经明确耗尽；不能只看首屏或第一批结果。

所有发现的产品和截图都要进入候选登记表，至少记录 `candidate_id`、产品名、来源 URL、查询词/模式、发现批次、页面角色/交互阶段/渲染状态初判、`candidate_status`（`accepted`、`rejected`、`not_reviewed`）和处置原因。候选未进入报告时必须留下 rejected 或 not_reviewed 记录并说明原因，不得静默丢弃；候选数量、有效素材数量、fallback 数量和未审核数量要能在最终交付中追溯。只有通过语义审核和质量审核的素材才进入最终报告，候选池本身不等于有效竞品。

若检索来源受权限、分页或结果可见性限制，先完成来源访问准备中的覆盖影响判断和必要用户决定，再记录实际看到的范围并继续使用下一优先级来源、用户上传或 device capture；不得把固定 catalog、fixture、历史验收结果或旧报告中的产品当作本次开放式发现的替代。发现阶段与最终竞品选择阶段分开，最终数量由任务覆盖度、页面匹配度、素材质量和来源可追溯性共同决定。

## 发现证据登记与跨阶段关联

正式发现记录必须把“来源访问准备”“来源尝试”和“候选登记”关联但分开保存，不把来源访问状态混入 `Source Candidate`。`sources.json` 至少包含以下五部分：

- `access_preparation`：相关来源的能力预检、一次性用户决定、登录后复查和恢复检查点；只保存会话标识和观察，不保存凭据。

- `source_attempts`：一次来源入口/查询/筛选/分页尝试一条记录，含 `id`、`entry_url`、`query_mapping`、`actual_query`、`search_mode`、`discovery_batch`、`web_text_accessible`、`browser_accessible`、`browser_interactive`、`content_available`、`access_status`、`observed_scope`、`attempt_status` 和 `failure_reason`。
- `candidates`：每个发现结果一条记录，含 `id`、`source_attempt_id`、产品与目标页、`source_entry_url`、`source_detail_url`、`source_asset_url`、候选排名、`candidate_status` 和 `disposition_reason`。
- `candidate_pool`：本轮实际进入截图/后续审核的候选 ID 列表。
- `candidate_limit`：明确 `max: 50`、计数单位 `candidate_records`、适用范围 `candidate_pool`、排序依据和 `truncated_candidate_ids`。

来源入口 URL、单屏详情 URL、图片资源 URL 可以不同，但必须分别使用 `source_entry_url`、`source_detail_url`、`source_asset_url`，并通过 `source_attempt_id` / `source_candidate_id` 关联。浏览器截图必须同时保留 `source_attempt_id`、`source_candidate_id`、`requested_url` 及三类来源 URL；语义审核和素材记录继续保留 `capture_id`、`source_candidate_id` 与 `source_attempt_id`。

跨阶段必须按以下链路校验：`source_attempts.id → candidates.source_attempt_id → captures.source_candidate_id → semantic_reviews.target_id → materials.capture_id → classification.material_ids → report`。缺失或错误引用必须明确报错；历史产物无法可靠还原时记录“历史证据缺口”，不编造 ID、浏览器操作、截图审核或运行记录。旧的仅含 `sources` 或仅含 `captures` 的产物只能作为兼容诊断输入，不能宣称满足正式证据契约。

候选状态只能是 `accepted`、`rejected` 或 `not_reviewed`，每条都必须有处置原因。超过 50 个时，50 个只限制 `candidate_pool` 的候选记录数；所有超出记录仍保留在 `candidates` 中，并写入 `not_reviewed`/`rejected` 与截断原因，不能静默丢弃。Python 只检查 ID、字段、URL 角色、状态和上限，不决定候选的页面相关性。

## 目标页面、交互阶段与状态先验

开始找素材前，Agent 必须把需求拆成三个互相独立的轴，并在结构化 Task 的假设或研究说明中写清楚本次纳入与排除的范围：

- `page_role / path`：用户要完成什么任务、处于哪条页面路径，例如发现/首页、列表/结果、详情、发布/创建、编辑、设置、确认/成功等。
- `interaction_stage`：用户动作处于什么阶段，例如操作前、输入或编辑中、提交/保存后、操作完成后。
- `render_state`：页面当前如何呈现，例如已加载完整、进行中/加载中、空结果、错误/权限/登录拦截、占位或新手引导。

页面角色、交互阶段和渲染状态不能互相替代。用户要求“发布页”时，首页上的加号只是入口，不等于发布编辑页；要求“详情页”时，列表卡片只是入口，不等于详情页；要求“设置页”时，设置入口所在的个人页也不等于设置页。反过来，如果用户明确要求首页、发现或入口体验，它们就可以作为目标页面，但必须在 Task 中明确写成目标角色。

通用默认状态策略：除非用户明确研究过程态或异常态，优先纳入“已加载、主体完整、可支持横向比较”的页面；默认排除加载中、空态、错误、权限/登录拦截、占位和未完成输入等过渡或异常状态。登录状态与页面角色必须分开判断：完整可用但未登录的目标页面标记为 `logged_out_complete`，只要主体和目标任务完整，可以纳入并在标签中保留未登录状态；出现登录墙、权限阻断或无法查看主体内容时标记为 `login_intercept`，默认排除并进入 fallback。若用户要求纳入过程态或异常态，必须把每种状态单独记录、单独分类，不能和正常完成态混成一个页面类别，也不能为了补足竞品数量放宽准入。

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

分类必须发生在语义准入之后。Agent 先明确本次主比较维度，再根据实际页面逐项归组：宽泛搜集可按页面主任务、业务类型或可见设计模式组织；有明确改版目标时优先按要解决的设计问题组织。跨行业样本只有在共同设计机制和本次研究价值都明确时才可同组。每个 collected Material 必须且只能进入一个分组；不能因都出现“会员”“钱包”“服务”“资产”等宽泛内容就强行合组，也不能按固定产品名称建立规则。

Classification Plan v2 必须保存主维度、适用范围，以及每组的纳入标准、共同机制、逐成员理由和与相邻组的差异。`material_labels` 至少保留 `page_role`、`path_stage`、`interaction_stage`、`render_state`、`login_state`。登录状态、交互阶段和页面路径要可区分，但未登录不能成为容纳不同业务的兜底组。自己的账户中心不等于他人的公开主页，个人中心首屏不等于服务抽屉或滚动下段；Target 式奖励余额不等于任务中心；迅雷式文件与云盘管理不因出现会员或推荐服务进入订单电商组。

分类完成后，桌面图墙以约 5 张卡片为一行容量。相邻小组在容量足够时整体并排，如 2＋2、3＋2；当前行剩余容量放不下下一组时，下一组整体换行，不拆卡填空，也不使用 dense 或瀑布流回填。单组超过一行容量时独占整行并在组内顺序换行；窄屏按 4/3/2/1 列逐级调整，不为塞满空位无限缩小截图。每组标题、副标题和边界保持独立，排版不得改变语义分组或研究顺序。

单个分组超过 20 张时，初始展示 20 张；每次点击“更多”再展开 20 张，直到该组全部展示。多组分别计数，展开后不得丢图、重复或串组；响应式切换要保留已经展开的状态。

单卡默认只显示产品名、平台/地区与影响理解的状态简标、完整比例截图、简短参考重点；明确设计目标时可再显示一条简洁借鉴。未登录、历史版本、抽屉、下段、子页、原图带标注等关键边界用短标识保留。完整路径/页面角色/渲染状态、版本日期、来源 URL、证据 ID、审核说明、适用条件与详细限制进入默认关闭的“页面详情”。这些字段仍保存在 `report_data.json`，详情中的来源链接和离线资产继续可用。图片放大与详情开关必须是独立控件，并支持键盘操作。

## 交付前反例检查

阶段 4 前，Agent 必须对候选和最终素材各做一次反例复核：是否把上游入口当成目标工作页、把相邻页面角色当成目标页面、把操作中或加载态当成完成态、把空态/错误/登录态当成正常内容、把低质量图当成有效素材、把错误产品/平台/页面 Surface 当成目标素材。发现任一问题时，拒绝并触发 fallback，而不是继续生成报告。

分析结论还要逐条复核：是否有实际素材支撑，是否说明值得参考什么，是否服务研究问题，是否忽略例外或过度推断，是否和其他结论重复，是否只是替换产品名也成立的空话。发现问题时删除或重写，不能只补一条泛化免责声明。Agent 自查应结构化保存并明确不是独立验证；Python 只能验证复核记录、字段和引用，不通过关键词、字数或评分宣称分析正确。

对同一素材，必须把可见事实、语义审核、分类理由、分组 takeaway、逐图建议和综合结论一起复核；任一层改写后回查其他层，不能只改默认卡片。这个复核由 Agent 对照原图完成，结构校验只能确认数据传递与引用一致。

最终报告验收至少确认：纳入和排除状态与需求一致；每张图只有一个分组；分类主维度、成员理由和相邻组差异可追溯；候选登记表中的 rejected / not_reviewed 有处置原因；fallback 原因可追溯；来源 URL 与素材身份对应；小组按顺序整体并排或换行且组内连续；超过 20 张的分组初始展示 20 张并独立逐次展开 20 张；桌面和移动端无无意义横向溢出；详情开关、键盘放大和关闭互不误触；卡片和放大视图都能看清支撑分类与结论的 UI 证据。

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

阶段 3B 浏览器工作流在显式 `--capture-sources` 下消费通过访问准备校验的正式 `sources.json` 并输出独立 `captures.json`。旧 `{"sources":[...]}` 可作为兼容诊断输入保存，但正式采集会在截图执行器运行前拒绝并提示迁移。Browser Capture 只证明候选 URL 被真实浏览器加载并截图；截图仍待阶段 3C 语义审核，不会自动成为 `semantic accepted` 或 `collected Material`。

阶段 3C 消费已有截图、来源登记和 Agent 的结构化视觉审核：

```bash
python3 -m competitor_analysis_skill --task-file <task.json> \
  --sources-file <sources.json> \
  --captures-file <captures.json> \
  --manual-captures-file <manual-captures.json> \
  --semantic-reviews-file <semantic-reviews.json> \
  --output reports/<name>
```

Agent 必须逐项判断产品身份、页面角色、交互阶段、渲染状态、登录状态、目标页面匹配、目标 Surface 匹配、页面主体完整性、图片类型和视觉可读性，并提供非空 `semantic_reason` 与 `review_reason_codes`。Review Contract 只要求 Python 校验这些字段的结构和允许值；不得由 Python 根据图片尺寸、关键词、文件名、URL、OCR 或图像规则推断截图语义。移动端 Task 只有 matched/matched/matched/complete/ui_page 才能声明 `semantic_status=accepted`。输出独立的 `reviewed_materials.json` 与 `fallback_requests.json`，不会提前进入分类或 HTML 报告。

阶段 4 消费 `reviewed_materials.json`、Agent 生成的 `classification-plan.json` 与 `--analysis-file analysis.json`：Python 只过滤三重状态均通过的 collected Materials、校验分类计划与分析引用、复制报告所需图片到独立 `assets/`，并生成 `classification.json`、`report_data.json` 和 HTML 报告。分类维度、分组、分组原因和多维 labels 全部来自 Agent；Python 不根据 `product_type`、`notes` 或关键词推断页面结构。无有效素材时输出 `unavailable` 和 fallback 清单。

### 报告分析交接

Agent 按 [报告内容契约 v2](docs/REPORT_CONTENT_CONTRACT.md) 先完成分析工作底稿，再压缩为报告内容。逐图记录具体区域、控件、信息和布局等可见事实；横向整理共性、差异与例外；形成支持什么任务及带来什么取舍的设计判断；再写对本次目标的借鉴建议、适用条件和证据边界。完整推理保存在结构化数据中，报告正文只展示有用结论。

每条有效推断尽量包含具体做法、参考价值和必要条件。以下内容不能充当主要分析：提升体验、层级清晰等通用口号；原样复述用户要求；纯控件清单；真实可追溯、点击放大等执行说明；截图没有支持的产品机制；没有数据的转化、留存、效率或频率结论。位置靠前不等于高频，卡片更大不等于更有效，用户要求强化会员也不等于直接做更大的会员卡。

头部只放整份报告最重要且有引用的发现，不凑固定数量；分类副标题用一句话说明这组应比较或借鉴什么，不重复组名、数量和状态；结尾综合各组的方案、条件和待验证事项，不复制头部。一句话需求总结样本模式、差异与适用场景，不编造用户产品或业务目标；详细需求结合真实现状、目标和约束给出建议顺序，不把原始长需求堆在头部。

分类计划的 `reason` 与 `audit` 解释为什么这样分；面向读者的一句话结论写在 `analysis.groups[].takeaway.statement`。使用稳定的组 ID、素材 ID 和分析过程 ID，允许一条判断引用多张图。区分可见观察、设计推断和待验证问题；缺少证据用 `information_gaps` 说明。Python 只检查契约、引用与完整覆盖，不代替 Agent 的语义与分析质量审核。

用户提供现状图或明确文字现状时才写 `current_state`，图片保存在分析输入目录内；有图时标出具体问题区域，分开保存可见事实、用户提供事实与 Agent 推断，并关联有竞品素材支撑的结论。现状不加入竞品 materials、classification 或覆盖统计。无现状就省略，不补空模块。没有使用数据时不得判断功能高频或低频，也不得仅凭截图决定不同会员业务必须合并。

默认顺序为：标题与核心结论 → 分类导航 → 可选且默认折叠的“现状与问题分析” → 分类截图与参考分析 → 默认整体折叠的“来源与筛选说明” → 竞品分析小结。卡片技术字段默认折叠，来源、分类审核与自查记录完整保留；可省略不适用模块，缺判断依据应简短说明。

分析源只维护在 `analysis.json`；`report_data.json.analysis` 是生成快照，不再独立改写。交付必须可经正式入口重新生成，不能靠生成后修改 HTML 才成立。使用 `--report-data-file <report_data.json> --classification-plan-file <revised-classification.json> --analysis-file <revised-analysis.json> --output <新目录>` 可整体替换分类和分析后重放；这不执行新来源搜集，不补造旧证据。v1 输入继续兼容但不会被标为满足 v2；`generation.analysis_standard` 只说明契约版本和复核类型，不等于语义正确。归档/重放始终标注历史时间与证据边界，不称为当前最新版。

正式报告必须分别展示来源访问统计、候选 `accepted/rejected/not_reviewed`、素材审核（语义审核）、素材流水线状态和产品 fallback；“素材流水线排除数为 0”不能被解释为“候选没有排除”。报告还要显示有效产品覆盖数、无有效素材产品数、待审核候选数和来源访问未知边界，并能回溯到登记记录。`report.html` 是最终交付；`sources.json`、`captures.json`、`reviewed_materials.json`、`fallback_requests.json`、`classification.json` 和 `report_data.json` 是阶段中间产物，不应单独冒充最终报告；`--offline`、fixture 和静态测试只属于离线演示/自动化验证。

安装浏览器依赖：

```bash
python3 -m pip install -r requirements.txt
python3 -m playwright install chromium
```

Python 只读取、校验、排序和持久化 Agent 提供的任务，不负责通过关键词或固定名单生成语义判断。自然语言位置参数仅保留为 `legacy/demo` 兼容入口，不代表通用自然语言理解能力；固定示例映射隔离在 `legacy_demo.py`，`requirements.py` 只保留旧导入别名，正式 `--task-file` 流程不调用该解析器。正式验收和生产使用不得用它替代结构化 Task、来源登记和截图审核。

legacy/demo 兼容入口（不承担通用语义理解）：

```bash
python3 -m competitor_analysis_skill "<自然语言调研需求>" --output reports/<name>
```

输出 `report.html` 和 `materials.json`，并在 `materials.json.compatibility` 标记 `legacy_demo_only` 与非正式入口。HTML 可直接打开，截图可点击放大；无法验证的页面显示 `needs_manual_capture`，不使用替代图片凑数。

历史产物若缺少来源尝试、候选处置或跨阶段 ID，只能在验收记录中标记为“历史证据缺口”；不能通过补写猜测字段把旧报告改标为正式验证通过。

## 执行边界

主流程是：Agent 理解需求并生成结构化任务、建立高召回候选池、登记候选处置状态、Python 校验任务契约、保留用户指定竞品并整理计划、公开来源采集、质量筛选、统一素材池、动态分类、报告生成。Agent 必须负责理解真实目标、识别目标页面、提取明确指定产品、规划必要的补充竞品、持续发现候选、记录假设和排除原因，并输出符合 `competitor_analysis_skill/task_contract.py` 的任务；随后才交给 Python。Python 只负责结构校验、状态校验、指定竞品优先排序和持久化，不能通过不断增加关键词或 `if/else` 假装成通用自然语言理解模型。

本阶段不接入 OpenAI API，也不增加模型调用依赖。任务不足以执行时使用 `task_status: needs_clarification`，不进入采集，且不能把该值写入素材 `collection_status`。

`catalog.py` 中的内置候选只允许通过显式 fixture/demo 路径使用，不能作为正式流程的自动 fallback。正式任务中用户指定竞品标记 `planning_source: user_specified`，Agent 补充竞品标记 `planning_source: agent_planned`；只有显式 fixture 任务才使用 `fixture_demo`。在线结果通过素材中的 `provenance: online` 标识；内置离线结果标记为 `builtin_candidate`。

## 扩展规则

新增来源应实现独立采集器并输出统一素材字段，不修改报告消费接口。Agent 根据 collected 素材差异选择地区、产品类型、页面结构或设计模式等维度并生成 Classification Plan；Python 只校验和稳定生成分组，不把任何单一维度作为固定模板。
