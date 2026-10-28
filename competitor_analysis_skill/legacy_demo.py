"""Bounded natural-language parser for the historical offline demo.

This module deliberately contains the fixed example mappings.  The formal
``--task-file`` workflow never imports their result or uses them for semantic
classification.
"""

import re

from .task_contract import StructuredTask, validate_task


def parse_legacy_demo_request(request: str) -> StructuredTask:
    if not isinstance(request, str) or not request.strip():
        raise ValueError("request 不能为空")
    target_page = _target_page(request)
    specified = _specified_products(request, target_page)
    regions = ["CN", "Global"] if re.search(r"海内外|国内外", request) else []
    assumptions = []
    if not regions and target_page and re.search(r"热门产品", request):
        assumptions.append("按用户使用‘热门产品’语义，竞品范围由 Agent 规划；用户未指定地区")
    needs_clarification = target_page is None or (target_page == "搜索结果页" and not regions)
    task = StructuredTask({
        "raw_request": request,
        "request": request,
        "research_goal": "为产品设计提供页面参考",
        "target_page": target_page or "待确认页面",
        "regions": regions,
        "product_scope": ["直播产品"] if target_page == "直播礼物面板" else [],
        "specified_products": specified,
        "platforms": ["Web", "iOS", "Android"] if target_page == "直播礼物面板" else [],
        "constraints": [],
        "assumptions": assumptions,
        "needs_clarification": needs_clarification,
        "task_status": "needs_clarification" if needs_clarification else "planned",
        "planning_strategy": "user_only" if specified else "agent_only",
        "competitors": [],
    })
    if not needs_clarification:
        task["assumptions"].append(
            "legacy/demo 自然语言入口仅覆盖固定示例，不承担通用语义理解；正式流程应使用 Agent 任务文件"
        )
    validate_task(task)
    return task


def _target_page(request):
    if re.search(r"搜索结果页|search results page", request, re.I):
        return "搜索结果页"
    if re.search(r"直播.*礼物面板|礼物面板.*直播", request):
        return "直播礼物面板"
    return None


def _specified_products(request, target_page):
    if target_page != "直播礼物面板":
        return []
    names = []
    for pattern, name in (
        (r"虎牙", "虎牙"),
        (r"斗鱼", "斗鱼"),
        (r"抖音(?:直播)?", "抖音"),
        (r"\bTwitch\b", "Twitch"),
    ):
        if re.search(pattern, request, re.I):
            names.append(name)
    return names


__all__ = ["parse_legacy_demo_request"]
