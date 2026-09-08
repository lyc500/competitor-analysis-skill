# Stage 5B-R1 Task A 来源尝试

## 执行顺序

本轮对 Task 中每个竞品先使用专业 UI / 设计参考数据库。三个竞品都在 Priority 1 得到可核验的完整 App Screen，因此没有进入 Priority 2 public Web、Priority 3 user upload 或 Priority 4 device capture。来源网站与目标 UI 分开记录；参考网站页面截图只作为来源访问证据，不进入 Material。

| 产品 | 目标平台 | 首选 UI 数据库 | 搜索 / 页面 URL | 目标 App UI | 图片来源 | public Web fallback | 最终状态 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 起点读书 | iOS App | UI Notes | `https://uinotes.com/pin?functions=66`；最终 Pin `566060765477449935`、`886504874566301516` | 找到作品与漫画两个完整搜索结果 Screen | UI Notes 公开单图 asset URL | 否；Priority 1 已满足 | 2 个 collected |
| LinkedIn | iOS App | Refero | `https://refero.design/apps/search?query=product%20search`；最终 Screen `cc88bfb1-4f91-45a7-8b8f-c50eeafdf60d` | 找到含查询、地区、筛选、结果总数与职位列表的完整 Screen | Refero 公开单图 asset URL | 否；Priority 1 已满足 | 1 个 collected |
| WhatsApp | iOS App | Refero | `https://refero.design/apps/search?query=video%20search`；最终 Screen `5239ecce-ed0c-47f5-ac6c-8abc007bc590` | 找到联系人和通话分区的完整搜索结果 Screen | Refero 公开单图 asset URL | 否；Priority 1 已满足 | 1 个 collected |

## 限制与拒绝记录

- UI Notes 的小红书、淘宝和哔哩哔哩 App 专属 `functions=66` 筛选会跳转登录页；未登录、未绕过限制，也未把登录页计为素材。
- UI Notes 小红书 App 公开首批预览包含带设备外框和宣传标题的展示图，按 Mockup / 营销素材规则排除。
- UI Notes 公开“搜索结果”截图库可浏览的前十张单图中，选择起点读书的两个完整结果状态；单图顶端的 UI Notes 来源水印予以保留，不裁切、不伪造。
- Refero 广义查询返回的多张候选与目标页不一致，包括设置页、语音输入过程、App 内 Mobile Web 以及其他非结果状态，均未进入 Review 或 Material。
- 未使用固定产品到 URL 映射；上述清单只属于本次 Agent 生成的验收 Task 与来源记录。

真实来源访问证据位于 `evidence/source-*.png`，最终 Material 只使用 `captures/` 中的四张单屏 App UI。
