import hashlib
from copy import deepcopy
from urllib.parse import urlsplit, urlunsplit

ALLOWED_SOURCE_TYPES = {"ui_database", "public_web"}
ALLOWED_FIELDS = {"product_name", "target_page", "source_type", "source_url", "source_title", "source_context"}


class SourceDiscoveryError(ValueError):
    pass


def normalize_url(value):
    if not isinstance(value, str) or not value.strip():
        raise SourceDiscoveryError("source_url 不能为空")
    raw = value.strip()
    parts = urlsplit(raw)
    scheme = parts.scheme.lower()
    if scheme not in {"http", "https"}:
        raise SourceDiscoveryError("source_url 仅允许 http/https")
    if parts.username is not None or parts.password is not None:
        raise SourceDiscoveryError("source_url 不得包含用户名或密码")
    if not parts.hostname:
        raise SourceDiscoveryError("source_url 缺少 hostname")
    try:
        port = parts.port
    except ValueError as exc:
        raise SourceDiscoveryError("source_url 端口无效") from exc
    host = parts.hostname.lower()
    netloc = host
    if ":" in host and not host.startswith("["):
        netloc = f"[{host}]"
    if port and not ((scheme == "http" and port == 80) or (scheme == "https" and port == 443)):
        netloc += f":{port}"
    path = parts.path or "/"
    return urlunsplit((scheme, netloc, path, parts.query, ""))


def process_sources(task, records):
    competitors = {c["product_name"].casefold() for c in task.get("competitors", [])}
    if task.get("task_status") != "ready":
        raise SourceDiscoveryError("只有 ready 任务可以处理来源候选")
    results, seen = [], set()
    for index, raw in enumerate(records):
        if not isinstance(raw, dict):
            raise SourceDiscoveryError(f"sources[{index}] 必须是对象")
        extra = set(raw) - ALLOWED_FIELDS
        if extra:
            raise SourceDiscoveryError(f"sources[{index}] 包含不允许字段: {', '.join(sorted(extra))}")
        for field in ("product_name", "target_page", "source_type", "source_url"):
            if not isinstance(raw.get(field), str) or not raw[field].strip():
                raise SourceDiscoveryError(f"sources[{index}].{field} 不能为空")
        product = raw["product_name"].strip()
        if product.casefold() not in competitors:
            raise SourceDiscoveryError(f"来源候选竞品未在任务中: {product}")
        if raw["target_page"].strip() != task["target_page"]:
            raise SourceDiscoveryError(f"sources[{index}].target_page 与任务不一致")
        if raw["source_type"] not in ALLOWED_SOURCE_TYPES:
            raise SourceDiscoveryError(f"阶段 3A 不支持 source_type: {raw['source_type']}")
        normalized = normalize_url(raw["source_url"])
        key = (product.casefold(), normalized)
        if key in seen:
            continue
        seen.add(key)
        stable = f"{product.casefold()}\n{task['target_page']}\n{normalized}".encode()
        item = {"product_name": product, "target_page": task["target_page"], "source_type": raw["source_type"], "source_url": raw["source_url"].strip(), "normalized_url": normalized, "candidate_status": "pending", "id": "src-" + hashlib.sha256(stable).hexdigest()[:16]}
        for field in ("source_title", "source_context"):
            if field in raw:
                if not isinstance(raw[field], str):
                    raise SourceDiscoveryError(f"sources[{index}].{field} 必须是字符串")
                item[field] = raw[field]
        results.append(item)
    return sorted(results, key=lambda item: (item["product_name"].casefold(), item["normalized_url"]))
