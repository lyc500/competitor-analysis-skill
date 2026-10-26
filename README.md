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

Agent 使用真实浏览器或其他可用公开搜索能力发现来源，不能把来源网站整页直接当作竞品素材。正式 `sources-input.json` 要独立登记来源尝试和候选：

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
      "access_status": "accessible",
      "observed_scope": "首屏并下滑两批",
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
  }
}
```

运行来源登记阶段：

```bash
python3 -m competitor_analysis_skill \
  --task-file task.json \
  --sources-file sources-input.json \
  --output reports/my-pages-stage2
```

`source_entry_url`、`source_detail_url`、`source_asset_url` 分别表示来源入口、单屏详情和图片资源，允许不同，但必须通过 `source_attempt_id`、`source_candidate_id` 关联。50 个只限制 `candidate_pool` 的候选记录数；超出记录仍保留在 `candidates` 中，必须标记 `rejected`/`not_reviewed` 和截断原因。

### 3. 浏览器截图阶段

显式加 `--capture-sources` 才会启动真实 Chromium：

```bash
python3 -m competitor_analysis_skill \
  --task-file task.json \
  --sources-file reports/my-pages-stage2/sources.json \
  --capture-sources \
  --output reports/my-pages-stage3b
```

输出的 `captures.json` 只证明候选 URL 被浏览器加载并记录了截图结果；它不是语义审核结果，也不是最终素材。

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

Agent 观察已通过审核的实际素材后生成 `classification-plan.json`，再执行：

```bash
python3 -m competitor_analysis_skill \
  --task-file task.json \
  --reviewed-materials-file reports/my-pages-stage3c/reviewed_materials.json \
  --classification-plan-file classification-plan.json \
  --output reports/my-pages
```

最终交付是 `reports/my-pages/report.html`。报告按每组 5 列展示，超过 20 张时每次点击“更多”展开 20 张，并支持点击图片放大。

报告统计分别展示来源访问、候选处置、素材审核、素材流水线、产品 fallback、有效覆盖和待审核边界，避免把“素材流水线排除数为 0”误读为“所有候选都没有被排除”。

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

该路径的结果只能用于离线结构演示；正式使用必须由 Agent 先生成结构化 Task、来源尝试、候选登记和视觉审核记录。

## 安装与测试

```bash
python3 -m pip install -r requirements.txt
python3 -m playwright install chromium
python3 -m unittest discover -s tests -p 'test_*.py' -v
```

测试会区分契约、fixture、静态文档检查和真实 Chromium/本地 HTTP 验证。若浏览器、网络、登录或权限阻塞，验收记录必须明确未验证范围，不能用旧报告替代。
