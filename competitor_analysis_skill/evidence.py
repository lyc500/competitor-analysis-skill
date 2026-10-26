"""Cross-stage evidence contracts and deterministic coverage statistics.

The Agent supplies discovery meaning and visual decisions.  This module only
checks references, shapes, limits and counters; it never decides whether a
candidate is semantically relevant.
"""

from copy import deepcopy
import hashlib

from .source_discovery import normalize_url


UNKNOWN = "unknown"
MAX_CANDIDATE_POOL = 50
SOURCE_TYPES = {"ui_database", "public_web"}
ACCESS_STATUSES = {"accessible", "login_required", "paywall", "empty", "error", "blocked", UNKNOWN}
ATTEMPT_STATUSES = {"completed", "exhausted", "blocked", "not_verified"}
CANDIDATE_STATUSES = {"accepted", "rejected", "not_reviewed"}
BOOL_OR_UNKNOWN = {True, False, UNKNOWN}


class DiscoveryContractError(ValueError):
    pass


class EvidenceLinkError(ValueError):
    pass


def _text(value, field, error=DiscoveryContractError):
    if not isinstance(value, str) or not value.strip():
        raise error(f"{field} 必须是非空字符串")
    return value.strip()


def _url(value, field, required=False):
    if value in (None, "") and not required:
        return ""
    return normalize_url(_text(value, field))


def _bool_or_unknown(value, field):
    if value not in BOOL_OR_UNKNOWN:
        raise DiscoveryContractError(f"{field} 必须是布尔值或 unknown")
    return value


def _query_mapping(value, field):
    if not isinstance(value, dict):
        raise DiscoveryContractError(f"{field} 必须是对象")
    raw_intent = _text(value.get("raw_page_intent"), f"{field}.raw_page_intent")
    mapped_terms = value.get("mapped_terms")
    taxonomy_terms = value.get("source_taxonomy_terms")
    if not isinstance(mapped_terms, list) or not mapped_terms or not all(isinstance(item, str) and item.strip() for item in mapped_terms):
        raise DiscoveryContractError(f"{field}.mapped_terms 必须是非空字符串数组")
    if not isinstance(taxonomy_terms, list) or not all(isinstance(item, str) and item.strip() for item in taxonomy_terms):
        raise DiscoveryContractError(f"{field}.source_taxonomy_terms 必须是字符串数组")
    return {
        "raw_page_intent": raw_intent,
        "mapped_terms": [item.strip() for item in mapped_terms],
        "source_taxonomy_terms": [item.strip() for item in taxonomy_terms],
    }


def _validate_attempt(raw, index):
    if not isinstance(raw, dict):
        raise DiscoveryContractError(f"source_attempts[{index}] 必须是对象")
    required = (
        "id", "source_type", "source_provider", "entry_url", "query_mapping",
        "actual_query", "search_mode", "discovery_batch", "web_text_accessible",
        "browser_accessible", "browser_interactive", "content_available",
        "access_status", "observed_scope", "attempt_status", "failure_reason",
    )
    missing = [field for field in required if field not in raw]
    if missing:
        raise DiscoveryContractError(f"source_attempts[{index}] 缺少字段: {', '.join(missing)}")
    item = dict(raw)
    item["id"] = _text(item["id"], f"source_attempts[{index}].id")
    item["source_type"] = _text(item["source_type"], f"source_attempts[{index}].source_type")
    if item["source_type"] not in SOURCE_TYPES:
        raise DiscoveryContractError(f"source_attempts[{index}].source_type 无效")
    item["source_provider"] = _text(item["source_provider"], f"source_attempts[{index}].source_provider")
    item["entry_url"] = _url(item["entry_url"], f"source_attempts[{index}].entry_url", required=True)
    item["query_mapping"] = _query_mapping(item["query_mapping"], f"source_attempts[{index}].query_mapping")
    for field in ("actual_query", "search_mode", "observed_scope", "failure_reason"):
        if not isinstance(item[field], str):
            raise DiscoveryContractError(f"source_attempts[{index}].{field} 必须是字符串")
        item[field] = item[field].strip()
    if not item["actual_query"]:
        raise DiscoveryContractError(f"source_attempts[{index}].actual_query 不能为空")
    if not item["search_mode"]:
        raise DiscoveryContractError(f"source_attempts[{index}].search_mode 不能为空")
    if not isinstance(item["discovery_batch"], int) or item["discovery_batch"] < 1:
        raise DiscoveryContractError(f"source_attempts[{index}].discovery_batch 必须是正整数")
    for field in ("web_text_accessible", "browser_accessible", "browser_interactive", "content_available"):
        item[field] = _bool_or_unknown(item[field], f"source_attempts[{index}].{field}")
    if item["access_status"] not in ACCESS_STATUSES:
        raise DiscoveryContractError(f"source_attempts[{index}].access_status 无效")
    if item["attempt_status"] not in ATTEMPT_STATUSES:
        raise DiscoveryContractError(f"source_attempts[{index}].attempt_status 无效")
    if item["attempt_status"] == "blocked" and not item["failure_reason"]:
        raise DiscoveryContractError(f"source_attempts[{index}] blocked 必须填写 failure_reason")
    return item


def _validate_candidate(raw, index, attempts, competitors, target_page):
    if not isinstance(raw, dict):
        raise DiscoveryContractError(f"candidates[{index}] 必须是对象")
    required = (
        "id", "source_attempt_id", "product_name", "target_page",
        "source_entry_url", "source_detail_url", "source_asset_url",
        "candidate_rank", "candidate_status", "disposition_reason",
    )
    missing = [field for field in required if field not in raw]
    if missing:
        raise DiscoveryContractError(f"candidates[{index}] 缺少字段: {', '.join(missing)}")
    item = dict(raw)
    item["source_attempt_id"] = _text(item["source_attempt_id"], f"candidates[{index}].source_attempt_id")
    if item["source_attempt_id"] not in attempts:
        raise DiscoveryContractError(f"candidates[{index}].source_attempt_id 未登记: {item['source_attempt_id']}")
    item["product_name"] = _text(item["product_name"], f"candidates[{index}].product_name")
    if item["product_name"].casefold() not in competitors:
        raise DiscoveryContractError(f"候选竞品未在任务中: {item['product_name']}")
    item["target_page"] = _text(item["target_page"], f"candidates[{index}].target_page")
    if item["target_page"] != target_page:
        raise DiscoveryContractError(f"candidates[{index}].target_page 与任务不一致")
    attempt = attempts[item["source_attempt_id"]]
    item["source_entry_url"] = _url(item["source_entry_url"], f"candidates[{index}].source_entry_url", required=True)
    if item["source_entry_url"] != attempt["entry_url"]:
        raise DiscoveryContractError(f"candidates[{index}].source_entry_url 与来源尝试不一致")
    item["source_detail_url"] = _url(item["source_detail_url"], f"candidates[{index}].source_detail_url")
    item["source_asset_url"] = _url(item["source_asset_url"], f"candidates[{index}].source_asset_url")
    if not item["source_detail_url"] and not item["source_asset_url"]:
        raise DiscoveryContractError(f"candidates[{index}] 至少需要 source_detail_url 或 source_asset_url")
    if not isinstance(item["candidate_rank"], int) or item["candidate_rank"] < 1:
        raise DiscoveryContractError(f"candidates[{index}].candidate_rank 必须是正整数")
    if item["candidate_status"] not in CANDIDATE_STATUSES:
        raise DiscoveryContractError(f"candidates[{index}].candidate_status 无效")
    item["disposition_reason"] = _text(item["disposition_reason"], f"candidates[{index}].disposition_reason")
    item["id"] = _text(item["id"], f"candidates[{index}].id") if item.get("id") else ""
    if not item["id"]:
        stable = "\n".join((item["source_attempt_id"], item["product_name"], item["source_detail_url"], item["source_asset_url"], str(item["candidate_rank"]), str(index))).encode()
        item["id"] = "cand-" + hashlib.sha256(stable).hexdigest()[:16]
    item["query_mapping"] = deepcopy(attempt["query_mapping"])
    item["actual_query"] = attempt["actual_query"]
    item["search_mode"] = attempt["search_mode"]
    item["discovery_batch"] = attempt["discovery_batch"]
    return item


def validate_discovery_payload(task, payload):
    if not isinstance(payload, dict):
        raise DiscoveryContractError("来源发现记录必须是对象")
    for field in ("source_attempts", "candidates", "candidate_pool", "candidate_limit"):
        if field not in payload:
            raise DiscoveryContractError(f"来源发现记录缺少字段: {field}")
    attempts_raw = payload["source_attempts"]
    candidates_raw = payload["candidates"]
    if not isinstance(attempts_raw, list) or not isinstance(candidates_raw, list):
        raise DiscoveryContractError("source_attempts 和 candidates 必须是数组")
    attempts = []
    attempt_by_id = {}
    for index, raw in enumerate(attempts_raw):
        item = _validate_attempt(raw, index)
        if item["id"] in attempt_by_id:
            raise DiscoveryContractError(f"来源尝试 ID 重复: {item['id']}")
        attempt_by_id[item["id"]] = item
        attempts.append(item)
    competitors = {item["product_name"].casefold() for item in task.get("competitors", [])}
    candidates = []
    candidate_by_id = {}
    for index, raw in enumerate(candidates_raw):
        item = _validate_candidate(raw, index, attempt_by_id, competitors, task.get("target_page"))
        if item["id"] in candidate_by_id:
            raise DiscoveryContractError(f"候选 ID 重复: {item['id']}")
        candidate_by_id[item["id"]] = item
        candidates.append(item)
    pool = payload["candidate_pool"]
    if not isinstance(pool, list) or not all(isinstance(value, str) and value for value in pool):
        raise DiscoveryContractError("candidate_pool 必须是字符串 ID 数组")
    if len(pool) != len(set(pool)):
        raise DiscoveryContractError("candidate_pool 不得包含重复 ID")
    if len(pool) > MAX_CANDIDATE_POOL:
        raise DiscoveryContractError("candidate_pool 超过 50 个候选记录")
    for candidate_id in pool:
        if candidate_id not in candidate_by_id:
            raise DiscoveryContractError(f"candidate_pool 引用未知候选: {candidate_id}")
        if candidate_by_id[candidate_id]["candidate_status"] != "accepted":
            raise DiscoveryContractError("candidate_pool 只能包含 candidate_status=accepted 的候选")
    accepted_ids = {item["id"] for item in candidates if item["candidate_status"] == "accepted"}
    if accepted_ids != set(pool):
        raise DiscoveryContractError("accepted 候选必须完整进入 candidate_pool，不能静默丢弃")
    limit = payload["candidate_limit"]
    if not isinstance(limit, dict):
        raise DiscoveryContractError("candidate_limit 必须是对象")
    if limit.get("max") != MAX_CANDIDATE_POOL or limit.get("unit") != "candidate_records" or limit.get("applies_to") != "candidate_pool":
        raise DiscoveryContractError("candidate_limit 必须明确 50 个 candidate_records 仅适用于 candidate_pool")
    ordering_basis = _text(limit.get("ordering_basis"), "candidate_limit.ordering_basis")
    truncated = limit.get("truncated_candidate_ids")
    if not isinstance(truncated, list) or len(truncated) != len(set(truncated)):
        raise DiscoveryContractError("candidate_limit.truncated_candidate_ids 必须是唯一 ID 数组")
    for candidate_id in truncated:
        if candidate_id not in candidate_by_id:
            raise DiscoveryContractError(f"截断记录引用未知候选: {candidate_id}")
        if candidate_id in pool:
            raise DiscoveryContractError("被截断候选不得同时进入 candidate_pool")
        if candidate_by_id[candidate_id]["candidate_status"] == "accepted":
            raise DiscoveryContractError("被截断候选必须有 rejected 或 not_reviewed 处置")
    if len(candidates) > MAX_CANDIDATE_POOL and not truncated:
        raise DiscoveryContractError("发现候选超过 50 个时必须记录截断候选")
    if len(candidates) <= MAX_CANDIDATE_POOL and truncated:
        raise DiscoveryContractError("候选未超过 50 个时不应填写截断候选")
    return {
        "source_attempts": attempts,
        "candidates": candidates,
        "candidate_pool": list(pool),
        "candidate_limit": {
            "max": MAX_CANDIDATE_POOL,
            "unit": "candidate_records",
            "applies_to": "candidate_pool",
            "ordering_basis": ordering_basis,
            "truncated_candidate_ids": list(truncated),
        },
    }


def validate_capture_links(registry, captures):
    if not isinstance(registry, dict):
        raise EvidenceLinkError("截图关联缺少来源登记")
    try:
        candidates = {item["id"]: item for item in registry["candidates"]}
        attempts = {item["id"]: item for item in registry["source_attempts"]}
    except (KeyError, TypeError):
        raise EvidenceLinkError("截图关联缺少 source_attempts/candidates 登记")
    seen = set()
    for index, raw in enumerate(captures or []):
        if not isinstance(raw, dict):
            raise EvidenceLinkError(f"captures[{index}] 必须是对象")
        capture_id = _text(raw.get("id"), f"captures[{index}].id", EvidenceLinkError)
        if capture_id in seen:
            raise EvidenceLinkError(f"capture ID 重复: {capture_id}")
        seen.add(capture_id)
        candidate_id = _text(raw.get("source_candidate_id"), f"captures[{index}].source_candidate_id", EvidenceLinkError)
        attempt_id = _text(raw.get("source_attempt_id"), f"captures[{index}].source_attempt_id", EvidenceLinkError)
        candidate = candidates.get(candidate_id)
        if candidate is None:
            raise EvidenceLinkError(f"截图引用未登记候选: {candidate_id}")
        if candidate.get("candidate_status") != "accepted":
            raise EvidenceLinkError(f"截图只能引用 candidate_status=accepted 的候选: {candidate_id}")
        if attempt_id not in attempts:
            raise EvidenceLinkError(f"截图引用未登记来源尝试: {attempt_id}")
        if candidate["source_attempt_id"] != attempt_id:
            raise EvidenceLinkError(f"截图的 source_attempt_id 与候选不一致: {candidate_id}")
        if raw.get("product_name", "").casefold() != candidate["product_name"].casefold():
            raise EvidenceLinkError(f"截图产品与候选不一致: {candidate_id}")
        if raw.get("target_page") != candidate["target_page"]:
            raise EvidenceLinkError(f"截图目标页面与候选不一致: {candidate_id}")
        for field in ("source_entry_url", "source_detail_url", "source_asset_url"):
            if field not in raw:
                raise EvidenceLinkError(f"截图缺少 {field} 角色字段: {capture_id}")
        if not raw.get("requested_url"):
            raise EvidenceLinkError(f"截图缺少 requested_url: {capture_id}")
        for field in ("source_entry_url", "source_detail_url", "source_asset_url"):
            if field in raw and raw[field]:
                actual = _url(raw[field], f"captures[{index}].{field}")
                if actual != candidate[field]:
                    raise EvidenceLinkError(f"截图的 {field} 与候选不一致: {candidate_id}")
        if raw.get("requested_url"):
            requested = _url(raw["requested_url"], f"captures[{index}].requested_url")
            allowed = {value for value in (candidate["source_detail_url"], candidate["source_asset_url"], candidate["source_entry_url"]) if value}
            if requested not in allowed:
                raise EvidenceLinkError(f"截图 requested_url 未关联候选 URL: {candidate_id}")
    return True


def validate_reviewed_material_links(registry, capture_targets, reviews, materials):
    """Validate the handoff from captures/reviews into reviewed materials.

    This deliberately checks only referential integrity and status consistency.
    It does not decide whether the image is semantically the requested page.
    """
    if not isinstance(registry, dict):
        raise EvidenceLinkError("素材关联缺少来源登记")
    candidates = {item["id"]: item for item in registry.get("candidates", [])}
    attempts = {item["id"]: item for item in registry.get("source_attempts", [])}
    capture_targets = list(capture_targets or [])
    reviews = list(reviews or [])
    materials = list(materials or [])
    captures = {item.get("id"): item for item in capture_targets if isinstance(item, dict)}
    review_ids = {item.get("target_id") for item in reviews if isinstance(item, dict)}
    if len(captures) != len(capture_targets):
        raise EvidenceLinkError("capture_targets 中存在无效记录")
    validate_capture_links(registry, capture_targets)
    for capture_id, capture in captures.items():
        if capture.get("capture_status") == "captured" and capture_id not in review_ids:
            raise EvidenceLinkError(f"captured 缺少语义审核: {capture_id}")
    for index, material in enumerate(materials):
        if not isinstance(material, dict):
            raise EvidenceLinkError(f"materials[{index}] 必须是对象")
        capture_id = material.get("capture_id")
        if not capture_id:
            if material.get("source_candidate_id") or material.get("source_type") in {"browser", "ui_database"}:
                raise EvidenceLinkError(f"在线素材缺少 capture_id: materials[{index}]")
            continue
        capture = captures.get(capture_id)
        if capture is None:
            raise EvidenceLinkError(f"素材引用未登记截图: {capture_id}")
        if capture.get("capture_status") != "captured":
            raise EvidenceLinkError(f"素材只能引用 captured 截图: {capture_id}")
        for field in ("source_candidate_id", "source_attempt_id", "product_name", "target_page"):
            if material.get(field) != capture.get(field):
                raise EvidenceLinkError(f"素材的 {field} 与截图不一致: {capture_id}")
        for field in ("source_entry_url", "source_detail_url", "source_asset_url"):
            if field in material and material.get(field) != capture.get(field):
                raise EvidenceLinkError(f"素材的 {field} 与截图不一致: {capture_id}")
        candidate_id = capture.get("source_candidate_id")
        if candidate_id not in candidates or candidates[candidate_id].get("source_attempt_id") not in attempts:
            raise EvidenceLinkError(f"素材的来源链不完整: {capture_id}")
        if capture_id not in review_ids:
            raise EvidenceLinkError(f"素材缺少对应语义审核: {capture_id}")


def build_evidence_statistics(task, source_attempts=None, candidates=None, reviews=None, materials=None, fallback_requests=None, capture_targets=None):
    source_attempts = list(source_attempts or [])
    candidates = list(candidates or [])
    reviews = list(reviews or [])
    materials = list(materials or [])
    fallback_requests = list(fallback_requests or [])
    capture_targets = list(capture_targets or [])
    source_statuses = {status: sum(1 for item in source_attempts if item.get("access_status") == status) for status in sorted(ACCESS_STATUSES)}
    unknown_access = sum(
        1 for item in source_attempts
        if item.get("access_status") == UNKNOWN
        or any(item.get(field) == UNKNOWN for field in ("web_text_accessible", "browser_accessible", "browser_interactive", "content_available"))
    )
    candidate_counts = {status: sum(1 for item in candidates if item.get("candidate_status") == status) for status in ("accepted", "rejected", "not_reviewed")}
    review_counts = {status: sum(1 for item in reviews if item.get("semantic_status") == status) for status in ("accepted", "rejected")}
    review_counts["not_reviewed"] = max(len(capture_targets) - len(reviews), 0)
    collection_counts = {status: sum(1 for item in materials if item.get("collection_status") == status) for status in ("collected", "rejected", "pending", "needs_manual_capture", "unavailable")}
    fallback_counts = {status: sum(1 for item in fallback_requests if item.get("status") == status) for status in ("resolved", "open")}
    products = {item.get("product_name", "").casefold() for item in task.get("competitors", []) if item.get("product_name")}
    collected_products = {item.get("product_name", "").casefold() for item in materials if item.get("collection_status") == "collected"}
    return {
        "sources": {"attempted": len(source_attempts), "access_status": source_statuses, "unknown_access": unknown_access},
        "candidates": candidate_counts,
        "semantic_reviews": review_counts,
        "materials": collection_counts,
        "fallback": fallback_counts,
        "coverage": {
            "planned_product_count": len(products),
            "products_with_collected_material": len(products & collected_products),
            "products_without_collected_material": len(products - collected_products),
            "pending_candidate_count": candidate_counts["not_reviewed"],
            "source_access_boundary_count": unknown_access,
        },
    }
