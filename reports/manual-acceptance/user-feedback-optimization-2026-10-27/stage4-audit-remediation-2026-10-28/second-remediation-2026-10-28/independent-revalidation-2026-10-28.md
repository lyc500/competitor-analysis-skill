# 第二轮修正独立复验

日期：2026-10-28

检查对象：`main` 工作区，基础 HEAD `030a962882f9b04731445dc0e1e5607d9086a1db` 及其全部未提交优化。

结论：**可带明确限制进入正式交付**。

本记录来自交付前独立读取、探针、原图复核、正式重生成和测试；此前修正方的 STATUS 与总结只作为导航。

## 四项复验

- 旧 `{"sources":[...]}` 在正式 `--capture-sources` 下于截图执行器之前被拒绝。独立 CLI 子进程退出码 1，pipeline 与 CLI 拦截探针记录执行器调用 0 次，未生成 `captures.json`；无采集离线兼容仍可读取并标为 `legacy_incomplete`；合法 `public_only` 路径只执行允许的候选。
- 豆包、Wise、NYT、Airbuds 的原图、逐图事实、语义审核、分类理由、卡片、快照和综合小结口径一致。豆包只支持金币商城/任务中心入口及登录提示；Wise 只支持账户切换、Settings、Help；NYT 只作当前可见下段局部参考；Airbuds 只支持身份与个人内容表达。
- 整个 `captures.json` 缺失时，错误稳定列出 `cand-a, cand-b`；个别完成候选记录缺失时只列 `cand-b`。两种情况截图执行器均未调用，没有静默重跑候选池。
- 两份报告由正式入口在 `/private/tmp` 独立重生成。场景 A 12 个文件、场景 B 10 个文件，文件集合和逐文件 SHA-256 与交付报告一致。Playwright Chromium 确认修正文案进入默认卡片和折叠分类审核区，图片加载、放大、Escape 关闭、默认折叠及综合小结末尾正常。

## 实际验证

- `python3 -B -m unittest discover -s tests -p 'test_capture_workflow.py' -v`：13 项通过。
- `python3 -B -m unittest discover -s tests -p 'test_source_access.py' -v`：24 项通过。
- `python3 -B -m unittest discover -s tests -p 'test_*.py' -q`：190 项通过，0 failure/error/skip，退出码 0；保留 localhost socket `ResourceWarning` 和预期连接断开产生的 BrokenPipe 日志。
- `PYTHONPYCACHEPREFIX=/private/tmp/independent-second-round-pycache python3 -m compileall -q competitor_analysis_skill tests`：通过。
- `git diff --check`：通过。
- Skill Creator `quick_validate.py`：`Skill is valid!`。
- 历史归档 `reports/manual-acceptance/v0.1-user-tests-2026-10-26/`：90/90 文件路径、SHA-256 和 mtime 与清单一致。

首次在受限沙箱直接点名模块运行时，38 项中出现 4 个环境/调用方式错误：一个来自禁止绑定本地回环端口，三个来自未按项目 discover 方式加入 `tests/` 夹具路径；没有实现断言失败。随后按项目实际方式复跑并保留上述结果。

## 明确保留的限制

1. R8 真实“用户选择登录或公开继续—人工认证—同会话能力复查—恢复未完成采集”尚未完整触发。自动化状态流和真实网站能力预检不能替代这条真实链路。
2. NYT 当前截图与 You 标签根层首屏的关系未证实；它只作为当前可见下段内容卡的局部参考。
3. 测试中的少量 socket `ResourceWarning` 与 BrokenPipe 输出是已记录的非阻塞清理问题。

未发现新的 P0 或阻断正式交付的 P1。
