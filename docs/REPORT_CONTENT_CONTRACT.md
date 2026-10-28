# 通用报告内容契约 v2

2026-10-27，用户反馈优化第 2 阶段。v2 在 v1 的可重放报告结构上增加分析工作底稿、分类审核依据、现状区域和交付前人工复核。Python 校验结构、状态、引用和完整覆盖；分析是否正确仍由 Agent 或人工判断。

## 职责与数据位置

Agent 在逐图视觉审核后撰写 `classification-plan.json` 和 `analysis.json`。前者保存比较维度、组边界和成员理由；后者保存研究问题、分析过程与面向读者的最终结论。正式 Stage 4 通过 `report_bundle.py` 将两者嵌入 `report_data.json`，再由通用 renderer 生成 HTML。

`classification-plan.json` 与 `analysis.json` 是可编辑源，`report_data.json` 是某次生成的完整快照。不要在多个 JSON 中复制维护同一份结论，也不要生成后手改 HTML。历史重放可以用 `--classification-plan-file` 或 `--analysis-file` 整体替换对应快照，不做字段合并。

正式在线运行还会把 `sources.json.access_preparation` 作为来源证据快照带入 `report_data.json`。renderer 只在默认关闭的“来源与筛选说明”中展示当前能力、用户决定、恢复状态和访问边界；影响结论的重大覆盖缺口另以短提示保留。访问准备、登录复查和同会话恢复字段见 [来源访问准备契约](SOURCE_ACCESS_CONTRACT.md)。它们不与分析结论重复维护，也不代替素材语义审核。

## analysis v2 顶层字段

| 字段 | v2 | 含义 |
| --- | --- | --- |
| `schema_version` | 必需，整数 `2` | 选择新版契约 |
| `title` | 必需 | 面向读者的标题 |
| `research.question`, `research.scope` | 必需 | 研究问题与实际覆盖范围 |
| `research.goals`, `research.constraints` | 可选 | 只记录用户已知目标与约束 |
| `analysis_process` | 必需 | 逐图事实、横向比较和可选现状推理工作底稿 |
| `overall` | 必需 | 总判断 Claim |
| `key_findings` | 可选 | 按参考价值排序的 Claim 数组，不凑固定数量 |
| `current_state` | 可选 | 用户现状、具体图上区域和问题判断 |
| `groups` | 必需 | 每个非空组恰好一个 `takeaway` |
| `materials` | 必需 | 每张有效素材恰好一个 `insight` |
| `synthesis` | 必需 | 综合判断与待验证问题，二者均不得为空 |
| `information_gaps` | 可选 | 明确未知、未提供或不适用 |
| `methodology` | 可选 | 过程与证据边界，默认收进折叠区 |
| `quality_review` | 必需 | Agent 自查或人工复核记录 |

所有字符串必须非空；未知字段、错误类型、重复 ID 和失效引用都会被拒绝。`information_gaps.status` 只允许 `unknown`、`not_provided`、`not_applicable`。缺失信息应明确说明，不为满足模板编造判断。

## 先分析，再压缩表达

`analysis_process.material_observations` 必须恰好覆盖全部有效竞品素材：

```json
{
  "id": "obs-mat-a",
  "material_id": "mat-a",
  "visible_facts": ["任务卡显示今日目标、当前进度和下一步按钮"],
  "evidence_boundaries": ["静态截图不能证明该卡片的使用频率或完成率"]
}
```

`analysis_process.comparisons` 保存横向分析。只要报告有两张以上素材，每张素材都必须至少进入一次比较；单张报告不得伪造比较。每条比较包含：

- `material_ids`：至少两张不同的有效素材；
- `comparison_findings`：共性、差异和例外；
- `design_judgment`：做法支持什么任务；
- `recommendation` 与 `applicability`：本次可借鉴什么、何时适用；
- `tradeoffs` 与 `evidence_boundaries`：必要取舍和证据边界。

工作底稿保存在 `report_data.json.analysis`，供追溯和复核；报告正文只显示压缩后的结论，不铺满完整推理过程。

## Claim 与稳定引用

```json
{
  "id": "finding-task-card",
  "kind": "inference",
  "statement": "任务卡同时给出状态与下一步动作，适合目标明确的连续任务。",
  "evidence_refs": [
    {"kind": "material", "id": "mat-a"},
    {"kind": "material", "id": "mat-b"}
  ],
  "analysis_refs": ["cmp-task"],
  "recommendation": "用一项进度和一个动作替代纯活动文案。",
  "applicability": "任务规则能提供稳定状态与下一步。",
  "limitations": "卡片高度和效果仍需原型与行为验证。"
}
```

`kind` 为 `observation`、`inference` 或 `question`。所有 Claim ID 在整份分析中全局唯一。v2 的每条 Claim 必须用 `analysis_refs` 关联工作底稿；`inference` 必须填写建议、适用条件和限制。证据可引用：

- `material`：本报告实际接受的竞品素材；
- `group`：至少含一张有效素材的稳定分类 ID；
- `current_state`：现状对象、现状图片或具体区域 ID。

分组 takeaway 必须引用本组或组内素材，逐图 insight 必须引用自己的素材，现状判断必须引用现状证据。`analysis_refs` 还必须与 Claim 的素材证据有机械关联：逐图 insight 的底稿须涉及该图，分组 takeaway 的底稿须涉及组内素材，其他带竞品证据的 Claim 至少有一项底稿涉及其素材或分组展开后的成员。这样可阻止“ID 存在但指向另一张图”的错误追溯；它仍不判断文字含义是否正确。单条结论可引用多张图或多个组。Python 不通过关键词、长度或评分判断内容是否有价值。

## classification v2

`classification-plan.json` 的 `schema_version=2`。除原有 `classification_dimension`、`classification_reason`、`groups` 和 `material_labels` 外，还必须提供：

```json
{
  "comparison_basis": {
    "primary_dimension": "本次改版要解决的设计问题",
    "rationale": "明确目标时按共同设计机制比较",
    "scope": "只比较已审核的目标页面"
  },
  "groups": [{
    "id": "group-task",
    "name": "任务动作与进度",
    "reason": "供审核的归组说明",
    "material_ids": ["mat-a", "mat-b"],
    "audit": {
      "inclusion_criteria": "可见任务目标、状态或下一步动作",
      "shared_mechanism": "在首屏把任务状态连接到动作",
      "member_reasons": [
        {"material_id": "mat-a", "reason": "可见今日目标与当前进度"},
        {"material_id": "mat-b", "reason": "可见下一步动作与奖励"}
      ],
      "adjacent_difference": "奖励余额没有任务目标，不纳入本组"
    }
  }]
}
```

每个有效素材必须且只能进入一个非空组，每组成员理由必须恰好覆盖本组。`material_labels` 必须恰好覆盖全部素材，并至少保留 `page_role`、`path_stage`、`interaction_stage`、`render_state`、`login_state`。登录态、页面路径和交互阶段是比较条件，不得成为把不同主任务混在一起的兜底组。

影响等价比较的状态由结构化 labels 提供。除必需字段外，可用 `version_status=historical_version`、`annotation_status=original_annotated` 等显式状态让卡片显示“历史版本”“原图带标注”；renderer 不从产品名、来源 URL 或审核长文本猜测这些状态。未登录、访客、抽屉、滚动下段、子页和加载受限可由标准状态字段确定性显示。完整 labels 仍只在默认关闭的页面详情中展开。

`groups[].reason` 与 `audit` 是分类审核依据，放在折叠的“来源与筛选说明”；`analysis.groups[].takeaway.statement` 是读者看到的一句话结论。两者不能共用一个字段。

## 可选现状分析

有现状图时，`current_state.regions` 必须标出至少一个具体区域：

```json
{
  "id": "current-task-row",
  "image_id": "current-screen",
  "label": "任务中心区",
  "visible_fact": "只有一行活动文案，没有可见进度或下一步按钮"
}
```

`analysis_process.current_state` 分开保存用户提供事实、与目标的关系、Agent 推断、竞品结论引用和证据边界。现状结论必须关联至少一条有竞品素材支撑的 Claim。不得从现状截图推断使用频率，也不得仅凭截图决定不同会员业务必须合并。现状图片输出到独立 `assets/current-…`，不进入竞品 materials、分类、产品数、截图数或覆盖统计。没有现状时整个模块省略。

## 卡片与分组布局

主卡只显示产品身份、平台/地区、必要状态短标、原比例截图和 `analysis.materials[].insight.statement`；`research.goals` 非空时可增加精简的 `recommendation`。适用条件、限制、Claim 证据链接、全部 labels、审核说明、版本日期、来源 URL 和证据链 ID 放入默认关闭的页面详情，不从 `report_data.json` 删除。

桌面布局以五列为容量单位，把相邻分类作为不可交错的整体顺序放置：2＋2、3＋2 可同排，4＋2 时第二组换行。超过五张的组占满一行后在组内换行。响应式容量依次降为 4、3、2、1；不启用 dense 回填。20 张渐进展开以组为单位保存状态，视口变化不重新初始化。

## 交付前人工复核

`quality_review.reviewed_claim_ids` 必须恰好覆盖全部最终 Claim。复核检查：证据支撑、参考价值、研究相关性、例外与过度推断、重复结论、可替换产品名仍成立的空话。发现问题应删除或重写，并可在 `edits` 中保留前后记录。

同一素材的可见事实、语义审核、分类理由、分组 takeaway、逐图建议和综合结论属于同一条证据链。任何一层因逐图复核而改写时，Agent 必须一起复核其余层；默认卡片与折叠区不能出现相互矛盾的口径。Python 只校验字段、引用与覆盖，不能代替原图内容复核。

`review_type` 为 `agent_self_review` 或 `human_review`。Agent 自查必须标记 `independent:false`；报告折叠区会明确说明它不是独立质量验证。Python 只能确认复核记录完整，不能声称分析语义已经由程序验证。

## 默认结构与兼容

标题与核心结论 → 分类导航 → 可选且默认关闭的现状分析 → 分类截图与参考分析 → 默认整体关闭的来源与筛选说明 → 竞品分析小结。分类副标题只显示一句 `statement`；建议、条件和限制保存在结构化数据与单图/综合分析中。卡片详情默认关闭，截图可放大，素材复制到独立 `assets/`，每组超过 20 张的渐进展开继续保留。

v1 分析和分类计划仍可读取，以便历史报告重放；它们不会被补造 v2 工作底稿、分类审核或复核记录。`generation.analysis_standard` 为 `v2_agent_self_review`、`v2_human_review`、`legacy_v1` 或 `missing`，`standard_acceptance` 继续为 `not_assessed`。通过结构校验只表示数据可生成，不代表分析正确或历史证据升级为当前版本。

## 正式生成与重放

```bash
python3 -B -m competitor_analysis_skill \
  --task-file task.json \
  --reviewed-materials-file stage3c/reviewed_materials.json \
  --classification-plan-file classification-plan.json \
  --analysis-file analysis.json \
  --output reports/new-run

python3 -B -m competitor_analysis_skill \
  --report-data-file reports/new-run/report_data.json \
  --classification-plan-file revised-classification.json \
  --analysis-file revised-analysis.json \
  --output reports/new-run-replay
```

重放只能搭配替换分类、替换分析和新输出目录，不访问来源、不补造证据、不得覆盖输入。两场景 Stage 2 历史素材分析重放及前后对照见 [验收记录](../reports/manual-acceptance/user-feedback-optimization-2026-10-27/stage2-analysis-replay/README.md)；新来源正式运行、浏览器检查和逐项验收见 [第 4 阶段最终验收](../reports/manual-acceptance/user-feedback-optimization-2026-10-27/stage4-final-acceptance/README.md)。自动化覆盖见 `test_analysis.py`、`test_classification.py`、`test_report_content_pipeline.py`、`test_browser_report_content.py` 与 `test_source_access.py`。
