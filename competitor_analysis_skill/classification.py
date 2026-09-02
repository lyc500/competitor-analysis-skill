def classify_assets(assets: list[dict]) -> dict:
    dimension = _choose_dimension(assets)
    groups = {}
    for asset in assets:
        label = _label(asset, dimension)
        groups.setdefault(label, []).append(asset["id"])
    return {"classification_dimension": dimension,
            "groups": [{"name": name, "reason": _reason(name), "asset_ids": ids} for name, ids in groups.items()]}


def _choose_dimension(assets):
    values = {asset.get("region") for asset in assets}
    if len(values) > 1 and len({asset.get("product_type") for asset in assets}) == 1:
        return "地区"
    types = {asset.get("product_type") for asset in assets}
    if len(types) > 1 and len(values) == 1:
        return "产品类型"
    return "页面结构模式"


def _label(asset, dimension):
    if dimension == "地区":
        return asset.get("region", "未知地区")
    if dimension == "产品类型":
        return asset.get("product_type", "未知类型")
    return _mode(asset)


def _mode(asset):
    text = f"{asset.get('notes', '')} {asset.get('product_type', '')}"
    if "流" in text or "feed" in text.lower():
        return "连续内容流"
    if "分栏" in text or "筛选" in text or asset.get("product_type") == "电商":
        return "分栏筛选"
    return "综合结果"


def _reason(name):
    return {"连续内容流": "结果以连续内容流为主要组织方式", "分栏筛选": "通过分栏和筛选组织大量结果", "综合结果": "以综合结果列表承载多种内容"}.get(name, f"按{name}归组，便于横向浏览")
