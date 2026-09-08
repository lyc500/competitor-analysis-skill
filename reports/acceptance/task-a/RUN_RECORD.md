# Stage 5B Task A 真实端到端运行记录

## 执行信息

- 执行任务：`帮我搜集一下海内外热门产品的搜索结果页。`
- 执行时间：2026-09-08 01:49–02:01 UTC（北京时间 09:49–10:01）。
- 执行 Agent：Codex。
- 执行机器：Apple Silicon MacBook Air，macOS 15.5（Darwin 24.5.0，arm64）。
- Python：3.9.6；Playwright：1.60.0；Pillow：11.3.0。
- Chromium：148.0.7778.96，真实 headless Chromium；未使用 mock。
- 执行起始 commit：`4e64e45a903c38c7cf3a6c70747aaa5c57fd308d`，开始时本地 `HEAD` 与 `origin/main` 一致且工作区 clean。
- Task Contract：`task.json` 与已通过 Stage 5A 的 `tests/fixtures/acceptance/task_a.json` 一致。

## 执行假设与来源发现

搜索结果页必须带查询词。本次 Agent 以 `product design` 作为跨产品主要中性查询词；为同一竞品补充第二个真实候选时，按页面可用性使用 `mobile interface design` 或 `design pattern`。查询词和本次竞品清单只存在于验收输入、运行记录与截图中，没有写入 production catalog、planner 或 Python 固定映射。

来源由 Agent 在本次执行中通过真实 Web 搜索和官网页面发现，全部为 `public_web`。没有使用 fixture URL、`SEARCH_CATALOG`、builtin candidate、Logo、OG Image 或营销图凑数。

## 实际命令

实际运行时使用临时虚拟环境，并通过 `PLAYWRIGHT_BROWSERS_PATH` 指向本机已安装的 Chromium；正式业务入口未被替代。

```text
env PATH=/private/tmp/competitor-analysis-skill-venv/bin:/usr/bin:/bin:/usr/sbin:/sbin \
  PLAYWRIGHT_BROWSERS_PATH=/private/tmp/competitor-analysis-playwright-browsers \
  python3 -m competitor_analysis_skill \
  --task-file reports/acceptance/task-a/task.json \
  --sources-file reports/acceptance/task-a/sources-input.json \
  --capture-sources \
  --output reports/acceptance/task-a

env PATH=/private/tmp/competitor-analysis-skill-venv/bin:/usr/bin:/bin:/usr/sbin:/sbin \
  PLAYWRIGHT_BROWSERS_PATH=/private/tmp/competitor-analysis-playwright-browsers \
  python3 -m competitor_analysis_skill \
  --task-file reports/acceptance/task-a/task.json \
  --captures-file reports/acceptance/task-a/captures.json \
  --semantic-reviews-file reports/acceptance/task-a/semantic-reviews.json \
  --output reports/acceptance/task-a

env PATH=/private/tmp/competitor-analysis-skill-venv/bin:/usr/bin:/bin:/usr/sbin:/sbin \
  PLAYWRIGHT_BROWSERS_PATH=/private/tmp/competitor-analysis-playwright-browsers \
  python3 -m competitor_analysis_skill \
  --task-file reports/acceptance/task-a/task.json \
  --reviewed-materials-file reports/acceptance/task-a/reviewed_materials.json \
  --classification-plan-file reports/acceptance/task-a/classification-plan.json \
  --output reports/acceptance/task-a
```

最终报告验证由本地 `ThreadingHTTPServer` 提供 `reports/acceptance/task-a/`，再由同一套真实 Chromium 打开 `report.html`、检查全部 `.asset-image`、点击首张真实截图并检查 dialog 图片。

## 真实来源、Capture、语义与机械质量

`captured` 只表示 Chromium 产生了截图。Agent 随后逐张实际查看全部 10 张 captured 截图；2 个 failed Capture 没有创建伪 Review。机械质量 `accepted` 只表示图片可解码且尺寸、格式等合格，不会覆盖语义拒绝。

| 竞品 | 真实请求 URL | Capture | Agent Semantic Review | Mechanical Quality | 最终状态与真实原因 |
| --- | --- | --- | --- | --- | --- |
| 百度 | `https://www.baidu.com/s?wd=product%20design` | captured，HTTP 200 | rejected | accepted | rejected；画面是百度安全验证滑块，不是搜索结果。 |
| 百度 | `https://m.baidu.com/s?word=product%20design` | captured，HTTP 200 | rejected | accepted | rejected；跳转到百度图形验证码，不是搜索结果。 |
| Google | `https://www.google.com/search?q=product%20design` | captured，HTTP 200 | rejected | accepted | rejected；跳转到 unusual traffic / sorry 页面，没有结果列表。 |
| Google | `https://www.google.com.hk/search?q=product%20design&hl=en` | captured，HTTP 200 | rejected | accepted | rejected；同样被 unusual traffic 页面替代。 |
| 小红书 | `https://www.xiaohongshu.com/search_result?keyword=product%20design` | captured，HTTP 200 | rejected | accepted | rejected；画面仅显示“IP 存在风险”的安全限制。 |
| 小红书 | `https://www.xiaohongshu.com/search_result?keyword=product%20design&type=51` | captured，HTTP 200 | rejected | accepted | rejected；画面仍是安全限制，不是搜索结果。 |
| 哔哩哔哩 | `https://search.bilibili.com/all?keyword=Product%20Design` | captured，HTTP 200 | accepted | accepted | collected；真实搜索词、类型标签、排序入口和多行视频结果均可见，登录提示没有替代主体结果。 |
| 哔哩哔哩 | `https://search.bilibili.com/all?keyword=design%20pattern` | captured，HTTP 200 | accepted | accepted | collected；真实搜索词、类型标签、排序入口和视频卡片流均可见。 |
| Perplexity | `https://www.perplexity.ai/search?q=product%20design` | failed，HTTP 403 | 不创建 Review | 不适用 | unavailable；真实页面请求被 HTTP 403 拒绝，无截图。 |
| Perplexity | `https://www.perplexity.ai/search?q=mobile%20interface%20design` | failed，HTTP 403 | 不创建 Review | 不适用 | unavailable；真实页面请求被 HTTP 403 拒绝，无截图。 |
| Amazon | `https://www.amazon.com/s?k=product+design` | captured，HTTP 200 | accepted | accepted | collected；查询词、结果数量、筛选、排序和多条商品结果可见。 |
| Amazon | `https://www.amazon.com/s?k=mobile+interface+design` | captured，HTTP 200 | accepted | accepted | collected；筛选栏、排序及商品图、价格、评分、配送信息可见，配送提示未替代主体。 |

Capture 元数据与实际截图见 `captures.json` 和 `captures/`；逐图结论见 `semantic-reviews.json`；机械复核和最终 Material 状态见 `reviewed_materials.json`。

## Stage 3C 结果与 fallback

- reviewed Material：10 个。
- `quality_status = accepted`：10 个 captured 文件。
- `semantic_status = accepted` 且最终 `collection_status = collected`：4 个。
- `semantic_status = rejected` 且最终 `collection_status = rejected`：6 个。
- Perplexity 的 2 个 failed Capture 不生成 Material 或伪 Review。
- 有效地域：CN 2 个（哔哩哔哩），Global 2 个（Amazon）。
- 有效产品：2 个；Task Contract 中 6 个竞品均保留，没有因采集困难删除。

Fallback 最终状态：

| 竞品 | 状态 | 原因 |
| --- | --- | --- |
| 百度 | open | 公开截图被验证码替代，没有有效 Material。 |
| Google | open | 公开截图被 unusual traffic 页面替代，没有有效 Material。 |
| 小红书 | open | 公开截图被 IP 风控页面替代，没有有效 Material。 |
| 哔哩哔哩 | resolved | 已有 2 个真实 collected Material。 |
| Perplexity | open | 两个候选均返回 HTTP 403，没有有效 Material。 |
| Amazon | resolved | 已有 2 个真实 collected Material。 |

没有伪造 `user_upload` 或 `device_capture`；open fallback 保持 open。

## Agent Classification Plan 与报告

Agent 在 4 个真实 collected Material 形成后才决定分类，最终维度为：

```text
真实搜索结果的内容组织方式
```

分组：

1. `商品筛选与购买决策列表`：2 个 Amazon Material。
2. `视频内容筛选与封面卡片流`：2 个哔哩哔哩 Material。

每个 collected Material 恰好进入一个分组；rejected / failed 项没有进入分类。分类理由和动态标签来自本次截图中实际可见的结果载体、决策信息和筛选排序方式，不根据 `product_type`、`notes` 或关键词推断。

Stage 4 正式入口生成了 `classification.json`、`report_data.json`、`report.html` 和报告本地 `assets/`。最终主图墙只有 4 个 collected Material，HTML 使用安全相对资产路径。

## 真实 Chromium 报告验证

- 本地 HTTP 状态：200。
- `.asset-image` 数量：4。
- 四张主图 `naturalWidth`：`[1440, 1440, 1440, 1440]`。
- 实际点击：首张 Amazon 真实截图。
- `dialog[open]`：成功出现。
- 放大图 `naturalWidth`：1440。
- 资源路径错误：未发现。
- 页面证据：`evidence/report-page.png`。
- 放大证据：`evidence/report-dialog-open.png`。

## 执行中发现并修复的通用缺陷

本次真实 E2E 暴露两个确定性通用缺陷，均按失败测试先行做了最小修复，没有增加任何站点专用逻辑，也没有降低 semantic / quality 门槛：

1. Chromium 路由防护对无法解析的第三方子资源抛出异常，会让主页面 Capture 批次中断。新增真实浏览器回归测试，确认无效子资源被终止而合法主页面仍可截图。
2. CLI 使用相对 `--captures-file` 时，Stage 3C 会把相对截图路径二次拼接到输出目录，导致存在的截图被误判为 missing。新增正式 CLI 回归测试并统一从 captures 文件所在目录解析路径。

两项修复后的正式流程重新完整执行，本文所有最终数字均来自修复后的持久化产物。

## 完整回归验证

提交前真实执行：

```text
python3 -m unittest discover -s tests -v
```

结果：83 项通过，0 失败，0 error，0 skip；其中真实 Chromium Capture 测试和报告浏览器测试均实际执行。另执行 `python3 -m compileall competitor_analysis_skill tests`、验收产物一致性脚本和 `git diff --check`，结果均须为退出状态 0 后才提交。

## 最终结论

Task A 取得 4 张真实有效截图，且 CN 与 Global 各有 2 张；每份有效素材均同时满足 semantic accepted、mechanical quality accepted、collection collected 和有效 `image_path`。动态分类与最终 HTML 已生成，并由真实 Chromium 完成图片加载和点击放大验证。

**Stage 5B Task A 达到自验收硬门槛，当前状态为“真实 Task A 执行完成，等待独立复验”。**

Stage 5C 未执行；Task B 未执行；V0.1 MVP 仍未通过；iPhone 镜像自动化尚未实现。
