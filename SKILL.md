---
name: competitor-analysis
description: 根据自然语言需求搜集竞品页面、筛选公开素材、动态分类并生成可点击放大的 HTML 报告。
---

# 竞品分析 Skill

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

Agent 必须逐项判断产品身份、目标页面匹配、页面主体完整性和图片类型，并提供 `semantic_reason`。只有 matched/matched/complete/ui_page 才能声明 `semantic_status=accepted`。Python 只校验 Review Contract，并将 browser、user_upload、device_capture 统一交给阶段 2 机械质量复验；它不通过关键词、文件名、URL、OCR 或图像规则推断语义。输出独立的 `reviewed_materials.json` 与 `fallback_requests.json`，不会提前进入分类或 HTML 报告。

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

新增来源应实现独立采集器并输出统一素材字段，不修改报告消费接口。分类器根据素材差异选择地区、产品类型、页面结构或设计模式等维度，不把任何单一维度作为固定模板。
