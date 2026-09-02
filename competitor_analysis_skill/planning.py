from .catalog import builtin_search_candidates
from .requirements import ResearchTask


def plan_competitors(task: ResearchTask) -> list[dict]:
    selected = builtin_search_candidates(task.regions)
    if task.specified_products:
        named = {name.lower() for name in task.specified_products}
        selected = [row for row in selected if row["product_name"].lower() in named]
    return selected
