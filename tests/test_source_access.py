import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from competitor_analysis_skill.evidence import validate_discovery_payload
from competitor_analysis_skill.pipeline import run_pipeline
from competitor_analysis_skill.source_access import SourceAccessError, validate_source_access


class SourceAccessContractTests(unittest.TestCase):
    def task(self):
        return {
            "raw_request": "搜集我的页",
            "research_goal": "比较个人中心",
            "target_page": "我的页",
            "target_surface": "mobile_app",
            "regions": ["CN", "Global"],
            "platforms": ["iOS", "Android"],
            "specified_products": [],
            "assumptions": [],
            "needs_clarification": False,
            "task_status": "ready",
            "planning_strategy": "agent_only",
            "competitors": [{
                "product_name": "产品A", "region": "CN", "product_type": "工具",
                "platform": "iOS", "target_page": "我的页",
                "planning_source": "agent_planned", "priority": "high", "reason": "代表性",
            }],
        }

    def attempt(self, attempt_id="att-ui"):
        return {
            "id": attempt_id,
            "source_type": "ui_database",
            "source_provider": "UI DB",
            "entry_url": "https://example.com/search",
            "query_mapping": {
                "raw_page_intent": "我的页",
                "mapped_terms": ["Profile"],
                "source_taxonomy_terms": ["Account"],
            },
            "actual_query": "Profile",
            "search_mode": "taxonomy",
            "discovery_batch": 1,
            "web_text_accessible": "unknown",
            "browser_accessible": True,
            "browser_interactive": True,
            "content_available": True,
            "access_status": "accessible",
            "observed_scope": "结果首屏与详情",
            "attempt_status": "completed",
            "failure_reason": "",
        }

    def check(self, **overrides):
        value = {
            "id": "check-preflight-ui",
            "source_attempt_id": "att-ui",
            "phase": "preflight",
            "checked_at": "2026-10-27T10:00:00+00:00",
            "browser_session_id": "chrome-user1",
            "browser_session_kind": "agent_browser",
            "browser_tab_id": "tab-a",
            "page_open": True,
            "search_usable": True,
            "filter_usable": True,
            "detail_usable": True,
            "original_asset_usable": True,
            "pagination_usable": True,
            "authentication_state": "authenticated",
            "access_barrier": "none",
            "visible_scope": "搜索、筛选、详情、原图和下一页均可用",
            "coverage_impact": "none",
            "notes": "复用现有标签",
        }
        value.update(overrides)
        return value

    def preparation(self, checks=None, decision=None, resume=None):
        return {
            "schema_version": 1,
            "id": "access-batch-1",
            "research_scope": "我的页公开来源",
            "started_at": "2026-10-27T09:59:00+00:00",
            "completed_at": "2026-10-27T10:12:00+00:00",
            "relevant_source_attempt_ids": ["att-ui"],
            "checks": checks or [self.check()],
            "decision": decision or {
                "status": "not_required",
                "prompted_at": "",
                "decided_at": "2026-10-27T10:01:00+00:00",
                "restricted_source_attempt_ids": [],
                "summary": "相关来源能力可用，不阻塞采集",
            },
            "resume": resume or {
                "status": "not_needed",
                "checkpoint_candidate_ids": [],
                "completed_candidate_ids": [],
                "remaining_candidate_ids": [],
                "recheck_ids": [],
                "resumed_at": "",
            },
        }

    def candidate(self, candidate_id="cand-1", rank=1):
        return {
            "id": candidate_id, "source_attempt_id": "att-ui", "product_name": "产品A",
            "target_page": "我的页", "source_entry_url": "https://example.com/search",
            "source_detail_url": f"https://example.com/detail/{rank}", "source_asset_url": "",
            "candidate_rank": rank, "candidate_status": "accepted", "disposition_reason": "进入审核",
        }

    def discovery_payload(self, candidates, preparation):
        return {
            "source_attempts": [self.attempt()],
            "candidates": candidates,
            "candidate_pool": [candidate["id"] for candidate in candidates],
            "candidate_limit": {
                "max": 50, "unit": "candidate_records", "applies_to": "candidate_pool",
                "ordering_basis": "相关性", "truncated_candidate_ids": [],
            },
            "access_preparation": preparation,
        }

    def capture_record(self, candidate_id="cand-1", rank=1):
        return {
            "id": f"cap-{candidate_id}", "source_candidate_id": candidate_id,
            "source_attempt_id": "att-ui", "product_name": "产品A", "target_page": "我的页",
            "source_entry_url": "https://example.com/search",
            "source_detail_url": f"https://example.com/detail/{rank}", "source_asset_url": "",
            "requested_url": f"https://example.com/detail/{rank}",
            "capture_status": "captured", "quality_status": "accepted",
            "screenshot_path": f"captures/cap-{candidate_id}.png",
        }

    def save_completed_capture(self, output, candidate_id="cand-1", rank=1):
        capture_dir = output / "captures"
        capture_dir.mkdir(parents=True, exist_ok=True)
        fixture = Path(__file__).parent / "fixtures" / "materials" / "valid.png"
        (capture_dir / f"cap-{candidate_id}.png").write_bytes(fixture.read_bytes())
        (output / "captures.json").write_text(json.dumps({
            "captures": [self.capture_record(candidate_id, rank)],
        }, ensure_ascii=False), encoding="utf-8")

    def test_public_or_authenticated_source_can_continue_without_prompt(self):
        result = validate_source_access(self.preparation(), [self.attempt()], [])
        self.assertEqual(result["decision"]["status"], "not_required")
        self.assertEqual(result["checks"][0]["browser_session_id"], "chrome-user1")

    def test_normalized_access_record_can_be_saved_and_validated_again(self):
        first = validate_source_access(self.preparation(), [self.attempt()], [])
        second = validate_source_access(first, [self.attempt()], [])
        self.assertEqual(second, first)
        first["current_checks_by_source"]["att-ui"] = "missing-check"
        with self.assertRaisesRegex(SourceAccessError, "检查记录不一致"):
            validate_source_access(first, [self.attempt()], [])

    def test_material_login_limits_require_one_pending_choice(self):
        check = self.check(
            authentication_state="anonymous", access_barrier="login_required",
            detail_usable=False, original_asset_usable=False, pagination_usable=False,
            coverage_impact="material", visible_scope="仅能看首屏缩略图",
        )
        decision = {
            "status": "pending_user_choice",
            "prompted_at": "2026-10-27T10:01:00+00:00",
            "decided_at": "",
            "restricted_source_attempt_ids": ["att-ui"],
            "summary": "详情、原图和分页受登录限制；等待一次性选择",
        }
        result = validate_source_access(self.preparation([check], decision), [self.attempt()], [])
        self.assertEqual(result["decision"]["status"], "pending_user_choice")

    def test_material_auth_limit_cannot_be_marked_not_required(self):
        check = self.check(
            authentication_state="anonymous", access_barrier="login_required",
            detail_usable=False, original_asset_usable=False, pagination_usable=False,
            coverage_impact="material", visible_scope="仅能看公开缩略图",
        )
        with self.assertRaisesRegex(SourceAccessError, "重大认证限制.*用户选择"):
            validate_source_access(self.preparation([check]), [self.attempt()], [])

    def test_public_only_choice_is_final_for_same_batch(self):
        check = self.check(
            authentication_state="anonymous", access_barrier="login_required",
            detail_usable=False, original_asset_usable=False, pagination_usable=False,
            coverage_impact="material", visible_scope="公开首屏",
        )
        decision = {
            "status": "public_only",
            "prompted_at": "2026-10-27T10:01:00+00:00",
            "decided_at": "2026-10-27T10:02:00+00:00",
            "restricted_source_attempt_ids": ["att-ui"],
            "summary": "用户选择本轮只使用公开内容；同一限制不再询问",
        }
        result = validate_source_access(self.preparation([check], decision), [self.attempt()], [])
        self.assertEqual(result["decision"]["status"], "public_only")
        self.assertTrue(result["decision"]["choice_is_final_for_batch"])

    def test_login_resume_requires_later_recheck_in_same_session(self):
        before = self.check(
            authentication_state="anonymous", access_barrier="login_required",
            detail_usable=False, original_asset_usable=False, pagination_usable=False,
            coverage_impact="material", visible_scope="公开首屏",
        )
        after = self.check(
            id="check-recheck-ui", phase="recheck",
            checked_at="2026-10-27T10:10:00+00:00", browser_tab_id="tab-b",
            authentication_state="authenticated", access_barrier="none",
            coverage_impact="none", visible_scope="登录后复查全部能力可用",
        )
        decision = {
            "status": "login_then_continue",
            "prompted_at": "2026-10-27T10:01:00+00:00",
            "decided_at": "2026-10-27T10:02:00+00:00",
            "restricted_source_attempt_ids": ["att-ui"],
            "summary": "用户选择登录后继续",
        }
        resume = {
            "status": "resumed",
            "checkpoint_candidate_ids": [],
            "completed_candidate_ids": [],
            "remaining_candidate_ids": [],
            "recheck_ids": ["check-recheck-ui"],
            "resumed_at": "2026-10-27T10:11:00+00:00",
        }
        result = validate_source_access(self.preparation([before, after], decision, resume), [self.attempt()], [])
        self.assertEqual(result["resume"]["status"], "resumed")
        self.assertEqual(result["checks"][1]["browser_session_id"], "chrome-user1")

    def test_historical_auth_limit_does_not_block_a_recovered_current_check(self):
        before = self.check(
            authentication_state="anonymous", access_barrier="login_required",
            detail_usable=False, original_asset_usable=False, pagination_usable=False,
            coverage_impact="material", visible_scope="最初只能看公开缩略图",
        )
        after = self.check(
            id="check-recheck-ui", phase="recheck", checked_at="2026-10-27T10:10:00+00:00",
            authentication_state="authenticated", access_barrier="none",
            coverage_impact="none", visible_scope="当前搜索、详情、原图与分页均可用",
        )
        result = validate_source_access(self.preparation([before, after]), [self.attempt()], [])
        self.assertEqual(result["decision"]["status"], "not_required")
        self.assertEqual(result["current_checks_by_source"]["att-ui"], "check-recheck-ui")

    def test_login_recheck_may_still_be_paywalled(self):
        before = self.check(
            authentication_state="anonymous", access_barrier="login_required",
            detail_usable=False, original_asset_usable=False, pagination_usable=False,
            coverage_impact="material", visible_scope="公开首屏",
        )
        after = self.check(
            id="check-recheck-ui", phase="recheck", checked_at="2026-10-27T10:10:00+00:00",
            authentication_state="authenticated", access_barrier="paywall",
            original_asset_usable=False, pagination_usable=False,
            coverage_impact="material", visible_scope="登录后仍仅有订阅前预览",
        )
        decision = {
            "status": "login_then_continue", "prompted_at": "2026-10-27T10:01:00+00:00",
            "decided_at": "2026-10-27T10:02:00+00:00", "restricted_source_attempt_ids": ["att-ui"],
            "summary": "用户选择登录后继续",
        }
        resume = {
            "status": "partial", "checkpoint_candidate_ids": [], "completed_candidate_ids": [],
            "remaining_candidate_ids": [], "recheck_ids": ["check-recheck-ui"],
            "resumed_at": "2026-10-27T10:11:00+00:00",
        }
        result = validate_source_access(self.preparation([before, after], decision, resume), [self.attempt()], [])
        self.assertEqual(result["resume"]["status"], "partial")

        resume["status"] = "resumed"
        with self.assertRaisesRegex(SourceAccessError, "不能标记为完全恢复"):
            validate_source_access(self.preparation([before, after], decision, resume), [self.attempt()], [])

    def test_decision_and_resume_times_must_stay_inside_batch(self):
        decision = {
            "status": "not_required", "prompted_at": "",
            "decided_at": "2026-10-27T10:13:00+00:00",
            "restricted_source_attempt_ids": [], "summary": "无需登录",
        }
        with self.assertRaisesRegex(SourceAccessError, "必须位于预检批次时间内"):
            validate_source_access(self.preparation(decision=decision), [self.attempt()], [])

        resume = {
            "status": "not_needed", "checkpoint_candidate_ids": [],
            "completed_candidate_ids": [], "remaining_candidate_ids": [],
            "recheck_ids": [], "resumed_at": "2026-10-27T10:11:00+00:00",
        }
        with self.assertRaisesRegex(SourceAccessError, "无需登录恢复"):
            validate_source_access(self.preparation(resume=resume), [self.attempt()], [])

    def test_network_error_is_not_misclassified_as_login(self):
        check = self.check(
            page_open=False, search_usable="unknown", filter_usable="unknown",
            detail_usable="unknown", original_asset_usable="unknown", pagination_usable="unknown",
            authentication_state="unknown", access_barrier="network_error",
            coverage_impact="material", visible_scope="DNS 失败，未观察到登录页面",
        )
        result = validate_source_access(self.preparation([check]), [self.attempt()], [])
        self.assertEqual(result["checks"][0]["access_barrier"], "network_error")
        self.assertEqual(result["decision"]["status"], "not_required")

    def test_session_expiry_cannot_reuse_an_earlier_accessible_result(self):
        expired = self.check(
            id="check-expired-ui", phase="recheck", checked_at="2026-10-27T10:10:00+00:00",
            page_open=True, search_usable=False, filter_usable=False, detail_usable=False,
            original_asset_usable=False, pagination_usable=False,
            authentication_state="expired", access_barrier="session_expired",
            coverage_impact="material", visible_scope="同一会话已跳转登录页",
        )
        decision = {
            "status": "pending_user_choice", "prompted_at": "2026-10-27T10:11:00+00:00",
            "decided_at": "", "restricted_source_attempt_ids": ["att-ui"],
            "summary": "会话已过期，等待一次性选择",
        }
        result = validate_source_access(self.preparation([self.check(), expired], decision), [self.attempt()], [])
        self.assertEqual(result["current_checks_by_source"]["att-ui"], "check-expired-ui")

    def test_credentials_and_cookie_material_are_rejected(self):
        unsafe = self.preparation()
        unsafe["checks"][0]["cookie"] = "secret"
        with self.assertRaisesRegex(SourceAccessError, "不允许字段"):
            validate_source_access(unsafe, [self.attempt()], [])

    def test_resume_partition_rejects_duplicate_or_lost_candidates(self):
        candidates = [{"id": "cand-1"}, {"id": "cand-2"}]
        resume = {
            "status": "resumed", "checkpoint_candidate_ids": ["cand-1"],
            "completed_candidate_ids": ["cand-1"], "remaining_candidate_ids": ["cand-1"],
            "recheck_ids": [], "resumed_at": "2026-10-27T10:11:00+00:00",
        }
        with self.assertRaisesRegex(SourceAccessError, "重复"):
            validate_source_access(self.preparation(resume=resume), [self.attempt()], candidates)
        resume["remaining_candidate_ids"] = []
        with self.assertRaisesRegex(SourceAccessError, "完整"):
            validate_source_access(self.preparation(resume=resume), [self.attempt()], candidates)

    def test_discovery_inherits_capture_fields_and_keeps_access_preparation(self):
        payload = {
            "source_attempts": [self.attempt()],
            "candidates": [{
                "id": "cand-1", "source_attempt_id": "att-ui", "product_name": "产品A",
                "target_page": "我的页", "source_entry_url": "https://example.com/search",
                "source_detail_url": "https://example.com/detail/1", "source_asset_url": "",
                "candidate_rank": 1, "candidate_status": "accepted", "disposition_reason": "进入审核",
            }],
            "candidate_pool": ["cand-1"],
            "candidate_limit": {"max": 50, "unit": "candidate_records", "applies_to": "candidate_pool", "ordering_basis": "相关性", "truncated_candidate_ids": []},
            "access_preparation": self.preparation(),
        }
        result = validate_discovery_payload(self.task(), payload)
        candidate = result["candidates"][0]
        self.assertEqual(candidate["source_type"], "ui_database")
        self.assertEqual(candidate["source_provider"], "UI DB")
        self.assertEqual(candidate["target_surface"], "mobile_app")
        self.assertEqual(candidate["browser_session_id"], "chrome-user1")
        self.assertEqual(result["access_preparation"]["id"], "access-batch-1")

    def test_formal_capture_gate_requires_preflight_and_preserves_b1_fields(self):
        payload = {
            "source_attempts": [self.attempt()],
            "candidates": [{
                "id": "cand-1", "source_attempt_id": "att-ui", "product_name": "产品A",
                "target_page": "我的页", "source_entry_url": "https://example.com/search",
                "source_detail_url": "https://example.com/detail/1", "source_asset_url": "",
                "candidate_rank": 1, "candidate_status": "accepted", "disposition_reason": "进入审核",
            }],
            "candidate_pool": ["cand-1"],
            "candidate_limit": {"max": 50, "unit": "candidate_records", "applies_to": "candidate_pool",
                                "ordering_basis": "相关性", "truncated_candidate_ids": []},
        }
        with TemporaryDirectory() as directory:
            root = Path(directory); source = root / "sources.json"
            source.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "access_preparation"):
                run_pipeline(self.task(), root / "without-preflight", sources_file=source,
                             capture_sources_flag=True)
            payload["access_preparation"] = self.preparation()
            source.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
            with patch("competitor_analysis_skill.pipeline.capture_sources", return_value=[]):
                result = run_pipeline(self.task(), root / "with-preflight", sources_file=source,
                                      capture_sources_flag=True)
            saved = json.loads(result["sources_json"].read_text(encoding="utf-8"))
            candidate = saved["candidates"][0]
            self.assertEqual((candidate["source_type"], candidate["source_provider"], candidate["target_surface"]),
                             ("ui_database", "UI DB", "mobile_app"))
            self.assertEqual(candidate["browser_session_id"], "chrome-user1")

    def test_formal_capture_does_not_run_before_pending_choice(self):
        check = self.check(
            authentication_state="anonymous", access_barrier="login_required",
            detail_usable=False, original_asset_usable=False, pagination_usable=False,
            coverage_impact="material", visible_scope="仅能看公开缩略图",
        )
        decision = {
            "status": "pending_user_choice", "prompted_at": "2026-10-27T10:01:00+00:00",
            "decided_at": "", "restricted_source_attempt_ids": ["att-ui"],
            "summary": "重大登录限制影响详情与原图，等待用户一次选择",
        }
        payload = self.discovery_payload([self.candidate()], self.preparation([check], decision))
        with TemporaryDirectory() as directory:
            root = Path(directory); source = root / "sources.json"
            source.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
            with patch("competitor_analysis_skill.pipeline.capture_sources") as capture:
                with self.assertRaisesRegex(ValueError, "用户的一次性选择"):
                    run_pipeline(self.task(), root / "out", sources_file=source, capture_sources_flag=True)
                capture.assert_not_called()

    def test_formal_cli_stops_before_capture_when_choice_is_pending(self):
        check = self.check(
            authentication_state="anonymous", access_barrier="login_required",
            detail_usable=False, original_asset_usable=False, pagination_usable=False,
            coverage_impact="material", visible_scope="仅能看公开缩略图",
        )
        decision = {
            "status": "pending_user_choice", "prompted_at": "2026-10-27T10:01:00+00:00",
            "decided_at": "", "restricted_source_attempt_ids": ["att-ui"],
            "summary": "重大登录限制影响详情与原图，等待用户一次选择",
        }
        payload = self.discovery_payload([self.candidate()], self.preparation([check], decision))
        with TemporaryDirectory() as directory:
            root = Path(directory)
            task_path = root / "task.json"
            source_path = root / "sources.json"
            output = root / "out"
            task_path.write_text(json.dumps(self.task(), ensure_ascii=False), encoding="utf-8")
            source_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
            completed = subprocess.run(
                [sys.executable, "-m", "competitor_analysis_skill", "--task-file", str(task_path),
                 "--sources-file", str(source_path), "--capture-sources", "--output", str(output)],
                cwd=Path(__file__).parents[1], capture_output=True, text=True,
            )
            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("用户的一次性选择", completed.stderr)
            self.assertFalse((output / "captures.json").exists())

    def test_public_only_choice_runs_currently_accessible_candidates(self):
        check = self.check(
            authentication_state="anonymous", access_barrier="login_required",
            search_usable=False, filter_usable=False, detail_usable=True,
            original_asset_usable=False, pagination_usable=False,
            coverage_impact="material", visible_scope="公开详情可打开，搜索与更多结果需登录",
        )
        decision = {
            "status": "public_only", "prompted_at": "2026-10-27T10:01:00+00:00",
            "decided_at": "2026-10-27T10:02:00+00:00", "restricted_source_attempt_ids": ["att-ui"],
            "summary": "用户选择本批只使用当前公开可访问详情",
        }
        payload = self.discovery_payload([self.candidate()], self.preparation([check], decision))
        with TemporaryDirectory() as directory:
            root = Path(directory); source = root / "sources.json"
            source.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
            with patch("competitor_analysis_skill.pipeline.capture_sources", return_value=[self.capture_record()]) as capture:
                result = run_pipeline(self.task(), root / "out", sources_file=source, capture_sources_flag=True)
            self.assertEqual([item["id"] for item in capture.call_args.args[0]], ["cand-1"])
            saved = json.loads(result["captures_json"].read_text(encoding="utf-8"))
            self.assertEqual(saved["capture_execution"]["executed_candidate_ids"], ["cand-1"])

    def test_public_only_choice_skips_candidate_whose_detail_is_still_restricted(self):
        check = self.check(
            authentication_state="anonymous", access_barrier="login_required",
            search_usable=True, filter_usable=False, detail_usable=False,
            original_asset_usable=False, pagination_usable=False,
            coverage_impact="material", visible_scope="搜索列表公开，详情仍需登录",
        )
        decision = {
            "status": "public_only", "prompted_at": "2026-10-27T10:01:00+00:00",
            "decided_at": "2026-10-27T10:02:00+00:00", "restricted_source_attempt_ids": ["att-ui"],
            "summary": "用户选择本批只使用当前公开内容；受限详情不执行",
        }
        payload = self.discovery_payload([self.candidate()], self.preparation([check], decision))
        with TemporaryDirectory() as directory:
            root = Path(directory); source = root / "sources.json"
            source.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
            with patch("competitor_analysis_skill.pipeline.capture_sources") as capture:
                result = run_pipeline(self.task(), root / "out", sources_file=source, capture_sources_flag=True)
                capture.assert_not_called()
            saved = json.loads(result["captures_json"].read_text(encoding="utf-8"))
            self.assertEqual(saved["capture_execution"]["skipped_candidate_ids"], ["cand-1"])
            self.assertIn("detail_usable=true", saved["capture_execution"]["skip_reasons"]["cand-1"])

    def test_completed_checkpoint_preserves_capture_without_rerunning_executor(self):
        before = self.check(
            authentication_state="anonymous", access_barrier="login_required",
            detail_usable=False, original_asset_usable=False, pagination_usable=False,
            coverage_impact="material", visible_scope="登录前受限",
        )
        after = self.check(
            id="check-recheck-ui", phase="recheck", checked_at="2026-10-27T10:10:00+00:00",
            authentication_state="authenticated", access_barrier="none",
            coverage_impact="none", visible_scope="登录后复查可用",
        )
        decision = {
            "status": "login_then_continue", "prompted_at": "2026-10-27T10:01:00+00:00",
            "decided_at": "2026-10-27T10:02:00+00:00", "restricted_source_attempt_ids": ["att-ui"],
            "summary": "用户选择登录后继续",
        }
        resume = {
            "status": "resumed", "checkpoint_candidate_ids": ["cand-1"],
            "completed_candidate_ids": ["cand-1"], "remaining_candidate_ids": [],
            "recheck_ids": ["check-recheck-ui"], "resumed_at": "2026-10-27T10:11:00+00:00",
        }
        payload = self.discovery_payload([self.candidate()], self.preparation([before, after], decision, resume))
        with TemporaryDirectory() as directory:
            root = Path(directory); source = root / "sources.json"; output = root / "out"
            source.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
            self.save_completed_capture(output)
            with patch("competitor_analysis_skill.pipeline.capture_sources") as capture:
                result = run_pipeline(self.task(), output, sources_file=source, capture_sources_flag=True)
                capture.assert_not_called()
            saved = json.loads(result["captures_json"].read_text(encoding="utf-8"))
            self.assertEqual([item["source_candidate_id"] for item in saved["captures"]], ["cand-1"])
            self.assertEqual(saved["capture_execution"]["executed_candidate_ids"], [])

    def test_partial_resume_runs_only_remaining_candidate_and_keeps_completed_capture(self):
        candidates = [self.candidate("cand-1", 1), self.candidate("cand-2", 2)]
        before = self.check(
            authentication_state="anonymous", access_barrier="login_required",
            detail_usable=False, original_asset_usable=False, pagination_usable=False,
            coverage_impact="material", visible_scope="登录前受限",
        )
        after = self.check(
            id="check-recheck-ui", phase="recheck", checked_at="2026-10-27T10:10:00+00:00",
            authentication_state="authenticated", access_barrier="none",
            coverage_impact="none", visible_scope="登录后复查可用",
        )
        decision = {
            "status": "login_then_continue", "prompted_at": "2026-10-27T10:01:00+00:00",
            "decided_at": "2026-10-27T10:02:00+00:00", "restricted_source_attempt_ids": ["att-ui"],
            "summary": "用户选择登录后继续",
        }
        resume = {
            "status": "partial", "checkpoint_candidate_ids": ["cand-1"],
            "completed_candidate_ids": ["cand-1"], "remaining_candidate_ids": ["cand-2"],
            "recheck_ids": ["check-recheck-ui"], "resumed_at": "2026-10-27T10:11:00+00:00",
        }
        payload = self.discovery_payload(candidates, self.preparation([before, after], decision, resume))
        with TemporaryDirectory() as directory:
            root = Path(directory); source = root / "sources.json"; output = root / "out"
            source.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
            self.save_completed_capture(output)
            with patch("competitor_analysis_skill.pipeline.capture_sources", return_value=[self.capture_record("cand-2", 2)]) as capture:
                result = run_pipeline(self.task(), output, sources_file=source, capture_sources_flag=True)
            self.assertEqual([item["id"] for item in capture.call_args.args[0]], ["cand-2"])
            self.assertTrue(capture.call_args.args[0][0]["requires_authenticated_session"])
            saved = json.loads(result["captures_json"].read_text(encoding="utf-8"))
            self.assertEqual([item["source_candidate_id"] for item in saved["captures"]], ["cand-1", "cand-2"])
            self.assertEqual(saved["capture_execution"]["executed_candidate_ids"], ["cand-2"])

    def test_blocked_resume_does_not_run_remaining_candidate(self):
        before = self.check(
            authentication_state="anonymous", access_barrier="login_required",
            detail_usable=False, original_asset_usable=False, pagination_usable=False,
            coverage_impact="material", visible_scope="登录前受限",
        )
        after = self.check(
            id="check-recheck-ui", phase="recheck", checked_at="2026-10-27T10:10:00+00:00",
            authentication_state="anonymous", access_barrier="login_required",
            detail_usable=False, original_asset_usable=False, pagination_usable=False,
            coverage_impact="material", visible_scope="复查后仍受限",
        )
        decision = {
            "status": "login_then_continue", "prompted_at": "2026-10-27T10:01:00+00:00",
            "decided_at": "2026-10-27T10:02:00+00:00", "restricted_source_attempt_ids": ["att-ui"],
            "summary": "用户选择登录后继续",
        }
        resume = {
            "status": "blocked", "checkpoint_candidate_ids": [], "completed_candidate_ids": [],
            "remaining_candidate_ids": ["cand-1"], "recheck_ids": ["check-recheck-ui"],
            "resumed_at": "2026-10-27T10:11:00+00:00",
        }
        payload = self.discovery_payload([self.candidate()], self.preparation([before, after], decision, resume))
        with TemporaryDirectory() as directory:
            root = Path(directory); source = root / "sources.json"
            source.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
            with patch("competitor_analysis_skill.pipeline.capture_sources") as capture:
                result = run_pipeline(self.task(), root / "out", sources_file=source, capture_sources_flag=True)
                capture.assert_not_called()
            saved = json.loads(result["captures_json"].read_text(encoding="utf-8"))
            self.assertEqual(saved["capture_execution"]["skipped_candidate_ids"], ["cand-1"])

    def test_missing_captures_file_names_all_completed_candidates_without_rerun(self):
        before = self.check(
            authentication_state="anonymous", access_barrier="login_required",
            detail_usable=False, original_asset_usable=False, pagination_usable=False,
            coverage_impact="material", visible_scope="登录前受限",
        )
        after = self.check(
            id="check-recheck-ui", phase="recheck", checked_at="2026-10-27T10:10:00+00:00",
            authentication_state="authenticated", access_barrier="none",
            coverage_impact="none", visible_scope="登录后复查可用",
        )
        decision = {
            "status": "login_then_continue", "prompted_at": "2026-10-27T10:01:00+00:00",
            "decided_at": "2026-10-27T10:02:00+00:00", "restricted_source_attempt_ids": ["att-ui"],
            "summary": "用户选择登录后继续",
        }
        resume = {
            "status": "resumed", "checkpoint_candidate_ids": ["cand-1"],
            "completed_candidate_ids": ["cand-1"], "remaining_candidate_ids": [],
            "recheck_ids": ["check-recheck-ui"], "resumed_at": "2026-10-27T10:11:00+00:00",
        }
        payload = self.discovery_payload([self.candidate()], self.preparation([before, after], decision, resume))
        with TemporaryDirectory() as directory:
            root = Path(directory); source = root / "sources.json"
            source.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
            with patch("competitor_analysis_skill.pipeline.capture_sources") as capture:
                with self.assertRaisesRegex(ValueError, "captures.json.*cand-1"):
                    run_pipeline(self.task(), root / "out", sources_file=source, capture_sources_flag=True)
                capture.assert_not_called()

    def test_missing_completed_candidate_record_names_only_affected_candidate(self):
        candidates = [self.candidate("cand-1", 1), self.candidate("cand-2", 2)]
        before = self.check(
            authentication_state="anonymous", access_barrier="login_required",
            detail_usable=False, original_asset_usable=False, pagination_usable=False,
            coverage_impact="material", visible_scope="登录前受限",
        )
        after = self.check(
            id="check-recheck-ui", phase="recheck", checked_at="2026-10-27T10:10:00+00:00",
            authentication_state="authenticated", access_barrier="none",
            coverage_impact="none", visible_scope="登录后复查可用",
        )
        decision = {
            "status": "login_then_continue", "prompted_at": "2026-10-27T10:01:00+00:00",
            "decided_at": "2026-10-27T10:02:00+00:00", "restricted_source_attempt_ids": ["att-ui"],
            "summary": "用户选择登录后继续",
        }
        resume = {
            "status": "resumed", "checkpoint_candidate_ids": ["cand-1", "cand-2"],
            "completed_candidate_ids": ["cand-1", "cand-2"], "remaining_candidate_ids": [],
            "recheck_ids": ["check-recheck-ui"], "resumed_at": "2026-10-27T10:11:00+00:00",
        }
        payload = self.discovery_payload(candidates, self.preparation([before, after], decision, resume))
        with TemporaryDirectory() as directory:
            root = Path(directory); source = root / "sources.json"; output = root / "out"
            source.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
            self.save_completed_capture(output, "cand-1", 1)
            with patch("competitor_analysis_skill.pipeline.capture_sources") as capture:
                with self.assertRaisesRegex(ValueError, "有效截图产物: cand-2"):
                    run_pipeline(self.task(), output, sources_file=source, capture_sources_flag=True)
                capture.assert_not_called()


if __name__ == "__main__":
    unittest.main()
