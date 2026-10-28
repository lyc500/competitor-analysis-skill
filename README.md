# 竞品分析 Skill V0.1

这是一个面向产品设计师的证据驱动竞品页面搜集 Skill：Agent 负责理解需求、规划竞品、发现来源、逐图视觉审核和动态分类；Python 负责结构化契约、跨阶段关联、机械质量校验、统计和 HTML 报告生成。

正式使用以结构化 Task 为入口。根目录 [`SKILL.md`](SKILL.md) 是 Codex/Agent 的工作流说明；本 README 说明可执行的阶段交接。

## 正式流程

### 1. Agent 生成结构化 Task

Agent 先识别目标页面、页面路径、交互阶段、渲染状态、登录状态、目标 Surface、地区和竞品范围，再写入 `task.json`。Python 不通过关键词代替语义理解，也不从固定 catalog 自动规划正式竞品。

最小示例：

```json
{
  "raw_request": "帮我搜集国内外知名 App 的我的页",
  "research_goal": "比较个人中心的首屏组织方式",
  "target_page": "我的页",
  "target_surface": "mobile_app",
  "regions": ["CN", "Global"],
  "platforms": ["iOS", "Android"],
  "specified_products": [],
  "assumptions": ["默认纳入已加载、主体完整的目标页"],
  "needs_clarification": false,
  "task_status": "ready",
  "planning_strategy": "agent_only",
  "competitors": [
    {
      "product_name": "示例产品",
      "region": "CN",
      "product_type": "内容社区",
      "platform": "iOS / Android",
      "target_page": "我的页",
      "planning_source": "agent_planned",
      "priority": "medium",
      "reason": "个人中心结构具有代表性"
    }
  ]
}
```

正式任务入口：

```bash
python3 -m competitor_analysis_skill \
  --task-file task.json \
  --output reports/my-pages
```

### 2. 来源发现与候选登记

Agent 理解范围后，先在后续采集使用的浏览器会话中快速检查本次相关来源的页面、搜索/筛选、详情、原图和分页能力。登录限制实质影响覆盖时才一次性请用户选择正常登录后继续或仅用公开内容；登录后必须实际复查并从检查点恢复。完整协议见 [来源访问准备契约](docs/SOURCE_ACCESS_CONTRACT.md)。随后发现候选，不能把来源网站整页直接当作竞品素材。正式 `sources-input.json` 要把访问准备、来源尝试和候选关联保存：

```json
{
  "source_attempts": [
    {
      "id": "att-uinotes-01",
      "source_type": "ui_database",
      "source_provider": "UI Notes",
      "entry_url": "https://uinotes.com/search",
      "query_mapping": {
        "raw_page_intent": "我的页",
        "mapped_terms": ["Profile", "You", "Account"],
        "source_taxonomy_terms": ["我的", "个人中心"]
      },
      "actual_query": "我的",
      "search_mode": "tag_search",
      "discovery_batch": 1,
      "web_text_accessible": "unknown",
      "browser_accessible": true,
      "browser_interactive": true,
      "content_available": true,
      "access_status": "paywall",
      "observed_scope": "首批结果可见，继续翻页需要订阅",
      "attempt_status": "completed",
      "failure_reason": ""
    }
  ],
  "candidates": [
    {
      "id": "cand-product-a-01",
      "source_attempt_id": "att-uinotes-01",
      "product_name": "示例产品",
      "target_page": "我的页",
      "source_entry_url": "https://uinotes.com/search",
      "source_detail_url": "https://uinotes.com/apps/example/screen-01",
      "source_asset_url": "https://cdn.example.com/screen-01.png",
      "candidate_rank": 1,
      "candidate_status": "accepted",
      "disposition_reason": "进入截图和逐图审核"
    }
  ],
  "candidate_pool": ["cand-product-a-01"],
  "candidate_limit": {
    "max": 50,
    "unit": "candidate_records",
    "applies_to": "candidate_pool",
    "ordering_basis": "页面匹配度、覆盖度和来源可追溯性",
    "truncated_candidate_ids": []
  },
  "access_preparation": {
    "schema_version": 1,
    "id": "access-batch-01",
    "research_scope": "我的页相关来源",
    "started_at": "2026-10-27T10:00:00+08:00",
    "completed_at": "2026-10-27T10:05:00+08:00",
    "relevant_source_attempt_ids": ["att-uinotes-01"],
    "checks": [{
      "id": "check-uinotes-preflight",
      "source_attempt_id": "att-uinotes-01",
      "phase": "preflight",
      "checked_at": "2026-10-27T10:02:00+08:00",
      "browser_session_id": "chrome-profile-a",
      "browser_session_kind": "agent_browser",
      "browser_tab_id": "tab-a",
      "page_open": true,
      "search_usable": true,
      "filter_usable": true,
      "detail_usable": true,
      "original_asset_usable": true,
      "pagination_usable": false,
      "authentication_state": "authenticated",
      "access_barrier": "paywall",
      "visible_scope": "首批结果可见，后续需订阅",
      "coverage_impact": "minor",
      "notes": "当前范围足以继续"
    }],
    "decision": {
      "status": "not_required",
      "prompted_at": "",
      "decided_at": "2026-10-27T10:05:00+08:00",
      "restricted_source_attempt_ids": [],
      "summary": "限制未实质影响本批覆盖"
    },
    "resume": {
      "status": "not_needed",
      "checkpoint_candidate_ids": [],
      "completed_candidate_ids": [],
      "remaining_candidate_ids": [],
      "recheck_ids": [],
      "resumed_at": ""
    }
  }
}
```

当前仍有 material 级登录、验证或会话过期限制时，`decision.status=not_required` 会被拒绝；历史上受限但当前复查已恢复的来源不会被旧状态永久阻塞。截图阶段实际消费 `resume.completed_candidate_ids` 与 `remaining_candidate_ids`：有效完成项保留，只有剩余可执行项传给截图执行器，`blocked` 项不执行。已有截图缺失或损坏时会报出受影响候选，要求保留 ID 并显式移回 remaining，不静默重跑全部候选。执行结果保存为 `captures.json.capture_execution`。

运行来源登记阶段：

```bash
python3 -m competitor_analysis_skill \
  --task-file task.json \
  --sources-file sources-input.json \
  --output reports/my-pages-stage2
```

`source_entry_url`、`source_detail_url`、`source_asset_url` 分别表示来源入口、单屏详情和图片资源，允许不同，但必须通过 `source_attempt_id`、`source_candidate_id` 关联。50 个只限制 `candidate_pool` 的候选记录数；超出记录仍保留在 `candidates` 中，必须标记 `rejected`/`not_reviewed` 和截断原因。

50 条不是搜集完成标准。Agent 按地区、代表性产品、关键设计问题和有效样本缺口决定是否继续；池满后只在可能补足实质缺口或替换低价值候选时继续。截止时间到达时可以保存检查点、未审核/截断处置和剩余缺口后交付，但不能把主动停止写成来源耗尽或完整覆盖。

### 3. 浏览器截图阶段

显式加 `--capture-sources` 才会启动真实 Chromium：

```bash
python3 -m competitor_analysis_skill \
  --task-file task.json \
  --sources-file reports/my-pages-stage2/sources.json \
  --capture-sources \
  --output reports/my-pages-stage3b
```

正式 `--capture-sources` 只接受包含 `source_attempts`、`candidates`、候选池和 `access_preparation` 的结构化来源。旧 `{"sources":[...]}` 仍可离线读取或诊断，但实际采集会在截图执行器运行前拒绝并给出迁移提示。结构化正式来源没有通过访问准备、仍等待用户选择或等待登录复查时也会拒绝继续。批量截图在同一命令内按会话 ID 复用浏览器 context；不同会话隔离。Agent 桌面浏览器的认证状态不能伪装成 Python Playwright 已复用，必要时由当前浏览器获取素材并保存同一证据链。输出的 `captures.json` 只证明候选 URL 被浏览器加载并记录了截图结果；它不是语义审核结果，也不是最终素材。

### 4. Agent 逐图语义审核

Agent 必须逐图填写产品身份、页面角色、交互阶段、渲染状态、登录状态、目标页面匹配、Surface、主体完整性、图片类型、视觉质量和审核理由。Python 只校验字段结构、允许值、来源 ID 和图片机械质量，不判断截图语义。

```bash
python3 -m competitor_analysis_skill \
  --task-file task.json \
  --sources-file reports/my-pages-stage2/sources.json \
  --captures-file reports/my-pages-stage3b/captures.json \
  --semantic-reviews-file semantic-reviews.json \
  --output reports/my-pages-stage3c
```

`reviewed_materials.json` 和 `fallback_requests.json` 是阶段 3C 中间产物。跨阶段关联必须满足：

```text
source_attempts.id
  → candidates.source_attempt_id
  → captures.source_candidate_id
  → semantic_reviews.target_id
  → materials.capture_id
  → classification.material_ids
  → report
```

缺失或错误引用会明确报错。历史产物如果没有登记信息，只记录为历史证据缺口，不补造 ID、浏览器操作或审核结论。

### 5. 动态分类与正式 HTML 报告

Agent 观察已通过审核的实际素材后生成 `classification-plan.json` 和 `analysis.json`，再执行。classification v2 先声明主比较维度，并为每组保存纳入标准、共同机制、逐成员理由和相邻组差异；登录态、页面路径与交互阶段作为标签保留。分类审核的 `reason/audit` 与读者看到的 `takeaway` 分开保存，不按关键词或产品名自动分组。

analysis v2 采用“逐图可见事实 → 横向比较 → 设计判断 → 借鉴建议 → 证据边界”的工作流。工作底稿保存在结构化数据中，最终报告只显示压缩后的核心结论、分类副标题、单图参考和综合小结。每条设计推断都关联素材/分组与分析过程 ID，并说明建议、适用条件和限制。完整字段见 [报告内容契约](docs/REPORT_CONTENT_CONTRACT.md)。

```bash
python3 -m competitor_analysis_skill \
  --task-file task.json \
  --reviewed-materials-file reports/my-pages-stage3c/reviewed_materials.json \
  --classification-plan-file classification-plan.json \
  --analysis-file analysis.json \
  --output reports/my-pages
```

最终交付是 `reports/my-pages/report.html`。通用顺序为标题与核心结论、分类导航、可选现状分析、分类截图与参考分析、来源与筛选说明、竞品分析小结。现状、卡片详情、来源过程默认折叠；不适用模块省略，缺少判断依据时简短说明。现状图单独复制，不计入竞品数量。有现状图时分析指向具体区域，并区分可见事实、用户事实与推断。

卡片默认只保留产品名、平台/地区、影响理解的状态短标、原比例截图和简短参考重点；路径、页面角色、渲染状态、版本日期、来源链接、证据 ID、审核记录、适用条件与详细限制放入“页面详情”。桌面一行约容纳 5 张卡片，相邻小组在可完整容纳时整体并排；放不下的组整体换到下一行，单个大组独占宽度后在组内换行。移动端按实际宽度降为 4/3/2/1 列，不使用 dense 回填。每组超过 20 张时独立逐次展开 20 张，切换响应式宽度不会重置已展开状态。图片和现状图可通过鼠标或键盘放大。

报告统计分别展示来源访问、候选处置、素材审核、素材流水线、产品 fallback、有效覆盖和待审核边界，避免把“素材流水线排除数为 0”误读为“所有候选都没有被排除”。

`report_data.json` 保存本次完整分析、分类审核、自查记录和证据快照，`assets/` 保存报告所有展示图片；不要生成后手改 HTML。Agent 自查只作为辅助复核，明确标记为非独立验证。旧 v1 输入仍可生成，但不会补造 v2 工作底稿或改标为满足新版标准。

### 6. 从结构化快照重新生成

```bash
python3 -B -m competitor_analysis_skill \
  --report-data-file reports/my-pages/report_data.json \
  --classification-plan-file revised-classification.json \
  --analysis-file revised-analysis.json \
  --output reports/my-pages-replay
```

这是显式重放，报告与命令输出均说明未进行新的来源搜集或证据验收。两个替换文件均可省略；提供时整体替换，不做字段合并，也不与采集参数混用。正式更新编辑原始源文件后重跑步骤 5；历史重放每次新建目录，不覆盖旧产物。结构与入口验收见 [第 1 阶段历史重放](reports/manual-acceptance/user-feedback-optimization-2026-10-27/stage1-replay/README.md)，分析质量、分类反例与现状区域验收见 [第 2 阶段历史素材分析重放](reports/manual-acceptance/user-feedback-optimization-2026-10-27/stage2-analysis-replay/README.md)，信息层级、小组并排与折叠交互验收见 [第 3 阶段布局重放](reports/manual-acceptance/user-feedback-optimization-2026-10-27/stage3-layout-replay/README.md)，新来源访问与全任务验收见 [第 4 阶段最终验收](reports/manual-acceptance/user-feedback-optimization-2026-10-27/stage4-final-acceptance/README.md)。

## 产物边界

- 正式报告：`report.html`，面向设计师浏览和放大截图。
- 阶段中间产物：`sources.json`、`captures.json`、`reviewed_materials.json`、`fallback_requests.json`、`classification.json`、`report_data.json`，用于交接和追溯，不能单独冒充最终验收。
- 离线演示/自动化测试：`--offline`、fixture、静态契约测试和本地测试夹具。它们不能证明真实来源访问、真实浏览器操作或真实视觉审核。
- 历史格式：只有 `sources` 或只有 `captures` 的旧产物可用于诊断兼容性，但缺少正式证据链时必须明确标记缺口。

## Legacy/demo 入口

自然语言位置参数仅为兼容旧演示，使用固定候选和有限能力，不是正式的通用自然语言入口：

```bash
python3 -m competitor_analysis_skill \
  "帮我搜集一下海内外热门产品的搜索结果页" \
  --offline \
  --output reports/offline-demo
```

固定示例解析位于 `competitor_analysis_skill/legacy_demo.py`；`requirements.py` 只保留旧导入兼容别名，正式 `--task-file` 分支不会调用该解析器。该路径的 `materials.json.compatibility.status` 为 `legacy_demo_only`，结果只能用于离线结构演示；正式使用必须由 Agent 先生成结构化 Task、来源尝试、候选登记和视觉审核记录。

## 安装与测试

```bash
python3 -m pip install -r requirements.txt
python3 -m playwright install chromium
python3 -m unittest discover -s tests -p 'test_*.py' -v
```

测试会区分契约、fixture、静态文档检查和真实 Chromium/本地 HTTP 验证。若浏览器、网络、登录或权限阻塞，验收记录必须明确未验证范围，不能用旧报告替代。
