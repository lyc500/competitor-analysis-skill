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


def run_pipeline(request, output_dir: Path, fetch: bool = True, materials_file=None, sources_file=None, capture_sources_flag=False):
    if sources_file and isinstance(request, str):
        raise ValueError("--sources-file 必须与结构化 --task-file 一起使用")
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
