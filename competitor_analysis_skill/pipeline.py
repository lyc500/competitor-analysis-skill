import json
from pathlib import Path

from PIL import Image, UnidentifiedImageError

from .classification import classify_assets
from .collector import collect_candidate
from .materials import process_materials
from .source_discovery import process_sources, process_discovery_payload
from .browser_capture import capture_sources
from .evidence import build_evidence_statistics, validate_capture_links, validate_reviewed_material_links
from .planning import plan_competitors
from .report import render_report
from .report_bundle import write_report_bundle
from .legacy_demo import parse_legacy_demo_request
from .task_contract import load_task


def _non_stage4_classification():
    return {
        "classification_status": "unavailable",
        "classification_dimension": "",
        "classification_reason": "正式动态分类仅在 Stage 4 Agent Classification Plan 流程执行",
        "groups": [],
        "material_labels": [],
    }


def _validate_fallback_consistency(task, valid_materials, fallback_requests):
    if not isinstance(fallback_requests, list):
        raise ValueError("fallback_requests 必须是数组")
    task_pairs = {
        (competitor["product_name"].casefold(), task["target_page"])
        for competitor in task["competitors"]
    }
    collected_pairs = {
        (material["product_name"].casefold(), material["page_name"])
        for material in valid_materials
    }
    for index, fallback in enumerate(fallback_requests):
        if not isinstance(fallback, dict):
            raise ValueError(f"fallback_requests[{index}] 必须是对象")
        product_name = fallback.get("product_name")
        target_page = fallback.get("target_page")
        status = fallback.get("status")
        if not isinstance(product_name, str) or not isinstance(target_page, str):
            raise ValueError(f"fallback_requests[{index}] 缺少产品或目标页面")
        if status not in {"open", "resolved"}:
            raise ValueError(f"fallback_requests[{index}] status 无效")
        pair = (product_name.casefold(), target_page)
        if pair not in task_pairs:
            continue
        if pair in collected_pairs and status != "resolved":
            raise ValueError("fallback 状态与 collected 素材矛盾：已有素材必须 resolved")
        if pair not in collected_pairs and status == "resolved":
            raise ValueError("fallback 状态与 collected 素材矛盾：无素材不得 resolved")


def _read_json(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"无法读取证据文件 {path}: {exc}") from exc


def _formal_discovery_from_file(task, path):
    data = _read_json(path)
    if not isinstance(data, dict) or "source_attempts" not in data or "candidates" not in data:
        raise ValueError("历史来源记录缺少 source_attempts/candidates；这是旧格式证据缺口，请重新执行来源发现，不能补造 ID")
    return process_discovery_payload(task, data)


def _current_access_checks(discovery):
    preparation = discovery["access_preparation"]
    checks = {check["id"]: check for check in preparation["checks"]}
    return {
        source_id: checks[check_id]
        for source_id, check_id in preparation["current_checks_by_source"].items()
    }


def _candidate_accessible(candidate, check):
    if candidate.get("source_detail_url"):
        field = "detail_usable"
    elif candidate.get("source_asset_url"):
        field = "original_asset_usable"
    else:
        field = "page_open"
    if check.get(field) is True:
        return True, ""
    return False, f"当前来源检查未确认 {field}=true（{check.get('access_barrier', 'unknown')}）"


def _load_completed_captures(output_dir, discovery, completed_ids):
    if not completed_ids:
        return []
    path = output_dir / "captures.json"
    if not path.exists():
        raise ValueError(
            "已完成候选缺少 captures.json 有效截图产物: "
            + ", ".join(completed_ids)
            + "；请保留候选 ID，并将受影响项移回 remaining 后重试"
        )
    data = _read_json(path)
    records = data.get("captures", data) if isinstance(data, dict) else data
    if not isinstance(records, list):
        raise ValueError("已完成候选的 captures.json 必须包含 captures 数组")
    completed = set(completed_ids)
    selected = [record for record in records if record.get("source_candidate_id") in completed]
    by_candidate = {}
    for record in selected:
        candidate_id = record.get("source_candidate_id")
        if candidate_id in by_candidate:
            raise ValueError(f"已完成候选存在重复截图记录: {candidate_id}")
        by_candidate[candidate_id] = record
    missing = [candidate_id for candidate_id in completed_ids if candidate_id not in by_candidate]
    invalid = []
    root = output_dir.resolve()
    for candidate_id in completed_ids:
        record = by_candidate.get(candidate_id)
        if record is None:
            continue
        relative = record.get("screenshot_path")
        if record.get("capture_status") != "captured" or record.get("quality_status") != "accepted" or not relative:
            invalid.append(candidate_id)
            continue
        artifact = (output_dir / relative).resolve()
        if root != artifact and root not in artifact.parents:
            invalid.append(candidate_id)
            continue
        try:
            with Image.open(artifact) as image:
                image.verify()
        except (FileNotFoundError, OSError, UnidentifiedImageError):
            invalid.append(candidate_id)
    if missing or invalid:
        affected = sorted(set(missing + invalid))
        raise ValueError(
            "已完成候选缺少有效截图产物: " + ", ".join(affected) +
            "；请保留候选 ID，并将受影响项移回 remaining 后重试"
        )
    validate_capture_links(discovery, selected)
    return [by_candidate[candidate_id] for candidate_id in completed_ids]


def _capture_execution_plan(discovery, sources, output_dir):
    preparation = discovery["access_preparation"]
    decision = preparation["decision"]
    resume = preparation["resume"]
    if decision["status"] == "pending_user_choice":
        raise ValueError("来源登录限制影响覆盖，必须先取得用户的一次性选择")
    if resume["status"] == "waiting_for_login":
        raise ValueError("等待用户完成登录及实际复查后才能恢复截图")

    source_by_id = {source["id"]: source for source in sources}
    if resume["status"] in {"resumed", "partial", "blocked"}:
        completed_ids = list(resume["completed_candidate_ids"])
        intended_ids = list(resume["remaining_candidate_ids"])
    else:
        completed_ids = []
        intended_ids = list(discovery["candidate_pool"])
    preserved = _load_completed_captures(output_dir, discovery, completed_ids)

    current_checks = _current_access_checks(discovery)
    executable = []
    skipped_ids = []
    skip_reasons = {}
    for candidate_id in intended_ids:
        source = source_by_id[candidate_id]
        if resume["status"] == "blocked":
            skipped_ids.append(candidate_id)
            skip_reasons[candidate_id] = "登录或认证条件复查后仍未解除"
            continue
        check = current_checks[source["source_attempt_id"]]
        allowed, reason = _candidate_accessible(source, check)
        if not allowed:
            skipped_ids.append(candidate_id)
            skip_reasons[candidate_id] = reason
            continue
        capture_source = dict(source)
        if (
            decision["status"] == "login_then_continue"
            and source["source_attempt_id"] in decision["restricted_source_attempt_ids"]
            and check.get("authentication_state") == "authenticated"
        ):
            capture_source["requires_authenticated_session"] = True
        executable.append(capture_source)
    execution = {
        "resume_status": resume["status"],
        "planned_candidate_ids": intended_ids,
        "completed_candidate_ids": completed_ids,
        "executed_candidate_ids": [source["id"] for source in executable],
        "skipped_candidate_ids": skipped_ids,
        "skip_reasons": skip_reasons,
    }
    return preserved, executable, execution


def run_pipeline(request, output_dir: Path, fetch: bool = True, materials_file=None, sources_file=None, capture_sources_flag=False, captures_file=None, semantic_reviews_file=None, manual_captures_file=None, reviewed_materials_file=None, classification_plan_file=None, analysis_file=None):
    if analysis_file and not reviewed_materials_file:
        raise ValueError("--analysis-file 必须搭配 --reviewed-materials-file 或 --report-data-file")
    if sources_file and isinstance(request, str):
        raise ValueError("--sources-file 必须与结构化 --task-file 一起使用")
    if semantic_reviews_file and isinstance(request, str):
        raise ValueError("--semantic-reviews-file 必须与结构化 --task-file 一起使用")
    if (captures_file or manual_captures_file) and not semantic_reviews_file:
        raise ValueError("--captures-file/--manual-captures-file 必须搭配 --semantic-reviews-file")
    output_dir.mkdir(parents=True, exist_ok=True)
    if isinstance(request, str):
        task = parse_legacy_demo_request(request)
        # Legacy CLI compatibility only: fixed fixtures are never used by task-file flow.
        if task["task_status"] == "planned":
            task["planning_strategy"] = "fixture_demo"
            competitors = plan_competitors(task, fixture=True)
            task["competitors"] = competitors
            task["task_status"] = "ready"
            load_task(task)
        else:
            competitors = []
    else:
        task = load_task(request)
        competitors = plan_competitors(task)
    if reviewed_materials_file:
        if isinstance(request, str): raise ValueError("--reviewed-materials-file 必须与 --task-file 一起使用")
        if any((materials_file, sources_file, capture_sources_flag, captures_file, semantic_reviews_file, manual_captures_file, fetch is False)):
            raise ValueError("Stage 4 输入不得与其他阶段参数或 --offline 同时使用")
        reviewed_path = Path(reviewed_materials_file)
        data = json.loads(reviewed_path.read_text(encoding="utf-8"))
        if not isinstance(data, dict) or not isinstance(data.get("materials"), list):
            raise ValueError("reviewed_materials.json 必须包含 materials 数组")
        embedded = data.get("task")
        if embedded and embedded.get("target_page") != task["target_page"]:
            raise ValueError("reviewed materials 的 target_page 与任务不一致")
        if embedded and embedded.get("target_surface", "user_specified") != task.get("target_surface", "user_specified"):
            raise ValueError("reviewed materials 的 target_surface 与任务不一致")
        materials = data["materials"]
        discovery = None
        if "source_attempts" in data or "candidates" in data:
            discovery = process_discovery_payload(task, data)
        has_online_capture = any(
            material.get("capture_id") or material.get("source_candidate_id") or material.get("source_type") in {"browser", "ui_database"}
            for material in materials
        )
        if has_online_capture and discovery is None:
            raise ValueError("reviewed_materials 缺少来源尝试/候选登记；历史证据关联无法可靠还原")
        if discovery is not None:
            try:
                validate_reviewed_material_links(
                    discovery,
                    data.get("capture_targets", []),
                    data.get("reviews", []),
                    materials,
                )
            except ValueError as exc:
                raise ValueError(f"素材与截图/审核登记关联失败: {exc}") from exc
        ids = [m.get("id") for m in materials]
        if any(not isinstance(i, str) for i in ids) or len(ids) != len(set(ids)): raise ValueError("reviewed materials ID 必须唯一")
        task_products = {c["product_name"].casefold() for c in task["competitors"]}
        for m in materials:
            if m.get("product_name", "").casefold() not in task_products or m.get("page_name") != task["target_page"]: raise ValueError("reviewed material 与任务不一致")
            if m.get("collection_status") == "collected" and not (m.get("semantic_status") == "accepted" and m.get("quality_status") == "accepted" and m.get("image_path")): raise ValueError("collected material 状态不一致")
            if task.get("target_surface") == "mobile_app" and m.get("collection_status") == "collected":
                platform = m.get("platform", "").casefold()
                if not (m.get("target_surface") == "mobile_app" and m.get("target_surface_match") == "matched" and ("ios" in platform or "android" in platform) and "web" not in platform):
                    raise ValueError("collected material 的 Mobile Surface 状态不一致")
        valid = [m for m in materials if m.get("collection_status") == "collected" and m.get("semantic_status") == "accepted" and m.get("quality_status") == "accepted"]
        fallback = data.get("fallback_requests", [])
        _validate_fallback_consistency(task, valid, fallback)
        evidence_statistics = build_evidence_statistics(
            task,
            source_attempts=discovery.get("source_attempts", []) if discovery else [],
            candidates=discovery.get("candidates", []) if discovery else [],
            reviews=data.get("reviews", []),
            materials=materials,
            fallback_requests=fallback,
            capture_targets=data.get("capture_targets", []),
        )
        plan = None
        if classification_plan_file:
            plan_data = json.loads(Path(classification_plan_file).read_text(encoding="utf-8")); plan = plan_data.get("classification", plan_data) if isinstance(plan_data, dict) else plan_data
        if valid and plan is None: raise ValueError("存在有效素材时必须提供 --classification-plan-file")
        classification = classify_assets(materials, plan)
        report_data = {"task": task.to_dict(), "materials": valid, "classification": classification, "fallback_requests": fallback, "evidence_statistics": evidence_statistics, "coverage_boundary": evidence_statistics["coverage"], "excluded_summary": {status: sum(1 for m in materials if m.get("collection_status") == status) for status in ("rejected", "pending", "unavailable")}}
        if discovery:
            report_data["source_evidence"] = discovery
        if analysis_file:
            report_data["analysis"] = _read_json(analysis_file)
        return write_report_bundle(report_data, output_dir, reviewed_path.parent,
                                   Path(analysis_file).parent if analysis_file else None)
    if semantic_reviews_file:
        if not captures_file and not manual_captures_file:
            raise ValueError("--semantic-reviews-file 必须搭配 --captures-file 或 --manual-captures-file")
        if capture_sources_flag or fetch is False or materials_file:
            raise ValueError("阶段 3C 不得与 --capture-sources、--offline 或 --materials-file 同时使用")
        from .semantic_review import process_semantic_reviews
        def read_records(path, key):
            data = _read_json(path)
            return data.get(key, data) if isinstance(data, dict) else data
        capture_data = _read_json(captures_file) if captures_file else {}
        captures = capture_data.get("captures", capture_data) if isinstance(capture_data, dict) else capture_data
        discovery = None
        if captures_file and captures:
            discovery = _formal_discovery_from_file(task, sources_file) if sources_file else (
                process_discovery_payload(task, capture_data) if isinstance(capture_data, dict) and "source_attempts" in capture_data and "candidates" in capture_data else None
            )
            if discovery is None:
                raise ValueError("captures 缺少 source_attempts/candidates；历史截图与来源登记无法可靠关联")
            try:
                validate_capture_links(discovery, captures)
            except ValueError as exc:
                raise ValueError(f"截图与来源登记关联失败: {exc}") from exc
        manuals = read_records(manual_captures_file, "manual_captures") if manual_captures_file else []
        reviews = read_records(semantic_reviews_file, "reviews")
        result = process_semantic_reviews(task, captures, manuals, reviews, output_dir,
                                          Path(captures_file).parent if captures_file else None,
                                          Path(manual_captures_file).parent if manual_captures_file else None)
        reviewed = output_dir / "reviewed_materials.json"
        fallback = output_dir / "fallback_requests.json"
        payload = {"task": task.to_dict(), **(discovery or {}), "capture_targets": captures, **result}
        reviewed.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        fallback.write_text(json.dumps(result["fallback_requests"], ensure_ascii=False, indent=2), encoding="utf-8")
        return {"reviewed_materials_json": reviewed, "fallback_requests_json": fallback, "payload": payload}
    sources_json = None
    discovery = None
    legacy_sources = None
    if sources_file:
        source_path = Path(sources_file)
        source_data = _read_json(source_path)
        formal_discovery = (
            isinstance(source_data, dict)
            and "source_attempts" in source_data
            and "candidates" in source_data
        )
        if capture_sources_flag and not formal_discovery:
            raise ValueError(
                "正式 --capture-sources 不接受旧 sources 格式；请迁移为包含 "
                "source_attempts、candidates、candidate_pool、candidate_limit 和 "
                "access_preparation 的结构化来源输入"
            )
        if formal_discovery:
            discovery = process_discovery_payload(task, source_data)
            sources = [item for item in discovery["candidates"] if item["id"] in discovery["candidate_pool"]]
            for source in sources:
                source["target_surface"] = task.get("target_surface", "user_specified")
        else:
            source_records = source_data.get("sources", source_data) if isinstance(source_data, dict) else source_data
            legacy_sources = process_sources(task, source_records)
            sources = legacy_sources
        sources_json = output_dir / "sources.json"
        source_payload = {"task": task.to_dict()}
        if discovery:
            source_payload.update(discovery)
            source_payload["sources"] = discovery["candidates"]
        else:
            source_payload.update({"sources": legacy_sources, "compatibility": {"status": "legacy_incomplete", "gaps": ["缺少 source_attempts、source_candidate_id 关联和候选处置登记；不可作为正式证据"]}})
        sources_json.write_text(json.dumps(source_payload, ensure_ascii=False, indent=2), encoding="utf-8")
        if capture_sources_flag:
            if discovery.get("access_preparation_status") != "validated":
                raise ValueError("正式浏览器截图前必须提供并通过 access_preparation 来源访问预检")
            preserved, executable, capture_execution = _capture_execution_plan(discovery, sources, output_dir)
            new_captures = capture_sources(executable, output_dir) if executable else []
            captures = preserved + new_captures
            candidate_ids = [capture.get("source_candidate_id") for capture in captures]
            if len(candidate_ids) != len(set(candidate_ids)):
                raise ValueError("恢复后的截图记录不得重复候选 ID")
            validate_capture_links(discovery, captures)
            captures_json = output_dir / "captures.json"
            capture_payload = {
                "task": task.to_dict(), "captures": captures,
                "capture_execution": capture_execution,
            }
            capture_payload.update(discovery)
            captures_json.write_text(json.dumps(capture_payload, ensure_ascii=False, indent=2), encoding="utf-8")
        else:
            captures_json = None
    if materials_file:
        material_path = Path(materials_file)
        data = json.loads(material_path.read_text(encoding="utf-8"))
        records = data.get("materials", data) if isinstance(data, dict) else data
        assets = process_materials(records, output_dir, material_path.parent)
    else:
        assets = [] if not isinstance(request, str) else [collect_candidate(item, output_dir, fetch=fetch) for item in competitors]
    classification = _non_stage4_classification()
    payload = {"task": task.to_dict(), "competitors": competitors, "assets": assets, "classification": classification}
    if isinstance(request, str):
        payload["compatibility"] = {
            "status": "legacy_demo_only",
            "formal_entry": False,
            "limitations": [
                "固定示例映射不承担通用自然语言理解",
                "不得用于正式竞品选择、语义分类或验收",
            ],
        }
    assets_json = output_dir / "materials.json"
    report_html = output_dir / "report.html"
    assets_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    report_html.write_text(render_report(task.to_dict(), assets, classification), encoding="utf-8")
    if sources_json:
        payload["sources"] = sources
    if discovery:
        payload.update(discovery)
    return {"assets_json": assets_json, "report_html": report_html, "sources_json": sources_json, "captures_json": locals().get("captures_json"), "payload": payload}
