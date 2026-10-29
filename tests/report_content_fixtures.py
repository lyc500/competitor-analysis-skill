"""Synthetic report content; never third-party collection evidence."""
import json
from pathlib import Path


def claim(cid, text, refs=None, **extra):
    return {"id": cid, "kind": "inference", "statement": text,
            "evidence_refs": refs or [{"kind": "material", "id": "mat-a"}], **extra}


def analysis(with_current=False):
    value = {
        "schema_version": 1,
        "title": "入口层级比较",
        "research": {"question": "怎样减少查找层级？", "scope": "两个完整目标页面", "goals": [], "constraints": []},
        "overall": claim("overall", "将主要操作与辅助入口分层"),
        "key_findings": [claim("finding", "主要操作集中于内容之前", kind="observation")],
        "groups": [{"group_id": "group-main", "takeaway": claim("group-takeaway", "一排主操作便于与辅助列表区分", [{"kind": "group", "id": "group-main"}])}],
        "materials": [{"material_id": "mat-a", "insight": claim("material-focus", "主操作独立成行", recommendation="优先保留与当前任务有关的操作", applicability="目标操作数量较少时", limitations="实际排序仍需访问数据")}],
        "synthesis": {"findings": [claim("summary", "先确定主操作，再决定辅助入口位置")],
                      "validation_questions": [claim("check", "哪些入口实际使用更频繁？")]},
        "information_gaps": [],
        "coverage_assessment": {
            "status": "limited", "summary": "当前只有一个独立案例，只能作为方向参考",
            "research_question": "怎样减少查找层级？",
            "questions": [{"id": "q-layer", "question": "主要操作与辅助入口如何分层",
                           "material_ids": ["mat-a"], "comparison_ids": [],
                           "strategies": ["主要操作独立成行"], "status": "single_case"}],
            "gaps": [{"reason": "discovery_insufficient", "detail": "缺少第二个独立案例",
                      "question_ids": ["q-layer"], "source_attempt_ids": []}],
            "user_decision": {"status": "not_required", "research_question": "怎样减少查找层级？",
                              "provenance": "not_required"},
        },
    }
    if with_current:
        value["current_state"] = {
            "id": "current", "description": "用户提供的现状说明：入口并列",
            "images": [{"id": "current-image", "image_path": "current.png", "caption": "用户现状"}],
            "findings": [claim("current-finding", "现状入口缺少分层", [{"kind": "current_state", "id": "current"}], kind="observation")],
        }
    return value


def classification_v2(ids=("mat-a",), name="主操作成行"):
    return {
        "schema_version": 2,
        "classification_dimension": "本次设计问题",
        "classification_reason": "先按要解决的问题归组，再保留路径与状态标签",
        "comparison_basis": {
            "primary_dimension": "主要操作与辅助入口的组织机制",
            "rationale": "本次研究需要比较操作层级，而不是按产品行业分桶",
            "scope": "只比较已审核的完整目标页面",
        },
        "groups": [{
            "id": "group-main", "name": name, "reason": "共同采用主操作独立成行的机制",
            "material_ids": list(ids),
            "audit": {
                "inclusion_criteria": "页面把主要操作从辅助入口中独立出来",
                "shared_mechanism": "用独立横排表达当前任务的主要操作",
                "member_reasons": [{"material_id": mid, "reason": "可见主要操作与辅助入口分层"} for mid in ids],
                "adjacent_difference": "不包含只按行业或登录状态相同、但主任务不同的页面",
            },
        }],
        "material_labels": [{"material_id": mid, "labels": {
            "page_role": "target_page", "path_stage": "root", "interaction_stage": "browse_before_action",
            "render_state": "loaded_complete", "login_state": "logged_in",
        }} for mid in ids],
    }


def analysis_v2(with_current=False):
    def v2claim(cid, text, refs=None, process=("obs-a",), kind="inference", **extra):
        value = claim(cid, text, refs, kind=kind, analysis_refs=list(process), **extra)
        if kind == "inference":
            value.setdefault("recommendation", "按当前研究目标选择该做法")
            value.setdefault("applicability", "可见任务和页面状态与证据一致时")
            value.setdefault("limitations", "静态截图不能证明使用频率或行为效果")
        return value

    value = {
        "schema_version": 2,
        "title": "入口层级比较",
        "research": {"question": "怎样减少查找层级？", "scope": "一个完整目标页面", "goals": [], "constraints": []},
        "analysis_process": {
            "material_observations": [{
                "id": "obs-a", "material_id": "mat-a",
                "visible_facts": ["主要操作独立成行，辅助入口位于其后"],
                "evidence_boundaries": ["截图只能证明当前可见结构"],
            }],
            "comparisons": [],
        },
        "overall": v2claim("overall", "主要操作独立成行，适合先处理当前任务再浏览辅助入口"),
        "key_findings": [v2claim("finding", "主要操作位于辅助入口之前", kind="observation")],
        "groups": [{"group_id": "group-main", "takeaway": v2claim(
            "group-takeaway", "重点比较主操作是否与当前任务一致，而不是比较入口数量",
            [{"kind": "group", "id": "group-main"}])}],
        "materials": [{"material_id": "mat-a", "insight": v2claim(
            "material-focus", "主操作独立成行，可用于验证当前任务是否需要一级入口") }],
        "synthesis": {
            "findings": [v2claim("summary", "先确认主任务，再决定哪些入口保留在首层")],
            "validation_questions": [v2claim("check", "哪些入口在目标任务中实际被使用？", kind="question")],
        },
        "information_gaps": [],
        "coverage_assessment": {
            "status": "limited", "summary": "当前只有一个独立案例，只能作为方向参考",
            "research_question": "怎样减少查找层级？",
            "questions": [{"id": "q-layer", "question": "主要操作与辅助入口如何分层",
                           "material_ids": ["mat-a"], "comparison_ids": [],
                           "strategies": ["主要操作独立成行"], "status": "single_case"}],
            "gaps": [{"reason": "discovery_insufficient", "detail": "缺少第二个独立案例",
                      "question_ids": ["q-layer"], "source_attempt_ids": []}],
            "user_decision": {"status": "not_required", "research_question": "怎样减少查找层级？",
                              "provenance": "not_required"},
        },
    }
    if with_current:
        value["current_state"] = {
            "id": "current", "description": "用户提供的现状说明：入口并列",
            "images": [{"id": "current-image", "image_path": "current.png", "caption": "用户现状"}],
            "regions": [{"id": "current-actions", "image_id": "current-image", "label": "功能入口区",
                         "visible_fact": "多个入口以相同尺寸连续排列"}],
            "findings": [v2claim("current-finding", "现状没有区分本次目标与辅助入口",
                                 [{"kind": "current_state", "id": "current-actions"}],
                                 process=("current-analysis",))],
        }
        value["analysis_process"]["current_state"] = {
            "id": "current-analysis",
            "user_provided_facts": ["用户希望减少辅助入口对主要任务的干扰"],
            "goal_relationship": "入口同权会削弱本次需要突出的主要任务",
            "inferences": ["可先按本次目标区分主要操作和辅助入口"],
            "reference_claim_ids": ["material-focus"],
            "evidence_boundaries": ["没有访问频率数据，不能据此判断入口高频或低频"],
        }
    claim_ids = ["overall", "finding", "group-takeaway", "material-focus", "summary", "check"]
    if with_current:
        claim_ids.append("current-finding")
    value["quality_review"] = {
        "review_type": "agent_self_review", "independent": False,
        "reviewed_claim_ids": claim_ids,
        "checks": {key: True for key in (
            "evidence_supported", "reference_value_clear", "research_relevant",
            "exceptions_considered", "duplicates_resolved", "generic_claims_removed")},
        "edits": [],
        "notes": ["该记录只证明完成 Agent 人工复核，不是独立质量验证"],
    }
    return value


def inputs(root):
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    image = (Path(__file__).parent / "fixtures/materials/valid.png").read_bytes()
    (root / "a.png").write_bytes(image)
    (root / "current.png").write_bytes(image)
    task = {"raw_request": "比较入口", "research_goal": "用户原始长需求不应冒充结论", "target_page": "功能页",
            "regions": ["CN"], "specified_products": ["产品A"], "assumptions": [], "needs_clarification": False,
            "task_status": "ready", "planning_strategy": "user_only", "competitors": [
                {"product_name": "产品A", "region": "CN", "product_type": "工具", "platform": "Web",
                 "target_page": "功能页", "planning_source": "user_specified", "priority": "high", "reason": "指定"}]}
    material = {"id": "mat-a", "product_name": "产品A", "page_name": "功能页", "image_path": "a.png",
                "source_type": "user_upload", "collection_method": "user_provided", "provenance": "user_upload",
                "collection_status": "collected", "semantic_status": "accepted", "quality_status": "accepted",
                "semantic_reason": "语义审核依据", "quality_reason": "机械质量依据", "notes": "历史与版本说明",
                "region": "CN", "product_type": "工具", "platform": "Web", "source_url": ""}
    classification = {"classification_dimension": "操作层级", "classification_reason": "审核维度解释",
                      "groups": [{"id": "group-main", "name": "主操作成行", "reason": "归组审核理由，不是读者结论", "material_ids": ["mat-a"]}],
                      "material_labels": [{"material_id": "mat-a", "labels": {"state": "loaded"}}]}
    files = {"task": task, "reviewed": {"task": task, "materials": [material], "fallback_requests": []},
             "classification": classification, "analysis": analysis_v2(),
             "snapshot": {"task": task, "materials": [material], "classification": classification, "fallback_requests": []}}
    for name, data in files.items():
        (root / (name + ".json")).write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return files
