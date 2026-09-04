from .task_contract import ContractError, validate_task


def plan_competitors(task: dict, *, fixture=False) -> list[dict]:
    if task.get("task_status") == "needs_clarification":
        return []
    if fixture:
        if task.get("planning_strategy") != "fixture_demo":
            raise ContractError("固定目录只能通过 planning_strategy=fixture_demo 显式启用")
        from .catalog import builtin_search_candidates
        rows = builtin_search_candidates(task.get("regions", []))
        for row in rows:
            row.update({"platform": "Web", "target_page": task["target_page"], "planning_source": "fixture_demo"})
        return rows
    competitors = [dict(row) for row in task.get("competitors", [])]
    ordered = [row for _, row in sorted(enumerate(competitors), key=lambda item: (
        0 if item[1]["planning_source"] == "user_specified" else 1,
        item[1]["priority"] != "high", item[0]))]
    candidate = dict(task)
    candidate["competitors"] = ordered
    validate_task(candidate)
    return ordered
