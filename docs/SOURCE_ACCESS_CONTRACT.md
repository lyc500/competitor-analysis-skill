# 来源访问准备契约

更新时间：2026-10-28

正式在线采集在理解研究范围后、批量发现和截图前，使用与后续采集相同的浏览器会话对本次相关来源做快速能力检查。它不要求遍历所有网站，也不保存 cookie、密码、验证码、storage state 或其他凭据。

`sources-input.json.access_preparation` 与既有 `source_attempts`、`candidates` 同库存储。Agent 负责选择来源、实际观察和判断覆盖影响；Python 只校验字段、时间顺序、引用、用户决定、同会话复查和恢复分区。

## 能力检查

每条 `checks[]` 记录一个来源、阶段、浏览器会话与标签，以及：

- 页面能否打开；
- 搜索、筛选、详情、原图和分页/滚动是否可用；
- 来源认证状态；
- `login_required`、`paywall`、`security_verification`、`network_error`、`empty_results`、`session_expired` 等实际边界；
- 可见范围、对本次覆盖的影响和必要说明。

头像或登录按钮不能单独证明能力。网络错误不能写成未登录；登录后仍受订阅限制时保留 `paywall`。同一网站不同会话或标签若能力不同，应分别检查，不能把一个成功状态泛化到其他上下文。来源网站认证状态与竞品 App 截图中的 `login_state` 是两套字段。

## 用户决定

只有重大登录、验证或会话过期限制实质影响研究覆盖时，Agent 才一次汇总已可用来源、建议登录来源、订阅边界和公开范围限制，并提供“协助登录后继续”或“仅用当前公开内容继续”。

- `not_required`：当前有效检查没有 material 级认证限制，不阻塞搜集；历史检查曾受限但当前复查已经恢复时可以使用；
- `pending_user_choice`：已汇总限制，等待一次选择；
- `public_only`：用户选择当前公开范围，同一批次不重复询问；
- `login_then_continue`：用户选择正常登录，必须完成复查后恢复。

用户选择登录后，`recheck` 必须晚于决定并复用该来源已有的有效浏览器会话。用户说“已登录”不是成功证据；需要重新检查搜索、详情、原图和分页。恢复记录将候选分成已完成与待继续，二者不能重复或丢失。登录后仍受订阅限制可记录为 `partial` 或 `blocked`，不得自动购买或绕过限制。

`not_required` 不能覆盖当前仍存在的 material 级 `login_required`、`security_verification` 或 `session_expired`。订阅 `paywall`、网络异常与真实无结果分别记录，不自动解释成“登录即可解决”。用户已经选择 `public_only` 后，只执行当前检查明确支持所需详情或原图能力的候选，并在同一批次复用选择，不重复打断。

## 正式入口

`--capture-sources` 只接受带正式 `source_attempts/candidates`、候选池和通过校验的 `access_preparation` 的来源输入。旧 `{"sources":[...]}` 格式可以继续用于离线读取、诊断或历史重放；一旦请求实际采集，会在截图执行器运行前拒绝，并提示迁移到正式来源契约。系统不得把缺失预检或用户选择自动补成“已就绪”或 `not_required`。等待用户选择或等待登录时会停止截图。规范化输出可以保存后再次读取；派生的 `current_checks_by_source` 和 `choice_is_final_for_batch` 会重新计算并校验一致性。

截图执行器消费恢复检查点，而不是每次接收整个 `candidate_pool`：

- `completed_candidate_ids` 对应的已有截图必须仍存在、能解码、状态有效且与候选证据链一致；满足这些条件时直接保留，不重复截图或审核；
- `remaining_candidate_ids` 才进入本次执行计划；部分完成和失败重试只处理这一部分；
- `remaining_candidate_ids` 为空时不调用截图执行器；
- `blocked` 在条件未解除时不执行剩余候选，复查恢复后只处理仍待继续的候选；
- 已完成产物缺失或损坏时明确报出受影响候选，要求保留候选 ID 并将这些候选移回 remaining，不静默重跑全部候选。

每次正式截图输出 `capture_execution`，保存计划候选、已完成候选、实际执行候选、跳过候选和跳过原因，供统计与恢复复核。执行前的用户决定校验和实际执行计划使用同一份当前检查。

浏览器批量截图在同一次命令中按 `browser_session_kind/browser_session_id` 复用 context，同一会话可延续正常 cookie；不同会话隔离。Agent 桌面浏览器的认证状态不能自动转移给 Python Playwright，输入若声明必须复用已认证 Agent 会话，正式截图会明确拒绝伪装复用，改由现有浏览器完成候选获取并保存关联记录。

测试夹具只能证明状态流和契约。第三方网站的真实访问、登录、复查和恢复必须另存浏览器观察证据；未实际发生登录恢复时，不得用 mock 标成真实通过。
