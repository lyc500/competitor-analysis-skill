from pathlib import Path

from .manual_capture import ManualCaptureError, process_manual_captures
from .materials import process_materials


class SemanticReviewError(ValueError):
    pass


ENUMS = {
    "target_kind": {"browser_capture", "manual_capture"},
    "semantic_status": {"accepted", "rejected"},
    "product_identity": {"matched", "mismatched", "unclear"},
    "target_page_match": {"matched", "mismatched", "unclear"},
    "page_completeness": {"complete", "incomplete", "unclear"},
    "asset_kind": {"ui_page", "logo", "share_card", "marketing_image", "cover", "unrelated", "unknown"},
}
REVIEW_FIELDS = ("target_id", "target_kind", "semantic_status", "product_identity", "target_page_match", "page_completeness", "asset_kind", "semantic_reason", "review_source")


def _review(raw, index):
    if not isinstance(raw, dict):
        raise SemanticReviewError(f"reviews[{index}] 必须是对象")
    missing = [field for field in REVIEW_FIELDS if field not in raw]
    if missing:
        raise SemanticReviewError(f"review 缺少字段: {', '.join(missing)}")
    result = dict(raw)
    for field in REVIEW_FIELDS:
        if not isinstance(result[field], str) or not result[field].strip():
            raise SemanticReviewError(f"review.{field} 不能为空")
        result[field] = result[field].strip()
    for field, allowed in ENUMS.items():
        if result[field] not in allowed:
            raise SemanticReviewError(f"无效 {field}: {result[field]}")
    if result["review_source"] != "agent_visual_review":
        raise SemanticReviewError("review_source 必须为 agent_visual_review")
    if result["semantic_status"] == "accepted" and not (
        result["product_identity"] == "matched"
        and result["target_page_match"] == "matched"
        and result["page_completeness"] == "complete"
        and result["asset_kind"] == "ui_page"
    ):
        raise SemanticReviewError("semantic_status=accepted 与审核字段不一致")
    return result


def _path(base, value):
    path = Path(value)
    return path if path.is_absolute() else Path(base) / path


def process_semantic_reviews(task, captures, manuals, reviews, output_dir, captures_base_dir=None, manuals_base_dir=None):
    competitors = {item["product_name"].casefold(): item for item in task["competitors"]}
    captures = list(captures or [])
    try:
        manuals = process_manual_captures(task, list(manuals or []))
    except ManualCaptureError as exc:
        raise SemanticReviewError(str(exc)) from exc
    capture_by_id = {}
    for index, capture in enumerate(captures):
        if not isinstance(capture, dict) or not isinstance(capture.get("id"), str) or not capture["id"].strip():
            raise SemanticReviewError(f"captures[{index}] 缺少有效 id")
        capture = dict(capture); capture["id"] = capture["id"].strip()
        if capture["id"] in capture_by_id:
            raise SemanticReviewError(f"capture ID 重复: {capture['id']}")
        if capture.get("product_name", "").casefold() not in competitors:
            raise SemanticReviewError("capture 竞品未在任务中")
        if capture.get("target_page") != task["target_page"]:
            raise SemanticReviewError("capture target_page 与任务不一致")
        if capture.get("capture_status") not in {"captured", "failed", "blank"}:
            raise SemanticReviewError(f"无效 capture_status: {capture.get('capture_status')}")
        capture_by_id[capture["id"]] = capture
    manual_by_id = {item["id"]: item for item in manuals}
    collision = set(capture_by_id) & set(manual_by_id)
    if collision:
        raise SemanticReviewError(f"capture/manual target ID 冲突: {sorted(collision)[0]}")
    targets = {**capture_by_id, **manual_by_id}
    parsed_reviews = [_review(item, index) for index, item in enumerate(reviews or [])]
    review_by_id = {}
    for review in parsed_reviews:
        if review["target_id"] in review_by_id:
            raise SemanticReviewError(f"review target_id 重复: {review['target_id']}")
        if review["target_id"] not in targets:
            raise SemanticReviewError(f"review target_id 不存在: {review['target_id']}")
        expected_kind = "manual_capture" if review["target_id"] in manual_by_id else "browser_capture"
        if review["target_kind"] != expected_kind:
            raise SemanticReviewError("review target_kind 与目标不一致")
        review_by_id[review["target_id"]] = review
    for capture in capture_by_id.values():
        status = capture.get("capture_status")
        if status == "captured":
            path = capture.get("screenshot_path")
            if not isinstance(path, str) or not path.strip():
                raise SemanticReviewError("captured 截图必须有 screenshot_path")
            if not _path(captures_base_dir or output_dir, path).is_file():
                raise SemanticReviewError("截图文件不存在")
            if capture["id"] not in review_by_id:
                raise SemanticReviewError(f"captured 缺少语义审核: {capture['id']}")
        elif capture["id"] in review_by_id:
            raise SemanticReviewError("failed/blank capture 不可接受语义审核")
    materials = []
    for capture in capture_by_id.values():
        review = review_by_id.get(capture["id"])
        if capture.get("capture_status") != "captured" or review is None:
            continue
        competitor = competitors[capture["product_name"].casefold()]
        materials.append({
            "id": f"mat-{capture['id']}", "product_name": competitor["product_name"], "page_name": task["target_page"],
            "region": competitor["region"], "product_type": competitor["product_type"], "platform": competitor["platform"],
            "image_path": str(_path(captures_base_dir or output_dir, capture["screenshot_path"])), "source_type": "browser",
            "source_url": capture.get("final_url") or capture.get("requested_url", ""), "captured_at": capture.get("captured_at", ""),
            "collection_method": "browser_screenshot", "provenance": "online", "semantic_status": review["semantic_status"],
            "semantic_reason": review["semantic_reason"], "collection_status": "pending", "quality_status": "pending", "quality_reason": "",
            "observed_structure": [], "observed_patterns": [], "notes": "", "failure_reason": "", "capture_id": capture["id"],
            "source_candidate_id": capture.get("source_candidate_id", ""), "requested_url": capture.get("requested_url", ""), "final_url": capture.get("final_url", ""),
        })
    for manual in manuals:
        review = review_by_id.get(manual["id"])
        if review is None:
            raise SemanticReviewError(f"manual capture 缺少语义审核: {manual['id']}")
        competitor = competitors[manual["product_name"].casefold()]
        materials.append({
            "id": f"mat-{manual['id']}", "product_name": competitor["product_name"], "page_name": task["target_page"],
            "region": competitor["region"], "product_type": competitor["product_type"], "platform": competitor["platform"],
            "image_path": str(_path(manuals_base_dir or output_dir, manual["image_path"])), "source_type": manual["source_type"],
            "source_url": manual.get("source_url", ""), "captured_at": manual.get("captured_at", ""),
            "collection_method": "user_provided" if manual["source_type"] == "user_upload" else "manual_device_capture",
            "provenance": "user_upload" if manual["source_type"] == "user_upload" else "device_capture", "semantic_status": review["semantic_status"],
            "semantic_reason": review["semantic_reason"], "collection_status": "pending", "quality_status": "pending", "quality_reason": "",
            "observed_structure": [], "observed_patterns": [], "notes": manual.get("notes", ""), "failure_reason": "", "manual_capture_id": manual["id"],
        })
    output_dir = Path(output_dir); output_dir.mkdir(parents=True, exist_ok=True)
    processed = process_materials(materials, output_dir)
    fallback = []
    for competitor in task["competitors"]:
        product = competitor["product_name"]
        rows = [item for item in processed if item["product_name"] == product and item["page_name"] == task["target_page"]]
        resolved = any(item["collection_status"] == "collected" for item in rows)
        fallback.append({"product_name": product, "target_page": task["target_page"], "status": "resolved" if resolved else "open", "reason": "已有有效素材" if resolved else "公开截图失败或未通过语义审核", "allowed_methods": ["user_upload", "device_capture"]})
    return {"reviews": parsed_reviews, "materials": processed, "fallback_requests": fallback}
