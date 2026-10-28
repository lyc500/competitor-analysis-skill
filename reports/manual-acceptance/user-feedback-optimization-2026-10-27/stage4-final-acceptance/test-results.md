# 第 4 阶段最终执行结果

执行日期：2026-10-28。以下项目按证据类型分开记录，测试夹具不代替第三方网站实测，浏览器检查也不代替分析语义判断。

## 正式流程与可复现性

- `run_acceptance.py`：场景 A、场景 B、设置页通用验证各执行来源登记、Stage 3C 审核和正式 Stage 4，共 9 条命令，全部退出码 0。原始命令、stdout、stderr 见 `actual-command-log.json`。
- `verify_reproducibility.py`：从保存的审核素材、分类、分析和本地资产生成到新临时目录；场景 A 12 个、场景 B 10 个、设置页 4 个文件，共 26 个文件逐文件 SHA-256 完全一致。见 `reproducibility.json`。
- 三份报告都由正式 CLI 生成，没有手改 HTML。历史素材只在已标注的“种子复查”与虎牙现状输入中使用，未冒充本次首次发现。

## 自动化与静态检查

- `python3 -B -m unittest discover -s tests -p 'test_*.py' -q`：175 项通过，0 failure、0 error、0 skip，用时 29.639 秒。保留 3 条 localhost 测试服务器未关闭 socket 的 `ResourceWarning`，未影响结果。
- `env PYTHONPYCACHEPREFIX=/tmp/competitor-analysis-pycache python3 -B -m compileall -q ...`：通过。默认 macOS Python 缓存位置不在沙箱写入范围，因此显式使用可写的 `/tmp` 缓存。
- `git diff --check`：通过。
- Ruby YAML 解析 `SKILL.md` frontmatter：通过，名称为 `competitor-analysis`。
- Skill 只读压力复测：候选容量与覆盖停止条件、截止时检查点/缺口、访问准备后的 fallback 顺序三项均通过。该复测检查工作流规则，不代表真实网站访问。

## 浏览器与人工验收

- `browser_acceptance.py`：三份报告全部通过。图片全部加载；卡片详情、现状和来源过程默认关闭；综合小结为最后主要模块；键盘打开灯箱及 Escape 关闭有效；1440×1000 与 390×844 均无横向溢出。结构化几何和状态见 `browser-evidence/browser-validation.json`，代表性整页截图见 `browser-evidence/*.png`。
- 场景 A 桌面布局为 2＋3、2＋1＋1；场景 B 为 2＋2，第三个 2 张组整体换行；移动端保持分类和素材原顺序单列展示。
- 人工分析复核逐图检查事实、引用、分类边界、参考价值、例外和过度推断，见 `manual-analysis-review.md`。这是 Agent 自查，明确不是独立语义验证。

## 真实来源边界

- UI Notes、Refero、Mobbin、PTTRNS 的真实浏览器预检见 `source-access-observation.json` 和 `.md`；14 张原图及哈希见 `raw-assets/`、`raw-asset-manifest.json`。
- 本次没有发生新的第三方登录，也没有发生用户选择“仅公开内容继续”。登录恢复、公开继续、订阅仍限、会话过期和网络异常分支由契约/会话夹具验证，不能写成真实网站流程已跑通。
- UI Notes、Refero、Mobbin 的隐藏订阅内容没有访问，结论只覆盖本次可见和通过审核的样本。
