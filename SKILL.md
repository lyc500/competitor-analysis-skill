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
