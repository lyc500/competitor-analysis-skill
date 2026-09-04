from copy import deepcopy


TASK_STATUSES = {"planned", "needs_clarification", "ready", "blocked", "completed"}
PLANNING_STRATEGIES = {"user_only", "agent_only", "mixed", "fixture_demo"}
PLANNING_SOURCES = {"user_specified", "agent_planned", "fixture_demo"}
REQUIRED_TASK_FIELDS = {
    "raw_request", "research_goal", "target_page", "regions", "specified_products",
    "assumptions", "needs_clarification", "task_status", "planning_strategy", "competitors",
}
REQUIRED_COMPETITOR_FIELDS = {
    "product_name", "region", "product_type", "platform", "target_page",
    "planning_source", "priority", "reason",
}


class ContractError(ValueError):
    """Raised when a task violates the stage 1 data contract."""


class StructuredTask(dict):
    """Mapping with attribute access for compatibility with the existing pipeline."""

    def __getattr__(self, name):
        if name == "request":
            return self["raw_request"]
        try:
            return self[name]
        except KeyError as exc:
            raise AttributeError(name) from exc

    def to_dict(self):
        return deepcopy(dict(self))


def validate_task(task):
    if not isinstance(task, dict):
        raise ContractError("task 必须是对象")
    missing = REQUIRED_TASK_FIELDS - set(task)
    if missing:
        raise ContractError(f"任务缺少字段: {', '.join(sorted(missing))}")
    if not isinstance(task["raw_request"], str) or not task["raw_request"].strip():
        raise ContractError("raw_request 不能为空")
    if not isinstance(task["target_page"], str) or not task["target_page"].strip():
        raise ContractError("target_page 不能为空")
    if task["task_status"] not in TASK_STATUSES:
        raise ContractError(f"无效 task_status: {task['task_status']}")
    if task["planning_strategy"] not in PLANNING_STRATEGIES:
        raise ContractError(f"无效 planning_strategy: {task['planning_strategy']}")
    if not isinstance(task["needs_clarification"], bool):
        raise ContractError("needs_clarification 必须是布尔值")
    if task["needs_clarification"] != (task["task_status"] == "needs_clarification"):
        raise ContractError("needs_clarification 与 task_status 不一致")
    if task["task_status"] == "ready" and not task["competitors"]:
        raise ContractError("ready 任务必须包含竞品")
    if task["task_status"] == "needs_clarification" and task["competitors"]:
        raise ContractError("needs_clarification 任务不能包含竞品计划")
    if not isinstance(task["regions"], list) or not isinstance(task["specified_products"], list):
        raise ContractError("regions 和 specified_products 必须是数组")
    if not isinstance(task["assumptions"], list):
        raise ContractError("assumptions 必须是数组")

    sources = []
    specified = {name.casefold() for name in task["specified_products"]}
    seen_products = set()
    for index, competitor in enumerate(task["competitors"]):
        if not isinstance(competitor, dict):
            raise ContractError(f"competitors[{index}] 必须是对象")
        missing_competitor = REQUIRED_COMPETITOR_FIELDS - set(competitor)
        if missing_competitor:
            raise ContractError(f"competitors[{index}] 缺少字段: {', '.join(sorted(missing_competitor))}")
        source = competitor["planning_source"]
        if source not in PLANNING_SOURCES:
            raise ContractError(f"无效 planning_source: {source}")
        sources.append(source)
        name = competitor["product_name"]
        if name.casefold() in seen_products:
            raise ContractError(f"竞品重复: {name}")
        seen_products.add(name.casefold())
        if source == "user_specified" and name.casefold() not in specified:
            raise ContractError(f"user_specified 竞品未出现在 specified_products: {name}")
        if source != "user_specified" and name.casefold() in specified:
            raise ContractError(f"指定竞品必须标记为 user_specified: {name}")
    if task["task_status"] == "ready":
        expected = ("user_only" if sources and all(s == "user_specified" for s in sources)
                    else "agent_only" if sources and all(s == "agent_planned" for s in sources)
                    else "fixture_demo" if sources and all(s == "fixture_demo" for s in sources)
                    else "mixed")
        if task["planning_strategy"] != expected:
            raise ContractError(f"planning_strategy 与竞品来源不一致，应为 {expected}")
    elif task["planning_strategy"] == "fixture_demo":
        raise ContractError("fixture_demo 只能用于显式 fixture 任务")
    if task["planning_strategy"] == "fixture_demo" and not sources:
        raise ContractError("fixture_demo 任务必须显式提供 fixture 竞品")
    if task["planning_strategy"] == "fixture_demo" and any(s != "fixture_demo" for s in sources):
        raise ContractError("fixture_demo 任务只能包含 fixture_demo 竞品")
    return task


def make_task(**values):
    task = StructuredTask(values)
    validate_task(task)
    return task
