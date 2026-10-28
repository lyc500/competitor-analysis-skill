from copy import deepcopy
import hashlib

class ClassificationError(ValueError):
    pass

def _text(value, field):
    if not isinstance(value, str) or not value.strip():
        raise ClassificationError(f"{field} 必须是非空字符串")
    return value.strip()

def _object(value, allowed, required, field):
    if not isinstance(value, dict):
        raise ClassificationError(f"{field} 必须是对象")
    extra = set(value) - set(allowed)
    missing = set(required) - set(value)
    if extra:
        raise ClassificationError(f"{field} 包含未知字段: {', '.join(sorted(extra))}")
    if missing:
        raise ClassificationError(f"{field} 缺少字段: {', '.join(sorted(missing))}")

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
    version = classification_plan.get("schema_version", 1)
    if type(version) is not int or version not in (1, 2):
        raise ClassificationError("classification.schema_version 只支持 1 或 2")
    if version == 2:
        _object(classification_plan,
                {"schema_version", "classification_status", "classification_dimension",
                 "classification_reason", "comparison_basis", "groups", "material_labels"},
                {"schema_version", "classification_dimension", "classification_reason",
                 "comparison_basis", "groups", "material_labels"},
                "classification")
        if "classification_status" in classification_plan and classification_plan["classification_status"] != "ready":
            raise ClassificationError("新版有效分类的 classification_status 必须为 ready")
    dimension = _text(classification_plan.get("classification_dimension"), "classification_dimension")
    reason = _text(classification_plan.get("classification_reason"), "classification_reason")
    comparison_basis = None
    if version == 2:
        comparison_basis = classification_plan.get("comparison_basis")
        _object(comparison_basis, {"primary_dimension", "rationale", "scope"},
                {"primary_dimension", "rationale", "scope"}, "comparison_basis")
        comparison_basis = {key: _text(comparison_basis[key], f"comparison_basis.{key}")
                            for key in ("primary_dimension", "rationale", "scope")}
    groups = classification_plan.get("groups")
    if not isinstance(groups, list) or not groups:
        raise ClassificationError("groups 必须是非空数组")
    valid_set = set(ids); seen_names = set(); seen_group_ids = set(); assigned = [] ; output_groups = []
    for index, group in enumerate(groups):
        if not isinstance(group, dict): raise ClassificationError(f"groups[{index}] 必须是对象")
        if version == 2:
            _object(group, {"id", "name", "reason", "material_ids", "asset_ids", "audit"},
                    {"id", "name", "reason", "material_ids", "audit"}, f"groups[{index}]")
        name = _text(group.get("name"), f"groups[{index}].name"); group_reason = _text(group.get("reason"), f"groups[{index}].reason")
        group_id = _text(group["id"], f"groups[{index}].id") if "id" in group else "group-" + hashlib.sha256(name.encode("utf-8")).hexdigest()[:16]
        if group_id in seen_group_ids:
            raise ClassificationError(f"分组 ID 重复: {group_id}")
        seen_group_ids.add(group_id)
        members = group.get("material_ids")
        if not isinstance(members, list): raise ClassificationError(f"groups[{index}].material_ids 必须是数组")
        if version == 2 and not members:
            raise ClassificationError(f"groups[{index}] 新版分类不得包含空组")
        if version == 2 and "asset_ids" in group and group["asset_ids"] != members:
            raise ClassificationError(f"groups[{index}].asset_ids 必须与 material_ids 一致")
        if name in seen_names: raise ClassificationError(f"分组名称重复: {name}")
        seen_names.add(name)
        for material_id in members:
            if material_id not in valid_set:
                raise ClassificationError(f"无效素材不得分类: {material_id}" if any(m.get("id") == material_id for m in materials) else f"未知素材 ID: {material_id}")
            if material_id in assigned: raise ClassificationError(f"素材跨组重复: {material_id}")
            assigned.append(material_id)
        output_group = {"id": group_id, "name": name, "reason": group_reason,
                        "material_ids": list(members), "asset_ids": list(members)}
        if version == 2:
            audit = group.get("audit")
            _object(audit, {"inclusion_criteria", "shared_mechanism", "member_reasons", "adjacent_difference"},
                    {"inclusion_criteria", "shared_mechanism", "member_reasons", "adjacent_difference"},
                    f"groups[{index}].audit")
            output_audit = {key: _text(audit[key], f"groups[{index}].audit.{key}")
                            for key in ("inclusion_criteria", "shared_mechanism", "adjacent_difference")}
            member_reasons = audit["member_reasons"]
            if not isinstance(member_reasons, list):
                raise ClassificationError(f"groups[{index}].audit.member_reasons 必须是数组")
            seen_member_reasons = set(); normalized_reasons = []
            for reason_index, item in enumerate(member_reasons):
                _object(item, {"material_id", "reason"}, {"material_id", "reason"},
                        f"groups[{index}].audit.member_reasons[{reason_index}]")
                material_id = _text(item["material_id"], "成员理由 material_id")
                if material_id in seen_member_reasons:
                    raise ClassificationError(f"groups[{index}] 成员理由重复: {material_id}")
                seen_member_reasons.add(material_id)
                normalized_reasons.append({"material_id": material_id,
                                           "reason": _text(item["reason"], "成员理由 reason")})
            if seen_member_reasons != set(members):
                raise ClassificationError(f"groups[{index}] 成员理由必须恰好覆盖本组素材")
            output_audit["member_reasons"] = normalized_reasons
            output_group["audit"] = output_audit
        output_groups.append(output_group)
    if set(assigned) != valid_set or len(assigned) != len(valid):
        raise ClassificationError(f"collected 素材未恰好分组: {', '.join(sorted(valid_set - set(assigned)))}")
    labels = classification_plan.get("material_labels", [])
    if not isinstance(labels, list): raise ClassificationError("material_labels 必须是数组")
    output_labels = []; seen_label_ids = set()
    for index, item in enumerate(labels):
        if not isinstance(item, dict) or item.get("material_id") not in valid_set: raise ClassificationError(f"material_labels[{index}] 引用无效素材")
        if version == 2:
            _object(item, {"material_id", "labels"}, {"material_id", "labels"}, f"material_labels[{index}]")
        values = item.get("labels")
        if not isinstance(values, dict) or any(not isinstance(k, str) or not isinstance(v, str) for k, v in values.items()): raise ClassificationError(f"material_labels[{index}].labels 必须是字符串键值")
        if item["material_id"] in seen_label_ids:
            raise ClassificationError(f"material_labels[{index}] 素材标签重复")
        seen_label_ids.add(item["material_id"])
        if version == 2:
            required_labels = {"page_role", "path_stage", "interaction_stage", "render_state", "login_state"}
            if not required_labels <= set(values) or any(not values[key].strip() for key in required_labels):
                raise ClassificationError(f"material_labels[{index}] 缺少页面路径、交互阶段或登录状态标签")
        output_labels.append({"material_id": item["material_id"], "labels": deepcopy(values)})
    if version == 2 and seen_label_ids != valid_set:
        raise ClassificationError("新版分类的状态标签必须恰好覆盖全部素材")
    result = {"classification_status": "ready", "classification_dimension": dimension,
              "classification_reason": reason, "groups": output_groups, "material_labels": output_labels}
    if version == 2:
        result.update(schema_version=2, comparison_basis=comparison_basis)
    return result
