from pathlib import Path


class ManualCaptureError(ValueError):
    pass


ALLOWED_SOURCE_TYPES = {"user_upload", "device_capture"}


def process_manual_captures(task, records):
    if not isinstance(records, list):
        raise ManualCaptureError("manual_captures 必须是数组")
    competitors = {item["product_name"].casefold(): item for item in task["competitors"]}
    seen = set()
    result = []
    for index, raw in enumerate(records):
        if not isinstance(raw, dict):
            raise ManualCaptureError(f"manual_captures[{index}] 必须是对象")
        for field in ("id", "product_name", "target_page", "source_type", "image_path"):
            value = raw.get(field)
            if not isinstance(value, str) or not value.strip():
                raise ManualCaptureError(f"manual_captures[{index}].{field} 不能为空")
        item = dict(raw)
        item["id"] = item["id"].strip()
        item["product_name"] = item["product_name"].strip()
        item["target_page"] = item["target_page"].strip()
        item["source_type"] = item["source_type"].strip()
        if item["id"] in seen:
            raise ManualCaptureError(f"manual capture ID 重复: {item['id']}")
        seen.add(item["id"])
        if item["product_name"].casefold() not in competitors:
            raise ManualCaptureError(f"manual capture 竞品未在任务中: {item['product_name']}")
        if item["target_page"] != task["target_page"]:
            raise ManualCaptureError("manual capture target_page 与任务不一致")
        if item["source_type"] not in ALLOWED_SOURCE_TYPES:
            raise ManualCaptureError(f"无效 source_type: {item['source_type']}")
        item["image_path"] = item["image_path"].strip()
        result.append(item)
    return result
