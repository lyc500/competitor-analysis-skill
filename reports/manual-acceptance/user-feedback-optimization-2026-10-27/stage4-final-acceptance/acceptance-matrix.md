# R1–R8（含 R5A）逐项验收表

| 编号 | 用户要求 | 对应实现 | 验证方式与实际结果 | 证据位置 | 状态 |
| --- | --- | --- | --- | --- | --- |
| R1 | 截图详情默认折叠 | 主卡只显示身份、必要状态、原图和参考重点；完整 labels、日期、URL、审核与证据链进入 `.card-details` | 三份新报告所有详情默认关闭；展开可见完整字段，放大互不误触 | `report.py`；`browser-evidence/browser-validation.json`；两场景桌面截图 | 完成 |
| R2 | 分类有明确合理依据 | classification v2 保存主维度、纳入标准、共同机制、成员理由和相邻差异；读者结论另存 analysis takeaway | 场景 A 按回访任务分组，拒绝设置页/他人主页/抽屉；场景 B 按改版问题分组，抽屉与根层只做机制对照 | 两场景 `classification-plan.json`、`semantic-reviews.json`；`manual-analysis-review.md` | 完成 |
| R3 | 小分类整体并排 | 分类块作为顺序网格单元，5/4/3/2/1 响应式；不 dense 回填；组内 20 张独立展开 | 新报告场景 A 2＋3、2＋1＋1；场景 B 2＋2、2 整组换行；既有自动化覆盖 4＋2、21/45 张、多组展开 | `report.py`；`tests/test_browser_report_layout.py`；浏览器 JSON/截图 | 完成 |
| R4 | 头部展示研究发现 | overview 只消费结构化总判断、关键发现与必要限制；统计数量次要，规则进入过程区 | 两份新报告头部均为证据化判断，无“真实、可放大、可追溯”等宣传 | `analysis.json`；桌面截图 | 完成 |
| R5 | 结论先行且具体 | analysis v2 保存逐图事实、比较、判断、建议、条件、取舍和边界；Claim 引用素材与工作底稿 | 人工逐图核对 9＋6＋1 张；删除“突出重点提升体验”空话候选；结论不推断频率/转化 | 两场景 `analysis.json`、`report_data.json`；`manual-analysis-review.md` | 完成；复核为 Agent 自查，不是独立验证 |
| R5A | 可选折叠现状分析 | current_state 有独立图/区域 ID，不进入 materials/classification/竞品统计 | 场景 B 有折叠现状且显示 6 个竞品/6 张；A 和设置页省略；现状区域事实、用户目标、推断分开 | `scenario-b-redesign/input/analysis.json`；报告与浏览器 JSON | 完成 |
| R6 | 分类副标题为一句有效结论 | `groups[].audit/reason` 只用于审核；`analysis.groups[].takeaway.statement` 单句展示 | 浏览器查看每组副标题说明比较/借鉴机制，不含数量、状态或点击说明 | 分类与分析 JSON；桌面截图 | 完成 |
| R7 | 过程整体折叠，分析小结收尾 | 来源准备、筛选、统计、候选和分类审核在 methodology details；synthesis 最后 | 三份新报告过程默认关闭；最后一个 `data-module` 均为 synthesis；覆盖缺口短提示仍可见 | `report_content.py`、`report.py`；浏览器 JSON | 完成 |
| R8 | 采集前检查登录/能力并支持选择、复查、恢复 | `source_access.py` 契约；正式截图 gate；同会话 context 复用；报告折叠展示当前能力 | 契约测试覆盖登录可用、公开部分、A/B 决定、登录后复查、订阅仍限、会话过期、网络异常和候选恢复；真实浏览器完成 4 来源预检 | `tests/test_source_access.py`、`tests/test_capture_workflow.py`；`source-access-observation.*`；各 sources JSON | 通用实现完成；真实新登录/用户拒绝流程未触发，未冒充实测 |

## B1 补充缺口

正式候选现在从来源尝试继承 `source_type`、`source_provider`、`target_surface` 和浏览器会话标签；语义产物补齐 `target_page`，规范化 `access_preparation` 可保存后再次读取。三场景 9 条正式命令完整通过，证明 Task → 来源 → captures → reviews → materials → classification/analysis → report 的最小与实际链路不再因字段缺失断裂。

`verify_reproducibility.py` 又从保存的 `reviewed_materials.json`、`classification-plan.json`、`analysis.json` 和本地资产生成到独立临时目录；三场景共 26 个报告文件逐文件 SHA-256 相等，详见 `reproducibility.json`。这项检查证明正式交付不依赖生成后手改 HTML。

## 未通过或未实际触发

- 没有为了测试流程强迫用户重新登录或购买订阅。真实第三方“用户选择登录 → 人工认证 → 同会话复查 → 从检查点恢复”尚未发生；恢复状态机由本地契约/会话夹具证明。
- 本批没有重大登录限制，所以没有真实询问“仅公开内容继续”。PTTRNS 的限制记录为 minor，其他来源已满足覆盖；这不等同于用户拒绝登录案例实测。
- 受订阅限制的隐藏结果未访问，报告只代表当前可见范围；样本结论已相应收窄。
