# Stage 5C Task B 来源尝试

## 执行顺序

本轮按每个竞品先专业 UI / 设计参考数据库、再公开 Web / 官方页面的顺序执行。数据库页面和搜索结果只作为来源证据；最终 Material 必须是来源页面公开的、可确认属于目标产品的真实移动端 App Screen。没有绕过登录、订阅、验证码或 IP 风控，也没有使用 fixture、内置候选、设备 Mockup 或假截图。

## 用户指定竞品

| 产品 | 首选数据库尝试 | 公开 Web / 官方尝试 | 最终结果 |
| --- | --- | --- | --- |
| 虎牙 | [UI Notes 虎牙 App 搜索](https://uinotes.com/search?wd=%E8%99%8E%E7%89%99&type=app)：App 0；[虎牙直播搜索](https://uinotes.com/search?wd=%E8%99%8E%E7%89%99%E7%9B%B4%E6%92%AD&type=app)：App 0 | [百度经验步骤页](https://jingyan.baidu.com/article/6dad5075d23345e023e36e8f.html) 的礼物图有红框、像素化和水印；[天极图库](https://mydown.yesky.com/sjsoft/725757111_image.html) 逐图为宣传/营销图；另检查 [虎牙官方产品页](https://blog.huya.com/product/145)，为投票活动而非普通礼物选择面板 | `open`；无可靠未编辑单屏 |
| 斗鱼 | [UI Notes 斗鱼 App](https://uinotes.com/app/499685334452857431)：公开前 60 张预览逐图检查，未见目标礼物面板，继续内容要求登录 | [斗鱼鱼吧公开图](https://yubam.douyu.com/post/436337061586960247) 含直播和礼物区域，但有红色箭头/圆圈标注 | `open`；无可靠未编辑单屏 |
| 抖音直播 | [UI Notes 抖音 App](https://uinotes.com/app/761924085433031155)：公开前 40 张预览逐图检查，未见目标礼物面板；OCR 礼物筛选要求登录 | [创业邦公开文章](https://m.cyzone.cn/article/649976) 得到完整单屏；另检查三公子、脚本之家、零壹电商和百度经验的标注/裁切候选 | `resolved`；1 张 accepted |
| Twitch | [Refero Twitch App 搜索](https://refero.design/apps/search?query=Twitch)：公开结果未返回 Twitch 目标 Screen，完整结果要求登录/订阅 | [Twitch 官方 Android 帮助页](https://help.twitch.tv/s/article/watching-twitch-on-android-devices?language=en_US) 的 `725577-11u.png` 为完整 Cheermote 面板；官方 09u 为拼图、10u 为直播页、12u 为充值页；[Android Authority](https://www.androidauthority.com/twitch-donations-explained-3172301/) 为带标注拼图 | `resolved`；1 张 accepted |

## Agent 补充竞品

| 产品 | 来源尝试 | 最终结果 |
| --- | --- | --- |
| 快手直播 | 公开图片检索“快手直播 礼物面板 手机 App 截图 送礼”未取得可核验单屏；未下载或伪造候选 | `open`，仅保留 fallback |
| BIGO LIVE | [Refero BIGO LIVE 搜索](https://refero.design/apps/search?query=BIGO%20LIVE) 未返回目标 Screen；[Tech in Asia](https://www.techinasia.com/bigo-live-streaming-app) 得到 Android 单屏；[BIGO 官方礼物教程](https://www.bigo.tv/blog/bigo-live-virtual-gifts) 为三屏拼图；[caicalinks 教程](https://caicalinks.com/blog/great-bigo-instructions/) 为无直播上下文的局部面板 | `resolved`；Tech in Asia 单屏 accepted |

## accepted 素材

| Capture | 来源 | App Screen 事实 | 采集结果 |
| --- | --- | --- | --- |
| `cap-public-douyin-cyzone` | [创业邦](https://m.cyzone.cn/article/649976)；公开 asset URL 保存在 `captures.json` | 抖音直播画面下方礼物抽屉，礼物网格、抖币价格、多标签和赠送入口完整 | `semantic_status=accepted`、`quality_status=accepted`、`collection_status=collected` |
| `cap-public-twitch-official-cheer` | [Twitch Help](https://help.twitch.tv/s/article/watching-twitch-on-android-devices?language=en_US)，官方 `725577-11u.png` | Android App 聊天/直播上下文中的 Cheermote 网格、Bits 余额和 Get Bits | `semantic_status=accepted`、`quality_status=accepted`、`collection_status=collected` |
| `cap-public-bigo-techinasia` | [Tech in Asia](https://www.techinasia.com/bigo-live-streaming-app)；公开 asset URL 保存在 `captures.json` | Android App 直播背景、钻石余额、礼物网格、价格和 Send 控件完整 | `semantic_status=accepted`、`quality_status=accepted`、`collection_status=collected` |

## 拒绝规则与实际候选

以下候选全部保留在 `captures/`、`captures.json` 和 `semantic-reviews.json` 中作为可追溯尝试，但没有进入 `reviewed_materials.json` 的 collected 或最终报告：

- 虎牙百度经验：礼物网格虽可见，但红框、像素化和水印处理了核心 UI。
- 虎牙天极图库：宣传/营销图，无目标礼物面板。
- 斗鱼鱼吧：直播和礼物区域被红色箭头/圆圈标注。
- 抖音三公子：红色箭头/标注；脚本之家：礼物区域裁切、缺少直播上下文；零壹电商：红圈且为局部图；百度经验：红框/箭头。
- Twitch 官方 09u：多状态拼图；10u：无 Cheermote/礼物面板；12u：Get Bits 充值页；Android Authority：多画面并带标注。
- BIGO 官方教程：横向三屏拼图；caicalinks：只有面板局部、无直播上下文。

“直播页面但没有打开礼物面板”“充值/钱包/订阅页”“主播资料或排行榜”“营销图/Mockup”“数据库来源页本身”“gift animation only”“Desktop Web / Mobile Web”均不计入有效素材。拒绝候选不会被报告图墙或 Classification Plan 引用。

## 证据文件

- 数据库与来源访问证据：`evidence/source-uinotes-huya-search.png`、`source-uinotes-douyu-search.png`、`source-uinotes-douyu-app.png`、`source-refero-twitch-search.png`、`source-twitch-help.png`、`source-cyzone-douyin.png`。
- 最终报告真实 Chromium 证据：`evidence/report-page.png`、`evidence/report-dialog-open.png`。
- 原始候选与全部语义结果：`captures/`、`captures.json`、`semantic-reviews.json`。
