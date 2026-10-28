# 修正测试与验收结果

## 失败先行与缺陷复现

- `python3 -B -m unittest tests.test_source_access -v`：修正前新增用例出现 2 failure、4 error，复现了 `not_required` 放行、执行器提前调用、检查点完成项重跑与执行元数据缺失。
- 两个 legacy 边界新用例修正前均 error：pipeline 没有隔离后的 parser 符号，legacy 输出没有能力标记。
- 首轮最终全量回归执行 186 项，出现 1 failure、1 error：新执行计划误用于旧 `sources[]` 兼容输入。已增加明确 legacy 诊断分支，正式结构化来源仍强制 access preparation。

## 最终自动化

- `python3 -B -m unittest tests.test_source_access -v`：22 项通过。
- `python3 -B -m unittest discover -s tests -p 'test_capture_workflow.py' -q`：12 项通过。
- `python3 -B -m unittest discover -s tests -p 'test_analysis.py' -v`：16 项通过。
- `python3 -B -m unittest discover -s tests -p 'test_report_content_pipeline.py' -v`：12 项通过。
- 最终全量命令 `python3 -B -m unittest discover -s tests -p 'test_*.py' -q`：186 项通过，0 failure、0 error、0 skip，28.433 秒。通过用例输出 3 条既有 localhost socket `ResourceWarning`，不影响断言结果。
- `PYTHONPYCACHEPREFIX=/tmp/competitor-analysis-pycache-final python3 -m compileall -q competitor_analysis_skill tests`：通过。
- `git diff --check`：通过。
- `/tmp/competitor-analysis-quick-validator-venv/bin/python .../quick_validate.py /Users/yuchunli/competitor-analysis-skill`：`Skill is valid!`。首次系统 Python 因缺少 PyYAML 失败；依赖只安装在 `/tmp` venv，未写入项目依赖。

一次定向组合命令用 `python -m unittest tests.test_analysis ...` 运行时，因为这些测试按 discover 模式导入 `tests/report_content_fixtures.py`，出现 2 个 `ModuleNotFoundError`；改用仓库标准的 `discover -s tests -p ...` 后分别 16／12 项通过。这是命令调用方式问题，不是代码失败，记录保留。

最后一次全量复验先在受限沙箱内执行，174 项运行后有 9 个环境权限 error：本地 HTTP 用例不能绑定 `127.0.0.1`，Playwright Chromium 不能注册 macOS Mach 服务。随后以完全相同的命令在获准的非沙箱环境复跑，186 项全部通过；这里不把沙箱权限失败写成测试通过。

## 正式生成与可复现性

- 场景 A／B 均使用 `--task-file + --reviewed-materials-file + --classification-plan-file + --analysis-file` 生成。
- 最终文案收窄后再次独立 `/tmp` 重生成，A 的 12 个报告文件、B 的 10 个报告文件 SHA-256 全部一致；见 `reproducibility.json`。
- 没有把 2026-10-28 重生成写成新来源采集，原素材采集时间保留。

## 浏览器与人工验收

- `browser_acceptance.py` 在最终文案重生成后通过 2 个场景。首轮沙箱内 Chromium 启动被系统权限拒绝，获准在沙箱外运行；脚本初版使用了错误导航 selector，修正测试脚本后通过。
- 桌面 1440×1000 与移动 390×844 均无水平溢出；图片全部加载；卡片详情、现状和来源默认关闭；分类导航可定位；Enter 打开放大，Escape 关闭；综合小结为最后主要模块。
- 场景 A 的 2＋3 小组同排；场景 B 的 2＋2 同排，第三个 2 张组整体换行。移动端按组顺序堆叠。
- 人工逐图查看 9 张场景 A accepted 素材、6 张场景 B accepted 素材与虎牙现状图；重点复核哔哩哔哩、豆包、NYT、酷狗、Wise、Kickstarter 和虎牙现状的文案边界。

## 真实来源链路

- 同一 Chrome「用户1」配置只读复查 UI Notes、Refero、Mobbin、PTTRNS，列表／详情／主图结果见 `source-access-revalidation.json`。
- 本批未出现 material 级认证限制，没有真实发生用户选择、登录后同会话复查和恢复。对应状态为“自动化已覆盖、真实链路待触发”，不宣称全面通过。
