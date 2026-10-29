"""Agent-authored report content. Validate shape and references, never meaning."""
from copy import deepcopy


class AnalysisError(ValueError):
    pass


def _object(value, allowed, field, required=()):
    if not isinstance(value, dict):
        raise AnalysisError(f"{field} 必须是对象")
    if set(value) - set(allowed):
        raise AnalysisError(f"{field} 包含未知字段: {', '.join(sorted(set(value) - set(allowed)))}")
    if set(required) - set(value):
        raise AnalysisError(f"{field} 缺少字段: {', '.join(sorted(set(required) - set(value)))}")


def _text(value, field):
    if not isinstance(value, str) or not value.strip():
        raise AnalysisError(f"{field} 必须是非空字符串")


def _array(value, field):
    if not isinstance(value, list):
        raise AnalysisError(f"{field} 必须是数组")
    return value


def _text_array(value, field, required=False):
    items = _array(value, field)
    if required and not items:
        raise AnalysisError(f"{field} 不得为空")
    for item in items:
        _text(item, f"{field}[]")
    return items


def validate_analysis(value, materials, classification, require_detailed_coverage=False):
    """Return a deep copy; absent fields stay absent (no invented analysis)."""
    if not isinstance(value, dict):
        raise AnalysisError("analysis 必须是对象")
    version = value.get("schema_version")
    if type(version) is not int or version not in (1, 2):
        raise AnalysisError("analysis.schema_version 只支持 1 或 2")
    allowed = {"schema_version", "title", "research", "overall", "key_findings", "current_state",
               "groups", "materials", "synthesis", "information_gaps", "methodology", "coverage_assessment"}
    required = {"schema_version", "title", "research"}
    if version == 2:
        allowed |= {"analysis_process", "quality_review"}
        required |= {"analysis_process", "quality_review", "coverage_assessment", "overall", "groups", "materials", "synthesis"}
    _object(value, allowed, "analysis", required)
    _text(value["title"], "analysis.title")
    research = value["research"]
    _object(research, {"question", "scope", "goals", "constraints"}, "research", {"question", "scope"})
    for field in ("question", "scope"):
        _text(research[field], f"research.{field}")
    for field in ("goals", "constraints"):
        for item in _array(research.get(field, []), f"research.{field}"):
            _text(item, f"research.{field}")

    coverage = value.get("coverage_assessment")
    if coverage is not None:
        _object(coverage, {"status", "summary", "covered_questions", "questions", "gaps", "user_decision",
                           "research_question"},
                "coverage_assessment", {"status", "summary", "gaps", "user_decision"})
        if coverage["status"] not in ("sufficient", "limited", "insufficient"):
            raise AnalysisError("coverage_assessment.status 无效")
        decision = coverage["user_decision"]
        if isinstance(decision, dict):
            _object(decision, {"status", "research_question", "provenance"}, "coverage_assessment.user_decision",
                    {"status", "research_question", "provenance"})
            decision_status = decision["status"]
            _text(decision["research_question"], "coverage_assessment.user_decision.research_question")
            if decision["provenance"] not in ("not_required", "user_explicit"):
                raise AnalysisError("coverage_assessment.user_decision.provenance 无效")
        else:
            decision_status = decision
        if decision_status not in ("not_required", "continue_limited", "supplement_sources", "pending"):
            raise AnalysisError("coverage_assessment.user_decision 无效")
        _text(coverage["summary"], "coverage_assessment.summary")
        if "covered_questions" in coverage:
            _text_array(coverage["covered_questions"], "coverage_assessment.covered_questions", required=True)
        if not isinstance(coverage["gaps"], list):
            raise AnalysisError("coverage_assessment.gaps 必须是数组")
        if coverage["status"] in ("limited", "insufficient") and not coverage["gaps"]:
            raise AnalysisError("覆盖有限或不足时必须记录缺口")
        if coverage["status"] == "sufficient" and decision_status != "not_required":
            raise AnalysisError("覆盖充分时不应要求用户选择")
        if coverage["status"] == "insufficient" and decision_status in ("pending", "not_required"):
            raise AnalysisError("样本不足时必须记录用户选择继续小样本分析或补充来源")
        if require_detailed_coverage and not {"research_question", "questions"} <= set(coverage):
            raise AnalysisError("正式分析必须提供与本次研究问题关联的详细覆盖评估")
        if require_detailed_coverage and not isinstance(decision, dict):
            raise AnalysisError("正式分析必须记录与本次研究问题绑定的覆盖选择")
        if require_detailed_coverage and decision["research_question"] != value["research"]["question"]:
            raise AnalysisError("覆盖选择与本次研究问题不一致")
        if require_detailed_coverage and coverage["research_question"] != value["research"]["question"]:
            raise AnalysisError("覆盖评估与本次研究问题不一致")
        if require_detailed_coverage and coverage["status"] == "insufficient" and decision["provenance"] != "user_explicit":
            raise AnalysisError("样本不足时必须保存本次用户的明确选择")

    material_ids = {m["id"] for m in materials if m.get("collection_status") == "collected"
                    and m.get("semantic_status") == "accepted" and m.get("quality_status") == "accepted"
                    and m.get("image_path")}
    groups = {g["id"]: set(g["material_ids"]) for g in classification.get("groups", [])}
    current_ids = set()
    current = value.get("current_state")
    if "current_state" in value:
        current_allowed = {"id", "description", "images", "findings"}
        if version == 2:
            current_allowed.add("regions")
        _object(current, current_allowed, "current_state", {"id"})
        _text(current["id"], "current_state.id")
        current_ids.add(current["id"])
        if "description" in current:
            _text(current["description"], "current_state.description")
        images = _array(current.get("images", []), "current_state.images")
        if not images and not current.get("description"):
            raise AnalysisError("现状必须包含用户说明或现状图证据")
        image_ids = set()
        for item in images:
            _object(item, {"id", "image_path", "caption"}, "current_state.images[]", {"id", "image_path", "caption"})
            for field in ("id", "image_path", "caption"):
                _text(item[field], f"current_state.images[].{field}")
            if item["id"] in current_ids:
                raise AnalysisError("现状证据 ID 重复")
            current_ids.add(item["id"])
            image_ids.add(item["id"])
        if version == 2:
            regions = _array(current.get("regions", []), "current_state.regions")
            if images and not regions:
                raise AnalysisError("有现状图时必须标出具体问题区域")
            for item in regions:
                _object(item, {"id", "image_id", "label", "visible_fact"}, "current_state.regions[]",
                        {"id", "image_id", "label", "visible_fact"})
                for field in ("id", "image_id", "label", "visible_fact"):
                    _text(item[field], f"current_state.regions[].{field}")
                if item["image_id"] not in image_ids:
                    raise AnalysisError("现状问题区域引用不存在的现状图")
                if item["id"] in current_ids:
                    raise AnalysisError("现状证据 ID 重复")
                current_ids.add(item["id"])

    process_ids = set()
    process_materials = {}
    current_process = None
    if version == 2:
        process = value["analysis_process"]
        _object(process, {"material_observations", "comparisons", "current_state"}, "analysis_process",
                {"material_observations", "comparisons"})
        observations = _array(process["material_observations"], "analysis_process.material_observations")
        observed_materials = set()
        for index, item in enumerate(observations):
            field = f"analysis_process.material_observations[{index}]"
            _object(item, {"id", "material_id", "visible_facts", "evidence_boundaries"}, field,
                    {"id", "material_id", "visible_facts", "evidence_boundaries"})
            _text(item["id"], field+".id"); _text(item["material_id"], field+".material_id")
            if item["id"] in process_ids:
                raise AnalysisError("分析过程 ID 重复")
            process_ids.add(item["id"])
            if item["material_id"] not in material_ids or item["material_id"] in observed_materials:
                raise AnalysisError("逐图观察必须恰好对应一张有效素材")
            observed_materials.add(item["material_id"])
            process_materials[item["id"]] = {item["material_id"]}
            _text_array(item["visible_facts"], field+".visible_facts", required=True)
            _text_array(item["evidence_boundaries"], field+".evidence_boundaries", required=True)
        if observed_materials != material_ids:
            raise AnalysisError("逐图观察必须恰好覆盖全部有效素材")

        comparisons = _array(process["comparisons"], "analysis_process.comparisons")
        compared_materials = set()
        for index, item in enumerate(comparisons):
            field = f"analysis_process.comparisons[{index}]"
            _object(item, {"id", "material_ids", "comparison_findings", "design_judgment", "recommendation",
                           "applicability", "tradeoffs", "evidence_boundaries"}, field,
                    {"id", "material_ids", "comparison_findings", "design_judgment", "recommendation",
                     "applicability", "tradeoffs", "evidence_boundaries"})
            _text(item["id"], field+".id")
            if item["id"] in process_ids:
                raise AnalysisError("分析过程 ID 重复")
            process_ids.add(item["id"])
            members = _array(item["material_ids"], field+".material_ids")
            if len(members) < 2 or len(set(members)) != len(members) or not set(members) <= material_ids:
                raise AnalysisError("横向比较必须引用至少两张不同的有效素材")
            compared_materials.update(members)
            process_materials[item["id"]] = set(members)
            _text_array(item["comparison_findings"], field+".comparison_findings", required=True)
            for key in ("design_judgment", "recommendation", "applicability"):
                _text(item[key], field+"."+key)
            _text_array(item["tradeoffs"], field+".tradeoffs", required=True)
            _text_array(item["evidence_boundaries"], field+".evidence_boundaries", required=True)
        if len(material_ids) > 1 and compared_materials != material_ids:
            raise AnalysisError("横向比较必须覆盖全部有效素材；例外也需进入比较记录")
        if len(material_ids) <= 1 and comparisons:
            raise AnalysisError("单张素材不能伪造横向比较")

        if coverage and "questions" in coverage:
            question_ids = set()
            question_statuses = []
            product_by_material = {m["id"]: m.get("product_name", m["id"]) for m in materials}
            comparison_ids = {item["id"] for item in comparisons}
            for index, item in enumerate(_array(coverage["questions"], "coverage_assessment.questions")):
                field = f"coverage_assessment.questions[{index}]"
                _object(item, {"id", "question", "material_ids", "comparison_ids", "strategies", "status"}, field,
                        {"id", "question", "material_ids", "comparison_ids", "strategies", "status"})
                _text(item["id"], field+".id"); _text(item["question"], field+".question")
                if item["id"] in question_ids:
                    raise AnalysisError("覆盖问题 ID 重复")
                question_ids.add(item["id"])
                mids = _text_array(item["material_ids"], field+".material_ids")
                if len(set(mids)) != len(mids) or not set(mids) <= material_ids:
                    raise AnalysisError("覆盖问题引用不存在或重复的素材")
                cids = _text_array(item["comparison_ids"], field+".comparison_ids")
                if len(set(cids)) != len(cids) or not set(cids) <= comparison_ids:
                    raise AnalysisError("覆盖问题引用不存在或重复的横向比较")
                _text_array(item["strategies"], field+".strategies")
                if item["status"] not in ("comparable", "single_case", "missing"):
                    raise AnalysisError("覆盖问题 status 无效")
                independent = len({product_by_material[mid] for mid in mids})
                if item["status"] == "comparable" and (independent < 2 or not cids):
                    raise AnalysisError("可比较问题必须有至少两个独立产品案例及横向比较")
                if item["status"] == "single_case" and independent != 1:
                    raise AnalysisError("单案例问题必须只引用一个独立产品案例")
                if item["status"] == "missing" and mids:
                    raise AnalysisError("缺失问题不得引用素材")
                question_statuses.append(item["status"])
            if require_detailed_coverage and not question_statuses:
                raise AnalysisError("正式分析至少需要一个核心覆盖问题")
            if coverage["status"] == "sufficient" and any(s != "comparable" for s in question_statuses):
                raise AnalysisError("覆盖充分时每个核心问题都必须有可比较证据")
            if coverage["status"] == "insufficient" and all(s != "missing" for s in question_statuses):
                raise AnalysisError("覆盖不足必须对应至少一个缺少证据的核心问题")
            allowed_reasons = {"permission_restricted", "subscription_restricted", "discovery_insufficient",
                               "pending_review", "quality_rejected", "semantic_rejected", "scope_imbalance",
                               "evidence_boundary", "other"}
            for index, gap in enumerate(coverage["gaps"]):
                field = f"coverage_assessment.gaps[{index}]"
                if isinstance(gap, str):
                    if require_detailed_coverage:
                        raise AnalysisError("正式分析的覆盖缺口必须区分原因")
                    _text(gap, field)
                    continue
                _object(gap, {"reason", "detail", "question_ids", "source_attempt_ids"}, field,
                        {"reason", "detail", "question_ids", "source_attempt_ids"})
                if gap["reason"] not in allowed_reasons:
                    raise AnalysisError("覆盖缺口 reason 无效")
                _text(gap["detail"], field+".detail")
                qids = _text_array(gap["question_ids"], field+".question_ids")
                if not set(qids) <= question_ids:
                    raise AnalysisError("覆盖缺口引用不存在的核心问题")
                _text_array(gap["source_attempt_ids"], field+".source_attempt_ids")

        current_process = process.get("current_state")
        if current:
            _object(current_process, {"id", "user_provided_facts", "goal_relationship", "inferences",
                                      "reference_claim_ids", "evidence_boundaries"}, "analysis_process.current_state",
                    {"id", "user_provided_facts", "goal_relationship", "inferences",
                     "reference_claim_ids", "evidence_boundaries"})
            _text(current_process["id"], "analysis_process.current_state.id")
            if current_process["id"] in process_ids:
                raise AnalysisError("分析过程 ID 重复")
            process_ids.add(current_process["id"])
            process_materials[current_process["id"]] = set()
            _text_array(current_process["user_provided_facts"], "analysis_process.current_state.user_provided_facts")
            _text(current_process["goal_relationship"], "analysis_process.current_state.goal_relationship")
            _text_array(current_process["inferences"], "analysis_process.current_state.inferences", required=True)
            if not current_process["reference_claim_ids"]:
                raise AnalysisError("现状分析必须关联至少一条有竞品素材支撑的结论")
            _text_array(current_process["reference_claim_ids"], "analysis_process.current_state.reference_claim_ids")
            _text_array(current_process["evidence_boundaries"], "analysis_process.current_state.evidence_boundaries", required=True)
        elif current_process is not None:
            raise AnalysisError("没有现状时不得提供现状分析过程")

    available = {"material": material_ids,
                 "group": {gid for gid, members in groups.items() if members & material_ids},
                 "current_state": current_ids}
    claim_ids = set()
    claim_evidence = {}

    def check_claim(claim, field):
        claim_allowed = {"id", "kind", "statement", "evidence_refs", "recommendation", "applicability", "limitations"}
        claim_required = {"id", "kind", "statement", "evidence_refs"}
        if version == 2:
            claim_allowed.add("analysis_refs"); claim_required.add("analysis_refs")
        _object(claim, claim_allowed, field, claim_required)
        for key in ("id", "statement", "recommendation", "applicability", "limitations"):
            if key in claim:
                _text(claim[key], f"{field}.{key}")
        if claim["kind"] not in ("observation", "inference", "question"):
            raise AnalysisError(f"{field}.kind 无效")
        if claim["id"] in claim_ids:
            raise AnalysisError(f"结论 ID 重复: {claim['id']}")
        claim_ids.add(claim["id"])
        refs = _array(claim["evidence_refs"], f"{field}.evidence_refs")
        if not refs:
            raise AnalysisError(f"{field} 必须有证据引用")
        seen = set()
        for ref in refs:
            _object(ref, {"kind", "id"}, f"{field}.evidence_refs[]", {"kind", "id"})
            _text(ref["kind"], "引用 kind"); _text(ref["id"], "引用 id")
            if ref["kind"] not in available or ref["id"] not in available[ref["kind"]]:
                raise AnalysisError(f"{field} 引用不存在或无效: {ref['kind']}/{ref['id']}")
            key = (ref["kind"], ref["id"])
            if key in seen:
                raise AnalysisError(f"{field} 证据引用重复")
            seen.add(key)
        if version == 2:
            analysis_refs = _text_array(claim["analysis_refs"], f"{field}.analysis_refs", required=True)
            if len(set(analysis_refs)) != len(analysis_refs) or not set(analysis_refs) <= process_ids:
                raise AnalysisError(f"{field} 引用不存在或重复的分析过程")
            evidence_materials = {ref_id for kind, ref_id in seen if kind == "material"}
            for kind, ref_id in seen:
                if kind == "group":
                    evidence_materials.update(groups[ref_id])
            if evidence_materials and not any(process_materials[ref] & evidence_materials for ref in analysis_refs):
                raise AnalysisError(f"{field} 的分析过程与证据对象无关")
            if claim["kind"] == "inference":
                for key in ("recommendation", "applicability", "limitations"):
                    if key not in claim:
                        raise AnalysisError(f"{field} 的设计判断缺少 {key}")
        claim_evidence[claim["id"]] = seen
        return seen

    if "overall" in value:
        check_claim(value["overall"], "overall")
        if version == 2 and value["overall"]["kind"] != "inference":
            raise AnalysisError("新版总判断必须明确标为 inference")
    for item in _array(value.get("key_findings", []), "key_findings"):
        check_claim(item, "key_findings[]")
    if current:
        if version == 2 and not current.get("findings"):
            raise AnalysisError("新版现状必须包含有依据的问题分析")
        for item in _array(current.get("findings", []), "current_state.findings"):
            refs = check_claim(item, "current_state.findings[]")
            if not any(kind == "current_state" for kind, _ in refs):
                raise AnalysisError("现状判断必须引用现状证据")
            if version == 2 and current_process["id"] not in item["analysis_refs"]:
                raise AnalysisError("现状判断必须引用现状分析过程")

    for section, subject, content in (("groups", "group_id", "takeaway"), ("materials", "material_id", "insight")):
        seen = set()
        for item in _array(value.get(section, []), section):
            _object(item, {subject, content}, section+"[]", {subject, content})
            sid = item[subject]; _text(sid, subject)
            valid = groups if section == "groups" else material_ids
            if sid not in valid:
                raise AnalysisError(f"{subject} 引用不存在: {sid}")
            if sid in seen:
                raise AnalysisError(f"{subject} 重复: {sid}")
            seen.add(sid)
            refs = check_claim(item[content], section+"[]."+content)
            supports_subject = ("material", sid) in refs if section == "materials" else (
                ("group", sid) in refs or any(kind == "material" and mid in groups[sid] for kind, mid in refs))
            if not supports_subject:
                raise AnalysisError(f"{subject} 的结论必须引用本组或本素材证据")
            if version == 2:
                related_materials = {sid} if section == "materials" else groups[sid]
                if not any(process_materials[ref] & related_materials for ref in item[content]["analysis_refs"]):
                    label = "本素材" if section == "materials" else "本组"
                    raise AnalysisError(f"{subject} 的分析过程必须涉及{label}")
            if version == 2 and section == "groups" and item[content]["kind"] != "inference":
                raise AnalysisError("分类副标题必须是设计判断")
        if version == 2:
            expected = {gid for gid, members in groups.items() if members} if section == "groups" else material_ids
            if seen != expected:
                raise AnalysisError(f"新版 {section} 必须恰好覆盖全部对象")

    if "synthesis" in value:
        synthesis = value["synthesis"]
        _object(synthesis, {"findings", "validation_questions"}, "synthesis")
        for field in ("findings", "validation_questions"):
            items = _array(synthesis.get(field, []), f"synthesis.{field}")
            if version == 2 and not items:
                raise AnalysisError(f"新版 synthesis.{field} 不得为空")
            for item in items:
                check_claim(item, f"synthesis.{field}[]")
                if version == 2:
                    expected_kind = "inference" if field == "findings" else "question"
                    if item["kind"] != expected_kind:
                        raise AnalysisError(f"synthesis.{field} 的结论类型应为 {expected_kind}")
    for item in _array(value.get("information_gaps", []), "information_gaps"):
        _object(item, {"section", "status", "reason"}, "information_gaps[]", {"section", "status", "reason"})
        _text(item["section"], "information_gaps.section"); _text(item["reason"], "information_gaps.reason")
        if item["status"] not in ("unknown", "not_provided", "not_applicable"):
            raise AnalysisError("information_gaps.status 无效")
    for item in _array(value.get("methodology", []), "methodology"):
        _object(item, {"title", "text"}, "methodology[]", {"title", "text"})
        _text(item["title"], "methodology.title"); _text(item["text"], "methodology.text")
    if not claim_ids and not value.get("information_gaps"):
        raise AnalysisError("分析至少需要一条有依据的判断或明确的信息缺口")
    if version == 2:
        reference_claim_ids = current_process["reference_claim_ids"] if current_process else []
        if current_process:
            for claim_id in reference_claim_ids:
                if claim_id not in claim_ids or not any(kind in ("material", "group") for kind, _ in claim_evidence[claim_id]):
                    raise AnalysisError("现状分析必须关联有竞品素材支撑的结论")
        review = value["quality_review"]
        _object(review, {"review_type", "independent", "reviewed_claim_ids", "checks", "edits", "notes"},
                "quality_review", {"review_type", "independent", "reviewed_claim_ids", "checks", "edits", "notes"})
        if review["review_type"] not in ("agent_self_review", "human_review"):
            raise AnalysisError("quality_review.review_type 无效")
        if type(review["independent"]) is not bool:
            raise AnalysisError("quality_review.independent 必须是布尔值")
        if review["review_type"] == "agent_self_review" and review["independent"]:
            raise AnalysisError("Agent 自查不得标记为独立验证")
        reviewed = _text_array(review["reviewed_claim_ids"], "quality_review.reviewed_claim_ids", required=True)
        if len(set(reviewed)) != len(reviewed) or set(reviewed) != claim_ids:
            raise AnalysisError("交付前复核必须恰好覆盖全部最终结论")
        checks = review["checks"]
        check_names = {"evidence_supported", "reference_value_clear", "research_relevant",
                       "exceptions_considered", "duplicates_resolved", "generic_claims_removed"}
        _object(checks, check_names, "quality_review.checks", check_names)
        if any(type(checks[key]) is not bool for key in check_names):
            raise AnalysisError("quality_review.checks 必须是布尔值")
        if not all(checks.values()):
            raise AnalysisError("存在未完成的分析复核项，应删除或重写结论后再交付")
        edits = _array(review["edits"], "quality_review.edits")
        for index, item in enumerate(edits):
            _object(item, {"candidate_id", "action", "before", "after", "reason"},
                    f"quality_review.edits[{index}]", {"candidate_id", "action", "before", "reason"})
            for key in ("candidate_id", "before", "reason"):
                _text(item[key], f"quality_review.edits[{index}].{key}")
            if item["action"] not in ("rewritten", "removed"):
                raise AnalysisError("quality_review.edits.action 无效")
            if item["action"] == "rewritten":
                if "after" not in item:
                    raise AnalysisError("重写记录必须包含 after")
                _text(item["after"], f"quality_review.edits[{index}].after")
            elif "after" in item:
                raise AnalysisError("删除记录不应包含 after")
        _text_array(review["notes"], "quality_review.notes", required=True)
    return deepcopy(value)
