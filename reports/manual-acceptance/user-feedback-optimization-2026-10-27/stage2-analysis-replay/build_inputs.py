"""Build Stage 2 historical-replay inputs from reviewed Stage 1 snapshots.

This script is acceptance evidence, not a production classifier. Every grouping,
observation and judgment below was authored after visual review of the archived
screenshots. The formal CLI consumes only the generated JSON files.
"""
from __future__ import annotations

import json
from pathlib import Path
import shutil


HERE = Path(__file__).resolve().parent
STAGE1 = HERE.parent / "stage1-replay"


def dump(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def inference(cid, statement, evidence, analysis_refs, recommendation, applicability, limitations):
    return {
        "id": cid,
        "kind": "inference",
        "statement": statement,
        "evidence_refs": evidence,
        "analysis_refs": analysis_refs,
        "recommendation": recommendation,
        "applicability": applicability,
        "limitations": limitations,
    }


def observation(cid, statement, evidence, analysis_refs):
    return {
        "id": cid,
        "kind": "observation",
        "statement": statement,
        "evidence_refs": evidence,
        "analysis_refs": analysis_refs,
    }


def question(cid, statement, evidence, analysis_refs):
    return {
        "id": cid,
        "kind": "question",
        "statement": statement,
        "evidence_refs": evidence,
        "analysis_refs": analysis_refs,
    }


def refs(kind, *ids):
    return [{"kind": kind, "id": item} for item in ids]


def collect_claim_ids(analysis):
    claims = [analysis["overall"], *analysis.get("key_findings", [])]
    claims += [item["takeaway"] for item in analysis["groups"]]
    claims += [item["insight"] for item in analysis["materials"]]
    claims += analysis["synthesis"]["findings"]
    claims += analysis["synthesis"]["validation_questions"]
    claims += analysis.get("current_state", {}).get("findings", [])
    return [item["id"] for item in claims]


def review(analysis, edits):
    return {
        "review_type": "agent_self_review",
        "independent": False,
        "reviewed_claim_ids": collect_claim_ids(analysis),
        "checks": {
            "evidence_supported": True,
            "reference_value_clear": True,
            "research_relevant": True,
            "exceptions_considered": True,
            "duplicates_resolved": True,
            "generic_claims_removed": True,
        },
        "edits": edits,
        "notes": [
            "逐图检查可见事实后再写比较、判断与建议；删除了仅复述控件或执行流程的候选结论。",
            "这是同一 Agent 的交付前人工自查，只辅助暴露遗漏与过度推断，不是独立质量验证。",
        ],
    }


def member(mid, product, group, fact, boundary, insight, recommendation, applicability, limitation,
           login="logged_in", path="personal_center_root_first_view",
           interaction="browse_before_action", role="personal_center"):
    return {
        "id": mid,
        "product": product,
        "group": group,
        "fact": fact,
        "boundary": boundary,
        "insight": insight,
        "recommendation": recommendation,
        "applicability": applicability,
        "limitation": limitation,
        "labels": {
            "page_role": role,
            "path_stage": path,
            "interaction_stage": interaction,
            "render_state": "loaded_complete",
            "login_state": login,
        },
    }


def build_one_sentence():
    items = [
        member("mat-096876602836684120", "豆包爱学", "learning",
               "头像下方并排放置金币商城与任务中心，学习记录位于其后。",
               "截图只能证明首屏层级，不能证明两个入口的访问频率。",
               "用成对卡片把可行动的任务与资产放在身份区之后，可让学习目标直接进入下一步。",
               "只有当任务与金币共同服务学习闭环时再并排；否则应拆开表达。",
               "有明确每日任务或学习激励的产品。",
               "当前画面没有任务进度，不能据此判断任务卡是否足够。"),
        member("mat-133323406851668822", "豆包爱学", "learning",
               "未登录时仍展示金币商城、任务中心、学习记录和设置，顶部提供登录入口。",
               "未登录画面不提供登录后的真实资产与个性化内容。",
               "未登录页保留功能骨架，可用于预告登录后能做什么，而不必把全部页面替换成登录拦截。",
               "只展示可理解且登录后确实可用的入口，并清楚处理需要登录的动作。",
               "希望在登录前解释产品价值的个人中心。",
               "不能用这张图判断登录后资产的视觉权重。", login="logged_out"),
        member("mat-004403109497668392", "多邻国", "learning",
               "自己的头像、账号 ID、加入年份、课程、关注关系、添加好友和学习概览出现在同一页面。",
               "这是自己的个人页，不能当作浏览他人公开主页的证据。",
               "把学习概览与社交身份放在同一页，适合让成长记录同时承担自我回顾和关系建立。",
               "先确认产品是否真的需要可见的学习身份与好友关系。",
               "学习行为具有社交或展示价值的产品。",
               "截图不能说明用户是否常用添加好友或装扮入口。", role="own_profile"),
        member("mat-168392972276229080", "不背单词", "learning-settings",
               "昵称、会员标识、酷币与装备后接外观、沉浸场景和学习设置，画面为浅色主题。",
               "酷币和装备是产品特有资产，不能直接迁移到其他业务。",
               "把学习资产与个性化设置相邻，可让用户从成果状态进入学习环境调整。",
               "资产必须能解释后续设置或学习行为，否则会增加首屏噪音。",
               "有学习资产和个性化环境的产品。",
               "主题和资产并列不证明它们具有相同优先级。"),
        member("mat-248305763204570159", "不背单词", "learning-settings",
               "与浅色样本保持同一信息结构，仅切换为深色主题。",
               "它是视觉主题变体，不是新的信息架构样本。",
               "同构的深浅主题适合检查卡片层级与状态色在不同背景下是否仍可辨认。",
               "只把它用于主题可读性对照，不重复计算结构模式。",
               "需要同时支持深浅主题的既有个人中心。",
               "不能据此增加某种布局的样本权重。"),
        member("mat-227130207557343885", "微信读书", "learning",
               "游客身份下仍显示会员、充值币、读书排行、阅读时长、在读、读完、笔记与书单入口。",
               "部分数值可能是游客占位，不能视为真实个人记录。",
               "游客页保留完整内容管理框架，可用于解释登录后会沉淀哪些阅读记录。",
               "占位状态要与真实记录区分，并给出清楚的登录价值。",
               "内容记录是登录主要收益的产品。",
               "不能用零值或空值判断功能是否被使用。", login="guest"),
        member("mat-406465221275907801", "微信读书", "learning",
               "身份区后集中显示会员、排行、82 小时 23 分钟阅读时长、在读、读完、笔记、订阅与书单。",
               "静态累计值不能说明近期活跃或入口使用频率。",
               "把累计进度与内容集合并列，可让个人中心同时回答读了多少和接下来读什么。",
               "优先选择能支持回顾或继续阅读的指标，避免堆放与行动无关的数字。",
               "有长期内容记录与继续消费任务的产品。",
               "无法从截图判断这些指标是否提升阅读留存。"),
        member("mat-8b8ed53b-f284-46c6-97c8-45aeeed50a00", "The New York Times", "learning",
               "You 页显示订阅身份，并用 Your interests、History、Saved 分段；当前选中 Saved 并展示文章列表。",
               "这是 Saved 子页的已加载状态，不代表账户根页默认内容。",
               "当个人内容足够多时，用子导航分开兴趣、历史和收藏，比把三类列表连续堆在首屏更易定位。",
               "子导航只有在每类内容都值得独立浏览时才成立。",
               "收藏和历史构成主要回访任务的内容产品。",
               "单张已选中子页不能说明三个分段的使用优先级。",
               path="personal_center_saved_tab", interaction="subtab_selected", role="content_library"),
        member("mat-176567570728999594", "百度翻译", "learning",
               "未登录身份区之后先展示超级 VIP，再展示订单、课程、生词、配音及更多服务。",
               "未登录状态不能说明用户自己的学习记录和订单如何呈现。",
               "登录前展示课程、生词等能力入口，可让用户预览个人中心覆盖的学习任务。",
               "必须区分可直接使用、需要登录和仅作权益说明的入口。",
               "工具产品希望在账户页承接学习服务时。",
               "会员卡在前不等于会员是用户进入页面的高频目的。", login="logged_out"),
        member("mat-261238806478543829", "百度翻译", "learning",
               "登录身份与关注、收藏、评论、笔记在上方，VIP 与订单、课程、生词、配音及更多服务在下方。",
               "页面同时容纳内容关系、学习与交易入口，截图不能给出它们的真实优先级。",
               "先聚合个人内容关系，再承接学习与交易服务，可避免把所有入口混成一个宫格。",
               "需要先确定内容关系是否比订单和会员更接近页面主任务。",
               "同时沉淀内容互动与学习资料的工具产品。",
               "仍需访问数据决定哪些入口应留在首屏。"),
        member("mat-025429166561164948", "智谱清言", "creator",
               "头像与编辑资料后依次出现我的作品、智能体中心、消息、会员积分、订单和任务中心。",
               "截图不能说明作品与智能体入口的实际使用频率。",
               "把作品和创作工具放在身份区之后，可让个人中心承担创作管理，而不是只做账户设置。",
               "创作资产必须是用户回访个人中心的真实任务。",
               "用户会持续创建、发布或管理作品的产品。",
               "会员、订单和任务仍需与创作入口区分层级。", role="creator_center"),
        member("mat-612887545133740724", "懂车帝", "creator",
               "登录入口下展示动态、关注、粉丝与创作中心，其后才是订阅收藏、订单和车主服务。",
               "这是自己的账户入口，不是他人的公开主页；未登录数值不代表真实资产。",
               "先呈现关系与创作身份，再放交易和车主服务，适合用身份主线约束多业务入口。",
               "只有当创作与关系是账户核心任务时才采用这一顺序。",
               "内容社区叠加交易或服务业务的产品。",
               "登录状态下的真实内容密度仍需复核。", login="logged_out", role="creator_center"),
        member("mat-438158835260733576", "酷狗畅听版", "library",
               "未登录入口下仍显示我喜欢、已下载、最近播放列表，并保留底部播放器。",
               "未登录列表可能来自本地记录，不能等同于云端个人资产。",
               "把收藏、下载和最近播放放在同一区域，可直接支持继续听与离线管理。",
               "需要区分本地记录与登录后同步内容。",
               "个人中心的主任务是返回媒体内容的产品。",
               "不能用登录前可见性推断跨设备同步能力。", login="logged_out", role="media_library"),
        member("mat-392538942926681954", "迅雷", "library",
               "身份区后展示收藏历史、下载文件、云盘文件等统计，随后是云盘空间、文件工具与推荐服务。",
               "游戏中心和推荐服务存在，但不改变文件管理是画面主要信息。",
               "用文件数量与容量状态连接下载、云盘和工具入口，适合支持继续处理文件。",
               "把文件状态作为核心时，应把推荐服务降到其后，避免与文件任务同权。",
               "下载或云盘管理是个人中心主要任务的产品。",
               "会员身份不能成为把它归入订单或电商页面的依据。", role="file_library"),
        member("mat-667567417512043064", "喜茶GO", "commerce",
               "登录入口与余额占位后，依次提供订单、客服、团餐预定、兑换中心、发票与评价。",
               "未登录余额占位不能代表真实账户资产。",
               "即使未登录也保留完整交易服务目录，可让用户先找到订单、客服或发票再触发登录。",
               "登录拦截应发生在需要身份的动作上，而不是遮住整个服务结构。",
               "用户可能带着明确售后或交易任务进入个人中心。",
               "无法从截图判断哪些服务最常用。", login="logged_out", role="order_service_center"),
        member("mat-792439682643464941", "喜茶GO", "commerce",
               "登录身份下先显示喜茶券、喜卡与喜钱包，再提供订单、客服、兑换和积分商城。",
               "截图不能说明券、卡、钱包的使用频率或价值高低。",
               "把可消费资产放在订单服务之前，适合让用户先确认权益余额再进入交易处理。",
               "资产必须能直接用于本产品消费，否则不应占据首屏。",
               "券卡余额与点单形成闭环的消费产品。",
               "三类资产并列会增加认知成本，仍需按业务定义取舍。", role="order_service_center"),
        member("mat-658360019995979356", "拼多多", "commerce",
               "微信登录入口下显示订单状态、钱包、优惠券、收藏、店铺关注、历史浏览与商品推荐。",
               "未登录页只证明服务骨架可见，不能证明真实资产层级。",
               "按订单阶段提供直接入口，并把收藏和浏览记录接到推荐内容，可支持交易前后两类回访。",
               "需要明确订单处理和继续购物哪一个是当前页面的主任务。",
               "个人中心同时承担订单处理与再次购买的电商。",
               "商品推荐占比大不等于更有效。", login="logged_out", role="order_service_center"),
        member("mat-551540436152132377", "拼多多", "commerce",
               "昵称与收货地址后展示订单状态、钱包、收藏、优惠券和购物推荐。",
               "头像提示不遮挡主体，但截图不能说明提示是否影响操作。",
               "把地址与订单状态放在身份区附近，可让用户快速确认交易身份和履约进度。",
               "只有地址会频繁影响交易任务时才应靠前。",
               "履约状态与收货信息紧密相关的电商。",
               "推荐内容的面积不能作为转化效果证据。", role="order_service_center"),
        member("mat-018621050003319015", "阿里巴巴", "commerce",
               "支付宝快捷登录之后是订单状态、优惠权益及推荐、上新、收藏和足迹商品。",
               "未登录页面不能展示真实采购账户和订单资产。",
               "快捷登录后直接预览订单与采购发现入口，适合降低企业采购用户寻找交易状态的路径。",
               "采购身份和个人消费身份不同，入口文案需匹配实际账户关系。",
               "采购交易是个人中心主任务的 B2B 平台。",
               "不能把推荐商品出现理解为账户页的唯一重点。", login="logged_out", role="order_service_center"),
        member("mat-327553016242661235", "盒马", "commerce",
               "会员身份与权益卡片后展示红包、余额、省钱额，再接订单状态和服务宫格。",
               "省钱额是展示值，不能证明权益对消费决策的影响。",
               "把可用权益与订单状态分成相邻层，可同时支持下单前确认资产和下单后处理履约。",
               "需要限制权益指标数量，并保证每项都能进入明确动作。",
               "会员权益与即时零售交易紧密相连的产品。",
               "会员卡更大不等于对用户更有效。", role="order_service_center"),
        member("mat-176174415809164424", "小象超市", "commerce",
               "登录入口后提供券卡、订单状态、售后、客服、企业采购、扫码与地址。",
               "未登录状态不能说明真实订单和资产如何呈现。",
               "把售后、客服和地址与订单阶段放在同一服务区，可覆盖即时零售的交易后任务。",
               "辅助入口应围绕真实交易路径分组，避免仅按图标数量排布。",
               "配送、售后和地址都是订单链路组成部分的零售产品。",
               "不能由画面位置推断企业采购属于高频。", login="logged_out", role="order_service_center"),
        member("mat-026234696324700781", "转转", "commerce",
               "登录入口下先放收藏与足迹，再分购买订单、出售订单、资产估价与交易工具。",
               "未登录画面不含真实买卖记录。",
               "按买入和卖出两条角色路径拆分订单，可减少双边交易用户在同一列表中辨认任务的成本。",
               "只有用户确实会在两种交易角色间切换时才值得双路径。",
               "同时支持买卖双方任务的交易平台。",
               "无法从截图判断两条路径的使用比例。", login="logged_out", role="order_service_center"),
        member("mat-508614918845893842", "得物", "commerce",
               "未登录入口下同时提供创作中心、收藏、想要、足迹、关注、我有、订单、钱包和商家入驻。",
               "页面横跨内容关系、交易和商家角色，截图不能给出各角色的真实权重。",
               "将想要、我有与订单相邻，可围绕商品关系连接交易前收藏和交易后资产。",
               "需要明确普通买家与商家入口是否应共享同一首屏。",
               "商品社区与交易关系同时存在的平台。",
               "入口齐全不等于层级合理；仍需按目标角色删减。", login="logged_out", role="order_service_center"),
        member("mat-08723dab-7694-4c3b-a061-6dd9393de0db", "Target", "commerce",
               "My Target 首屏依次显示购买历史、年度节省、Circle 奖励余额和社区支持票数。",
               "奖励余额和节省额是结果状态，不是任务列表或任务进度。",
               "把购买记录与已获权益放在同一账户首屏，可解释会员关系带来的可见价值。",
               "只有收益口径清楚且可核对时才展示累计价值。",
               "零售账户需要同时承接购买记录与会员权益时。",
               "0 金额不能说明页面未加载，也不能证明权益展示提升转化。", role="order_service_center"),
        member("mat-fac3a0c7-d886-41dd-b9d5-12b86df97f1b", "Wise", "settings",
               "Your account 页面列出商业账户、设置、帮助、隐私安全、退出和会员编号。",
               "截图是账户服务根页，没有交易流水或资产概览。",
               "将安全、帮助和账户切换集中成稳定列表，适合承担账户治理而非内容或交易概览。",
               "需要把高风险账户动作与普通帮助入口保持清楚分区。",
               "用户进入页面主要是维护身份、安全和账户类型时。",
               "不能因产品是金融服务就假定该页承担资产管理。", role="account_settings_root"),
        member("mat-533a310b-0a57-4b92-9f6f-205fb07cadf2", "ASOS", "settings-lower",
               "MY ACCOUNT 下段可见地址、支付方式、通知、联系偏好、社交账户、礼卡、帮助和反馈，并有滚动条。",
               "这是滚动后的下段视口，不能代表首屏内容与优先级。",
               "把地址、支付、通知和帮助按账户维护主题连续收纳，可作为二级管理区的组织参考。",
               "应在首屏已有核心任务入口的前提下，把这些管理项放入下段或二级页。",
               "账户维护项较多且不需要同时曝光的产品。",
               "不能用下段位置推断这些功能低频。",
               path="account_root_scrolled_lower", interaction="browse_after_scroll", role="account_management_lower"),
    ]

    group_specs = [
        ("learning", "group-learning-progress", "学习与内容进度",
         "持续内容行为与进度管理",
         "页面围绕学习进度、阅读记录、收藏或继续内容组织主要信息。",
         "通过记录、内容集合或进度状态帮助用户回顾并继续任务。",
         "与创作身份组相比，本组重点是自己的学习或内容消费记录；与媒体文件库相比，本组含进度、课程或内容关系。"),
        ("learning-settings", "group-learning-settings", "学习资产与个性化设置",
         "学习资产和环境配置",
         "页面主要呈现会员、虚拟资产、装备、外观、沉浸场景或学习设置，没有可见学习进度与内容记录。",
         "用学习资产连接个性化环境与设置，而不是承担继续内容或进度回顾。",
         "与学习进度组的差异是没有进度、记录、收藏或继续内容；不能只因同属教育产品合组。"),
        ("creator", "group-creator-identity", "创作身份与关系资产",
         "创作身份、作品和关系管理",
         "页面把作品、创作入口、动态或关注关系放在身份区附近。",
         "以身份与关系为主线承接创作管理，再放订单或其他服务。",
         "不把只有账户头像的页面纳入；自己的创作中心也不等同于浏览他人的公开主页。"),
        ("library", "group-media-file-library", "媒体与文件库",
         "继续媒体或文件处理",
         "页面主要呈现收藏、最近、下载、文件、容量或继续播放入口。",
         "用库状态连接继续消费、下载和文件管理。",
         "与订单组的差异是主对象为媒体或文件；出现会员、游戏或推荐入口不改变这一主任务。"),
        ("commerce", "group-order-benefits", "订单生命周期与消费权益",
         "围绕交易前后组织订单、权益与服务",
         "页面至少以订单状态、购买记录、售后或可消费权益为主要区域。",
         "用订单阶段和可用权益连接再次购买、履约与售后。",
         "不包含文件管理或纯账户设置；Target 的奖励是消费权益结果，不作为任务中心证据。"),
        ("settings", "group-account-settings", "账户设置根页",
         "身份、安全和账户治理",
         "页面以设置、隐私、安全、帮助、账户切换或退出为主要内容。",
         "把账户治理动作放在稳定的根页列表中。",
         "与消费组的差异是没有订单或购物权益主线；与下段组的差异是当前视口属于根页服务区。"),
        ("settings-lower", "group-account-lower", "账户管理下段",
         "滚动下段的账户维护收纳",
         "截图明确为账户页下段，并集中地址、支付、通知或帮助等维护项。",
         "在首屏之后用分区列表收纳账户维护动作。",
         "不能与首屏样本直接比较优先级，也不把下段位置解释为低频。"),
    ]
    by_group = {key: [item for item in items if item["group"] == key] for key, *_ in group_specs}
    plan_groups = []
    for key, gid, name, reason, criteria, mechanism, difference in group_specs:
        members = by_group[key]
        plan_groups.append({
            "id": gid,
            "name": name,
            "reason": reason,
            "material_ids": [item["id"] for item in members],
            "audit": {
                "inclusion_criteria": criteria,
                "shared_mechanism": mechanism,
                "member_reasons": [{"material_id": item["id"], "reason": item["fact"]} for item in members],
                "adjacent_difference": difference,
            },
        })
    plan = {
        "schema_version": 2,
        "classification_dimension": "页面主任务与实际设计机制",
        "classification_reason": "一句话宽泛搜集先按用户进入个人中心后要继续处理的对象归组；登录态、主题与路径阶段保留为标签，不再充当业务兜底分类。",
        "comparison_basis": {
            "primary_dimension": "个人中心承担的首要用户任务及其信息组织机制",
            "rationale": "只有主任务和设计机制相近的样本才便于横向比较；行业可以不同，但共同机制必须可见。",
            "scope": "历史归档的 26 张已审核截图；区分登录态、自己的账户与公开主页、首屏与滚动下段，不视为当前最新版。",
        },
        "groups": plan_groups,
        "material_labels": [{"material_id": item["id"], "labels": item["labels"]} for item in items],
    }

    observations = [{
        "id": "obs-" + item["id"],
        "material_id": item["id"],
        "visible_facts": [item["fact"]],
        "evidence_boundaries": [item["boundary"]],
    } for item in items]
    comparisons = [
        {
            "id": "cmp-learning",
            "material_ids": [item["id"] for item in by_group["learning"]],
            "comparison_findings": ["样本都把学习、阅读或收藏记录放进个人中心，但有的强调下一步任务，有的强调累计记录或内容集合。", "游客或未登录页面仍可能展示结构，但真实个人资产只有登录样本可见。"],
            "design_judgment": "记录只有能帮助回顾或继续内容时才值得占据首屏，不能因为都是教育或内容产品就统一成同一种宫格。",
            "recommendation": "先确定用户回来要继续的对象，再从任务、进度或内容集合中选择主要表达。",
            "applicability": "个人中心承担持续学习、阅读或收藏管理。",
            "tradeoffs": ["累计指标便于回顾，但可能挤压下一步动作。", "子导航便于管理大量内容，但增加一次选择。"],
            "evidence_boundaries": ["静态截图不提供近期使用频率、留存或转化数据。"],
        },
        {
            "id": "cmp-learning-settings",
            "material_ids": [item["id"] for item in by_group["learning-settings"]],
            "comparison_findings": ["两张不背单词截图的信息结构相同，均围绕会员、酷币、装备、外观和学习设置，仅主题明暗不同。"],
            "design_judgment": "这组支持比较学习资产与个性化环境的组织，不支持进度、记录或继续学习模式。",
            "recommendation": "只在学习资产能解释环境或设置动作时保留该层，并把深浅主题视为视觉状态而非两种结构。",
            "applicability": "产品具有虚拟学习资产、装备或可配置学习环境。",
            "tradeoffs": ["资产和设置靠前会压缩学习进度或继续内容的空间。"],
            "evidence_boundaries": ["截图没有学习进度、记录、收藏或继续内容，不能把它们归入进度组。"],
        },
        {
            "id": "cmp-creator",
            "material_ids": [item["id"] for item in by_group["creator"]],
            "comparison_findings": ["两页都在身份区后安排作品、创作或关系入口，再承接订单等次要业务。"],
            "design_judgment": "身份主线能约束多业务入口，但自己的创作中心不能被误读为他人的公开主页。",
            "recommendation": "当创作与关系确实是回访任务时，把作品和创作入口放在身份信息之后。",
            "applicability": "内容社区或创作者工具。",
            "tradeoffs": ["强化创作会压缩交易与账户服务的首屏空间。"],
            "evidence_boundaries": ["未登录样本不能证明真实作品与关系资产的呈现密度。"],
        },
        {
            "id": "cmp-library",
            "material_ids": [item["id"] for item in by_group["library"]],
            "comparison_findings": ["酷狗围绕喜欢、下载和最近播放，迅雷围绕下载、云盘、文件统计与容量；共同对象是可继续处理的媒体或文件。"],
            "design_judgment": "出现会员、游戏或推荐服务不改变库管理主任务，分类应以主要对象而不是附带入口决定。",
            "recommendation": "用最近、下载、收藏或容量状态连接继续处理动作，并把推荐服务降到其后。",
            "applicability": "媒体播放、下载或云盘文件管理。",
            "tradeoffs": ["状态概览有助于定位内容，但过多统计会挤压直接操作。"],
            "evidence_boundaries": ["截图不能证明本地与云端内容是否同步，也不能说明工具使用频率。"],
        },
        {
            "id": "cmp-commerce",
            "material_ids": [item["id"] for item in by_group["commerce"]],
            "comparison_findings": ["样本普遍用订单阶段、购买记录或售后入口组织交易后任务，部分再加入券卡、钱包或累计收益。", "Target 只展示购买历史和权益结果，没有任务列表、目标或下一步动作。"],
            "design_judgment": "订单与权益可以相邻，但权益结果不能被当作任务中心；推荐商品面积也不能证明更高转化。",
            "recommendation": "先按订单生命周期安排处理入口，再决定哪些可消费权益能帮助下一次交易。",
            "applicability": "零售、交易或生活服务的个人中心。",
            "tradeoffs": ["权益前置便于确认余额，但会减少订单处理空间。", "推荐内容支持再次购买，但可能遮蔽售后任务。"],
            "evidence_boundaries": ["静态截图不提供转化、复购或功能使用数据。"],
        },
        {
            "id": "cmp-account-path",
            "material_ids": [item["id"] for key in ("settings", "settings-lower") for item in by_group[key]],
            "comparison_findings": ["Wise 是账户服务根页，ASOS 是带滚动条的账户页下段；两者都收纳维护动作，但不能直接比较首屏优先级。"],
            "design_judgment": "页面路径与视口阶段必须先对齐；下段适合说明分区方式，不代表功能天然低频。",
            "recommendation": "用根页承接身份、安全与账户切换，用下段或二级页收纳地址、支付、通知和帮助。",
            "applicability": "账户维护项多于首屏可容纳范围。",
            "tradeoffs": ["收纳减少首屏噪音，但会增加查找路径。"],
            "evidence_boundaries": ["ASOS 截图不包含首屏，无法判断首屏已有内容。"],
        },
    ]

    gids = {key: gid for key, gid, *_ in group_specs}
    group_text = {
        "learning": ("重点比较记录如何帮助用户回顾或继续内容；适合持续学习与阅读，前提是先明确回来要继续什么。", "按任务、进度或内容集合选择一种主表达。", "个人中心承担持续内容行为。", "截图不能证明哪个入口最高频。"),
        "learning-settings": ("重点比较会员、学习资产和个性化设置如何形成环境配置入口；不含进度或继续内容证据。", "只保留能连接到学习环境或设置动作的资产。", "产品具有可配置学习环境与虚拟资产。", "深浅主题是视觉状态，不增加结构样本权重。"),
        "creator": ("重点比较作品、关系与创作入口如何围绕身份聚合；适合创作者账户，不宜套到只管理订单的页面。", "把作品与创作工具紧跟身份区。", "创作是账户的主要回访任务。", "自己的创作中心不等于他人的公开主页。"),
        "library": ("重点比较最近、下载、收藏和容量如何支持继续处理内容；会员或推荐入口不能改变文件与媒体主任务。", "先呈现库状态和继续操作，再放推荐服务。", "媒体或文件是个人中心的主要对象。", "截图不能证明同步能力或工具频率。"),
        "commerce": ("重点比较订单阶段、权益与售后如何围绕交易链组织；奖励结果不能当作任务中心。", "先按交易阶段组织，再选择能支持下一次消费的权益。", "个人中心承接购买、履约或售后。", "不能从面积和位置推断转化效果。"),
        "settings": ("重点比较安全、隐私与账户切换如何形成治理根页；适合账户维护，不承担内容或交易概览。", "保持账户治理入口稳定分区。", "进入页面的主要目的为维护账户。", "金融产品身份不代表当前页面是资产页。"),
        "settings-lower": ("重点比较地址、支付、通知和帮助如何在下段收纳；可借鉴分区，不能据此判断首屏优先级。", "把维护项放入清楚的下段或二级分区。", "首屏已有更核心的账户任务。", "滚动位置不能代表功能低频。"),
    }
    analysis = {
        "schema_version": 2,
        "title": "国内外 App「我的」页：按主任务比较信息组织",
        "research": {
            "question": "不同 App 的‘我的’页分别围绕什么主任务组织，哪些结构可在相近任务中参考？",
            "scope": "历史归档的 20 个产品、26 张移动端截图；本轮只重做分析与分类，不执行新的来源搜集。",
            "goals": [],
            "constraints": ["没有用户产品现状或明确业务目标，只总结样本模式、差异和适用场景。", "历史截图不代表当前最新版。"],
        },
        "analysis_process": {"material_observations": observations, "comparisons": comparisons},
        "overall": inference(
            "overall-main-task",
            "‘我的’页应先按用户要继续管理的对象选择参照：内容记录、学习环境、创作身份、媒体文件、交易订单和账户治理需要不同的首屏结构。",
            refs("group", *[gids[key] for key in ("learning", "learning-settings", "creator", "library", "commerce", "settings")]),
            ["cmp-learning", "cmp-learning-settings", "cmp-creator", "cmp-library", "cmp-commerce", "cmp-account-path"],
            "先写清目标页面的主任务，再从对应组比较入口层级；把登录态与路径阶段作为筛选标签。",
            "适用于尚未给出现状与改版目标的宽泛竞品搜集。",
            "这些样本只能支持可见结构判断，不能证明实际频率、转化或留存。"),
        "key_findings": [
            inference("finding-login-overlay", "登录态会改变可见资产，却不应把主任务不同的页面合成一个业务组。",
                      refs("material", "mat-133323406851668822", "mat-438158835260733576", "mat-018621050003319015"),
                      ["cmp-learning", "cmp-library", "cmp-commerce"],
                      "在分类内标注 logged_out 或 guest，并只比较登录前确实可见的结构。",
                      "同一业务任务需要比较登录前后的信息暴露。",
                      "未登录截图不能代表登录后的真实资产。"),
            inference("finding-xunlei-boundary", "迅雷的主要对象是下载、云盘和文件状态，与酷狗的媒体库更接近，不因会员和推荐服务进入订单组。",
                      refs("material", "mat-392538942926681954", "mat-438158835260733576"), ["cmp-library"],
                      "分类时以页面主要对象和连续任务为准，再记录附带业务。",
                      "比较媒体、下载或文件个人中心。",
                      "只基于当前可见页面，不能概括整个产品业务。"),
            inference("finding-target-boundary", "Target 的年度节省与奖励余额解释消费权益结果，没有目标、进度或下一步动作，不能作为任务中心样本。",
                      refs("material", "mat-08723dab-7694-4c3b-a061-6dd9393de0db"), ["cmp-commerce"],
                      "把它用于比较会员价值或消费权益表达，不用于推导任务卡。",
                      "研究零售账户的权益价值呈现。",
                      "余额为零不能说明功能无效，也不能推断转化。"),
            inference("finding-path-boundary", "账户根页、滚动下段和已选中子页只能比较各自阶段的组织方式，不能直接排名首屏优先级。",
                      refs("material", "mat-fac3a0c7-d886-41dd-b9d5-12b86df97f1b", "mat-533a310b-0a57-4b92-9f6f-205fb07cadf2", "mat-8b8ed53b-f284-46c6-97c8-45aeeed50a00"),
                      ["cmp-learning", "cmp-account-path"],
                      "比较前先对齐 path_stage 与 interaction_stage。",
                      "同一研究包含根页、子页或滚动状态。",
                      "单张静态截图不能还原完整路径。"),
        ],
        "groups": [],
        "materials": [],
        "synthesis": {"findings": [], "validation_questions": []},
        "information_gaps": [{"section": "current_state", "status": "not_provided", "reason": "用户没有提供产品现状或改版目标，本报告不生成针对某个产品的方案。"}],
        "methodology": [
            {"title": "历史素材分析重放", "text": "沿用既有证据与图片，仅重做逐图观察、分类和分析；没有执行新的来源搜集或登录检查，不视为当前版本验收。"},
            {"title": "分析边界", "text": "结论来自静态截图的可见结构；不把位置、面积或数值直接解释为高频、有效、转化或留存。"},
        ],
    }
    for key, gid, *_ in group_specs:
        statement, recommendation, applicability, limitation = group_text[key]
        analysis["groups"].append({"group_id": gid, "takeaway": inference(
            "group-takeaway-" + key, statement, refs("group", gid),
            ["cmp-account-path" if key in ("settings", "settings-lower") else "cmp-" + key],
            recommendation, applicability, limitation)})
    cmp_for_group = {"learning": "cmp-learning", "learning-settings": "cmp-learning-settings", "creator": "cmp-creator", "library": "cmp-library", "commerce": "cmp-commerce", "settings": "cmp-account-path", "settings-lower": "cmp-account-path"}
    for item in items:
        analysis["materials"].append({"material_id": item["id"], "insight": inference(
            "insight-" + item["id"], item["insight"], refs("material", item["id"]),
            ["obs-" + item["id"], cmp_for_group[item["group"]]], item["recommendation"], item["applicability"], item["limitation"])})
    analysis["synthesis"] = {
        "findings": [
            inference("summary-select-pattern", "先按继续内容、学习环境配置、创作管理、文件处理、交易服务或账户治理选择结构，再在同一主任务内比较入口层级。",
                      refs("group", *[gids[key] for key in ("learning", "learning-settings", "creator", "library", "commerce", "settings")]),
                      ["cmp-learning", "cmp-learning-settings", "cmp-creator", "cmp-library", "cmp-commerce", "cmp-account-path"],
                      "把页面主任务写成一个可完成的动作，并排除只有行业相同或都含会员的样本。",
                      "尚未确定具体改版目标的模式调研。",
                      "跨行业比较只能迁移共同机制，不能直接迁移业务模块。"),
            inference("summary-keep-state", "登录态、自己的账户、子页和滚动下段应作为比较条件持续保留，否则结构差异会被错误解释为设计优先级。",
                      refs("material", "mat-133323406851668822", "mat-004403109497668392", "mat-533a310b-0a57-4b92-9f6f-205fb07cadf2"),
                      ["cmp-learning", "cmp-creator", "cmp-account-path"],
                      "筛选样本时同时对齐主任务、页面角色和路径阶段。",
                      "需要跨状态或跨路径复用历史截图。",
                      "标签能避免误读，但不能替代完整交互路径验证。"),
        ],
        "validation_questions": [
            question("verify-primary-task", "目标产品的用户进入‘我的’页后最需要继续完成哪一件事？", refs("group", gids["learning"], gids["commerce"], gids["settings"]), ["cmp-learning", "cmp-commerce", "cmp-account-path"]),
            question("verify-login-visibility", "未登录时哪些功能只需预览，哪些动作必须在入口处触发登录？", refs("material", "mat-133323406851668822", "mat-667567417512043064"), ["cmp-learning", "cmp-commerce"]),
            question("verify-current-version", "进入设计决策前，哪些历史样本需要重新确认当前版本和完整路径？", refs("material", "mat-533a310b-0a57-4b92-9f6f-205fb07cadf2", "mat-8b8ed53b-f284-46c6-97c8-45aeeed50a00"), ["cmp-learning", "cmp-account-path"]),
        ],
    }
    analysis["quality_review"] = review(analysis, [
        {"candidate_id": "old-order-service-xunlei", "action": "rewritten", "before": "交易与文件类页面需先确认共同的入口组织机制。", "after": "迅雷按下载、云盘和文件管理归入媒体与文件库，不再与订单页合组。", "reason": "旧分类把不同主任务放进同一层级，宽泛提醒不能修复比较基础。"},
        {"candidate_id": "old-logged-out-catch-all", "action": "removed", "before": "国内｜未登录的完整个人中心。", "reason": "登录态只是证据条件，不能充当容纳内容、交易、文件和创作页面的业务分类。"},
    ])
    target = HERE / "one-sentence-my-pages"
    dump(target / "classification-plan.json", plan)
    dump(target / "analysis.json", analysis)


def build_detailed():
    items = [
        member("mat-cap-tencent", "腾讯视频", "membership", "身份区把视频 VIP、体育 VIP 和其他套餐并列，下一行是预约、下载、收藏与周边等操作。", "原图含教程红框；套餐关系与更新版本不能由截图确认。", "把会员身份与权益入口合在一区、常用操作独立成行，可避免会员与所有服务图标同权。", "先确认各会员是否共享身份、权益或续费动作，再决定是否聚合。", "会员确实是本次主任务且业务关系可解释。", "不能因为都叫会员就合并贵族、守护或平台会员。"),
        member("mat-cap-bilibili", "哔哩哔哩", "membership", "头像下方先出现大会员横条，随后是离线缓存、历史记录、我的收藏和稍后再看四个常用入口。", "这是历史版本；创作中心与观众常用入口属于不同任务。", "会员横条与四个内容操作形成两层，适合在有限高度内同时表达身份权益和继续观看。", "常用入口必须由本产品任务和访问数据确认。", "会员与内容消费都需要在个人中心首屏出现。", "下方仍有较多服务宫格，不宜整页照搬。"),
        member("mat-cap-kugou", "酷狗畅听版", "membership", "身份与会员条之后突出我喜欢、已下载和最近内容，播放器持续可见。", "画面没有独立任务进度，不能作为任务中心证据。", "让最近与收藏内容成为主角，可把个人中心从服务目录转成继续消费入口。", "仅保留 2—4 个能直接继续核心任务的入口。", "内容回访比账户管理更接近用户主任务。", "大面积内容列表会压缩会员与任务空间，仍需取舍。"),
        member("mat-cap-gooh", "Gooh旅记", "membership", "会员横条后是一排旅行宫盒、旅行足迹和收藏地点，再接加入行程、提醒等列表。", "列表化降低视觉密度，但不等于功能已经折叠。", "用会员横条、常用操作和服务列表形成三层，可在主页面保留核心动作并压低辅助服务。", "辅助列表仍需有全部服务或二级收纳策略。", "身份权益、常用动作和辅助服务可被清楚拆开。", "不能把列表位置解释为低频。"),
        member("mat-cap-caljimi", "CalJimi", "membership", "会员横幅和运营卡之后，把设备连接单列，并以实用功能分组展示便签、闹钟等入口。", "连续两条运营卡可能分散注意，截图不能证明分组更易用。", "按任务命名辅助功能组，比把所有图标铺成同权宫格更便于理解入口用途。", "减少运营卡数量，并保证分组名称对应用户任务。", "辅助功能较多且可以按用途稳定分组。", "不建议复制连续横幅或产品特有功能。"),
        member("mat-cap-doubao", "豆包爱学", "task", "身份区后把金币商城与任务中心并排成卡片，任务中心写有立即签到领金币。", "画面展示下一步动作，但没有任务完成进度。", "把任务从一行通知提升为可行动卡片，可让用户在首屏直接看到下一步和奖励。", "卡片只保留一个明确动作，并避免用奖励替代任务目标。", "任务有清楚的下一步和可解释奖励。", "并排资产与任务可能削弱主次，需根据本次目标调整。"),
        member("mat-cap-headway", "Headway", "task", "Profile 首屏用圆环展示每日 20 分钟目标、当前 0 分钟、连续天数和 Adjust goal。", "学习目标模型不能直接迁移到直播产品；大圆环占据较多空间。", "把目标、当前进度和调整动作放在同一任务卡，可让用户不进二级页就理解状态。", "把信息压缩为适合本产品的紧凑任务卡，并保留下一步动作。", "任务可以量化进度或连续完成状态。", "没有行为数据时不能决定卡片高度或每日目标形式。"),
        member("mat-cap-target", "Target", "reward", "账户首屏显示购买历史、年度节省、Circle 奖励余额和社区支持票数。", "这些是消费权益结果，没有任务目标、进度或下一步动作。", "用已获收益说明会员价值，可补充身份信息，但不应被当作任务中心结构。", "仅在收益口径清楚、与会员权益直接相关时展示。", "需要解释用户已获得的消费权益价值。", "0 金额不能说明未加载，也不能证明收益前置会提升付费转化。"),
        member("mat-cap-douyu-top", "斗鱼", "drawer", "个人页右侧抽屉打开后，上段以分组宫格承接贵族、浏览记录、任务中心、礼包等服务。", "这是已打开抽屉，不是个人中心首屏；部分本次目标模块也被收在抽屉里。", "抽屉能集中承接辅助服务，但本次要强化的会员与任务不应随其一起隐藏。", "主页面先保留会员、常用与任务，再把其余服务按任务分组收纳。", "辅助服务数量超过首屏可容纳范围。", "抽屉增加一次操作，分组过多仍会难找。", path="personal_center_drawer_top", interaction="drawer_open", role="services_drawer"),
        member("mat-cap-douyu-bottom", "斗鱼", "drawer", "同一抽屉滚动下段继续展示全部服务、账户维护项以及底部设置、反馈和装扮。", "这是抽屉滚动视口，不是与上图拼接的首页长图。", "抽屉下段把服务与设置分开，可用于收纳游戏绑定、礼包、免流和装扮等辅助入口。", "二级服务仍需分区，并给设置与帮助稳定位置。", "主页面已经明确保留核心任务。", "不能由下段位置判断功能低频。", path="personal_center_drawer_lower", interaction="drawer_open_scrolled", role="services_drawer"),
    ]
    group_specs = [
        ("membership", "group-membership-actions", "会员身份、权益与常用操作", "改版目标中的会员层级", "主页面同时展示会员身份或权益，以及一组可直接执行的常用操作。", "将会员状态、权益入口与常用动作分层，而不是简单放大会员卡。", "与任务组的差异是这里不要求目标、进度或下一步；与抽屉组的差异是样本都属于主页面。"),
        ("task", "group-task-progress", "任务动作与进度", "改版目标中的任务中心表达", "页面用卡片明确展示任务动作、目标或进度。", "让用户在首屏理解当前状态与下一步。", "不包含只展示奖励余额的 Target；奖励结果不能代替任务结构。"),
        ("reward", "group-reward-value", "会员收益与奖励结果", "区分会员价值和任务中心", "页面展示已节省、已获奖励或可用权益等结果状态，但没有任务目标或进度。", "用可核对的收益解释会员价值。", "与任务组的差异是没有待完成动作；与订单组的共同点是收益来自消费关系。"),
        ("drawer", "group-auxiliary-drawer", "辅助服务抽屉", "改版目标中的其他功能收纳", "截图是已打开的服务抽屉，并展示其上段或滚动下段。", "主页面保留核心模块，抽屉按任务分区承接辅助服务。", "不能把抽屉视口当作首屏，也不能因收纳位置推断功能低频。"),
    ]
    by_group = {key: [item for item in items if item["group"] == key] for key, *_ in group_specs}
    plan = {
        "schema_version": 2,
        "classification_dimension": "虎牙改版要解决的设计问题",
        "classification_reason": "围绕会员层级、任务表达、收益结果和辅助服务收纳分组；业务行业只作背景，不以出现会员、奖励或服务入口强行合组。",
        "comparison_basis": {
            "primary_dimension": "对本次改版问题可提供的共同设计机制",
            "rationale": "明确改版目标时，应按要解决的问题选参照，并保留页面角色和交互阶段差异。",
            "scope": "历史归档的 9 个竞品、10 张 App 截图；8 张个人中心主视口与 2 张已打开服务抽屉视口，现状图另计。",
        },
        "groups": [],
        "material_labels": [{"material_id": item["id"], "labels": item["labels"]} for item in items],
    }
    for key, gid, name, reason, criteria, mechanism, difference in group_specs:
        members = by_group[key]
        plan["groups"].append({"id": gid, "name": name, "reason": reason,
                               "material_ids": [item["id"] for item in members],
                               "audit": {"inclusion_criteria": criteria, "shared_mechanism": mechanism,
                                         "member_reasons": [{"material_id": item["id"], "reason": item["fact"]} for item in members],
                                         "adjacent_difference": difference}})

    observations = [{"id": "obs-" + item["id"], "material_id": item["id"],
                     "visible_facts": [item["fact"]], "evidence_boundaries": [item["boundary"]]} for item in items]
    comparisons = [
        {"id": "cmp-membership", "material_ids": [item["id"] for item in by_group["membership"]],
         "comparison_findings": ["样本都把会员或权益与常用操作分开，但腾讯与 B 站更强调身份和权益，酷狗强调继续内容，Gooh 与 CalJimi 再把辅助服务列表化。"],
         "design_judgment": "可借鉴的是身份权益、常用操作和辅助服务的分层关系，而不是把会员卡做得更大。",
         "recommendation": "先确认会员业务边界，再用紧凑身份权益区承接会员状态，并保留一排由数据确认的常用操作。",
         "applicability": "会员与常用操作都需要留在主页面。",
         "tradeoffs": ["会员区过大会挤压任务和内容。", "常用入口过多会重新退化成同权宫格。"],
         "evidence_boundaries": ["静态截图不能说明入口使用频率，历史版本不能视为当前实现。"]},
        {"id": "cmp-task", "material_ids": [item["id"] for item in by_group["task"]],
         "comparison_findings": ["豆包给出下一步签到与奖励，Headway 给出目标、当前进度和调整动作；两者分别补足动作与状态。"],
         "design_judgment": "有效任务卡需要回答现在是什么状态、下一步做什么；奖励只能辅助解释，不能替代任务。",
         "recommendation": "把虎牙的一行活动文案改成紧凑任务卡，优先显示一项进度或状态和一个下一步动作。",
         "applicability": "任务有明确目标、状态或可执行动作。",
         "tradeoffs": ["信息过全会占据首屏；只写奖励会弱化任务目标。"],
         "evidence_boundaries": ["两项能力来自不同样本，合并为一张卡是设计判断，需要原型验证。"]},
        {"id": "cmp-reward-boundary", "material_ids": ["mat-cap-target", "mat-cap-doubao", "mat-cap-tencent"],
         "comparison_findings": ["Target 展示消费收益结果，豆包展示待执行任务，腾讯展示会员身份和权益入口；三者解决的问题不同。"],
         "design_judgment": "已获收益可增强会员价值解释，但不构成任务中心；会员身份、收益和任务需要不同字段。",
         "recommendation": "如果虎牙能提供可核对的会员收益，可放在会员区；任务区仍保留独立状态和动作。",
         "applicability": "业务同时存在会员权益结果与任务中心。",
         "tradeoffs": ["收益口径复杂时会增加解释成本。"],
         "evidence_boundaries": ["截图不支持任何转化、付费或留存结论。"]},
        {"id": "cmp-drawer", "material_ids": [item["id"] for item in by_group["drawer"]],
         "comparison_findings": ["同一服务抽屉的上段展示服务宫格，下段继续展示更多服务与设置，说明收纳后仍需二级分区。"],
         "design_judgment": "抽屉适合承接辅助服务，但把会员和任务也藏入其中会违背本次强化目标。",
         "recommendation": "主页面保留会员、任务和经验证的常用操作，其余入口进入有分区的全部服务抽屉。",
         "applicability": "辅助入口较多，且用户可以接受一次额外打开操作。",
         "tradeoffs": ["收纳降低首屏密度，也增加发现和到达成本。"],
         "evidence_boundaries": ["当前只有打开和滚动后的静态视口，没有抽屉触发与返回路径证据。"]},
    ]
    gids = {key: gid for key, gid, *_ in group_specs}
    analysis = {
        "schema_version": 2,
        "title": "虎牙「我的」页：围绕会员、任务与辅助服务重建层级",
        "research": {
            "question": "怎样简化虎牙‘我的’页，同时让会员与任务更易理解，并收纳其他功能？",
            "scope": "历史归档的 9 个竞品、10 张截图，加 1 张用户提供的虎牙现状长图；现状图不计入竞品。",
            "goals": ["简化布局并突出常用功能。", "强化会员与任务模块。", "将其他功能收起。"],
            "constraints": ["未提供访问频率，不能由现有位置决定常用入口。", "会员业务关系未确认，不假定贵族、守护与平台会员可合并。", "历史截图不代表当前最新版。"],
        },
        "analysis_process": {"material_observations": observations, "comparisons": comparisons,
                             "current_state": {
                                 "id": "current-analysis",
                                 "user_provided_facts": ["用户希望简化布局、突出常用功能、强化会员与任务中心，并收起其他功能。"],
                                 "goal_relationship": "现状中会员入口与普通图标同级，任务只有一行活动文案，游戏及更多服务连续展开；这些区域正对应本次层级与收纳目标。",
                                 "inferences": ["可先把会员身份权益、任务状态动作和经验证的常用入口分别成层。", "游戏、游戏服务和更多服务可进入有分区的全部服务，但不能仅凭截图认定它们低频。"],
                                 "reference_claim_ids": ["finding-membership", "finding-task", "finding-drawer"],
                                 "evidence_boundaries": ["没有访问频率、点击、转化或留存数据。", "仅凭截图不能决定贵族、守护与平台会员是否应合并。"],
                             }},
        "overall": inference("overall-redesign", "先把会员身份与权益、任务状态与动作、经验证的常用入口分成三层，再让‘全部服务’承接其余功能。",
                             refs("group", gids["membership"], gids["task"], gids["drawer"]),
                             ["cmp-membership", "cmp-task", "cmp-drawer"],
                             "先做信息层级原型：紧凑会员区、可执行任务卡、一排常用入口和分区全部服务。",
                             "会员与任务确属本次主目标，且常用入口能用数据或研究确认。",
                             "会员业务能否合并、常用入口排序和抽屉发现成本仍需验证。"),
        "key_findings": [
            inference("finding-membership", "会员区应同时解释身份、可用权益或续费动作，并与常用操作分层；放大卡片本身不能解决会员价值不清。",
                      refs("material", "mat-cap-tencent", "mat-cap-bilibili", "mat-cap-gooh"), ["cmp-membership"],
                      "用一块紧凑区域回答用户拥有什么、能做什么，再把内容操作放到下一层。",
                      "会员业务关系和权益口径能够被清楚说明。",
                      "贵族、守护和平台会员是否能聚合必须由业务定义确认。"),
            inference("finding-task", "任务卡至少应给出一项状态或进度和一个下一步动作；奖励可以辅助，但不能替代任务目标。",
                      refs("material", "mat-cap-doubao", "mat-cap-headway"), ["cmp-task"],
                      "把现状的一行活动文案改成紧凑任务卡，并避免照搬占半屏的目标圆环。",
                      "任务有可解释的目标、状态和动作。",
                      "动作与进度来自两个样本，组合方案需要原型和任务规则验证。"),
            inference("finding-reward", "Target 的年度节省与奖励余额适合解释会员收益，不提供任务目标或动作，不能用来设计任务中心。",
                      refs("material", "mat-cap-target"), ["cmp-reward-boundary"],
                      "若虎牙有可核对的会员收益，将它放在会员层而不是任务层。",
                      "存在用户可理解的累计或待领取权益。",
                      "截图不支持收益展示提升付费转化的判断。"),
            inference("finding-drawer", "服务抽屉可以收纳游戏、礼包、免流和设置等辅助入口，但本次要强化的会员与任务应留在主页面。",
                      refs("material", "mat-cap-douyu-top", "mat-cap-douyu-bottom"), ["cmp-drawer"],
                      "主页面只保留目标模块和经验证常用入口，抽屉内部继续按任务分区。",
                      "辅助入口数量较多且允许一次额外操作。",
                      "抽屉是已打开和滚动后的视口，不能当作首页首屏。"),
        ],
        "current_state": {
            "id": "huya-current",
            "description": "用户提供的虎牙现状长图用于区域级对照，不计入竞品数量。",
            "images": [{"id": "huya-current-image", "image_path": "baseline-assets/huya-current.png", "caption": "用户提供的现状长图，仅用于对照"}],
            "regions": [
                {"id": "current-membership-row", "image_id": "huya-current-image", "label": "会员与功能入口区", "visible_fact": "成为守护、成为贵族与其他图标使用相近尺寸和同一行列体系。"},
                {"id": "current-task-row", "image_id": "huya-current-image", "label": "任务中心区", "visible_fact": "任务中心位于身份资产下方，只显示一行活动文案，没有可见进度或下一步按钮。"},
                {"id": "current-service-blocks", "image_id": "huya-current-image", "label": "游戏与更多服务区", "visible_fact": "核心入口之后继续展开我的游戏、游戏服务和更多服务三个区域。"},
            ],
            "findings": [
                inference("current-membership", "现状没有用层级区分会员身份权益和普通快捷入口，用户难以从这一排直接理解会员价值。",
                          refs("current_state", "current-membership-row") + refs("material", "mat-cap-tencent", "mat-cap-bilibili"), ["current-analysis", "cmp-membership"],
                          "先核对贵族、守护与平台会员的业务关系，再设计紧凑的身份权益区。",
                          "相关会员能共享至少一种身份、权益或续费关系。",
                          "相同图标尺寸只能证明视觉同级，不能证明用户认知或使用效果。"),
                inference("current-task", "任务中心虽在上方，却只有活动文案，未回答当前状态和下一步动作；可参考任务卡补足这两类信息。",
                          refs("current_state", "current-task-row") + refs("material", "mat-cap-doubao", "mat-cap-headway"), ["current-analysis", "cmp-task"],
                          "把一行文案改为一项状态或进度加一个明确动作的紧凑卡片。",
                          "虎牙任务有稳定状态与可执行下一步。",
                          "位置靠前不等于高频，卡片高度仍需原型验证。"),
                inference("current-services", "游戏、游戏服务和更多服务连续展开，占用主页面长度；可将非目标入口收入分区服务抽屉。",
                          refs("current_state", "current-service-blocks") + refs("material", "mat-cap-douyu-top", "mat-cap-douyu-bottom"), ["current-analysis", "cmp-drawer"],
                          "保留经数据确认的常用入口，其余按游戏、权益、工具和设置等任务分区收纳。",
                          "用户能通过明确入口找到全部服务。",
                          "没有访问数据，不能直接判定画面中的游戏或服务属于低频。"),
            ],
        },
        "groups": [], "materials": [],
        "synthesis": {"findings": [], "validation_questions": []},
        "information_gaps": [],
        "methodology": [
            {"title": "历史素材分析重放", "text": "沿用既有证据和图片，仅重做分析、分类与现状关联；没有执行新的来源搜集、登录检查或当前版本确认。"},
            {"title": "事实与推断边界", "text": "现状图用于确认可见区域；用户目标来自需求；会员聚合、常用排序和任务卡组合属于待验证设计判断。"},
        ],
    }
    group_text = {
        "membership": ("重点比较会员身份、权益与常用操作能否形成三层；适合会员是主任务之一时，仍需解释权益而非只放大卡片。", "用紧凑会员区连接身份、权益和动作。", "会员与内容操作都需留在主页面。", "业务关系未确认时不能合并不同会员。"),
        "task": ("重点比较下一步动作和进度如何组成可执行任务卡；适合目标明确的连续任务，卡片高度仍需验证。", "用一项状态或进度加一个动作替代纯活动文案。", "任务规则能提供稳定状态和下一步。", "位置与面积不能替代行为数据。"),
        "reward": ("已获收益可解释会员价值，但没有目标和动作，不能作为任务中心结构。", "将可核对收益放在会员层。", "业务存在清楚的权益收益口径。", "不能推断转化效果。"),
        "drawer": ("抽屉适合承接辅助服务并保留分区；本次要强化的会员与任务仍应留在主页面。", "用全部服务入口承接分区抽屉。", "辅助入口多且可接受额外一步。", "抽屉视口不能当作首屏。"),
    }
    cmp_for_group = {"membership": "cmp-membership", "task": "cmp-task", "reward": "cmp-reward-boundary", "drawer": "cmp-drawer"}
    for key, gid, *_ in group_specs:
        statement, recommendation, applicability, limitation = group_text[key]
        analysis["groups"].append({"group_id": gid, "takeaway": inference("group-takeaway-" + key, statement, refs("group", gid), [cmp_for_group[key]], recommendation, applicability, limitation)})
    for item in items:
        analysis["materials"].append({"material_id": item["id"], "insight": inference("insight-" + item["id"], item["insight"], refs("material", item["id"]), ["obs-" + item["id"], cmp_for_group[item["group"]]], item["recommendation"], item["applicability"], item["limitation"])})
    analysis["synthesis"] = {
        "findings": [
            inference("summary-sequence", "建议先确认会员业务关系，再定义任务卡字段，随后用数据选出一排常用入口，最后把其余服务分区收纳。",
                      refs("group", gids["membership"], gids["task"], gids["drawer"]), ["cmp-membership", "cmp-task", "cmp-drawer"],
                      "按业务定义、任务规则、入口证据和收纳结构的顺序推进原型。",
                      "本次目标确实是强化会员与任务并减少主页面入口。",
                      "任何一步缺少依据时都应缩小方案范围，而不是用更大的卡片或更多图标补齐。"),
            inference("summary-boundaries", "Target 可补充会员收益表达，斗鱼可补充服务收纳；两者分别不能替代任务卡和主页面层级。",
                      refs("material", "mat-cap-target", "mat-cap-douyu-top", "mat-cap-douyu-bottom"), ["cmp-reward-boundary", "cmp-drawer"],
                      "把每个样本只用于它能证明的机制，并在原型中保持模块职责分开。",
                      "需要组合多个样本解决不同设计问题。",
                      "组合后的整体方案尚未经过可用性和行为验证。"),
        ],
        "validation_questions": [
            question("verify-membership-definition", "贵族、守护与平台会员是否共享身份、权益或续费动作，哪些内容可以聚合？", refs("current_state", "current-membership-row"), ["current-analysis", "cmp-membership"]),
            question("verify-task-fields", "任务中心能稳定提供哪项状态、进度和下一步动作？", refs("current_state", "current-task-row") + refs("material", "mat-cap-doubao", "mat-cap-headway"), ["current-analysis", "cmp-task"]),
            question("verify-common-actions", "哪些入口有足够的访问或任务证据留在一排常用功能中？", refs("material", "mat-cap-bilibili", "mat-cap-kugou"), ["cmp-membership"]),
            question("verify-drawer-path", "用户能否发现并返回全部服务抽屉，收纳后关键辅助任务是否仍可完成？", refs("material", "mat-cap-douyu-top", "mat-cap-douyu-bottom"), ["cmp-drawer"]),
        ],
    }
    analysis["quality_review"] = review(analysis, [
        {"candidate_id": "old-task-reward-group", "action": "rewritten", "before": "任务动作、目标进度与已获收益可分别表达。", "after": "Target 单列为会员收益结果，只用于权益价值表达；豆包与 Headway 才用于任务动作与进度。", "reason": "旧分组仍把奖励余额与任务中心放在同一层级，容易制造错误等价。"},
        {"candidate_id": "old-membership-general", "action": "rewritten", "before": "会员权益与常用操作分层后，可把辅助服务放到次要位置。", "after": "会员区需解释身份、权益或动作；是否聚合贵族、守护与平台会员取决于业务关系。", "reason": "旧结论过于通用，也可能被误解为只需放大会员卡。"},
    ])
    target = HERE / "detailed-my-page-redesign"
    dump(target / "classification-plan.json", plan)
    dump(target / "analysis.json", analysis)
    baseline = target / "baseline-assets" / "huya-current.png"
    baseline.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(STAGE1 / "detailed-my-page-redesign" / "baseline-assets" / "huya-current.png", baseline)


if __name__ == "__main__":
    build_one_sentence()
    build_detailed()
