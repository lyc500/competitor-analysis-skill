import json
from pathlib import Path

from .classification import classify_assets
from .collector import collect_candidate
from .materials import process_materials
from .source_discovery import process_sources
from .browser_capture import capture_sources
from .planning import plan_competitors
from .report import render_report
from .requirements import parse_request
from .task_contract import load_task


def run_pipeline(request, output_dir: Path, fetch: bool = True, materials_file=None, sources_file=None, capture_sources_flag=False, captures_file=None, semantic_reviews_file=None, manual_captures_file=None):
    if sources_file and isinstance(request, str):
        raise ValueError("--sources-file 必须与结构化 --task-file 一起使用")
    if semantic_reviews_file and isinstance(request, str):
        raise ValueError("--semantic-reviews-file 必须与结构化 --task-file 一起使用")
    if (captures_file or manual_captures_file) and not semantic_reviews_file:
        raise ValueError("--captures-file/--manual-captures-file 必须搭配 --semantic-reviews-file")
    output_dir.mkdir(parents=True, exist_ok=True)
    if isinstance(request, str):
        task = parse_request(request)
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
    if semantic_reviews_file:
        if not captures_file and not manual_captures_file:
            raise ValueError("--semantic-reviews-file 必须搭配 --captures-file 或 --manual-captures-file")
        if capture_sources_flag or fetch is False or materials_file:
            raise ValueError("阶段 3C 不得与 --capture-sources、--offline 或 --materials-file 同时使用")
        from .semantic_review import process_semantic_reviews
        def read_records(path, key):
            data = json.loads(Path(path).read_text(encoding="utf-8"))
            return data.get(key, data) if isinstance(data, dict) else data
        captures = read_records(captures_file, "captures") if captures_file else []
        manuals = read_records(manual_captures_file, "manual_captures") if manual_captures_file else []
        reviews = read_records(semantic_reviews_file, "reviews")
        result = process_semantic_reviews(task, captures, manuals, reviews, output_dir,
                                          Path(captures_file).parent if captures_file else None,
                                          Path(manual_captures_file).parent if manual_captures_file else None)
        reviewed = output_dir / "reviewed_materials.json"
        fallback = output_dir / "fallback_requests.json"
        payload = {"task": task.to_dict(), **result}
        reviewed.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        fallback.write_text(json.dumps(result["fallback_requests"], ensure_ascii=False, indent=2), encoding="utf-8")
        return {"reviewed_materials_json": reviewed, "fallback_requests_json": fallback, "payload": payload}
    sources_json = None
    if sources_file:
        source_path = Path(sources_file)
        source_data = json.loads(source_path.read_text(encoding="utf-8"))
        source_records = source_data.get("sources", source_data) if isinstance(source_data, dict) else source_data
        sources = process_sources(task, source_records)
        sources_json = output_dir / "sources.json"
        sources_json.write_text(json.dumps({"task": task.to_dict(), "sources": sources}, ensure_ascii=False, indent=2), encoding="utf-8")
        if capture_sources_flag:
            captures = capture_sources(sources, output_dir)
            captures_json = output_dir / "captures.json"
            captures_json.write_text(json.dumps({"task": task.to_dict(), "sources": sources, "captures": captures}, ensure_ascii=False, indent=2), encoding="utf-8")
        else:
            captures_json = None
    if materials_file:
        material_path = Path(materials_file)
        data = json.loads(material_path.read_text(encoding="utf-8"))
        records = data.get("materials", data) if isinstance(data, dict) else data
        assets = process_materials(records, output_dir, material_path.parent)
    else:
        assets = [] if not isinstance(request, str) else [collect_candidate(item, output_dir, fetch=fetch) for item in competitors]
    classification = classify_assets(assets)
    payload = {"task": task.to_dict(), "competitors": competitors, "assets": assets, "classification": classification}
    assets_json = output_dir / "materials.json"
    report_html = output_dir / "report.html"
    assets_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    report_html.write_text(render_report(task.to_dict(), assets, classification), encoding="utf-8")
    if sources_json:
        payload["sources"] = sources
    return {"assets_json": assets_json, "report_html": report_html, "sources_json": sources_json, "captures_json": locals().get("captures_json"), "payload": payload}
