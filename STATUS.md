# 项目当前状态

更新时间：2026-10-28
当前阶段：正式 GitHub 交付与本地 Skill 更新已完成；新会话加载与真实来源预检已验证，两类新报告受外部工具审批阻塞；R8 真实登录链路仍待触发

## 2026-10-28 正式交付与生效验证

- [x] 已将全部验收实现、契约、测试和脱敏证据提交为 `4d982ebb8334f06ef650a301266a0074afb6cd9f`，直接推送 `origin/main`；`git ls-remote` 确认远端 main 与本地一致。
- [x] 实际 Codex Skill 位于 `/Users/yuchunli/.codex/skills/competitor-analysis`。更新前版本 `4d889ab` 已保留为本地回退分支 `rollback/pre-user-feedback-optimization-20261028`；安装仓库以 fast-forward 更新到交付提交。
- [x] 安装目录关键文件哈希与交付仓库一致，Python 实际导入路径指向安装目录；quick validator 通过，安装目录全量 190 项测试通过，保留 3 条 socket `ResourceWarning`。
- [x] 两个新 Codex 会话从自然语言请求触发安装 Skill，独立确认加载路径/提交并复用 Chrome 会话预检 UI Notes、Refero、Mobbin、PTTRNS；场景 B 正确把虎牙现状图标为历史输入且不计竞品。
- [ ] 两会话均因各自外部工具审批等待，尚未完成新的素材保存、结构化分析和正式 HTML 报告；审批解除后应在原会话续跑，不把当前状态记为两类真实任务全面通过。
- [x] 完整交付记录见 [正式交付与生效验证](reports/manual-acceptance/user-feedback-optimization-2026-10-27/stage4-audit-remediation-2026-10-28/second-remediation-2026-10-28/delivery-2026-10-28.md)。

## 2026-10-28 第二轮修正独立复验

- [x] 独立复验正式 CLI 与 pipeline：旧 `{"sources":[...]}` 在截图执行器前被拒绝，执行器调用 0 次且不生成 `captures.json`；离线兼容不采集，合法公开继续仍可执行允许候选。
- [x] 独立逐图复核豆包、Wise、NYT、Airbuds 及其事实、语义审核、分类理由、快照、默认卡片、折叠区和综合小结；四项越界已闭环，NYT 根层关系继续明确标为待验证。
- [x] 独立构造整个 `captures.json` 缺失和个别记录缺失；错误分别列出全部或受影响候选 ID，均未调用截图执行器。
- [x] 正式入口临时重生成 A 12 个、B 10 个文件，文件集合与逐文件 SHA-256 和交付报告一致；独立 Chromium 内容检查通过。
- [x] 独立全量测试 190 项通过，0 failure/error/skip；保留 socket `ResourceWarning` 与 BrokenPipe 非阻塞日志。`compileall`、`git diff --check`、quick validator、历史归档 90/90 哈希与 mtime 校验通过。
- [x] 复验记录见 [第二轮修正独立复验](reports/manual-acceptance/user-feedback-optimization-2026-10-27/stage4-audit-remediation-2026-10-28/second-remediation-2026-10-28/independent-revalidation-2026-10-28.md)。
- [ ] R8 真实“用户选择登录或公开继续—人工认证—同会话复查—恢复采集”仍未触发；这是外部证据缺口，不记为全面通过，也不视为当前代码缺陷。

## 2026-10-28 第二轮定向修正

- [x] 后续独立复验发现第一轮“3 个 P1 已全部修复”的结论过早：正式 `--capture-sources` 仍允许旧 `{"sources":[...]}` 绕过访问准备。本轮把门禁前移到截图执行器之前；旧格式只保留无采集读取/诊断兼容。正式 CLI main 探针记录执行器调用 0 次、无 `captures.json`。
- [x] 完整 `captures.json` 缺失时，错误稳定列出检查点中的全部 completed candidate ID；个别记录缺失只列受影响 ID。两种错误都要求保留 ID 并显式移回 remaining，不静默重跑候选池。
- [x] 两场景全部入选素材重新逐图复核。豆包分类理由不再称“任务对象清楚”；Wise 的事实、卡片、semantic reason 与分类理由全部移除截图未显示的安全/退出；NYT 只依据当前可见下段分析；Airbuds 只支持身份与个人内容表达，好友关系证据只引用 Duolingo。
- [x] `SKILL.md` 与报告内容契约明确同一素材的可见事实、语义审核、分类理由、takeaway、逐图建议和综合结论必须一起复核；Python 继续只验结构与引用，不以关键词代替语义判断。
- [x] 两份报告通过正式 task-file 入口重生成，临时目录 A 12 个、B 10 个文件集合与 SHA-256 全部一致。Playwright Chromium 复核图片、折叠分类理由、桌面小组并排、移动顺序、详情/放大、现状隔离和结尾小结通过。
- [x] 定向测试 85 项、最终全量 190 项通过，0 failure/error/skip；全量输出 3 条 localhost socket `ResourceWarning`。compileall、`git diff --check`、隔离 quick validator 与历史归档 90 个文件 SHA-256 校验通过。
- [x] 修正证据见 [第二轮验收记录](reports/manual-acceptance/user-feedback-optimization-2026-10-27/stage4-audit-remediation-2026-10-28/second-remediation-2026-10-28/README.md)。本轮不 commit、不 push、不安装。
- [ ] R8 真实“用户选择登录或公开继续—人工认证—同会话复查—恢复采集”仍未触发；自动化已覆盖，真实证据继续待未来 material 级限制出现时补充。

## 2026-10-28 独立审计针对性修正

- [x] 修复 material 级认证限制可被 `not_required` 绕过：校验以每个来源当前有效检查为准；当前仍受限时必须取得一次性用户选择，历史限制已由复查解除时不误阻塞。
- [x] 正式截图入口与访问校验共用当前检查和决定。`pending_user_choice`／`waiting_for_login` 不调用截图执行器；`public_only` 只执行当前能力允许的候选；登录后复查的候选保留真实会话要求。
- [x] 修复恢复链路忽略候选检查点：有效完成截图从既有产物加载并验证，只有 remaining 候选传给执行器；全部完成不调用执行器，blocked 不执行。损坏／缺失完成产物明确报候选 ID，不静默重跑全部。
- [x] 回归测试直接观察正式 pipeline 传给截图执行器的候选，覆盖当前重大限制＋not_required、公开继续、待选择 gate、全部／部分恢复、阻塞／解除、历史限制解除和损坏产物。
- [x] 固定自然语言示例映射隔离至 `legacy_demo.py`；`requirements.py` 只保留兼容别名，正式 task-file 流程测试确认不调用 legacy parser；demo 输出标记 `legacy_demo_only`。
- [x] 两个场景的结构化分析源完成逐图修正。场景 B 不再把入口写成任务进度，不把用户提出的会员目标写成现状事实，并将大卡片竞争改为条件性方案取舍；场景 A 将概括收窄到本批样本，纠正根层设置口径，九张卡片分别给出具体动作、条件或补充验证价值。
- [x] 修正报告由正式 task-file 入口生成到 [独立修正目录](reports/manual-acceptance/user-feedback-optimization-2026-10-27/stage4-audit-remediation-2026-10-28/README.md)，未手改 HTML。A/B 独立 `/tmp` 重生成分别 12／10 个文件逐字节一致。
- [x] Playwright Chromium 对两份修正报告完成桌面／移动复验：图片、默认折叠、分类导航、小组并排、详情开关、键盘放大和综合小结顺序通过；人工查看保存的四张整页截图。
- [x] 同一真实 Chrome 配置复查 UI Notes、Refero、Mobbin、PTTRNS。前三者详情可用但有订阅边界；PTTRNS 当前匿名、搜索与详情不可用，对本批覆盖影响为 minor，未触发登录选择。自动化链路已覆盖，真实“选择登录／拒绝登录—同会话复查—恢复”仍未发生，R8 不标全面实证通过。
- [x] 在 `/tmp` 隔离 venv 安装 PyYAML 后运行 Skill Creator quick validator：`Skill is valid!`；未增加项目依赖。
- [x] 最终全量自动化 **186 项通过，0 failure/error/skip**；定向 capture workflow 12 项、source access 22 项、analysis 16 项、report content pipeline 12 项通过。`compileall`、`git diff --check` 和隔离环境 quick validator 通过；旧用户测试归档仍为 90 个文件，本轮无文件修改时间落在 2026-10-28。本轮不 commit、不 push。

## 2026-10-28 用户反馈优化：第 4 阶段来源访问准备与最终验收

- [x] 新增 `source_access.py` 与 [来源访问准备契约](docs/SOURCE_ACCESS_CONTRACT.md)：同一份 `sources.json` 保存预检能力、认证/订阅/网络边界、覆盖影响、一次性用户决定、登录后复查和候选恢复位置；规范化结果可再次校验，不保存密码、验证码、cookie 或会话凭据。
- [x] 正式 `--capture-sources` 在存在来源/候选结构时要求有效访问准备；等待用户选择或等待登录会明确停止。批量截图按会话 ID 复用同一 Playwright context，不同会话隔离；声明 Agent 桌面认证会话时不会伪装成 Python 已复用。
- [x] 关闭 B1 正式链路缺口：候选继承来源类型、提供方、目标 Surface 和会话标签；语义产物补齐 `target_page`；来源尝试、候选、截图、审核、素材、分类和报告引用连续。来源网站登录态与截图内 App 登录态分别记录。
- [x] 真实浏览器预检 UI Notes、Refero、Mobbin 与 PTTRNS：前三者已有账号会话且局部受订阅限制，PTTRNS 新标签需要登录；其他来源可见范围足以支撑本批研究，因此未触发 A/B 阻塞。没有强迫重新登录或购买订阅；真实登录恢复与真实“仅公开继续”仍标为未触发，未用 mock 冒充实测。
- [x] 在 [Stage 4 新验收目录](reports/manual-acceptance/user-feedback-optimization-2026-10-27/stage4-final-acceptance/README.md) 保存任务、来源准备、候选处置、14 张新下载原图与哈希、逐图审核、分类/分析、正式命令、报告、本地资产、浏览器截图、人工分析复核和 R1–R8（含 R5A）逐项表。历史候选仅作为查找种子的素材明确标为本次重新打开详情/原图后的“种子复查”。
- [x] 两个真实场景由同一正式入口重跑：场景 A 14 个候选、9 张接受、5 张因页面角色/阶段不符拒绝；场景 B 6 张竞品图＋1 张独立虎牙现状图。另以同一张多邻国设置图做小范围设置页任务，证明准入规则没有写死为个人中心或虎牙。
- [x] 三份报告的真实 Chromium 验收通过：图片资源全部加载，详情/现状/过程默认关闭，键盘放大与 Escape 关闭可用，1440/390 无横向溢出，综合小结为最后主要模块。桌面实测场景 A 2＋3、2＋1＋1，场景 B 2＋2 后第三组整体换行；代表性截图与 JSON 在 `browser-evidence/`。
- [x] 分析由 Agent 逐图人工复核事实、引用、分类、参考价值、例外和推断边界；自动化只验证契约和行为。R1–R7、R5A 完成；R8 通用实现与真实预检完成，真实新登录/用户拒绝分支因本批未触发而保持未实测状态。
- [x] 最终验证：全量 **175 项通过，0 failure/error/skip**，有 3 条既有 localhost socket `ResourceWarning`；三场景 **9 条正式命令通过**；三份报告 Chromium 验收通过；保存输入再生成的 **26 个报告文件逐字节一致**；`compileall`（使用 `/tmp` 可写缓存）、`git diff --check` 和 Skill frontmatter 均通过。
- [x] Skill 独立压力复测通过：50 条容量与覆盖充分分开判断；时间/容量停止必须保存检查点与剩余缺口；访问准备及必要用户决定完成前不得静默 fallback。
- [x] 第 4 阶段未 commit、未 push。

## 2026-10-27 用户反馈优化：第 3 阶段信息层级、分类布局与折叠交互

- [x] R1：卡片默认区只保留产品名、平台/地区、关键状态短标、原比例截图和参考重点；详细路径/角色/渲染、版本日期、来源链接、证据链、审核、适用条件与完整限制进入默认关闭的“页面详情”。字段继续保留在 `report_data.json`。
- [x] R3：分类块进入五列容量网格，按原研究顺序整体放置；2＋2、3＋2 同排，4＋2 的第二组整体换行，单组超过五张占满宽度后组内换行。4/3/2/1 响应式容量不使用 dense 回填，不改变分析、分类或证据引用。
- [x] R3 展开边界：保留每组 20 张独立渐进展开。Chromium 覆盖 20、21、45 张、多组同时展开、素材 ID 顺序及桌面/移动切换后的状态保持，无丢图、重复或串组。
- [x] R4/R5A/R6/R7：结论先行与分类导航保留；现状存在时默认关闭、缺失时省略且不计竞品；组标题与单句 takeaway 独立；来源过程整体关闭；重大覆盖缺口只显示短提示；竞品分析小结仍是最后主要模块。
- [x] 图片与现状图改为独立可聚焦按钮。详情展开不会误触放大；Enter 可打开原图，Escape 和关闭按钮均可关闭。长产品名、长组名、长 URL、横竖比例图片及 1440/390 视口均通过无横向溢出检查。
- [x] [Stage 3 历史素材布局重放](reports/manual-acceptance/user-feedback-optimization-2026-10-27/stage3-layout-replay/README.md) 由通用入口生成。一句话场景实测 2＋2、1＋1；详细场景实测 2＋1＋2，并显示原图带标注、历史版本、抽屉和下段短标。分析、组成员与 Stage 2 相等，全部 assets 字节一致；没有新来源采集。
- [x] 全量自动化 **159 项通过，0 failure/error/skip**；保留既有 socket `ResourceWarning` 与一次测试服务器 BrokenPipe 日志。`compileall`、`git diff --check`、Skill frontmatter 和无 TODO 检查通过；旧归档 90 个文件与实施前哈希一致。
- [ ] R8/B1 来源登录预检、用户选择、同会话复查恢复与正式候选跨阶段衔接留待第 4 阶段。本轮未 commit、未 push。

## 2026-10-27 用户反馈优化：第 2 阶段分析质量与分类语义

- [x] `analysis.schema_version=2` 建立“逐图可见事实/边界 → 横向比较 → 设计判断 → 建议/条件/取舍”的结构化工作底稿。观察恰好覆盖全部有效素材；多素材报告的比较覆盖每张图；最终 Claim 用 `analysis_refs` 关联分析过程，且底稿必须涉及其素材证据，推断必须保存建议、适用条件和限制。
- [x] `classification.schema_version=2` 保存主比较维度、理由、范围、组纳入标准、共同机制、逐成员理由和相邻组差异；每张素材必须保存页面角色、路径、交互阶段、渲染和登录状态。Python 只校验结构、引用和覆盖，不增加关键词或固定产品分类。
- [x] 新增区域级现状契约：有现状图时必须标具体区域；用户事实、目标关系、Agent 推断、竞品引用和证据边界分开保存。虎牙现状按会员入口、任务中心、游戏与更多服务三个区域复核，现状图继续不计入竞品数量。
- [x] 新增交付前 `quality_review`：复核必须覆盖全部最终 Claim；Agent 自查固定 `independent=false`，报告明确其不是独立质量验证；争议候选允许记录重写或删除。
- [x] 正式 Stage 4 与显式重放均消费 v2；`--report-data-file` 可搭配 `--classification-plan-file` 和 `--analysis-file` 整体替换分类与分析。生成元数据区分 `v2_agent_self_review`、`v2_human_review`、`legacy_v1` 与 `missing`，通过契约不等于语义正确。
- [x] 用 2026-10-26 两个真实场景的现有素材完成 [Stage 2 历史素材分析重放](reports/manual-acceptance/user-feedback-optimization-2026-10-27/stage2-analysis-replay/README.md) 及 [前后对照](reports/manual-acceptance/user-feedback-optimization-2026-10-27/stage2-analysis-replay/before-after.md)：迅雷移入“媒体与文件库”；Target 与任务中心分离；11 张未登录兜底组取消，登录态改为标签；自己的账户、子页、滚动下段和抽屉状态保持可区分。
- [x] 两份报告由同一正式入口生成：一句话场景 20 个产品/26 张竞品图/7 组/无现状；详细场景 9 个竞品/10 张竞品图/4 组，1 张现状图另计。整包审查后将只有资产与设置证据的不背单词从进度组拆出；独立 `/tmp` 重放的 classification/report_data/HTML 和全部 26/11 个 assets 与验收目录逐字节一致。
- [x] Chromium 验收图片加载与放大、卡片/来源/现状默认折叠、综合小结最后、1440/390 无横向溢出。定向分析/分类/入口测试 **37 项通过**；全量 **153 项通过，0 failure/error/skip**，保留既有 socket `ResourceWarning` 与一次测试服务器 BrokenPipe 日志。
- [x] `compileall` 和 `git diff --check` 通过；旧真实用户测试归档 90 个文件与第 1 阶段保存的 SHA-256 清单完全一致。Skill Creator 的 `quick_validate.py` 因运行环境缺少 `PyYAML` 无法启动；未为此新增依赖，改用 Ruby YAML 解析确认 frontmatter 有效，并检查无 TODO 占位。
- [x] R3 已由第 3 阶段完成；R8/B1 正式采集前来源登录预检与同会话恢复、两场景新来源采集仍留待后续阶段。第 2 阶段未 commit、未 push。

## 2026-10-27 用户反馈优化：第 1 阶段统一报告结构与正式入口

- [x] 完成生成路径审计：两份旧归档都不能由旧通用 `report.py` 完整重建；归档没有保留一次性脚本，无法进一步区分脚本生成与生成后编辑。详细报告的头部、现状和部分综合分析只在 HTML，逐图借鉴另在 `research/selected-screens.json`；旧 `report_data.json` 均不能完整表达最终报告。
- [x] 新增 `analysis.py` 报告内容契约：研究问题/范围、总判断、关键发现、可选现状、分组 takeaway、逐图 insight、建议/条件/限制、综合小结、待验证和信息缺口；Claim 使用全局稳定 ID，支持多素材/分组/现状引用。未知字段、重复 ID、失效引用和无素材空组引用均失败。
- [x] `classification.py` 支持显式稳定 group ID，旧组名确定性派生兼容 ID；分类审核 `reason` 与给读者的 `takeaway` 分开，不再共用展示字段。
- [x] 正式 Stage 4 接入 `--analysis-file`，统一 `report_bundle.py` 消费结构化内容、复制竞品及现状资产、写 `report_data.json` 并生成 HTML。新增 `--report-data-file` 快照重放；明确标记 `formal/replay`、分析存在状态和 `standard_acceptance=not_assessed`，不降低原正式来源证据门槛。
- [x] 通用模板顺序统一为核心结论→分类导航→可选且默认关闭的现状分析→分类截图/参考→默认关闭的来源与筛选→综合小结。卡片标签、审核理由、质量理由、素材说明、证据 ID 和来源默认折叠；现状独立于竞品统计。无分析或缺核心模块时如实提示，不制造空壳或把旧 reason 冒充结论。
- [x] 新增 [报告内容契约](docs/REPORT_CONTENT_CONTRACT.md)，同步 README、SKILL、CONTEXT、DECISIONS 和 [总任务书](docs/superpowers/plans/2026-10-27-user-feedback-optimization.md)。分析可编辑源为 `analysis.json`，正式 `report_data.json.analysis` 是生成快照，分类文件不重复维护分析。
- [x] 在新目录完成两场景历史重放：`reports/manual-acceptance/user-feedback-optimization-2026-10-27/stage1-replay/`。一句话场景 20 个竞品/26 张图/无现状；详细场景 9 个竞品/10 张竞品图＋1 张独立现状图。命令和报告均标为非新采集验收，旧归档未覆盖。
- [x] Chromium 实测两份重放：内容图片全部加载、卡片/现状/来源默认关闭、图片放大可用、综合小结最后、1440/390 无水平溢出。全量回归 **141 项通过，0 failure/error/skip**；有既有 socket `ResourceWarning`。`git diff --check` 通过。
- [x] R2 在第 1 阶段只完成审核理由/读者结论的契约分离；语义增强已由第 2 阶段补齐。R3、R8/B1 与新来源采集仍待后续。
- [x] 第 1 阶段未 commit、未 push；随后按用户提示进入第 2 阶段。

## 2026-10-27 用户反馈优化：只读核实与任务书

- [x] 阅读根目录协作与产品文档、来源/截图/审核/分类/报告/正式入口实现及相关测试；启动时为干净的 `main`，HEAD `030a962`，origin 对应 lyc500/competitor-analysis-skill。
- [x] 建立 [优化任务书与逐项进度清单](docs/superpowers/plans/2026-10-27-user-feedback-optimization.md)，稳定编号 R1–R8（含独立 R5A），记录每项现状、缺口、拟修改位置、自动化及真实验收、阶段安排和兼容策略。
- [x] 区分详细报告的定制折叠/结论/现状模块与通用 renderer 缺口；核实一句话 20 个产品/26 张图，详细需求 9 个竞品/10 张图＋独立现状图。旧 README 关于“包含当前虎牙页面”的统计描述有误，任务书记勘误，旧文件不改。
- [x] 记录旧规则冲突：轻分析范围、每组固定五列和独立 section、遇来源登录限制直接 fallback、过程统计默认展开；新增 D-021 说明本次要求优先，尚未修改 SKILL/README 的执行实现说明。
- [x] 核实两份旧 reviewed_materials 均缺少当前正式入口所需来源/候选/截图登记字段；保留历史证据缺口，不补造引用。
- [x] 复现 B1：合法最小正式候选未继承来源类型等字段，交给 `_capture_one` 会在网络访问前产生 `KeyError: 'source_type'`；列入后续 R8 正式链路衔接，本轮未修复。
- [x] 基线测试复跑：`python3 -B -m unittest discover -s tests -p 'test_*.py' -q`。沙箱内 localhost 绑定受限，开放必要权限后 **119 项通过，0 failure/error/skip**；有两条现有 socket ResourceWarning，未作无关修复。
- [x] 本地 Chromium 只读查看两份归档，26 张及 10＋1 张图片全部加载；1440/390 宽度无水平溢出，确认详细报告 14 个 details 默认折叠及小组独占行。未重新逐图语义审核或验证全部外链。
- [x] 本轮仅新增任务书并同步 CONTEXT/DECISIONS/STATUS；没有修改产品代码、测试或旧验收产物，没有 commit/push。
- [x] 用户指定第 1 阶段已完成；P0 时的 P1–P5 暂定拆分已由实际阶段提示词覆盖。仍未执行真实第三方来源访问或登录恢复，也没有独立 build/lint/typecheck 配置可执行。

以下保留历史阶段状态与记录，不表示本次 R1–R8 已完成。

阶段状态总览：

- Stage 1：关闭。
- Stage 2：关闭。
- Stage 3A：关闭。
- Stage 3B：关闭。
- Stage 3C：关闭。
- Stage 4：关闭并通过独立验收。
- Stage 5A：独立验收通过 / 已关闭。
- Stage 5B：R1 移动端补正后独立验收通过 / 已关闭。
- Stage 5C：独立验收通过 / 已关闭。
- Cold-start：GPT 最终独立验收通过。
- 报告竖屏截图布局优化：GPT 独立视觉验收通过。
- V0.1 MVP：历史产品验收通过；2026-10-26 审计修正已完成工程实现，外部真实来源验收仍需单独执行。

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
- `python3 -m unittest discover -s tests -v`：93 项通过、0 失败、0 error、0 skip（含阶段 1/2/3A/3B/3C 回归、Stage 4 补正、真实 Chromium、Stage 5A Task Contract、Stage 5B 通用缺陷与 Mobile Surface 回归检查、Stage 5C Task Contract 回归、Cold-start 报告布局回归）。

### Stage 5B 首次执行的历史结论

- Task A 通过 Agent 发现的 12 个真实官方公开 URL 和正式 Chromium Capture 入口执行；Amazon 与哔哩哔哩各取得 2 个真实 collected Material，CN / Global 各 2 张。
- Agent 逐张查看全部 10 张 captured 截图；百度验证码、Google unusual traffic 和小红书 IP 风控页面均如实 semantic rejected，Perplexity 两个候选均为 HTTP 403。
- 所有 accepted Material 均重新通过 Pillow 机械质量检查；未将 CAPTCHA、错误页、登录/风控页或 failed Capture 视为有效截图。
- Task A 的 Stage 4 HTML 已由本地 HTTP + 真实 Chromium 打开，4 张主图成功加载，并实际点击 Amazon 截图验证 dialog 放大图成功加载。
- 上述工程 E2E 验证有效，但产品验收不通过：四张有效素材均为 Desktop Web，且没有优先执行专业 UI / 设计数据库来源。
- 首轮 8 个内置候选在线失败记录仍只是历史记录，不代表本次 Stage 5B 的真实结果。

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

- [x] Agent Semantic Review Contract：由 Agent 提供产品身份、目标页面、目标 Surface、主体完整性和素材类型判断，Python 只校验契约一致性。
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

## Stage 5A 已关闭并通过独立验收

- [x] 保存 Task A / B 的确定性用户输入与本次 Agent 生成的 Task Contract；竞品清单不写入 production catalog、planner 或 Python 固定映射。
- [x] Task A 使用 `agent_only`，覆盖国内与海外搜索结果页；Task B 保留四个用户指定直播产品并使用 `mixed` 补充代表性竞品。
- [x] 新增 Task / Planning Contract 与防固定目录回归测试，不使用 mock、假公网截图或假 collected Material 冒充真实 E2E。
- [x] 建立 Stage 5B / 5C 真实产物目录与运行记录规范，不创建空的成功产物。
- [x] 建立 V0.1 MVP Acceptance Report 骨架并写明后续硬门槛。

## Stage 5B（R1 移动端补正后）——独立验收通过 / 已关闭

- [x] 原始需求保持不变；Task Contract 显式增加 `target_surface = mobile_app`，目标平台只含 iOS/Android，不含 Web。
- [x] Agent 按移动端研究价值规划起点读书、LinkedIn、WhatsApp，覆盖 CN + Global；清单只存在于验收 Task，不进入 production 固定映射。
- [x] 对每个竞品先走专业 UI 数据库；真实 Chromium 已访问国内 UI Notes 和海外 Refero，数据库整页只作来源证据。
- [x] 来源元数据与目标 UI 解耦：UI 数据库来源保留 provider/page/asset URL，Material 独立保留 mobile App Surface 与 iOS 平台。
- [x] Agent 逐张视觉审核并确认 product/page/surface matched、complete、ui_page；Python 只校验 Review，不按尺寸、URL 或关键词推断。
- [x] Stage 3C 得到 4 个 Mobile App collected Material：起点读书 2、LinkedIn 1、WhatsApp 1；3 个产品，CN 1 个 / Global 2 个，4 张均来自 ui_database。
- [x] Agent 根据实际 Screen 生成“移动端搜索结果的任务与信息组织方式”Classification Plan；关键词 classification heuristic 未恢复。
- [x] 新报告图墙只含四张 iOS App Screen，上一轮 Amazon / 哔哩哔哩 Desktop Web 没有进入；旧 `reports/acceptance/task-a/` 保持完整。
- [x] 本地 HTTP + Chromium 148.0.7778.96 真实加载全部主图并点击起点读书 Screen；dialog 图片成功加载，资源请求失败为 0。
- [x] GPT 已基于 commit `3186bd0bed112414988782636c4ffe11d751f990` 完成 GitHub、四张原始 Mobile App UI 与报告交互证据的独立视觉复验；Stage 5B-R1 通过，Task A 正式验收通过，Stage 5B 已关闭。

## Stage 5C——GPT 独立视觉验收通过 / 已关闭

- [x] 保持用户原始需求与四个指定竞品顺序；虎牙、斗鱼、抖音直播、Twitch 均为 `user_specified/high`，Agent 补充快手直播和 BIGO LIVE；清单只存在于本次 Task Contract 和验收产物。
- [x] `target_page = 直播产品礼物面板`、`target_surface = mobile_app`，Task 平台仅为 iOS/Android；未引入 Web 平台或固定产品映射。
- [x] 真实 Chromium 访问 UI Notes / Refero 公开入口；登录、订阅和未公开结果没有被绕过，来源页与原始 App Screen 分开记录。
- [x] 16 个公开候选逐图检查，3 张通过 semantic + mechanical 双门槛并成为 collected：抖音直播 1、Twitch 1、BIGO LIVE 1；13 张标注、拼图、裁切、充值页、营销图或错误目标候选被拒绝。
- [x] 两个用户指定产品（抖音直播、Twitch）取得有效礼物面板；虎牙、斗鱼保留真实 `open` fallback；快手直播保留 `open` fallback。
- [x] Agent 根据三张真实 collected Screen 生成“礼物面板的组织与价值表达方式” Classification Plan；Python 只校验计划，不根据 `product_type`、`notes`、URL 或关键词推断页面结构。
- [x] Stage 4 报告只引用 3 张 collected Mobile App Screen；本地 HTTP + 真实 Chromium 实际加载全部主图，点击抖音 Screen 后 dialog 原图成功加载；证据位于 `reports/acceptance/task-b/evidence/`。
- [x] Task B 真实运行记录和来源尝试位于 `reports/acceptance/task-b/RUN_RECORD.md`、`SOURCE_ATTEMPTS.md`；Task A 历史证据未删除或修改。

独立视觉复验基于 commit `108c0d481823959fe5ed0fecaffa7b32510c5017` 完成：抖音直播、Twitch、BIGO LIVE 三张 accepted 原图，以及虎牙、斗鱼两张 rejected 原图均已实际查看；报告主图加载和 dialog 放大通过。虎牙、斗鱼因像素化、教程标注和水印维持 `open` fallback，结论合理。Stage 5C Task B 正式验收通过并关闭。

## Cold-start 最终独立验收

- [x] 一句自然语言需求驱动 Agent 完成目标页面识别、默认 Mobile App Surface 判断、竞品规划、来源发现、App Screen 获取、Semantic Review、Mechanical Quality、fallback、动态分类、HTML 报告和浏览器交互。
- [x] Cold-start 真实产物位于 `reports/acceptance/mvp-cold-start/`；小红书、Instagram、Medium 为有效 Mobile App UI，错误页面正确 rejected，知乎保留 open fallback。
- [x] GPT 已完成 Cold-start 的功能与视觉独立验收；未发现 Skill specification gap 或 implementation blocker。

## 报告竖屏截图布局优化

- [x] 通过约束卡片轨道、取消固定图片高度并保留原始比例，解决单卡大面积留白和竖屏截图过小问题。
- [x] GPT 已完成 Before / After 独立视觉验收；报告可直接浏览，多卡可并排，窄屏正常响应，Lightbox 保持可用。

## V0.1 后续优化候选

以下项目属于 V0.1 完成后的非阻塞优化，不影响当前 MVP 结论：

1. 竞品规划代表性继续提升：避免为了公开素材可得性降低竞品价值，提升头部竞品与代表性竞品选择质量。
2. 更多 UI Database / 公开来源适配：提高封闭产品公开 App Screen 的获取成功率。
3. `user_upload` / `device_capture` 流程继续完善。
4. iPhone 镜像自动化尚未实现。
5. 后续可增加更轻量、更高价值的设计洞察能力。
6. HTML 报告仍可继续优化视觉细节；“竖屏截图过小、单卡大面积留白”这一阻塞问题已经解决，不再作为当前缺陷。

## 2026-10-20 Skill 与报告能力优化

- [x] 开放式需求改为高召回候选发现：支持多模式检索、语义同义词扩展、持续分页/下滑至连续两批无新增，并要求记录候选登记、处置状态和原因。
- [x] 明确区分 `logged_out_complete` 与 `login_intercept`：完整的未登录目标页可纳入并标记状态，登录墙/权限阻断默认排除并进入 fallback。
- [x] 取消竞品数量 3–5 个上限；最终数量由目标覆盖、页面匹配、质量和来源可追溯性决定。
- [x] 报告分类组桌面端一行 5 张；单组超过 20 张时初始展示 20 张，通过“更多”按钮每次展开 20 张。
- [x] 新增 Skill 契约测试、报告静态契约测试和真实 Chromium 渐进展开回归；`python3 -m unittest discover -s tests -q`：100 项通过、0 失败、0 error、0 skip。

## 历史产品验收结论

V0.1 MVP 的历史产品验收通过。Stage 1、Stage 2、Stage 3A、Stage 3B、Stage 3C、Stage 4、Stage 5A、Stage 5B-R1、Stage 5C 和 Cold-start 均完成过相应历史验收；这些历史结论不替代本轮新增的证据链工程验收，也不替代本轮未执行的真实第三方来源验收。历史 rejected / fallback 证据仍保留在 `reports/acceptance/` 下。

## 2026-10-20 手工重新验收：知名 App“我的”页

- [x] 按当前 `SKILL.md` 重新执行开放式候选发现：UI Notes 标签搜图、OCR 搜图、“个人中心”同义词检索，并持续下滑至连续两批无新增。
- [x] 本轮独立候选登记 35 个：15 个通过语义与机械质量双门槛并进入报告，1 个因产品身份/页面主体不确定且为空态被拒绝，19 个保留 `not_reviewed` 及原因。
- [x] 新报告位于 `reports/manual-acceptance/v0.1-my-pages-rerun/report.html`；未读取或复用旧验收报告中的竞品、素材或结论。
- [x] 最终按“个人中心的核心组织方式”动态分为“成长与内容资产中心”“会员与服务聚合中心”“订单与交易资产中心”三组；本轮没有触发超过 20 张的渐进展开。
- [x] 本次未修改 production Python、Skill 或测试；仅新增本轮验收产物，并记录本状态结论。

## 2026-10-20 海外来源页面命名映射能力

- [x] 将海外来源检索抽象为通用的“页面意图 → 海外常用命名词族”步骤，不再把中文页面名称当作唯一英文查询词；规则覆盖“我的”、账户、发布、搜索和详情等页面类型。
- [x] 为“我的”/“个人中心”补充 `Profile`、`You`、`Me`、`Account`、`My Account`、`My Page` 词族，并接入 PTTRNS `Profile & Account`、Refero page type 15、Mobbin `My Account & Profile` 三类来源入口说明。
- [x] 明确记录原始名称、映射词族、实际查询词、来源入口、访问状态、可见范围、分页/滚动批次和候选处置；命中来源 taxonomy 不替代页面角色、交互阶段、渲染状态和视觉质量审核。
- [x] 明确海外来源的权限/空结果/错误/付费限制 fallback，不绕过登录或付费，不使用固定 catalog、fixture、历史报告补齐正式候选。
- [x] 新增 Skill 契约测试 `test_foreign_sources_translate_page_intent_to_local_naming_vocabulary`；定向测试通过。
- [x] 本轮仅验证三个海外入口的可发现性：PTTRNS 与 Mobbin 在当前 Web 工具中不可直接访问，Refero 可打开但未返回可解析的页面正文；没有把这些入口的可访问性误记为已采集素材。

## 2026-10-20 动态 UI 数据库访问状态修正

- [x] 将“文本工具可解析”和“真实浏览器可访问/可交互”拆为独立状态，新增 `web_text_accessible`、`browser_accessible`、`browser_interactive`、`content_available` 和 `access_status` 记录要求。
- [x] 对依赖 JavaScript、会话、滚动加载或筛选交互的 UI 数据库改为浏览器优先；文本抓取失败不再直接触发来源 fallback。
- [x] 明确浏览器可用时仍需提取单屏 App UI，并通过产品身份、页面角色、状态、Surface/平台和视觉质量审核；来源整页不能直接作为竞品素材。
- [x] 新增 Skill 契约测试 `test_dynamic_ui_databases_use_browser_access_as_separate_source_status`；定向测试通过。

## 2026-10-20 手工重新验收：国内外知名 App“我的”页（fresh rerun-2）

- [x] 以全新候选发现运行重新执行当前 `SKILL.md`：UI Notes 使用“我的”与“个人中心”检索并连续下滑；海外来源将“我的”映射为 `Profile / You / Me / Account / My Account / My Page`，分别访问 Refero、Mobbin、PTTRNS。
- [x] 本轮未读取或复用 `reports/acceptance/`、旧 `v0.1-my-pages/`、旧 `v0.1-my-pages-rerun/` 中的竞品、URL、截图或分类结论；未使用 fixture_demo、固定 catalog 或历史测试结果作为样本来源。
- [x] 11 个规划产品取得 12 张有效移动端截图：国内拼多多、豆包爱学（未登录/已登录两种状态）、酷狗畅听版；海外 Wise、Kickstarter、The New York Times、Airbuds、Badoo、Airbnb、Zomato、Yubo。
- [x] Refero 的 Duolingo 设置子页、Revolut 账户详情子页、Mobbin 的 Ahead 测评/进度页均被拒绝；PTTRNS 目标路径跳转首页，保留 fallback；Refero/Mobbin 的隐藏或付费边界未绕过。
- [x] Stage 2 来源发现、Stage 3C 语义与机械质量审核、Stage 4 动态分类均通过；报告按“我的页首屏主任务与个人资产组织方式”分为“身份资料与关系资产”“内容消费与成长资产”“交易服务与账户资产”三组。
- [x] 报告位于 `reports/manual-acceptance/v0.1-my-pages-rerun-2/report.html`，HTML 含 12 张卡片与 12 个本地资产；当前样本不超过 20 张，未触发“更多”按钮。
- [x] 全量自动化测试：`python3 -m unittest discover -s tests -p 'test_*.py' -q`，102 项通过；复跑需要本机 localhost 端口权限，沙箱首次运行的 3 个端口错误不代表代码失败。
- [x] 本轮未 commit、未 push，等待用户明确反馈“验证通过”。
- [x] 根据用户反馈调整报告展示：国内竞品置前并单独分组为“国内竞品｜主参考”，海外竞品单独分组为“海外竞品｜单独参考”，不再混排；海外 8 张素材遵循每行 5 张的网格规则在同一组内换行。
- [x] 已核对上一版差异：上一版规划 15 个国内产品并全部进入报告；本版规划为 3 个国内产品 + 8 个海外产品，豆包爱学有两个状态，因此国内从 15 张降为 4 张，主因是规划范围改变，不是审核大量拒绝。

## 2026-10-20 开放式竞品数量上限调整

- [x] 根据用户最新要求，将 Skill 的开放式候选池规则从“取消 3–5 个上限”明确为“最多 50 个”；50 个是容量上限，不是必须凑足的目标数量。
- [x] 超过 50 个时按目标相关性、地区/产品类型覆盖、页面匹配度、素材质量和来源可追溯性排序截断，并要求记录被截断候选及原因；页面语义和质量准入不因数量上限放宽。
- [x] 更新 `tests/test_skill_contract.py` 契约测试，并先观察旧 Skill 在新测试下失败，再修改 Skill 后定向测试通过。
- [x] 本次报告继续保持国内竞品组在前、海外竞品组最后；未执行 commit 或 push。

## 2026-10-26 审计修正：正式入口与证据链

- [x] 重新核实审计问题：旧 `reports/manual-acceptance/v0.1-my-pages-rerun-2/` 的来源登记与 captures/reviewed materials 的来源 ID 无法可靠对应；本轮未把旧记录当作新样本，也未编造修复 ID。
- [x] README 改为结构化 Task → 来源登记 → 浏览器截图 → Agent 语义审核 → 动态分类 → HTML 报告的可执行流程；自然语言位置参数明确标为 `legacy/demo`，并区分正式报告、阶段中间产物和离线演示。
- [x] 新增 `competitor_analysis_skill/evidence.py`：独立校验来源尝试、候选、来源 URL 角色、候选池 50 条边界、截断处置、未知访问状态及跨阶段引用。
- [x] Stage 3A/3B/3C/4 贯通 `source_attempt_id`、`source_candidate_id`、`capture_id`、`target_id`、`material_id`；错误或缺失引用明确失败，旧格式只走兼容路径并标记证据缺口。
- [x] 语义审核契约补足页面角色、交互阶段、渲染状态、登录状态和审核理由代码；这些字段由 Agent 提供，Python 仅校验结构和允许值。
- [x] 报告增加来源访问、候选处置、素材审核、素材流水线、产品 fallback、产品覆盖和待审核/未知边界的分项统计，避免将某一阶段的排除数误读为全链路排除数。
- [x] 新增行为测试覆盖来源断链、漏登记、错误引用、候选池超限与截断、未知访问状态、统计边界、重复展开和多组独立展开；保留已有文档关键词测试，但不把它作为功能完成依据。
- [x] 不依赖端口的回归：106 项通过；真实 Chromium/本地 HTTP：13 项通过；全量 `python3 -m unittest discover -s tests -p 'test_*.py' -q`：119 项通过。
- [ ] 本轮新验收未执行真实第三方来源搜索、逐图人工审核或真实竞品采集；新目录仅记录契约/工程验收证据。浏览器与本地 HTTP 回归已执行，不能替代外部来源验收。
- [ ] 未 commit、未 push；待后续用户明确要求时再处理版本发布。

## 2026-10-26 两个真实用户场景测试归档

- [x] 归档一句话需求“搜集国内外知名 app ‘我的’页的竞品截图”：最终报告包含 26 张有效截图、20 个产品，过程记录保留任务输入、来源尝试、候选、接受/拒绝和分类证据。
- [x] 归档详细需求“虎牙‘我的’页改版竞品参考”：保留当前页面与外部参考页面的区分，报告包含 9 个产品、10 张截图，以及会员/常用功能、任务成长、低频服务收纳三类改版参考。
- [x] 两个报告及其本地截图资产位于 `reports/manual-acceptance/v0.1-user-tests-2026-10-26/`；未复制原始 raw 候选池和一次性脚本，避免未入选素材被误读为结论。
- [x] 本次归档来源于两个真实用户任务，不使用 fixture_demo、固定 catalog 或 `reports/acceptance/` 中的历史样本替代；外部来源的当前可访问性仍可能受权限和站点状态影响。
