import json
from pathlib import Path

from .classification import classify_assets
from .collector import collect_candidate
from .planning import plan_competitors
from .report import render_report
from .requirements import parse_request


def run_pipeline(request: str, output_dir: Path, fetch: bool = True):
    output_dir.mkdir(parents=True, exist_ok=True)
    task = parse_request(request)
    competitors = plan_competitors(task)
    assets = [collect_candidate(item, output_dir, fetch=fetch) for item in competitors]
    classification = classify_assets(assets)
    payload = {"task": task.to_dict(), "competitors": competitors, "assets": assets, "classification": classification}
    assets_json = output_dir / "materials.json"
    report_html = output_dir / "report.html"
    assets_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    report_html.write_text(render_report(task.to_dict(), assets, classification), encoding="utf-8")
    return {"assets_json": assets_json, "report_html": report_html, "payload": payload}
