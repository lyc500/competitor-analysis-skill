# Stage 5 真实验收产物规范

本目录定义 Stage 5B / 5C 真实运行结果的保存方式。Stage 5B Task A 已真实执行，产物位于 `task-a/`，当前为“达到自验收门槛，等待独立复验”；Stage 5C Task B 尚未执行，因此不创建 `task-b/` 或任何空的成功产物。

`tests/fixtures/acceptance/task_a.json` 与 `task_b.json` 只是本次 Agent 生成的 Task Contract 验收输入，不是公网采集结果；其中的竞品清单也不属于 production catalog、planner 或 Python 固定映射。

## 后续目录结构

真实执行时，每个任务使用独立目录：

```text
reports/acceptance/
  task-a/
    RUN_RECORD.md
    task.json
    sources.json
    captures.json
    semantic-reviews.json
    reviewed_materials.json
    fallback_requests.json
    classification-plan.json
    classification.json
    report_data.json
    report.html
    assets/
  task-b/
    RUN_RECORD.md
    task.json
    sources.json
    captures.json
    semantic-reviews.json
    reviewed_materials.json
    fallback_requests.json
    classification-plan.json
    classification.json
    report_data.json
    report.html
    assets/
```

只保存真实执行过程中实际生成的文件。某一步未执行、失败或被环境阻塞时，对应文件可以不存在，但必须在 `RUN_RECORD.md` 中如实记录，不得创建空文件或伪造成功产物。

## 运行记录要求

每个 `RUN_RECORD.md` 至少记录：

- 执行时间、执行环境、代码 commit SHA 和操作人/Agent。
- 实际命令或操作步骤，以及每一步的开始、结束和结果。
- 使用的真实来源与 `collection_method`；来源或采集时间未知时明确标记未知。
- 浏览器真实打开、页面操作、截图、语义审核、机械质量检查、分类、报告生成和报告交互验证的证据。
- 每个失败项的真实状态：`blocked`、`failed`、`needs_manual_capture` 或 `unavailable`，以及未生成哪些产物。
- 是否达到对应 Task 硬门槛；未达到时不得写“完成”或“通过”。

## 真实性边界

- 禁止用 offline fixture、内置候选、假截图或空产物冒充真实公网执行。
- 浏览器截图不得自动视为 semantic accepted 或 collected；必须经过 Agent 视觉语义审核和机械质量检查。
- Logo、OG Image、分享图、营销图和无上下文图片不得计入有效页面截图。
- 网络或环境限制不会降低验收标准，只能形成可追溯的失败或 fallback 记录。
- Stage 5A 只准备验收输入与规范；Stage 5B Task A 已真实执行并等待独立复验；Stage 5C Task B 尚未执行。
