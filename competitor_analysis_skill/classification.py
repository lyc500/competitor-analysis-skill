from copy import deepcopy

class ClassificationError(ValueError):
    pass

def _text(value, field):
    if not isinstance(value, str) or not value.strip():
        raise ClassificationError(f"{field} 必须是非空字符串")
    return value.strip()

def _valid(materials):
    return [m for m in materials if m.get("collection_status") == "collected" and m.get("semantic_status") == "accepted" and m.get("quality_status") == "accepted" and isinstance(m.get("image_path"), str) and m["image_path"].strip()]

def classify_assets(materials, classification_plan=None):
    materials = list(materials or [])
    valid = _valid(materials)
    if not valid:
        return {"classification_status": "unavailable", "classification_dimension": "", "classification_reason": "当前没有有效 collected 素材", "groups": [], "material_labels": []}
    if classification_plan is None:
        raise ClassificationError("存在有效素材时必须提供 Classification Plan")
    ids = [m.get("id") for m in valid]
    if any(not isinstance(i, str) or not i for i in ids) or len(set(ids)) != len(ids):
        raise ClassificationError("collected 素材 ID 必须唯一")
    if not isinstance(classification_plan, dict):
        raise ClassificationError("Classification Plan 必须是对象")
    dimension = _text(classification_plan.get("classification_dimension"), "classification_dimension")
    reason = _text(classification_plan.get("classification_reason"), "classification_reason")
    groups = classification_plan.get("groups")
    if not isinstance(groups, list) or not groups:
        raise ClassificationError("groups 必须是非空数组")
    valid_set = set(ids); seen_names = set(); assigned = [] ; output_groups = []
    for index, group in enumerate(groups):
        if not isinstance(group, dict): raise ClassificationError(f"groups[{index}] 必须是对象")
        name = _text(group.get("name"), f"groups[{index}].name"); group_reason = _text(group.get("reason"), f"groups[{index}].reason")
        members = group.get("material_ids")
        if not isinstance(members, list): raise ClassificationError(f"groups[{index}].material_ids 必须是数组")
        if name in seen_names: raise ClassificationError(f"分组名称重复: {name}")
        seen_names.add(name)
        for material_id in members:
            if material_id not in valid_set:
                raise ClassificationError(f"无效素材不得分类: {material_id}" if any(m.get("id") == material_id for m in materials) else f"未知素材 ID: {material_id}")
            if material_id in assigned: raise ClassificationError(f"素材跨组重复: {material_id}")
            assigned.append(material_id)
        output_groups.append({"name": name, "reason": group_reason, "material_ids": list(members), "asset_ids": list(members)})
    if set(assigned) != valid_set or len(assigned) != len(valid):
        raise ClassificationError(f"collected 素材未恰好分组: {', '.join(sorted(valid_set - set(assigned)))}")
    labels = classification_plan.get("material_labels", [])
    if not isinstance(labels, list): raise ClassificationError("material_labels 必须是数组")
    output_labels = []
    for index, item in enumerate(labels):
        if not isinstance(item, dict) or item.get("material_id") not in valid_set: raise ClassificationError(f"material_labels[{index}] 引用无效素材")
        values = item.get("labels")
        if not isinstance(values, dict) or any(not isinstance(k, str) or not isinstance(v, str) for k, v in values.items()): raise ClassificationError(f"material_labels[{index}].labels 必须是字符串键值")
        output_labels.append({"material_id": item["material_id"], "labels": deepcopy(values)})
    return {"classification_status": "ready", "classification_dimension": dimension, "classification_reason": reason, "groups": output_groups, "material_labels": output_labels}
