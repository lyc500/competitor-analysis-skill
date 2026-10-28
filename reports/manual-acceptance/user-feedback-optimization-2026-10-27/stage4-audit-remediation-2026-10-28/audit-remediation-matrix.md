# 独立审计修正矩阵

| 优先级 | 根因 | 修改位置 | 回归测试 | 实际验证 | 结果与限制 |
| --- | --- | --- | --- | --- | --- |
| P1 登录限制可被 `not_required` 绕过 | 决定分支只检查字段组合，没有拒绝当前 material 级认证限制；执行入口与决定校验未共享执行 gate | `source_access.py`、`pipeline.py`、`tests/test_source_access.py` | 当前限制＋not_required 被拒；pending 不调用执行器；public_only 只执行可访问候选；历史限制解除不阻塞；登录复查更新当前状态 | 同一 Chrome 复查四来源；本批没有 material 级认证限制 | 代码与自动化通过；真实登录／拒绝登录链路未触发，R8 仍部分实证 |
| P1 恢复未使用候选检查点 | `capture_sources()` 总是接收整个 candidate pool，resume 只做数据校验 | `pipeline.py`、`tests/test_source_access.py`、`docs/SOURCE_ACCESS_CONTRACT.md` | 全部完成不调用执行器；部分完成只传 remaining；blocked 不执行；复查后仅恢复剩余；损坏完成产物报受影响 ID | pipeline mock 直接检查执行器实参；正式全量回归通过 | 通过。legacy sources 仍保留诊断兼容分支并标记 `legacy_incomplete`，不冒充正式检查点恢复 |
| P1 分析超出截图证据 | 分析契约引用有效，但 Agent 文案把任务入口写成进度，把用户会员目标写成现状事实，并把方案风险写成既有事实 | 两场景 `input/analysis.json`，通用生成入口不变 | 正式契约／引用测试；两场景从结构化输入重生成；浏览器与可复现性检查 | 逐图查看 Bilibili、豆包、虎牙现状等源图；新报告人工复核 | 通过。删除进度越界；现状明确“未显示独立平台会员入口”；大卡片竞争改成条件性建议 |
| P2 场景 A 概括和逐卡文案泛化 | 总判断超出样本，设置入口口径错误，九张卡片共用一句泛化建议 | 场景 A `input/analysis.json` | v2 分析契约、正式生成、浏览器验收 | 逐图核对 9 张 accepted 素材 | 通过。总判断限定“本批样本”；设置改为根层紧凑辅助入口；逐卡说明具体动作、条件或补充验证价值 |
| P2 固定产品映射可能污染正式入口 | 固定映射与正式 parser 同在 `requirements.py`，边界主要靠注释 | `legacy_demo.py`、`requirements.py`、`pipeline.py`、`__main__.py`、README、SKILL | 正式 task-file patch legacy parser 后仍运行；legacy 输出含 `legacy_demo_only`；既有旧导入测试通过 | CLI 帮助、正式报告命令与全量回归 | 通过。未新建自然语言解析系统，保留合理兼容性 |

## 保护项回归

- report bundle 与快照重放没有改写；两份报告独立重生成逐字节一致。
- reason 与 takeaway 继续分离。
- 卡片详情、现状和来源说明默认折叠；重大限制仍在头部短提示。
- 小分类按组并排，移动端顺序堆叠；20／21／45 张和多组展开由现有浏览器测试继续覆盖。
- 现状图不进入竞品数量；场景 B 仍为 6 张竞品图＋1 张现状图。
- 图片保持原比例，放大、Escape 关闭、分类导航和结尾小结通过实际 Chromium。
- 来源、候选、截图、审核、素材和报告引用保持原 ID，没有清空候选或检查点。
