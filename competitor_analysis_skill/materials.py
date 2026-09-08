from copy import deepcopy
from pathlib import Path

SOURCE_TYPES = {"ui_database", "public_web", "browser", "user_upload", "device_capture"}
COLLECTION_METHODS = {"database_asset", "web_candidate", "browser_screenshot", "user_provided", "manual_device_capture"}
PROVENANCES = {"online", "user_upload", "device_capture", "builtin_candidate"}
SEMANTIC_STATUSES = {"pending", "accepted", "rejected"}
QUALITY_STATUSES = {"pending", "accepted", "rejected", "missing"}
COLLECTION_STATUSES = {"pending", "collected", "rejected", "needs_manual_capture", "unavailable"}
TARGET_SURFACES = {"mobile_app", "web", "other", "user_specified"}
SURFACE_MATCHES = {"matched", "mismatched", "unclear", "not_applicable"}

REQUIRED_FIELDS = ("id", "product_name", "page_name", "region", "product_type", "platform", "source_type", "collection_method", "provenance", "semantic_status", "semantic_reason", "collection_status", "quality_status", "quality_reason", "observed_structure", "observed_patterns", "notes")

class MaterialError(ValueError):
    pass

def _text(value, field):
    if not isinstance(value, str):
        raise MaterialError(f"{field} 必须是字符串")
    if not value.strip():
        raise MaterialError(f"{field} 不能为空")
    return value.strip()

def standardize_material(data, output_dir=None):
    if not isinstance(data, dict):
        raise MaterialError("素材记录必须是对象")
    missing = [f for f in REQUIRED_FIELDS if f not in data]
    if missing:
        raise MaterialError(f"素材缺少字段: {', '.join(missing)}")
    result = deepcopy(data)
    result.setdefault("target_surface", "user_specified")
    result.setdefault("target_surface_match", "not_applicable")
    result.setdefault("source_provider", "")
    result.setdefault("source_asset_url", "")
    for field in ("id", "product_name", "page_name", "region", "product_type", "platform"):
        result[field] = _text(result[field], field)
    for field, allowed in (("source_type", SOURCE_TYPES), ("collection_method", COLLECTION_METHODS), ("provenance", PROVENANCES), ("semantic_status", SEMANTIC_STATUSES), ("quality_status", QUALITY_STATUSES), ("collection_status", COLLECTION_STATUSES)):
        if result[field] not in allowed:
            raise MaterialError(f"无效 {field}: {result[field]}")
    if result["target_surface"] not in TARGET_SURFACES:
        raise MaterialError(f"无效 target_surface: {result['target_surface']}")
    if result["target_surface_match"] not in SURFACE_MATCHES:
        raise MaterialError(f"无效 target_surface_match: {result['target_surface_match']}")
    for field in ("observed_structure", "observed_patterns"):
        if not isinstance(result[field], list) or not all(isinstance(v, str) for v in result[field]):
            raise MaterialError(f"{field} 必须是字符串数组")
    combinations = {
        "ui_database": {("database_asset", "online"), ("database_asset", "builtin_candidate")},
        "public_web": {("web_candidate", "online")},
        "browser": {("browser_screenshot", "online")},
        "user_upload": {("user_provided", "user_upload")},
        "device_capture": {("manual_device_capture", "device_capture")},
    }
    if (result["collection_method"], result["provenance"]) not in combinations[result["source_type"]]:
        raise MaterialError(f"来源字段组合不一致: {result['source_type']}/{result['collection_method']}/{result['provenance']}")
    if result["source_type"] == "ui_database":
        result["source_provider"] = _text(result["source_provider"], "source_provider")
    for field in ("source_provider", "source_asset_url"):
        if not isinstance(result[field], str):
            raise MaterialError(f"{field} 必须是字符串")
    for field in ("semantic_reason", "quality_reason", "notes"):
        if not isinstance(result[field], str):
            raise MaterialError(f"{field} 必须是字符串")
    if result["semantic_status"] in {"accepted", "rejected"} and not result["semantic_reason"].strip():
        raise MaterialError("semantic_reason 不能为空")
    result.setdefault("image_path", "")
    result.setdefault("source_url", "")
    result.setdefault("captured_at", "")
    result.setdefault("failure_reason", "")
    if not isinstance(result["failure_reason"], str):
        raise MaterialError("failure_reason 必须是字符串")
    if result["collection_status"] in {"rejected", "unavailable", "needs_manual_capture"} and not result["failure_reason"].strip():
        raise MaterialError("失败状态必须填写 failure_reason")
    if output_dir and result.get("image_path"):
        p = Path(result["image_path"])
        if p.is_absolute():
            try: p = p.resolve().relative_to(Path(output_dir).resolve())
            except ValueError: raise MaterialError("image_path 不得逃逸报告目录")
        result["image_path"] = p.as_posix()
    return result

def finalize_collection(material, mechanically_verified=False):
    platform = material.get("platform", "").casefold()
    mobile_platform = ("ios" in platform or "android" in platform) and "web" not in platform
    if material.get("duplicate_of"):
        material["collection_status"] = "rejected"
    elif material.get("target_surface") == "mobile_app" and (
        material.get("target_surface_match") != "matched" or not mobile_platform
    ):
        material["collection_status"] = "rejected"
    elif mechanically_verified and material.get("provenance") != "builtin_candidate" and material.get("semantic_status") == "accepted" and material.get("quality_status") == "accepted" and material.get("image_path"):
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
    seen_ids = set()
    for index, raw in enumerate(records):
        material = standardize_material(raw)
        material.pop("_mechanically_verified", None)
        if material["id"] in seen_ids:
            raise MaterialError(f"素材 ID 重复: {material['id']}")
        seen_ids.add(material["id"])
        mechanically_verified = False
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
                material["image_path"] = ""
                target.unlink(missing_ok=True)
            else:
                mechanically_verified = quality.status == "accepted"
        else:
            material.update({"quality_status": "missing", "quality_reason": "图片不存在", "image_path": "", "failure_reason": "图片不存在"})
        if material.get("quality_status") == "rejected" and not material.get("failure_reason"):
            material["failure_reason"] = material.get("quality_reason", "图片质量校验失败")
        material = finalize_collection(material, mechanically_verified=mechanically_verified)
        material.pop("_mechanically_verified", None)
        if material.get("content_sha256") and not material.get("duplicate_of"):
            by_digest[material["content_sha256"]] = material["id"]
        results.append(material)
    return results
