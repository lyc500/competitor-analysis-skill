"""Build Stage 4 acceptance inputs from the 2026-10-27 browser evidence.

The raw images in ../raw-assets were downloaded from live source pages in the
existing Chrome session.  This script only assembles the observed evidence and
Agent-authored analysis into the formal contracts; it does not claim a replay
to be a new source visit.
"""
from copy import deepcopy
import json
from pathlib import Path
import shutil
import hashlib

from PIL import Image


ROOT = Path(__file__).resolve().parent
RAW = ROOT / "raw-assets"
CAPTURED_AT = "2026-10-27T22:15:00+08:00"


ATTEMPTS = {
    "uinotes": {
        "id": "att-uinotes-profile", "source_type": "ui_database", "source_provider": "UI Notes",
        "entry_url": "https://uinotes.com/pin?functions=71",
        "query_mapping": {"raw_page_intent": "我的页 / 个人中心", "mapped_terms": ["我的", "个人中心"], "source_taxonomy_terms": ["个人中心"]},
        "actual_query": "功能：个人中心", "search_mode": "taxonomy_filter", "discovery_batch": 1,
        "web_text_accessible": True, "browser_accessible": True, "browser_interactive": True,
        "content_available": True, "access_status": "paywall", "observed_scope": "当前会话为非会员；1877 条中首批 20 张可见，详情与原图可打开，后续结果需会员",
        "attempt_status": "completed", "failure_reason": "",
    },
    "refero": {
        "id": "att-refero-profile", "source_type": "ui_database", "source_provider": "Refero",
        "entry_url": "https://refero.design/apps/search?page_types[id][]=15",
        "query_mapping": {"raw_page_intent": "我的页 / 个人中心", "mapped_terms": ["Profile", "Account"], "source_taxonomy_terms": ["Profile & Account"]},
        "actual_query": "Page type: Profile & Account", "search_mode": "taxonomy_filter", "discovery_batch": 1,
        "web_text_accessible": True, "browser_accessible": True, "browser_interactive": True,
        "content_available": True, "access_status": "paywall", "observed_scope": "当前账号会话可见首批 8 张，详情与图像可打开；其余 2174 张受 Pro 订阅限制",
        "attempt_status": "completed", "failure_reason": "",
    },
    "mobbin": {
        "id": "att-mobbin-profile", "source_type": "ui_database", "source_provider": "Mobbin",
        "entry_url": "https://mobbin.com/browse/ios/screens?sort=popularity&filter=screenPatterns.My+Account+%26+Profile",
        "query_mapping": {"raw_page_intent": "我的页 / 个人中心", "mapped_terms": ["My Account", "Profile"], "source_taxonomy_terms": ["My Account & Profile"]},
        "actual_query": "Screen pattern: My Account & Profile", "search_mode": "taxonomy_filter", "discovery_batch": 1,
        "web_text_accessible": True, "browser_accessible": True, "browser_interactive": True,
        "content_available": True, "access_status": "paywall", "observed_scope": "当前账号会话可见 2298 条中的首批 5 张；详情可开，下载与后续结果需 Pro",
        "attempt_status": "completed", "failure_reason": "",
    },
    "pttrns": {
        "id": "att-pttrns-profile", "source_type": "ui_database", "source_provider": "PTTRNS",
        "entry_url": "https://app.pttrns.com/",
        "query_mapping": {"raw_page_intent": "我的页 / 个人中心", "mapped_terms": ["Profile", "Account"], "source_taxonomy_terms": []},
        "actual_query": "Profile / Account", "search_mode": "site_filter", "discovery_batch": 1,
        "web_text_accessible": True, "browser_accessible": True, "browser_interactive": False,
        "content_available": False, "access_status": "login_required", "observed_scope": "旧标签残留 419 条列表，但详情与新标签均跳回首页登录入口，未纳入候选",
        "attempt_status": "blocked", "failure_reason": "免费账号登录后才可稳定搜索和打开详情",
    },
}


CHECKS = {
    "uinotes": {
        "id": "check-uinotes-preflight", "source_attempt_id": "att-uinotes-profile", "phase": "preflight",
        "checked_at": "2026-10-27T21:35:00+08:00", "browser_session_id": "chrome-user1",
        "browser_session_kind": "agent_browser", "browser_tab_id": "339184316",
        "page_open": True, "search_usable": True, "filter_usable": True, "detail_usable": True,
        "original_asset_usable": True, "pagination_usable": False, "authentication_state": "authenticated",
        "access_barrier": "paywall", "visible_scope": "个人中心 1877 条中的首批 20 张",
        "coverage_impact": "minor", "notes": "账号显示非会员；原图可获取，继续浏览需订阅",
    },
    "refero": {
        "id": "check-refero-preflight", "source_attempt_id": "att-refero-profile", "phase": "preflight",
        "checked_at": "2026-10-27T21:43:00+08:00", "browser_session_id": "chrome-user1",
        "browser_session_kind": "agent_browser", "browser_tab_id": "339183758",
        "page_open": True, "search_usable": True, "filter_usable": True, "detail_usable": True,
        "original_asset_usable": True, "pagination_usable": False, "authentication_state": "authenticated",
        "access_barrier": "paywall", "visible_scope": "Profile & Account 首批 8 张可见",
        "coverage_impact": "minor", "notes": "账号页与历史记录可见；后续 2174 张需 Pro",
    },
    "mobbin": {
        "id": "check-mobbin-preflight", "source_attempt_id": "att-mobbin-profile", "phase": "preflight",
        "checked_at": "2026-10-27T21:51:00+08:00", "browser_session_id": "chrome-user1",
        "browser_session_kind": "agent_browser", "browser_tab_id": "339183919",
        "page_open": True, "search_usable": True, "filter_usable": True, "detail_usable": True,
        "original_asset_usable": False, "pagination_usable": False, "authentication_state": "authenticated",
        "access_barrier": "paywall", "visible_scope": "2298 条中的首批 5 张可见",
        "coverage_impact": "minor", "notes": "Badoo 详情可开，但下载与更多结果需 Pro；未把压缩预览纳入素材",
    },
    "pttrns": {
        "id": "check-pttrns-preflight", "source_attempt_id": "att-pttrns-profile", "phase": "preflight",
        "checked_at": "2026-10-27T21:58:00+08:00", "browser_session_id": "chrome-user1",
        "browser_session_kind": "agent_browser", "browser_tab_id": "339184309",
        "page_open": True, "search_usable": False, "filter_usable": False, "detail_usable": False,
        "original_asset_usable": False, "pagination_usable": False, "authentication_state": "anonymous",
        "access_barrier": "login_required", "visible_scope": "新标签只显示首页登录入口；旧标签列表不可稳定复用",
        "coverage_impact": "minor", "notes": "其他已验证来源已提供足够候选，因此本批不因该登录限制阻塞",
    },
}


CANDIDATES = {
    "uinotes-bilibili": ("uinotes", "哔哩哔哩", "https://uinotes.com/pin/653270661085471375", "https://uinotes-img.oss-cn-shanghai.aliyuncs.com/image/origin-webp/653270661085471375.webp?v1", "uinotes/bilibili.webp"),
    "uinotes-pinduoduo": ("uinotes", "拼多多", "https://uinotes.com/pin/658360019995979356", "https://uinotes-img.oss-cn-shanghai.aliyuncs.com/image/origin-webp/658360019995979356.webp?v1", "uinotes/pinduoduo.webp"),
    "uinotes-doubao": ("uinotes", "豆包爱学", "https://uinotes.com/pin/133323406851668822", "https://uinotes-img.oss-cn-shanghai.aliyuncs.com/image/origin-webp/133323406851668822.webp?v1", "uinotes/doubao-aixue.webp"),
    "uinotes-kugou": ("uinotes", "酷狗畅听版", "https://uinotes.com/pin/438158835260733576", "https://uinotes-img.oss-cn-shanghai.aliyuncs.com/image/origin-webp/438158835260733576.webp?v1", "uinotes/kugou-lite.webp"),
    "uinotes-duolingo": ("uinotes", "Duolingo", "https://uinotes.com/pin/004403109497668392", "https://uinotes-img.oss-cn-shanghai.aliyuncs.com/image/origin-webp/004403109497668392.webp?v1", "uinotes/duolingo.webp"),
    "uinotes-douyu": ("uinotes", "斗鱼", "https://uinotes.com/pin/276511827925182237", "https://uinotes-img.oss-cn-shanghai.aliyuncs.com/image/origin-webp/276511827925182237.webp?v1", "uinotes/douyu-drawer.webp"),
    "refero-wise": ("refero", "Wise", "https://refero.design/screens/199c7406-cf97-46b2-8da0-0d80ab603631?page_types[id][]=15&source=search", "https://images.refero.design/screenshots/39/mobile/778adba6-19c0-4c90-8da3-e795d19ee5d5_thumb.jpg", "refero/wise.jpg"),
    "refero-kickstarter": ("refero", "Kickstarter", "https://refero.design/screens/01bf2c7b-fbf6-4c25-8986-49d846699fef?page_types[id][]=15&source=search", "https://images.refero.design/screenshots/171/mobile/4c96b3b6-7411-4e6a-aea4-8e8f6368df0f_thumb.jpg", "refero/kickstarter.jpg"),
    "refero-md-vinyl": ("refero", "MD Vinyl", "https://refero.design/screens/0bf7f2db-473e-4f8e-a293-4a20657d66bd?page_types[id][]=15&source=search", "https://images.refero.design/screenshots/291/mobile/80ede065-91b6-4dea-85c1-fa0679cee52b_thumb.jpg", "refero/md-vinyl.jpg"),
    "refero-tidal": ("refero", "TIDAL", "https://refero.design/screens/7a4d4c3f-687d-4501-b747-2dc1233f1928?page_types[id][]=15&source=search", "https://images.refero.design/screenshots/298/mobile/8e239981-6954-45a7-ba30-7626a9c56b46_thumb.jpg", "refero/tidal.jpg"),
    "refero-duolingo-settings": ("refero", "Duolingo", "https://refero.design/screens/b9a5366d-68c8-4e23-8c78-e84ed4359d8a?page_types[id][]=15&source=search", "https://images.refero.design/screenshots/5/mobile/a0378378-a44b-4e50-a909-32dd83776a40_thumb.jpg", "refero/duolingo.jpg"),
    "refero-revolut": ("refero", "Revolut", "https://refero.design/screens/8adec783-5f17-478d-ba28-f063eeebd7b8?page_types[id][]=15&source=search", "https://images.refero.design/screenshots/74/mobile/5fdac796-2bb6-45cb-93e3-d436232e72eb_thumb.jpg", "refero/revolut.jpg"),
    "refero-nyt": ("refero", "The New York Times", "https://refero.design/screens/bfcdc685-196c-4248-9161-0f2523082dae?page_types[id][]=15&source=search", "https://images.refero.design/screenshots/117/mobile/be5e6584-1045-4be2-8945-c53101553734_thumb.jpg", "refero/nyt.jpg"),
    "refero-airbuds": ("refero", "Airbuds", "https://refero.design/screens/cdb87543-4d9a-4f5e-9a95-035361942d3c?page_types[id][]=15&source=search", "https://images.refero.design/screenshots/150/mobile/c5435be1-12d5-45fb-9630-41a3fcbd2fb5_thumb.jpg", "refero/airbuds.jpg"),
}


PRODUCT_META = {
    "哔哩哔哩": ("CN", "视频社区"), "拼多多": ("CN", "电商"), "豆包爱学": ("CN", "学习工具"),
    "酷狗畅听版": ("CN", "音乐"), "Duolingo": ("Global", "学习工具"), "斗鱼": ("CN", "直播社区"),
    "Wise": ("Global", "金融工具"), "Kickstarter": ("Global", "众筹平台"), "MD Vinyl": ("Global", "音乐"),
    "TIDAL": ("Global", "音乐"), "Revolut": ("Global", "金融工具"), "The New York Times": ("Global", "新闻内容"),
    "Airbuds": ("Global", "社交音乐"),
}


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def task(raw_request, goal, target_page, candidate_keys):
    products = []
    for key in candidate_keys:
        name = CANDIDATES[key][1]
        if name not in products:
            products.append(name)
    competitors = []
    for name in products:
        region, product_type = PRODUCT_META[name]
        competitors.append({
            "product_name": name, "region": region, "product_type": product_type, "platform": "iOS",
            "target_page": target_page, "planning_source": "agent_planned", "priority": "high",
            "reason": "当前相关来源中可追溯的候选；最终是否纳入由逐图语义审核决定",
        })
    return {
        "raw_request": raw_request, "research_goal": goal, "target_page": target_page,
        "target_surface": "mobile_app", "platforms": ["iOS"], "regions": ["CN", "Global"],
        "specified_products": [], "assumptions": ["只使用公开可访问且可追溯的单屏 UI 素材"],
        "needs_clarification": False, "task_status": "ready", "planning_strategy": "agent_only",
        "competitors": competitors,
    }


def source_registry(target_page, candidate_keys, attempt_keys):
    attempts = [deepcopy(ATTEMPTS[key]) for key in attempt_keys]
    if target_page == "设置页":
        attempts[0]["query_mapping"] = {"raw_page_intent": "设置页", "mapped_terms": ["Settings"], "source_taxonomy_terms": ["Profile & Account"]}
        attempts[0]["actual_query"] = "Profile & Account results, visually reviewed for Settings"
    candidates = []
    for rank, key in enumerate(candidate_keys, 1):
        source, product, detail, asset, _ = CANDIDATES[key]
        attempt = ATTEMPTS[source]
        candidates.append({
            "id": "cand-" + key, "source_attempt_id": attempt["id"], "product_name": product,
            "target_page": target_page, "source_entry_url": attempts[[x["id"] for x in attempts].index(attempt["id"])]["entry_url"],
            "source_detail_url": detail, "source_asset_url": asset, "candidate_rank": rank,
            "candidate_status": "accepted", "disposition_reason": "来源详情和原图可访问，进入逐图语义审核；不预设最终纳入",
        })
    checks = [deepcopy(CHECKS[key]) for key in attempt_keys]
    access = {
        "schema_version": 1, "id": "access-" + target_page.replace(" ", "-").replace("/", "-").replace("／", "-"),
        "research_scope": f"{target_page}相关来源的采集能力与当前可见范围",
        "started_at": "2026-10-27T21:30:00+08:00", "completed_at": "2026-10-27T22:05:00+08:00",
        "relevant_source_attempt_ids": [ATTEMPTS[key]["id"] for key in attempt_keys], "checks": checks,
        "decision": {
            "status": "not_required", "prompted_at": "", "decided_at": "2026-10-27T22:05:00+08:00",
            "restricted_source_attempt_ids": [],
            "summary": "登录或订阅限制未实质阻断本批覆盖：继续使用当前会话可见范围，不购买订阅；PTTRNS 不纳入候选。",
        },
        "resume": {"status": "not_needed", "checkpoint_candidate_ids": [], "completed_candidate_ids": [],
                   "remaining_candidate_ids": [], "recheck_ids": [], "resumed_at": ""},
    }
    return {
        "source_attempts": attempts, "candidates": candidates,
        "candidate_pool": [item["id"] for item in candidates],
        "candidate_limit": {"max": 50, "unit": "candidate_records", "applies_to": "candidate_pool",
                            "ordering_basis": "页面主任务匹配度、来源可追溯性和区域覆盖", "truncated_candidate_ids": []},
        "access_preparation": access,
    }


def captures(target_page, candidate_keys):
    rows = []
    for key in candidate_keys:
        source, product, detail, asset, image = CANDIDATES[key]
        rows.append({
            "id": "cap-" + key, "source_candidate_id": "cand-" + key,
            "source_attempt_id": ATTEMPTS[source]["id"], "product_name": product, "target_page": target_page,
            "target_surface": "mobile_app", "platform": "iOS", "discovered_source_type": "ui_database",
            "source_provider": ATTEMPTS[source]["source_provider"], "source_entry_url": ATTEMPTS[source]["entry_url"],
            "source_detail_url": detail, "source_asset_url": asset, "requested_url": detail, "final_url": detail,
            "captured_at": CAPTURED_AT, "capture_status": "captured", "screenshot_path": "../../raw-assets/" + image,
            "failure_reason": "", "browser_name": "Chrome", "browser_session_id": "chrome-user1",
            "capture_method": "original_image_asset_from_rendered_source",
        })
    return {"captures": rows}


REVIEW_FACTS = {
    "uinotes-bilibili": ("personal_center_root", "logged_in", "本人资料、会员横条、离线缓存/历史/收藏和创作中心同时可见"),
    "uinotes-pinduoduo": ("personal_center_root", "logged_out_complete", "登录入口、订单状态、钱包/优惠、服务矩阵与商品推荐连续出现"),
    "uinotes-doubao": ("personal_center_root", "logged_out_complete", "登录入口之后直接给出金币商城、任务中心，再接学习记录与设置列表"),
    "uinotes-kugou": ("personal_center_root", "logged_out_complete", "免登录提示、收藏/下载快捷入口与最近播放内容同屏"),
    "uinotes-duolingo": ("own_profile", "logged_in", "头像、账号信息、学习语言、关系数据与添加好友入口组成本人资料页"),
    "uinotes-douyu": ("services_drawer", "logged_in", "服务抽屉覆盖在个人页上方，展示创作与推荐服务；不是个人中心根层首屏"),
    "refero-wise": ("account_management_root", "logged_in", "账户切换、设置、帮助和退出等账户管理动作组成根层"),
    "refero-kickstarter": ("own_profile", "logged_in", "Profile 标签下以 backed/saved 项目及状态进度承接回访任务"),
    "refero-md-vinyl": ("content_detail", "logged_in", "画面主体是单曲/唱片内容详情而非本人资料或个人中心"),
    "refero-tidal": ("other_profile_action_sheet", "logged_in", "操作表包含取消关注、分享、举报，主体是他人艺术家资料"),
    "refero-duolingo-settings": ("settings_root", "logged_in", "页面标题和条目共同表明这是设置根页"),
    "refero-revolut": ("other_person_profile", "logged_in", "Block/Report 等动作表明这是他人联系人公开资料"),
    "refero-nyt": ("you_tab_content", "logged_in", "底部 You 标签选中，页面以已保存/推荐内容卡片承接回访"),
    "refero-airbuds": ("own_profile", "logged_in", "本人身份、最近播放和收藏内容在同一资料页中"),
}


def reviews(target_page, candidate_keys, accepted_keys):
    rows = []
    for key in candidate_keys:
        role, login, fact = REVIEW_FACTS[key]
        accepted = key in accepted_keys
        rows.append({
            "target_id": "cap-" + key, "target_kind": "browser_capture",
            "semantic_status": "accepted" if accepted else "rejected", "product_identity": "matched",
            "target_page_match": "matched" if accepted else "mismatched", "target_surface_match": "matched",
            "page_role": role, "interaction_stage": "in_progress" if "drawer" in role or "sheet" in role else "before_action",
            "render_state": "loaded", "login_state": login, "page_completeness": "complete", "asset_kind": "ui_page",
            "review_reason_codes": ["product_identity", "target_page", "surface", "render_state", "completeness", "source_context"],
            "semantic_reason": fact + ("；与本次目标页面和移动端表面匹配。" if accepted else f"；因此不作为{target_page}竞品样本。"),
            "review_source": "agent_visual_review",
        })
    return {"reviews": rows}


def classification(groups, labels, dimension, rationale, scope):
    return {
        "schema_version": 2, "classification_dimension": dimension,
        "classification_reason": rationale,
        "comparison_basis": {"primary_dimension": dimension, "rationale": rationale, "scope": scope},
        "groups": [{
            "id": gid, "name": name, "reason": reason, "material_ids": ["mat-cap-" + key for key in keys],
            "audit": {"inclusion_criteria": criterion, "shared_mechanism": mechanism,
                      "member_reasons": [{"material_id": "mat-cap-" + key, "reason": member_reasons[key]} for key in keys],
                      "adjacent_difference": adjacent},
        } for gid, name, reason, keys, criterion, mechanism, member_reasons, adjacent in groups],
        "material_labels": [{"material_id": "mat-cap-" + key, "labels": labels[key]} for group in groups for key in group[3]],
    }


def make_analysis(title, research, groups, observations, comparisons, material_insights,
                  overall, key_findings, synthesis, validation_questions, info_gaps, current=None):
    claim_ids = []

    def claim(cid, statement, refs, process_refs, kind="inference", recommendation="", applicability="", limitations=""):
        value = {"id": cid, "kind": kind, "statement": statement,
                 "evidence_refs": [{"kind": kind_, "id": ref} for kind_, ref in refs],
                 "analysis_refs": list(process_refs)}
        if kind == "inference":
            value.update(recommendation=recommendation, applicability=applicability, limitations=limitations)
        claim_ids.append(cid)
        return value

    process = {
        "material_observations": [{"id": "obs-" + key, "material_id": "mat-cap-" + key,
                                   "visible_facts": data["facts"], "evidence_boundaries": data["boundaries"]}
                                  for key, data in observations.items()],
        "comparisons": comparisons,
    }
    value = {
        "schema_version": 2, "title": title, "research": research, "analysis_process": process,
        "overall": claim("overall", *overall),
        "key_findings": [claim("finding-" + str(index), *item) for index, item in enumerate(key_findings, 1)],
        "groups": [], "materials": [],
        "synthesis": {
            "findings": [claim("synthesis-" + str(index), *item) for index, item in enumerate(synthesis, 1)],
            "validation_questions": [claim("validation-" + str(index), *item, kind="question") for index, item in enumerate(validation_questions, 1)],
        },
        "information_gaps": info_gaps,
        "methodology": [{"title": "证据边界", "text": "结论来自静态截图的可见结构；不推断使用频率、转化率或留存效果。"}],
    }
    for gid, data in groups.items():
        value["groups"].append({"group_id": gid, "takeaway": claim("takeaway-" + gid, *data)})
    for key, data in material_insights.items():
        value["materials"].append({"material_id": "mat-cap-" + key, "insight": claim("insight-" + key, *data)})
    if current:
        value["current_state"] = current["state"]
        process["current_state"] = current["process"]
        value["current_state"]["findings"] = [claim("current-" + str(index), *item) for index, item in enumerate(current["findings"], 1)]
    value["quality_review"] = {
        "review_type": "agent_self_review", "independent": False, "reviewed_claim_ids": claim_ids,
        "checks": {name: True for name in ("evidence_supported", "reference_value_clear", "research_relevant",
                                              "exceptions_considered", "duplicates_resolved", "generic_claims_removed")},
        "edits": [{"candidate_id": "generic-claim", "action": "removed", "before": "突出重点可以提升体验",
                   "reason": "没有说明具体做法、条件或截图依据"}],
        "notes": ["逐图事实、横向比较和最终结论已由 Agent 人工复核；该记录不是独立验证。"],
    }
    return value


def labels_for(keys, overrides=None):
    overrides = overrides or {}
    result = {}
    for key in keys:
        role, login, _ = REVIEW_FACTS[key]
        result[key] = {
            "page_role": role, "path_stage": "root", "interaction_stage": "browse_before_action",
            "render_state": "loaded_complete", "login_state": "logged_out" if login == "logged_out_complete" else "logged_in",
        }
        result[key].update(overrides.get(key, {}))
    return result


def write_scenario(slug, task_data, registry, capture_data, review_data, classification_data, analysis_data):
    folder = ROOT / slug / "input"
    dump(folder / "task.json", task_data)
    dump(folder / "sources-input.json", registry)
    dump(folder / "captures-input.json", capture_data)
    dump(folder / "semantic-reviews.json", review_data)
    dump(folder / "classification-plan.json", classification_data)
    dump(folder / "analysis.json", analysis_data)


def scenario_a():
    keys = list(CANDIDATES)
    accepted = {"uinotes-bilibili", "uinotes-pinduoduo", "uinotes-doubao", "uinotes-kugou", "uinotes-duolingo",
                "refero-wise", "refero-kickstarter", "refero-nyt", "refero-airbuds"}
    task_data = task("帮我搜集一下国内外知名 App‘我的’页的竞品截图。",
                     "比较国内外知名 App 的我的页主任务、组织模式和适用场景", "我的页 / 个人中心", keys)
    group_specs = [
        ("group-profile", "身份与关系资料", "比较身份、关系与内容如何组成可回访的本人资料页", ["uinotes-duolingo", "refero-airbuds"],
         "本人资料是页面主任务，身份与关系信息均在根层可见", "以身份为锚点，再承接关系或个人内容",
         {"uinotes-duolingo": "以学习身份、语言和好友关系组织本人资料", "refero-airbuds": "以音乐身份、最近播放和收藏组织本人资料"},
         "不包含他人公开主页，也不把账户设置页并入资料页"),
        ("group-return", "回到内容与进度", "重点看页面如何让用户继续上次内容、收藏或项目进度", ["uinotes-kugou", "refero-kickstarter", "refero-nyt"],
         "页面根层以继续内容或查看进度为主要回访任务", "把个人页作为内容续接点，而非入口大全",
         {"uinotes-kugou": "最近播放与收藏/下载在首屏形成音乐续接", "refero-kickstarter": "backed/saved 项目状态承接项目回访", "refero-nyt": "You 标签用内容卡片承接保存与阅读"},
         "与身份资料组的差异是页面首要对象为内容或项目，而非关系资料"),
        ("group-service", "服务与资产总览", "比较订单、权益和常用动作如何在高密度页面里划分层级", ["uinotes-bilibili", "uinotes-pinduoduo"],
         "根层同时承担资产、服务与常用动作总览", "用条带、横排和分区组织多种服务",
         {"uinotes-bilibili": "会员、内容动作和创作入口分成不同区域", "uinotes-pinduoduo": "订单、资产、服务与推荐形成连续高密度分区"},
         "不因都含会员或钱包就与文件管理、公开主页等不同主任务合组"),
        ("group-task", "任务与学习入口", "看明确任务入口怎样在未登录骨架中仍保持可发现", ["uinotes-doubao"],
         "任务中心与学习相关入口在个人中心根层明确可见", "用少量卡片把任务对象与通用设置区分",
         {"uinotes-doubao": "金币商城与任务中心位于通用功能列表之前"},
         "与服务总览组的差异是核心对象为学习任务，而非多业务资产集合"),
        ("group-account", "账户管理根层", "把它作为轻量账户管理参照，避免把设置动作误当内容或服务入口", ["refero-wise"],
         "页面主任务是账户切换、安全设置与帮助", "以简短列表完成账户管理，不承载内容浏览",
         {"refero-wise": "账户切换、设置、帮助和退出构成完整管理根层"},
         "不与任务中心或他人资料页合组"),
    ]
    labels = labels_for(accepted, {"refero-nyt": {"path_stage": "you_tab_content", "interaction_stage": "tab_selected"}})
    class_data = classification(group_specs, labels, "页面主任务与信息组织机制",
        "宽泛搜集先按页面主任务归组；跨行业样本只有在承担相同回访机制时才比较。",
        "只比较通过语义与机械质量审核的移动 App 单屏；状态、路径和登录情况另行标记。")
    facts = {
        "uinotes-bilibili": (["会员横条位于身份区之后", "离线缓存、历史、收藏独立成一排", "创作中心与推荐服务分区"], ["素材为历史版本，不能代表当前线上结构", "位置不能证明使用频率"]),
        "uinotes-pinduoduo": (["订单、钱包/优惠、服务工具和推荐内容连续排列", "页面处于未登录完整状态"], ["只能观察信息密度和分区，不能判断转化效果"]),
        "uinotes-doubao": (["登录入口之后是金币商城与任务中心卡片", "学习记录、消息、帮助和设置使用列表"], ["未登录骨架不代表登录后的个性化内容"]),
        "uinotes-kugou": (["收藏、下载和最近播放同屏", "底部播放条与我的导航可见"], ["未登录状态不能证明真实内容丰富度"]),
        "uinotes-duolingo": (["身份、学习语言、关系数据和添加好友同屏"], ["关系数字不能推断活跃程度"]),
        "refero-wise": (["账户切换、设置、帮助和退出为主要条目"], ["仅能说明账户管理结构"]),
        "refero-kickstarter": (["Profile 标签呈现 backed/saved 项目", "项目卡展示状态和进度"], ["静态进度不能证明回访频率"]),
        "refero-nyt": (["You 标签选中", "内容卡片占据页面主体"], ["当前截图可能是标签下段，不能视为完整根层首屏"]),
        "refero-airbuds": (["身份信息、最近播放和收藏内容连续排列"], ["不能从卡片顺序推断内容重要性"]),
    }
    observations = {key: {"facts": value[0], "boundaries": value[1]} for key, value in facts.items()}
    comparisons = [
        {"id": "cmp-return-task", "material_ids": ["mat-cap-uinotes-duolingo", "mat-cap-refero-airbuds", "mat-cap-uinotes-kugou", "mat-cap-refero-kickstarter", "mat-cap-refero-nyt"],
         "comparison_findings": ["本人资料页围绕身份与关系组织，内容续接页围绕最近内容或项目状态组织"],
         "design_judgment": "个人中心根层应先回答用户回来要做什么，再选择身份或内容作为主体",
         "recommendation": "将回访任务相同的样本放在一起比较", "applicability": "适合内容、学习和社交产品的个人入口",
         "tradeoffs": ["内容主体会压缩通用设置的首屏空间"], "evidence_boundaries": ["不能从截图判断回访频率"]},
        {"id": "cmp-hub-density", "material_ids": ["mat-cap-uinotes-bilibili", "mat-cap-uinotes-pinduoduo", "mat-cap-uinotes-doubao", "mat-cap-refero-wise"],
         "comparison_findings": ["多业务总览依赖分区，单任务页用少量卡片或列表即可完成层级"],
         "design_judgment": "入口数量应由主任务数量决定，高密度总览不应成为默认模板",
         "recommendation": "先确定首层任务，再决定使用横排、卡片或列表", "applicability": "适合需要在资产、任务和设置之间取舍的个人中心",
         "tradeoffs": ["增加服务广度会削弱单一任务焦点"], "evidence_boundaries": ["页面密度不等于使用效率"]},
    ]
    def inf(statement, refs, proc, rec, app, limit="静态截图不能证明使用频率或业务效果"):
        return (statement, refs, proc, "inference", rec, app, limit)
    group_analysis = {
        "group-profile": inf("先比较身份信息是否服务于后续关系或内容动作，而不是只看头像区样式。", [("group", "group-profile")], ["cmp-return-task"], "保留能引出关系或个人内容的身份字段", "产品存在公开关系或个人内容时"),
        "group-return": inf("值得借鉴的是把最近内容或项目状态直接变成回访入口，并给通用设置让位。", [("group", "group-return")], ["cmp-return-task"], "优先展示可继续的内容对象", "个人中心承担内容续接任务时"),
        "group-service": inf("多业务入口需要按订单、资产、创作等任务分区；只共享‘服务’一词不足以合组。", [("group", "group-service")], ["cmp-hub-density"], "用业务任务划分区域并控制首屏组数", "确有多种独立业务需要汇总时"),
        "group-task": inf("任务卡应与通用设置形成清楚层级，并在未登录时仍说明任务对象。", [("group", "group-task")], ["obs-uinotes-doubao"], "让任务入口说明对象或收益，再接通用功能列表", "任务是明确回访目标时"),
        "group-account": inf("轻量账户管理页可以用短列表完成，不必借用内容卡或服务宫格。", [("group", "group-account")], ["obs-refero-wise"], "把切换、安全与帮助按动作排序", "页面主任务就是账户管理时"),
    }
    material_insights = {}
    insight_texts = {
        "uinotes-bilibili": "会员条带与常用内容动作、创作入口分区，可参考多角色任务的层级拆分。",
        "uinotes-pinduoduo": "订单、资产和服务分区提供高密度总览对照，也暴露首屏焦点被推荐内容稀释的取舍。",
        "uinotes-doubao": "两张任务卡先于通用列表，适合验证任务模块是否需要成为独立一级对象。",
        "uinotes-kugou": "收藏、下载与最近播放共同承接内容续接，适合内容型个人入口。",
        "uinotes-duolingo": "学习身份与好友关系同屏，适合资料页需要引出关系动作的场景。",
        "refero-wise": "短列表把账户切换、安全和帮助收束为管理任务，适合作为减法参照。",
        "refero-kickstarter": "项目状态直接出现在 Profile 标签中，适合需要持续跟踪对象的个人入口。",
        "refero-nyt": "You 标签把个人入口变成内容续接面，但该图可能是标签下段，根层结构仍需验证。",
        "refero-airbuds": "身份区后直接出现最近播放与收藏，适合以个人内容表达身份的产品。",
    }
    for key, text in insight_texts.items():
        material_insights[key] = inf(text, [("material", "mat-cap-" + key)], ["obs-" + key], "只借鉴与本次主任务一致的组织方式", "目标页面角色与截图一致时", observations[key]["boundaries"][0])
    analysis_data = make_analysis(
        "国内外 App 我的页：按回访任务选择结构", {"question": "知名 App 的我的页用哪些结构承接不同回访任务？", "scope": "9 张通过审核的中外移动 App 页面；另有 5 张候选因页面角色不匹配被拒绝", "goals": ["识别可比较的页面主任务", "总结结构差异与适用场景"], "constraints": ["不虚构用户产品或业务目标", "不从静态截图推断行为效果"]},
        group_analysis, observations, comparisons, material_insights,
        inf("‘我的’页没有通用模板：身份、内容续接、服务总览、任务入口和账户管理分别需要不同主体；先确定回访任务，再借鉴布局。", [("material", "mat-cap-uinotes-duolingo"), ("material", "mat-cap-uinotes-kugou"), ("material", "mat-cap-uinotes-bilibili"), ("material", "mat-cap-refero-wise")], ["cmp-return-task", "cmp-hub-density"], "先写清页面首要回访任务，再选择同任务样本", "宽泛个人中心研究"),
        [inf("内容型样本把最近内容或项目状态直接放进个人入口，通用设置退到次层。", [("material", "mat-cap-uinotes-kugou"), ("material", "mat-cap-refero-kickstarter"), ("material", "mat-cap-refero-nyt")], ["cmp-return-task"], "将可继续对象置于通用设置之前", "个人入口承担内容回访时"),
         inf("多业务总览的关键是按任务分区，而不是把会员、钱包和服务等宽泛名词当成共同分类依据。", [("material", "mat-cap-uinotes-bilibili"), ("material", "mat-cap-uinotes-pinduoduo")], ["cmp-hub-density"], "按订单、创作、资产等可解释任务划分", "确需汇总多种业务时")],
        [inf("先以主任务选择参考组：内容续接可看酷狗、Kickstarter 和 NYT；关系资料可看 Duolingo 与 Airbuds；多业务层级可看哔哩哔哩与拼多多。", [("group", "group-return"), ("group", "group-profile"), ("group", "group-service")], ["cmp-return-task", "cmp-hub-density"], "按目标任务缩小参考范围", "进入具体改版前"),
         inf("将 Wise 作为减法基线，可以检验某个模块是否属于账户管理；将拼多多作为密度上界，可以检验服务广度是否挤压主任务。", [("material", "mat-cap-refero-wise"), ("material", "mat-cap-uinotes-pinduoduo")], ["cmp-hub-density"], "同时保留轻量和高密度对照", "方案需要在简洁与业务覆盖之间取舍时")],
        [("不同产品的个人入口真实回访任务和使用频率是什么？", [("material", "mat-cap-uinotes-bilibili")], ["cmp-hub-density"]),
         ("NYT 的 You 标签根层首屏是否与当前截图下段保持同一内容结构？", [("material", "mat-cap-refero-nyt")], ["obs-refero-nyt"])],
        [{"section": "版本", "status": "unknown", "reason": "来源截图未统一提供 App 版本与日期，不能描述为当前最新版。"},
         {"section": "来源覆盖", "status": "unknown", "reason": "三个数据库后续结果受订阅限制，本报告只代表当前可见范围。"}],
    )
    write_scenario("scenario-a-my-pages", task_data, source_registry("我的页 / 个人中心", keys, ["uinotes", "refero", "mobbin", "pttrns"]),
                   captures("我的页 / 个人中心", keys), reviews("我的页 / 个人中心", keys, accepted), class_data, analysis_data)


def scenario_b():
    keys = ["uinotes-bilibili", "uinotes-doubao", "uinotes-kugou", "uinotes-douyu", "uinotes-pinduoduo", "refero-airbuds"]
    accepted = set(keys)
    task_data = task("这是我们现在的‘我的’页现状，我需要做一个改版，优化方向是简化布局，突出常用功能，并且强化会员、任务中心模块，其他功能收起来。根据这个目标帮我搜集可以参考的竞品页面。",
                     "结合虎牙现状，比较首屏减法、会员与任务呈现、次要入口收纳方式", "我的页 / 个人中心", keys)
    group_specs = [
        ("group-priority", "会员与任务形成一级对象", "比较会员和任务如何获得明确位置，同时避免只靠放大卡片", ["uinotes-bilibili", "uinotes-doubao"],
         "会员或任务拥有独立区域，并与通用入口区分", "用独立条带或任务卡建立层级",
         {"uinotes-bilibili": "会员条带与创作任务分区，说明两类对象可分层", "uinotes-doubao": "任务卡先于通用列表，任务对象清楚"},
         "不把含会员字样但页面主任务不同的样本自动纳入"),
        ("group-content", "首屏承接可继续内容", "比较常用内容动作如何在不扩大入口数量时保持可见", ["uinotes-kugou", "refero-airbuds"],
         "页面用最近内容、收藏或下载承接回访", "以内容对象替代泛化功能宫格",
         {"uinotes-kugou": "收藏、下载和最近播放同屏", "refero-airbuds": "最近播放与收藏紧随身份区"},
         "适用于内容续接，不等同于所有产品的常用功能"),
        ("group-containment", "次要服务收纳与密度上界", "用抽屉与高密度根层对照，判断哪些入口应留在首层", ["uinotes-douyu", "uinotes-pinduoduo"],
         "样本展示两种次要服务承载方式：抽屉收纳与根层铺开", "通过收纳与铺开对照首屏成本",
         {"uinotes-douyu": "服务抽屉把创作和推荐服务放在后续层级", "uinotes-pinduoduo": "订单、资产、服务和推荐全部铺开，形成密度上界"},
         "斗鱼是抽屉状态，拼多多是未登录根层；两者不是等价页面，只用于机制对照"),
    ]
    labels = labels_for(accepted, {"uinotes-douyu": {"page_role": "services_drawer", "path_stage": "personal_center_drawer", "interaction_stage": "drawer_open"},
                                            "uinotes-bilibili": {"version_status": "historical_version"},
                                            "uinotes-pinduoduo": {"login_state": "logged_out"},
                                            "uinotes-doubao": {"login_state": "logged_out"}, "uinotes-kugou": {"login_state": "logged_out"}})
    class_data = classification(group_specs, labels, "本次改版要解决的设计问题",
        "按会员/任务层级、内容续接和次要服务收纳三个问题归组；抽屉、未登录和历史版本作为状态标签保留。",
        "虎牙现状图只作为问题证据，不计入竞品；6 张竞品图均经过本轮来源复查和语义审核。")
    facts = {
        "uinotes-bilibili": (["会员条带位于身份区之后", "常用内容动作与创作任务分成两个区域"], ["历史版本，不能视为当前线上方案", "不能由位置推断高频"]),
        "uinotes-doubao": (["任务中心和金币商城是列表前的独立卡片", "设置类功能位于其后"], ["未登录状态，不能判断登录后个性化"]),
        "uinotes-kugou": (["收藏、下载与最近播放同屏", "通用入口数量较少"], ["未登录状态不能证明实际常用程度"]),
        "refero-airbuds": (["身份区后直接出现最近播放与收藏"], ["不能从排列推断转化或留存"]),
        "uinotes-douyu": (["服务抽屉覆盖在个人页上方", "创作和推荐服务集中在抽屉"], ["不是个人中心根层首屏，只能用于收纳机制参考"]),
        "uinotes-pinduoduo": (["订单、资产、服务和推荐内容连续铺开", "页面为未登录完整状态"], ["只作为密度上界，不能证明高密度更有效"]),
    }
    observations = {key: {"facts": value[0], "boundaries": value[1]} for key, value in facts.items()}
    comparisons = [
        {"id": "cmp-priority", "material_ids": ["mat-cap-uinotes-bilibili", "mat-cap-uinotes-doubao", "mat-cap-uinotes-kugou", "mat-cap-refero-airbuds"],
         "comparison_findings": ["会员/任务样本用独立条带或卡片，内容样本用可继续对象形成首屏焦点"],
         "design_judgment": "强化模块需要先说明用户要完成的任务，再决定条带、卡片或内容对象",
         "recommendation": "先建立模块职责和排序依据，再调整视觉面积", "applicability": "虎牙需要同时突出会员、任务和常用内容时",
         "tradeoffs": ["多个一级对象会重新造成首屏竞争"], "evidence_boundaries": ["截图不能证明哪些功能常用"]},
        {"id": "cmp-containment", "material_ids": ["mat-cap-uinotes-douyu", "mat-cap-uinotes-pinduoduo", "mat-cap-uinotes-bilibili"],
         "comparison_findings": ["抽屉可延后次要服务，高密度根层则保留更强发现性但增加浏览成本"],
         "design_judgment": "收起其他功能是层级决策，需要保留清楚入口和可恢复路径",
         "recommendation": "把低优先级服务放入稳定的二级容器，并在根层保留入口", "applicability": "次要入口多且根层空间有限时",
         "tradeoffs": ["收纳会降低次要服务的直接可见性"], "evidence_boundaries": ["没有使用数据，不能判定具体入口应被收起"]},
    ]
    def inf(statement, refs, proc, rec, app, limit="静态截图不能证明使用频率或业务效果"):
        return (statement, refs, proc, "inference", rec, app, limit)
    group_analysis = {
        "group-priority": inf("会员和任务可以分别形成一级对象；关键是职责分开，避免两个大卡片继续争抢同一首屏。", [("group", "group-priority")], ["cmp-priority"], "分别定义会员权益入口与任务进度入口", "两者都有明确独立任务时"),
        "group-content": inf("常用功能若本质是继续内容，可直接展示最近对象，减少先点入口再找内容的层级。", [("group", "group-content")], ["cmp-priority"], "用最近内容或收藏对象承接回访", "虎牙有可靠的最近观看或关注内容时"),
        "group-containment": inf("抽屉适合收纳次要服务，但根层必须保留稳定入口；拼多多只作为全部铺开的密度反例。", [("group", "group-containment")], ["cmp-containment"], "用二级容器收纳并保留可预期入口", "已用数据确认哪些服务可降级后"),
    }
    material_insights = {key: inf(text, [("material", "mat-cap-" + key)], ["obs-" + key], rec, app, observations[key]["boundaries"][0]) for key, text, rec, app in [
        ("uinotes-bilibili", "会员条带与创作任务分区，适合参考两类一级对象如何避免混成一个服务宫格。", "分开会员权益与任务进度", "虎牙两类业务都要保留一级入口时"),
        ("uinotes-doubao", "任务卡先于通用列表，适合参考任务对象如何获得独立层级。", "让任务卡说明进度或收益对象", "任务中心是明确回访任务时"),
        ("uinotes-kugou", "收藏、下载和最近播放直接承接内容回访，可作为常用内容的减法方案。", "优先展示可继续的内容", "有稳定最近内容数据时"),
        ("refero-airbuds", "最近播放与收藏紧随身份区，适合身份与内容连续的个人页。", "缩短身份到个人内容的距离", "个人内容能表达用户身份时"),
        ("uinotes-douyu", "抽屉集中次要服务，可参考收纳容器；它不是根层首屏，不能直接照搬排序。", "保留明确的更多入口并维护返回路径", "次要服务已由数据确认后"),
        ("uinotes-pinduoduo", "多类入口全部铺开形成密度上界，可用于检查虎牙是否仍把过多服务留在首层。", "把它作为反例清单逐项删减", "评审首屏信息量时"),
    ]}
    current_source = Path("reports/manual-acceptance/v0.1-user-tests-2026-10-26/detailed-my-page-redesign/assets/huya-current.png")
    current_target = ROOT / "scenario-b-redesign" / "input" / "huya-current.png"
    current_target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(current_source, current_target)
    current = {
        "state": {"id": "current-huya", "description": "用户提供的虎牙‘我的’页归档现状图，作为本轮明确输入基线；不计入竞品数量。",
                  "images": [{"id": "current-huya-image", "image_path": "huya-current.png", "caption": "虎牙现状图（用户测试归档输入）"}],
                  "regions": [
                      {"id": "current-huya-membership", "image_id": "current-huya-image", "label": "身份与会员区", "visible_fact": "身份、贵族/守护/会员等业务入口在上半区并列出现"},
                      {"id": "current-huya-actions", "image_id": "current-huya-image", "label": "常用动作区", "visible_fact": "观看记录、关注和任务等动作分散在多个模块"},
                      {"id": "current-huya-services", "image_id": "current-huya-image", "label": "更多服务区", "visible_fact": "页面下方连续铺开多组服务入口"},
                  ]},
        "process": {"id": "current-analysis", "user_provided_facts": ["用户目标是简化布局、突出常用功能、强化会员与任务中心并收起其他功能"],
                    "goal_relationship": "现状中多个业务入口和服务组同时竞争首屏，需要先定义一级任务与收纳边界。",
                    "inferences": ["会员、任务、常用内容应按任务职责分层", "次要服务可进入稳定二级容器"],
                    "reference_claim_ids": ["takeaway-group-priority", "takeaway-group-containment"],
                    "evidence_boundaries": ["没有虎牙使用数据，不能据此判定具体功能高频或低频", "不同会员业务是否合并需要业务关系验证"]},
        "findings": [
            ("现状上半区同时承载身份、多个会员相关业务与常用动作，改版应先明确各模块职责，再决定视觉权重。", [("current_state", "current-huya-membership"), ("current_state", "current-huya-actions")], ["current-analysis"], "observation"),
            ("下方服务入口连续铺开，与‘其他功能收起来’的目标直接相关；具体收起对象仍需使用数据确认。", [("current_state", "current-huya-services")], ["current-analysis"], "observation"),
        ],
    }
    analysis_data = make_analysis(
        "虎牙‘我的’页改版参考：先分任务，再做首屏减法", {"question": "怎样在虎牙现状上简化首屏，同时突出常用内容、会员和任务中心？", "scope": "用户提供现状图与 6 张本轮审核竞品；包含根层、未登录和服务抽屉状态", "goals": ["建立会员与任务的清楚层级", "收纳次要服务", "保留内容回访路径"], "constraints": ["现状图不计入竞品", "没有使用数据，不判定功能高低频"]},
        group_analysis, observations, comparisons, material_insights,
        inf("先把首屏拆成会员权益、任务进度和可继续内容三个职责，再把其余服务收进稳定二级容器；视觉放大应发生在职责确认之后。", [("material", "mat-cap-uinotes-bilibili"), ("material", "mat-cap-uinotes-doubao"), ("material", "mat-cap-uinotes-kugou"), ("material", "mat-cap-uinotes-douyu")], ["cmp-priority", "cmp-containment"], "先用业务与使用数据确认三个一级职责，再进入视觉方案", "虎牙本次改版目标"),
        [inf("会员与任务适合分成两个一级对象：前者说明权益身份，后者说明可执行进度，避免合并成含义模糊的大卡片。", [("material", "mat-cap-uinotes-bilibili"), ("material", "mat-cap-uinotes-doubao")], ["cmp-priority"], "分别定义信息和主动作", "两类业务都有独立用户任务时"),
         inf("常用功能若是继续观看、收藏或关注内容，可以用对象本身替代一排通用图标。", [("material", "mat-cap-uinotes-kugou"), ("material", "mat-cap-refero-airbuds")], ["cmp-priority"], "优先验证最近内容模块", "内容回访占主要使用场景时")],
        [inf("建议顺序是：先用数据确认常用任务；再拆分会员与任务模块职责；随后确定最近内容是否进首屏；最后把其余服务收进一个可预期入口。", [("group", "group-priority"), ("group", "group-content"), ("group", "group-containment")], ["cmp-priority", "cmp-containment"], "按顺序完成信息架构决策", "进入线框图前"),
         inf("斗鱼抽屉提供收纳机制，拼多多提供密度上界；两者用于边界判断，不应直接成为虎牙的成品布局。", [("material", "mat-cap-uinotes-douyu"), ("material", "mat-cap-uinotes-pinduoduo")], ["cmp-containment"], "把机制和页面状态写入方案依据", "评审次要服务收纳时")],
        [("虎牙各入口的使用率、任务完成率和业务优先级如何？", [("current_state", "current-huya-actions")], ["current-analysis"]),
         ("贵族、守护、平台会员在用户心智和权益上是否应合并？", [("current_state", "current-huya-membership")], ["current-analysis"]),
         ("服务抽屉的入口名称和返回路径能否被目标用户理解？", [("material", "mat-cap-uinotes-douyu")], ["cmp-containment"])],
        [{"section": "使用数据", "status": "not_provided", "reason": "缺少虎牙真实入口使用与任务数据，不能判定具体功能高频或低频。"},
         {"section": "业务关系", "status": "unknown", "reason": "贵族、守护和平台会员的业务关系需由产品侧确认。"},
         {"section": "版本", "status": "unknown", "reason": "部分来源没有当前版本时间，哔哩哔哩明确标记为历史版本。"}], current=current,
    )
    write_scenario("scenario-b-redesign", task_data, source_registry("我的页 / 个人中心", keys, ["uinotes", "refero", "mobbin", "pttrns"]),
                   captures("我的页 / 个人中心", keys), reviews("我的页 / 个人中心", keys, accepted), class_data, analysis_data)


def settings_validation():
    keys = ["refero-duolingo-settings"]
    task_data = task("小范围验证：搜集一个移动 App 设置页，确认流程没有写死为个人中心或虎牙。", "验证通用任务、分类、分析与报告入口", "设置页", keys)
    groups = [("group-settings", "账户设置根层", "检查设置页如何组织账户与偏好入口", keys,
               "页面标题与条目均指向设置根层", "用分区列表组织账户与偏好",
               {"refero-duolingo-settings": "标题与列表共同确认设置页角色"}, "不与本人资料页或公开主页混淆")]
    labels = labels_for(keys, {"refero-duolingo-settings": {"page_role": "settings_root"}})
    class_data = classification(groups, labels, "设置任务的分区方式", "按设置页的主要管理任务组织，不复用个人中心分类。", "单张设置页小范围通用性验证。")
    observations = {"refero-duolingo-settings": {"facts": ["设置标题可见", "账户和偏好条目使用分区列表"], "boundaries": ["单张样本不能形成横向规律"]}}
    def inf(statement, refs, proc, rec, app, limit="单张截图只能验证当前可见结构"):
        return (statement, refs, proc, "inference", rec, app, limit)
    analysis_data = make_analysis(
        "设置页通用能力小范围验证", {"question": "正式流程能否处理非个人中心目标页？", "scope": "1 张 Duolingo 设置页，只验证通用契约与渲染", "goals": ["检查规则未写死为个人中心"], "constraints": ["单张样本不输出横向规律"]},
        {"group-settings": inf("设置页的参考重点是管理任务的分区与命名，而不是身份或内容模块。", [("group", "group-settings")], ["obs-refero-duolingo-settings"], "按账户、通知和偏好等任务分区", "设置项数量较多时")},
        observations, [],
        {"refero-duolingo-settings": inf("分区列表让账户与偏好保持可扫描，适合作为设置根层的基础结构。", [("material", "mat-cap-refero-duolingo-settings")], ["obs-refero-duolingo-settings"], "先建立设置任务分区", "存在多类设置项时")},
        inf("同一正式入口可以把 Refero 候选在‘我的页’研究中拒绝、在‘设置页’研究中接受，说明语义判断跟随研究目标。", [("material", "mat-cap-refero-duolingo-settings")], ["obs-refero-duolingo-settings"], "每次按目标页重新审核候选", "研究目标变化时"),
        [],
        [inf("本次只证明设置页可进入通用结构；若要形成设计建议，需要增加其他设置页做横向比较。", [("material", "mat-cap-refero-duolingo-settings")], ["obs-refero-duolingo-settings"], "补充不同设置结构后再总结模式", "后续开展设置页专项研究时")],
        [("其他设置页采用列表、搜索或二级导航时有何差异？", [("material", "mat-cap-refero-duolingo-settings")], ["obs-refero-duolingo-settings"])],
        [{"section": "样本规模", "status": "not_applicable", "reason": "这是通用能力小范围验证，不承担完整竞品研究结论。"}],
    )
    write_scenario("generic-settings-validation", task_data, source_registry("设置页", keys, ["refero"]),
                   captures("设置页", keys), reviews("设置页", keys, set(keys)), class_data, analysis_data)


def write_access_evidence():
    dump(ROOT / "source-access-observation.json", {
        "evidence_type": "real_browser_observation", "observed_at": "2026-10-27T21:30:00+08:00",
        "browser": "Google Chrome profile 用户1", "session_id": "chrome-user1",
        "checks": list(CHECKS.values()),
        "interpretation": {
            "user_choice_required": False,
            "reason": "限制未实质影响本批覆盖；UI Notes 与 Refero 当前可见范围产生 14 个可审核候选，9 个通过场景 A 审核。",
            "subscription_note": "登录不能自动解除 UI Notes、Refero、Mobbin 的付费范围；本轮未购买订阅。",
            "app_login_note": "来源网站会话与截图内 App 登录状态分开记录。",
        },
        "security": "未保存 cookie、密码、验证码或会话凭据。",
    })
    (ROOT / "source-access-observation.md").write_text(
        "# 真实来源访问准备\n\n"
        "2026-10-27 在后续实际搜集使用的 Chrome 用户1会话中复查。UI Notes、Refero、Mobbin 均为已有账号会话；"
        "前两者可打开当前可见结果、详情和图像，Mobbin 详情可开但原图下载受 Pro 限制。PTTRNS 新标签和详情需要登录。\n\n"
        "本轮没有触发 A/B 选择：PTTRNS 的登录限制对覆盖影响为 minor，三个已登录来源的可见范围已提供足够的中外候选；"
        "登录也不能解除另外三个来源的订阅限制。继续使用当前公开/账号可见范围，未购买订阅。\n\n"
        "完整能力项、标签 ID、会话标签和覆盖影响见 `source-access-observation.json`。来源网站会话与截图内 App 登录状态分别记录。\n",
        encoding="utf-8",
    )


def write_asset_manifest():
    rows = []
    for path in sorted(RAW.rglob("*")):
        if not path.is_file():
            continue
        with Image.open(path) as image:
            rows.append({
                "path": path.relative_to(ROOT).as_posix(), "width": image.width, "height": image.height,
                "format": image.format, "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "evidence_type": "real_source_asset_downloaded_from_rendered_detail",
            })
    dump(ROOT / "raw-asset-manifest.json", {"generated_at": CAPTURED_AT, "assets": rows})


if __name__ == "__main__":
    scenario_a()
    scenario_b()
    settings_validation()
    write_access_evidence()
    write_asset_manifest()
