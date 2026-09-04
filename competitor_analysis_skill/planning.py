from .catalog import builtin_search_candidates


def plan_competitors(task: dict, *, fixture=False) -> list[dict]:
    if task.get("task_status") == "needs_clarification":
        return []
    if fixture:
        rows = builtin_search_candidates(task.get("regions", []))
        for row in rows:
            row.update({"platform": "Web", "target_page": task["target_page"], "planning_source": "fixture_demo"})
        return rows
    specified = task.get("specified_products", [])
    if task.get("target_page") == "直播礼物面板":
        user_rows = [_row(name, task, "user_specified", "用户明确指定的直播礼物面板竞品") for name in specified]
        additions = ["快手直播", "YouTube Live"]
        agent_rows = [_row(name, task, "agent_planned", "覆盖不同市场的直播产品补充样本") for name in additions if name.casefold() not in {n.casefold() for n in specified}]
        result = user_rows + agent_rows
    elif task.get("target_page") == "搜索结果页":
        names = ["百度", "小红书", "Google", "Bing", "Amazon"]
        result = [_row(name, task, "agent_planned", "与搜索结果页直接相关的代表性产品") for name in names]
    else:
        result = []
    return result


def _row(name, task, source, reason):
    region = "CN" if name in {"百度", "小红书", "虎牙", "斗鱼", "抖音", "快手直播"} else "Global"
    return {"product_name": name, "region": region, "product_type": "直播产品" if task["target_page"] == "直播礼物面板" else "综合搜索", "platform": "Web", "target_page": task["target_page"], "target_url": "", "planning_source": source, "priority": "high" if source == "user_specified" else "medium", "reason": reason, "planning_status": "planned"}
