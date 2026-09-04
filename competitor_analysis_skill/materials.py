from copy import deepcopy
from pathlib import Path

SOURCE_TYPES = {"ui_database", "public_web", "browser", "user_upload", "device_capture"}
COLLECTION_METHODS = {"database_asset", "web_candidate", "browser_screenshot", "user_provided", "manual_device_capture"}
PROVENANCES = {"online", "user_upload", "device_capture", "builtin_candidate"}
SEMANTIC_STATUSES = {"pending", "accepted", "rejected"}
QUALITY_STATUSES = {"pending", "accepted", "rejected", "missing"}
COLLECTION_STATUSES = {"pending", "collected", "rejected", "needs_manual_capture", "unavailable"}

REQUIRED_FIELDS = ("id", "product_name", "page_name", "region", "product_type", "platform", "source_type", "collection_method", "provenance", "semantic_status", "semantic_reason", "collection_status", "quality_status", "quality_reason", "observed_structure", "observed_patterns", "notes")

class MaterialError(ValueError):
    pass

def _text(value, field):
    if not isinstance(value, str):
        raise MaterialError(f"{field} 必须是字符串")
    return value

def standardize_material(data, output_dir=None):
    if not isinstance(data, dict):
        raise MaterialError("素材记录必须是对象")
    missing = [f for f in REQUIRED_FIELDS if f not in data]
    if missing:
        raise MaterialError(f"素材缺少字段: {', '.join(missing)}")
    result = deepcopy(data)
    for field in ("id", "product_name", "page_name", "region", "product_type", "platform", "semantic_reason", "quality_reason", "notes"):
        _text(result[field], field)
    for field, allowed in (("source_type", SOURCE_TYPES), ("collection_method", COLLECTION_METHODS), ("provenance", PROVENANCES), ("semantic_status", SEMANTIC_STATUSES), ("quality_status", QUALITY_STATUSES), ("collection_status", COLLECTION_STATUSES)):
        if result[field] not in allowed:
            raise MaterialError(f"无效 {field}: {result[field]}")
    for field in ("observed_structure", "observed_patterns"):
        if not isinstance(result[field], list) or not all(isinstance(v, str) for v in result[field]):
            raise MaterialError(f"{field} 必须是字符串数组")
    result.setdefault("image_path", "")
    result.setdefault("source_url", "")
    result.setdefault("captured_at", "")
    result.setdefault("failure_reason", "")
    if output_dir and result.get("image_path"):
        p = Path(result["image_path"])
        if p.is_absolute():
            try: p = p.resolve().relative_to(Path(output_dir).resolve())
            except ValueError: raise MaterialError("image_path 不得逃逸报告目录")
        result["image_path"] = p.as_posix()
    return result

def finalize_collection(material):
    if material.get("duplicate_of"):
        material["collection_status"] = "rejected"
    elif material.get("semantic_status") == "accepted" and material.get("quality_status") == "accepted" and material.get("image_path"):
        material["collection_status"] = "collected"
    elif material.get("quality_status") == "rejected" or material.get("semantic_status") == "rejected":
        material["collection_status"] = "rejected"
    elif material.get("quality_status") == "missing":
        material["collection_status"] = "unavailable"
    else:
        material["collection_status"] = "pending"
    return material

def process_materials(records, output_dir, base_dir=None):
    output_dir = Path(output_dir).resolve(); base_dir = Path(base_dir or output_dir).resolve()
    assets_dir = output_dir / "assets"; assets_dir.mkdir(parents=True, exist_ok=True)
    results = []
    by_digest = {}
    for index, raw in enumerate(records):
        material = standardize_material(raw)
        source = Path(material.get("image_path", "")) if material.get("image_path") else None
        if source and not source.is_absolute(): source = base_dir / source
        if source and source.exists() and source.is_file():
            safe_name = Path(material["image_path"]).name
            if not safe_name: safe_name = f"material-{index}.bin"
            target = assets_dir / f"{index:03d}-{safe_name}"
            target.write_bytes(source.read_bytes())
            material["image_path"] = target.relative_to(output_dir).as_posix()
            quality = __import__("competitor_analysis_skill.quality", fromlist=["assess_image"]).assess_image(target)
            material.update({"quality_status": quality.status, "quality_reason": quality.reason, "width": quality.width, "height": quality.height, "decode_format": quality.format, "content_sha256": quality.content_sha256})
            if quality.content_sha256 and quality.content_sha256 in by_digest:
                material["duplicate_of"] = by_digest[quality.content_sha256]
        else:
            material.update({"quality_status": "missing", "quality_reason": "图片不存在", "image_path": ""})
        material = finalize_collection(material)
        if material.get("content_sha256") and not material.get("duplicate_of"):
            by_digest[material["content_sha256"]] = material["id"]
        results.append(material)
    return results
