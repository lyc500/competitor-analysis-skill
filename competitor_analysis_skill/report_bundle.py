"""Self-contained report output shared by formal Stage 4 and explicit replay."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import shutil

from .analysis import validate_analysis
from .classification import classify_assets
from .quality import assess_image
from .report import render_report, _collected
from .task_contract import load_task


def read_json(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"无法读取报告输入 {path}: {exc}") from exc


def _image_source(value, base):
    if not isinstance(value, str) or not value.strip():
        raise ValueError("图片 image_path 必须是非空字符串")
    base = Path(base).resolve()
    path = Path(value)
    path = (path if path.is_absolute() else base / path).resolve()
    try:
        path.relative_to(base)
    except ValueError as exc:
        raise ValueError("图片 image_path 不得逃逸输入目录") from exc
    if not path.is_file():
        raise ValueError(f"图片不存在: {value}")
    return path


def write_report_bundle(payload, output_dir, materials_base, analysis_base=None, mode="formal"):
    """Only render validated content; copy every displayed asset into output/assets."""
    data = deepcopy(payload)
    task = load_task(data["task"])
    materials = data["materials"]
    if not isinstance(materials, list) or any(not isinstance(m, dict) for m in materials):
        raise ValueError("report_data.materials 必须是对象数组")
    valid = _collected(task, materials)
    classification = classify_assets(valid, data["classification"])
    analysis = data.get("analysis")
    if mode == "formal" and analysis and analysis.get("schema_version") != 2:
        raise ValueError("正式报告只接受 analysis v2；旧分析仅可用于历史重放")
    if "analysis" in data:
        analysis = validate_analysis(analysis, valid, classification, require_detailed_coverage=mode == "formal")
        coverage = analysis.get("coverage_assessment", {})
        decision = coverage.get("user_decision", {})
        decision_status = decision.get("status") if isinstance(decision, dict) else decision
        if coverage.get("status") == "insufficient" and decision_status == "supplement_sources":
            raise ValueError("样本不足且用户选择补充来源，不能提前生成正式报告")
    output_dir = Path(output_dir).resolve()
    # A replay must never overwrite the snapshot (including archived inputs).
    if mode == "replay" and output_dir == Path(materials_base).resolve():
        raise ValueError("重放必须使用新的输出目录，不能覆盖输入")
    copies = []

    def prepare_image(item, base, prefix=""):
        source = _image_source(item["image_path"], base)
        if prefix:
            quality = assess_image(source)
            if quality.status != "accepted":
                raise ValueError(f"现状图不可用: {quality.reason}")
        digest = hashlib.sha256(item["id"].encode("utf-8")).hexdigest()[:16]
        relative = "assets/" + prefix + digest + (source.suffix.lower() or ".png")
        target = output_dir / relative
        try:
            target.resolve().relative_to(output_dir / "assets")
        except ValueError as exc:
            raise ValueError("报告图片目标不得逃逸 assets 目录") from exc
        copies.append((source, target))
        item["image_path"] = relative

    for item in valid:
        prepare_image(item, materials_base)
    if analysis:
        for item in analysis.get("current_state", {}).get("images", []):
            prepare_image(item, analysis_base or materials_base, "current-")
    data.update(task=task.to_dict(), materials=valid, classification=classification, report_schema_version=1)
    if analysis:
        data["analysis"] = analysis
    data["generation"] = {
        "mode": mode,
        "analysis_status": "provided" if analysis else "missing",
        "analysis_standard": (
            "v2_" + analysis["quality_review"]["review_type"]
            if analysis and analysis.get("schema_version") == 2 else
            "legacy_v1" if analysis else "missing"
        ),
        "standard_acceptance": "not_assessed",
    }
    html = render_report(data["task"], valid, classification, data.get("fallback_requests"),
                         evidence_statistics=data.get("evidence_statistics"), analysis=analysis,
                         generation=data["generation"], source_evidence=data.get("source_evidence"))
    (output_dir / "assets").mkdir(parents=True, exist_ok=True)
    for source, target in copies:
        if source != target.resolve():
            shutil.copyfile(source, target)
    for name, value in (("classification.json", classification), ("report_data.json", data)):
        (output_dir / name).write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
    (output_dir / "report.html").write_text(html, encoding="utf-8")
    return {"classification_json": output_dir / "classification.json", "report_data_json": output_dir / "report_data.json",
            "report_html": output_dir / "report.html", "payload": data}


def replay_report(report_data_file, output_dir, analysis_file=None, classification_plan_file=None):
    """Re-render a local snapshot. This is never a new source/evidence acceptance."""
    source = Path(report_data_file)
    data = read_json(source)
    if not isinstance(data, dict) or not {"task", "materials", "classification"} <= set(data):
        raise ValueError("重放输入必须包含 task/materials/classification")
    if "report_schema_version" in data and (type(data["report_schema_version"]) is not int or data["report_schema_version"] != 1):
        raise ValueError("不支持该 report_schema_version")
    if analysis_file:
        data["analysis"] = read_json(analysis_file)
    if classification_plan_file:
        plan = read_json(classification_plan_file)
        data["classification"] = plan.get("classification", plan) if isinstance(plan, dict) else plan
    return write_report_bundle(data, output_dir, source.parent,
                               Path(analysis_file).parent if analysis_file else source.parent, mode="replay")
