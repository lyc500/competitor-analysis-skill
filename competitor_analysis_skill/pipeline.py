import json
from pathlib import Path

from .classification import classify_assets
from .collector import collect_candidate
from .planning import plan_competitors
from .report import render_report
from .requirements import parse_request
from .task_contract import load_task


def run_pipeline(request, output_dir: Path, fetch: bool = True):
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
    assets = [] if not isinstance(request, str) else [collect_candidate(item, output_dir, fetch=fetch) for item in competitors]
    classification = classify_assets(assets)
    payload = {"task": task.to_dict(), "competitors": competitors, "assets": assets, "classification": classification}
    assets_json = output_dir / "materials.json"
    report_html = output_dir / "report.html"
    assets_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    report_html.write_text(render_report(task.to_dict(), assets, classification), encoding="utf-8")
    return {"assets_json": assets_json, "report_html": report_html, "payload": payload}
