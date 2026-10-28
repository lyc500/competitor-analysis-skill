"""Mechanical contract for source-access preparation and resume evidence.

The Agent decides which sources matter, observes the browser, judges coverage
impact and writes the record.  This module only validates shape, references,
time order and resume bookkeeping.  It never infers login state from page text.
"""

from copy import deepcopy
from datetime import datetime


BOOL_OR_UNKNOWN = {True, False, "unknown"}
PHASES = {"preflight", "recheck"}
SESSION_KINDS = {"agent_browser", "playwright_batch", "external_browser"}
AUTH_STATES = {"authenticated", "anonymous", "unknown", "expired"}
ACCESS_BARRIERS = {
    "none", "login_required", "paywall", "security_verification",
    "network_error", "empty_results", "session_expired", "unknown",
}
COVERAGE_IMPACTS = {"none", "minor", "material"}
DECISION_STATUSES = {"not_required", "pending_user_choice", "public_only", "login_then_continue"}
RESUME_STATUSES = {"not_needed", "waiting_for_login", "resumed", "partial", "blocked"}

TOP_LEVEL_FIELDS = {
    "schema_version", "id", "research_scope", "started_at", "completed_at",
    "relevant_source_attempt_ids", "checks", "decision", "resume",
}
CHECK_FIELDS = {
    "id", "source_attempt_id", "phase", "checked_at", "browser_session_id",
    "browser_session_kind", "browser_tab_id", "page_open", "search_usable",
    "filter_usable", "detail_usable", "original_asset_usable",
    "pagination_usable", "authentication_state", "access_barrier",
    "visible_scope", "coverage_impact", "notes",
}
DECISION_FIELDS = {
    "status", "prompted_at", "decided_at", "restricted_source_attempt_ids", "summary",
}
RESUME_FIELDS = {
    "status", "checkpoint_candidate_ids", "completed_candidate_ids",
    "remaining_candidate_ids", "recheck_ids", "resumed_at",
}


class SourceAccessError(ValueError):
    pass


def _strict_fields(value, allowed, field, required=None):
    if not isinstance(value, dict):
        raise SourceAccessError(f"{field} 必须是对象")
    extra = set(value) - allowed
    missing = (required if required is not None else allowed) - set(value)
    if extra:
        raise SourceAccessError(f"{field} 包含不允许字段: {', '.join(sorted(extra))}")
    if missing:
        raise SourceAccessError(f"{field} 缺少字段: {', '.join(sorted(missing))}")


def _text(value, field, allow_empty=False):
    if not isinstance(value, str) or (not allow_empty and not value.strip()):
        qualifier = "字符串" if allow_empty else "非空字符串"
        raise SourceAccessError(f"{field} 必须是{qualifier}")
    return value.strip()


def _timestamp(value, field, allow_empty=False):
    text = _text(value, field, allow_empty=allow_empty)
    if not text and allow_empty:
        return "", None
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise SourceAccessError(f"{field} 必须是 ISO 8601 时间") from exc
    if parsed.tzinfo is None:
        raise SourceAccessError(f"{field} 必须包含时区")
    return text, parsed


def _unique_ids(value, field, known=None):
    if not isinstance(value, list) or not all(isinstance(item, str) and item.strip() for item in value):
        raise SourceAccessError(f"{field} 必须是字符串 ID 数组")
    result = [item.strip() for item in value]
    if len(result) != len(set(result)):
        raise SourceAccessError(f"{field} 不得包含重复 ID")
    if known is not None:
        unknown = set(result) - set(known)
        if unknown:
            raise SourceAccessError(f"{field} 引用未知 ID: {', '.join(sorted(unknown))}")
    return result


def _validate_check(raw, index, attempt_ids):
    field = f"access_preparation.checks[{index}]"
    _strict_fields(raw, CHECK_FIELDS, field)
    item = deepcopy(raw)
    for key in ("id", "source_attempt_id", "browser_session_id", "browser_tab_id", "visible_scope"):
        item[key] = _text(item[key], f"{field}.{key}")
    item["notes"] = _text(item["notes"], f"{field}.notes", allow_empty=True)
    if item["source_attempt_id"] not in attempt_ids:
        raise SourceAccessError(f"{field}.source_attempt_id 未登记")
    if item["phase"] not in PHASES:
        raise SourceAccessError(f"{field}.phase 无效")
    if item["browser_session_kind"] not in SESSION_KINDS:
        raise SourceAccessError(f"{field}.browser_session_kind 无效")
    item["checked_at"], checked_at = _timestamp(item["checked_at"], f"{field}.checked_at")
    for key in (
        "page_open", "search_usable", "filter_usable", "detail_usable",
        "original_asset_usable", "pagination_usable",
    ):
        if item[key] not in BOOL_OR_UNKNOWN:
            raise SourceAccessError(f"{field}.{key} 必须是布尔值或 unknown")
    if item["authentication_state"] not in AUTH_STATES:
        raise SourceAccessError(f"{field}.authentication_state 无效")
    if item["access_barrier"] not in ACCESS_BARRIERS:
        raise SourceAccessError(f"{field}.access_barrier 无效")
    if item["coverage_impact"] not in COVERAGE_IMPACTS:
        raise SourceAccessError(f"{field}.coverage_impact 无效")
    if item["access_barrier"] == "network_error" and item["authentication_state"] not in {"unknown", "expired"}:
        raise SourceAccessError(f"{field} 网络异常不能证明登录状态")
    if item["access_barrier"] == "session_expired" and item["authentication_state"] != "expired":
        raise SourceAccessError(f"{field} 会话过期必须标记 authentication_state=expired")
    return item, checked_at


def validate_source_access(raw, source_attempts, candidates):
    """Validate one preflight/decision/recheck/resume batch.

    The returned data is safe to embed in the existing discovery ledger.  It
    contains browser/session labels and observations, never cookies, passwords,
    verification codes or storage state.
    """
    _strict_fields(raw, TOP_LEVEL_FIELDS | {"current_checks_by_source"}, "access_preparation",
                   required=TOP_LEVEL_FIELDS)
    if raw["schema_version"] != 1:
        raise SourceAccessError("access_preparation.schema_version 必须为 1")
    item = deepcopy(raw)
    item["id"] = _text(item["id"], "access_preparation.id")
    item["research_scope"] = _text(item["research_scope"], "access_preparation.research_scope")
    item["started_at"], started_at = _timestamp(item["started_at"], "access_preparation.started_at")
    item["completed_at"], completed_at = _timestamp(item["completed_at"], "access_preparation.completed_at")
    if completed_at < started_at:
        raise SourceAccessError("access_preparation.completed_at 不得早于 started_at")

    attempt_ids = {attempt.get("id") for attempt in source_attempts if isinstance(attempt, dict)}
    relevant = _unique_ids(item["relevant_source_attempt_ids"], "access_preparation.relevant_source_attempt_ids", attempt_ids)
    if not relevant:
        raise SourceAccessError("access_preparation 必须包含至少一个相关来源")
    item["relevant_source_attempt_ids"] = relevant

    if not isinstance(item["checks"], list) or not item["checks"]:
        raise SourceAccessError("access_preparation.checks 必须是非空数组")
    checks = []
    check_times = {}
    check_by_id = {}
    source_checks = {attempt_id: [] for attempt_id in relevant}
    for index, raw_check in enumerate(item["checks"]):
        check, checked_at = _validate_check(raw_check, index, attempt_ids)
        if check["id"] in check_by_id:
            raise SourceAccessError(f"来源能力检查 ID 重复: {check['id']}")
        if check["source_attempt_id"] not in source_checks:
            raise SourceAccessError("来源能力检查不属于本批相关来源")
        if checked_at < started_at or checked_at > completed_at:
            raise SourceAccessError("来源能力检查时间必须位于预检批次时间内")
        check_by_id[check["id"]] = check
        check_times[check["id"]] = checked_at
        source_checks[check["source_attempt_id"]].append(check)
        checks.append(check)
    for attempt_id, values in source_checks.items():
        if not any(check["phase"] == "preflight" for check in values):
            raise SourceAccessError(f"相关来源缺少 preflight 检查: {attempt_id}")
        values.sort(key=lambda value: check_times[value["id"]])
    item["checks"] = checks

    _strict_fields(item["decision"], DECISION_FIELDS | {"choice_is_final_for_batch"},
                   "access_preparation.decision", required=DECISION_FIELDS)
    decision = deepcopy(item["decision"])
    if decision["status"] not in DECISION_STATUSES:
        raise SourceAccessError("access_preparation.decision.status 无效")
    decision["prompted_at"], prompted_at = _timestamp(
        decision["prompted_at"], "access_preparation.decision.prompted_at", allow_empty=True,
    )
    decision["decided_at"], decided_at = _timestamp(
        decision["decided_at"], "access_preparation.decision.decided_at", allow_empty=True,
    )
    decision["summary"] = _text(decision["summary"], "access_preparation.decision.summary")
    decision["restricted_source_attempt_ids"] = _unique_ids(
        decision["restricted_source_attempt_ids"],
        "access_preparation.decision.restricted_source_attempt_ids", relevant,
    )
    for label, value in (("prompted_at", prompted_at), ("decided_at", decided_at)):
        if value and not started_at <= value <= completed_at:
            raise SourceAccessError(f"access_preparation.decision.{label} 必须位于预检批次时间内")

    current_by_source = {
        attempt_id: max(values, key=lambda value: check_times[value["id"]])
        for attempt_id, values in source_checks.items()
    }
    current_auth_restricted = {
        attempt_id for attempt_id, check in current_by_source.items()
        if check["coverage_impact"] == "material" and check["access_barrier"] in {
            "login_required", "security_verification", "session_expired",
        }
    }
    preflight_by_source = {
        attempt_id: max(
            (check for check in values if check["phase"] == "preflight"),
            key=lambda value: check_times[value["id"]],
        )
        for attempt_id, values in source_checks.items()
    }
    preflight_auth_restricted = {
        attempt_id for attempt_id, check in preflight_by_source.items()
        if check["coverage_impact"] == "material" and check["access_barrier"] in {
            "login_required", "security_verification", "session_expired",
        }
    }
    restricted = set(decision["restricted_source_attempt_ids"])
    if decision["status"] == "not_required":
        if current_auth_restricted:
            raise SourceAccessError("当前仍有重大认证限制，不能标记为 not_required；必须取得用户选择")
        if restricted or prompted_at or not decided_at:
            raise SourceAccessError("无需用户选择时不得登记受限来源或提示时间，并须完成决定")
    else:
        expected_restricted = preflight_auth_restricted if decision["status"] == "login_then_continue" else current_auth_restricted
        if restricted != expected_restricted:
            raise SourceAccessError("用户选择涉及的受限来源必须与当前重大登录限制一致")
        if not restricted or not prompted_at:
            raise SourceAccessError("登录限制影响覆盖时必须一次汇总受限来源")
        if decision["status"] == "pending_user_choice" and decided_at:
            raise SourceAccessError("等待用户选择时不得填写 decided_at")
        if decision["status"] != "pending_user_choice" and not decided_at:
            raise SourceAccessError("用户已选择时必须填写 decided_at")
        if decided_at and decided_at < prompted_at:
            raise SourceAccessError("用户决定时间不得早于提示时间")
    derived_choice_final = decision["status"] == "public_only"
    supplied_choice_final = item["decision"].get("choice_is_final_for_batch")
    if supplied_choice_final is not None and supplied_choice_final is not derived_choice_final:
        raise SourceAccessError("access_preparation.decision.choice_is_final_for_batch 与决定状态不一致")
    decision["choice_is_final_for_batch"] = derived_choice_final
    item["decision"] = decision

    _strict_fields(item["resume"], RESUME_FIELDS, "access_preparation.resume")
    resume = deepcopy(item["resume"])
    if resume["status"] not in RESUME_STATUSES:
        raise SourceAccessError("access_preparation.resume.status 无效")
    candidate_ids = {candidate.get("id") for candidate in candidates if isinstance(candidate, dict) and candidate.get("id")}
    for key in ("checkpoint_candidate_ids", "completed_candidate_ids", "remaining_candidate_ids"):
        resume[key] = _unique_ids(resume[key], f"access_preparation.resume.{key}", candidate_ids)
    completed = set(resume["completed_candidate_ids"])
    remaining = set(resume["remaining_candidate_ids"])
    if completed & remaining:
        raise SourceAccessError("恢复记录的已完成与待继续候选不得重复")
    if candidate_ids and resume["status"] in {"resumed", "partial", "blocked"} and completed | remaining != candidate_ids:
        raise SourceAccessError("恢复记录必须完整覆盖候选，不能重复计数或丢失")
    if not set(resume["checkpoint_candidate_ids"]).issubset(completed):
        raise SourceAccessError("恢复检查点候选必须属于已完成候选")
    resume["recheck_ids"] = _unique_ids(
        resume["recheck_ids"], "access_preparation.resume.recheck_ids", check_by_id,
    )
    for recheck_id in resume["recheck_ids"]:
        if check_by_id[recheck_id]["phase"] != "recheck":
            raise SourceAccessError("恢复记录只能引用 recheck 检查")
    resume["resumed_at"], resumed_at = _timestamp(
        resume["resumed_at"], "access_preparation.resume.resumed_at", allow_empty=True,
    )
    if resumed_at and not started_at <= resumed_at <= completed_at:
        raise SourceAccessError("access_preparation.resume.resumed_at 必须位于预检批次时间内")

    if decision["status"] == "login_then_continue":
        if resume["status"] not in {"waiting_for_login", "resumed", "partial", "blocked"}:
            raise SourceAccessError("选择登录后继续时恢复状态无效")
        if resume["status"] in {"resumed", "partial", "blocked"}:
            if not resume["recheck_ids"] or not resumed_at:
                raise SourceAccessError("登录后恢复必须保存复查记录和恢复时间")
            for recheck_id in resume["recheck_ids"]:
                recheck = check_by_id[recheck_id]
                preflights = [
                    check for check in source_checks[recheck["source_attempt_id"]]
                    if check["phase"] == "preflight" and check_times[check["id"]] < check_times[recheck_id]
                ]
                if not preflights:
                    raise SourceAccessError("登录后复查必须晚于同一来源的预检")
                if all(check["browser_session_id"] != recheck["browser_session_id"] for check in preflights):
                    raise SourceAccessError("登录后复查必须复用有效浏览器会话")
                if decided_at and check_times[recheck_id] < decided_at:
                    raise SourceAccessError("登录后复查不得早于用户决定")
            if resumed_at < max(check_times[check_id] for check_id in resume["recheck_ids"]):
                raise SourceAccessError("恢复时间不得早于复查时间")
            if resume["status"] == "resumed" and any(
                check_by_id[check_id]["coverage_impact"] == "material"
                for check_id in resume["recheck_ids"]
            ):
                raise SourceAccessError("复查后仍有重大覆盖限制时不能标记为完全恢复")
        elif resume["recheck_ids"] or resumed_at:
            raise SourceAccessError("等待登录时不得提前登记复查或恢复时间")
    elif resume["status"] != "not_needed":
        raise SourceAccessError("未选择登录时不应登记登录恢复状态")
    elif resume["recheck_ids"] or resumed_at or any(
        resume[key] for key in ("checkpoint_candidate_ids", "completed_candidate_ids", "remaining_candidate_ids")
    ):
        raise SourceAccessError("无需登录恢复时不得登记恢复候选、复查或恢复时间")

    item["resume"] = resume
    derived_current = {
        attempt_id: current_by_source[attempt_id]["id"] for attempt_id in relevant
    }
    supplied_current = raw.get("current_checks_by_source")
    if supplied_current is not None and supplied_current != derived_current:
        raise SourceAccessError("access_preparation.current_checks_by_source 与检查记录不一致")
    item["current_checks_by_source"] = derived_current
    return item
