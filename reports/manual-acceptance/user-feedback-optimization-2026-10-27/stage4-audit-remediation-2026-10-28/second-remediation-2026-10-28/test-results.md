# 第二轮测试与校验结果

日期：2026-10-28。

## 失败先行与定向回归

- 修正前新增测试真实失败：旧 `sources` 格式进入 pipeline 时截图 mock 被调用并导致序列化错误；正式 CLI 返回 0；整个 `captures.json` 缺失错误不含 `cand-1`；SKILL 缺少同一素材各分析层一起复核的约束。
- 首次合并点名测试在受限沙箱运行：37 项中 33 项通过，4 个 error。截图测试因不允许绑定 `127.0.0.1`；三个报告测试因点名模块方式没有把 `tests/` 加入辅助模块搜索路径。没有断言失败。
- 改用项目既有 discovery 方式并允许本机回环端口后，六组定向测试分别为 13、24、11、16、9、12 项，合计 **85 项通过**，0 failure/error/skip。

## 全量与静态校验

- `python3 -B -m unittest discover -s tests -p 'test_*.py' -q`：最终复跑 **190 项通过**，0 failure/error/skip，28.233 秒；输出 3 条未关闭 localhost socket 的 `ResourceWarning`，不影响退出码 0。
- `PYTHONPYCACHEPREFIX=/private/tmp/competitor-analysis-second-remediation-pycache python3 -m compileall -q competitor_analysis_skill tests`：通过。
- `git diff --check`：通过。
- `/tmp/competitor-analysis-quick-validator-venv/bin/python .../quick_validate.py /Users/yuchunli/competitor-analysis-skill`：`Skill is valid!`；PyYAML 只存在 `/tmp` 隔离 venv，未增加项目依赖。
- 历史归档清单：90/90 文件集合一致，全部 SHA-256 与 `historical-archive-manifest.json` 相同。

## 正式生成、探针与浏览器

- 两份报告用 `python3 -B -m competitor_analysis_skill --task-file ... --reviewed-materials-file ... --classification-plan-file ... --analysis-file ...` 正式重生成。
- 独立临时目录重生成：A 12 个文件、B 10 个文件；文件集合与每个文件 SHA-256 全部一致，见 `reproducibility.json`。
- 正式 CLI main 负向探针：旧来源格式返回清楚迁移错误，截图执行器调用 0 次，未生成 `captures.json`，见 `legacy-cli-negative-probe.json`。
- Playwright Chromium：两份报告桌面 1440 与移动 390 均通过；图片加载、详情/来源/现状默认折叠、小组并排、移动顺序、详情与放大互不误触、Escape 关闭、修正文案进入折叠分类审核、综合小结最后均通过，见 `browser-validation.json` 和四张整页截图。

## 证据边界

真实第三方“用户选择登录或公开继续—人工认证—同会话复查—恢复采集”本轮没有触发。相关状态与 pipeline 衔接由自动化覆盖，不能记录成真实登录验收。
