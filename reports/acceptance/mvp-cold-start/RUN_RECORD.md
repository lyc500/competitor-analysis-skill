# V0.1 MVP Cold-start 真实使用验收运行记录

## 运行边界

- 基线：`1fc1f89589e9b21f865fce4d2dc569603459034a`
- 运行日期：2026-09-09
- 唯一用户输入：`帮我搜集一下国内外热门内容社区产品的用户个人主页。`
- 本轮没有读取或复用 Task A、Task B、Task 5B-R1、Task 5C 的产品清单、来源 URL、Classification Plan 或人工判断。
- 生产 Python、根目录 `SKILL.md` 和测试均未修改；没有使用 `fixture_demo`、production catalog 或产品名到 URL 的固定映射。

## Agent 对需求的理解

Agent 将目标页判断为 `用户个人主页`，将“国内外”解释为 `CN + Global`。用户没有指定端面，依据 `SKILL.md` 的默认规则将 `target_surface` 设为 `mobile_app`，优先寻找 iOS/Android App 单屏。这里的个人主页定义为能够同时观察身份、关系动作或统计，以及内容资产或导航的资料/账户页。

完整结构化合同保存在 `task.json`，任务状态为 `ready`，规划策略为 `agent_only`，`specified_products` 为空。

## Agent 竞品规划

Agent 根据目标页和实际需求差异规划四个代表性样本，没有在执行前由验收指令指定产品：

| 产品 | 地区 / 类型 | 入选理由 |
| --- | --- | --- |
| 小红书 | CN / 生活方式内容社区 | 个人页将身份统计、关注关系与笔记网格并置，代表内容资产型主页。 |
| 知乎 | CN / 知识内容社区 | 可对照回答/文章贡献与关注关系的组织方式；即使公开素材不足也保留目标。 |
| Instagram | Global / 视觉社交内容社区 | 个人页同时展示验证身份、关系统计、关注动作和视觉内容网格。 |
| Medium | Global / 创作者写作社区 | 账户页把关注关系、统计、编辑动作和 Stories/Lists/About 创作导航并置，补充非图片网格路径。 |

## 来源发现与实际尝试

来源候选经 `sources-input.json` → `sources.json` 标准化；所有来源均为本轮浏览器中重新发现的公开页面。

1. UI Notes 通用“个人主页”App 搜索未给出可用结果，未把搜索页当成素材。
2. UI Notes 小红书 App 截图库：`https://uinotes.com/app/748340650660839052`。在公开预览中逐张检查了首批 60 张 Screen；`https://uinotes.com/pin/281912682124983449`（Screen 043）为完整个人主页并进入采集；`https://uinotes.com/pin/445462243238162902`（Screen 001）为信息流/内容详情，保留为语义拒绝候选。
3. UI Notes 知乎 App 截图库：`https://uinotes.com/app/269449960604370329`。公开首批 60 张主要为信息流、回答/文章、评论和设置，没有能够确认的个人主页；没有用错误页面凑数，保留为 open fallback。
4. Refero Instagram profile 搜索得到并打开：`https://refero.design/screens/36a881f9-b456-47f9-b03c-f65bcde89c2a?query=Instagram%20profile&source=search`，其公开原始 Screen 资产进入采集。
5. Refero Medium profile 搜索得到并打开：`https://refero.design/screens/5b472505-d300-4558-b9ce-8706d1220181?query=Medium%20profile&source=search`，其公开原始 Screen 资产进入采集。
6. 探索性检查了 Refero Pinterest 候选（`https://refero.design/screens/d155eff1-16a0-4475-b506-887df32dbc76?query=Pinterest&source=search`），画面是带地址栏的 Mobile Web/Business 页面，不符合默认 App Surface，未纳入任务竞品或素材；Reddit profile 搜索结果未能确认产品身份，也未纳入。

## 页面采集与审核结果

`captures.json` 中共有 4 条真实公开原始 Screen 记录，原图只做文件复制，没有裁切、重采样或重新生成。

### Accepted（3）

- 小红书：`cap-ui-notes-xhs-profile`，480×1039 WEBP；头像、昵称/ID/IP、简介、关注/粉丝/获赞收藏统计、关注/私信动作和笔记/收藏网格完整。
- Instagram：`cap-refero-instagram-profile`，1125×2436 JPEG；Sony 验证身份、帖子/粉丝/关注统计、Follow/Message、资料标签和内容网格完整。
- Medium：`cap-refero-medium-profile`，1125×2436 JPEG；Followers/Following、View stats、Edit your profile、Stories/Lists/About 和创作内容入口完整。

### Rejected（1）

- 小红书：`cap-ui-notes-xhs-feed`，机械质量通过但语义拒绝；它是信息流/内容详情，不是用户个人主页，因此 `collection_status=rejected`，没有进入图墙或分类。

4 条记录的机械解码、格式、尺寸校验均通过；只有同时满足语义与机械条件的 3 条进入 `collected`。

### Fallback

`fallback_requests.json` 共 4 项：小红书、Instagram、Medium 为 `resolved`；知乎为 `open`，原因是公开预览未找到可确认目标页，允许后续 `user_upload` / `device_capture`。没有把失败页面标成 collected。

## 动态分类

Agent 在审核完 3 条 collected 素材后才生成 `classification-plan.json`，维度为：

> 个人主页中身份、关系与内容资产的编排方式

分类结果是“关系数据与内容网格并列的公开主页”（小红书、Instagram）和“账户导航与创作资产并置的个人页”（Medium）。标签来自逐张观察到的身份区、关系信息、内容资产和主要动作；Python 只校验计划并稳定生成分组，没有按 `product_type`、`notes`、URL 或关键词推断页面结构。

## 报告与真实浏览器验证

- `report.html`、`report_data.json` 和 `classification.json` 已生成；报告图墙只引用 `assets/c2855ae3cf18c532.webp`、`assets/a28df5710481a9ea.jpg`、`assets/da76933b229554be.jpg` 三个报告目录内的相对路径。知乎只显示 open fallback。
- 使用临时本地 HTTP Server 从本目录提供报告：`127.0.0.1:8790`。真实 Chromium 打开 `http://127.0.0.1:8790/report.html`，HTTP 日志确认报告请求 200，三张资产请求 200/304。
- Chromium 检查到 3 个 `.asset-image` 均 `complete=true` 且 `naturalWidth/naturalHeight` 分别为 `480×1039`、`1125×2436`、`1125×2436`。
- 通过真实页面定位器点击第一张截图后，`dialog#viewer.open=true`，放大图 `naturalWidth=480`、`naturalHeight=1039`。
- 浏览器证据保存为 `evidence/report-page.png` 与 `evidence/report-dialog-open.png`。

## Gap、阻塞与自验收结论

- Skill specification gap：未发现。当前 SKILL.md 足以指导目标理解、默认 Mobile App Surface、Agent 规划、公开来源优先级、语义/机械分工、fallback、动态分类和报告交互。
- MVP cold-start blocker：未发现。知乎缺失是公开素材的真实 fallback，不是流程阻塞；其余流程完成。
- 当前结论：**Cold-start 自验收通过，等待 GPT 最终独立复验。**
- 本记录不改变 `STATUS.md` 或 `docs/acceptance/V0.1_MVP_ACCEPTANCE_REPORT.md`；V0.1 MVP 不在本轮宣布通过。
