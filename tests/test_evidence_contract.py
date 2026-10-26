import json
import tempfile
import unittest
from pathlib import Path

from competitor_analysis_skill.pipeline import run_pipeline

from competitor_analysis_skill.evidence import (
    EvidenceLinkError,
    DiscoveryContractError,
    build_evidence_statistics,
    validate_capture_links,
    validate_discovery_payload,
    validate_reviewed_material_links,
)


class EvidenceContractTests(unittest.TestCase):
    def task(self):
        return {
            "target_page": "搜索结果页",
            "competitors": [{"product_name": "产品A"}, {"product_name": "产品B"}],
        }

    def full_task(self):
        return {
            "raw_request": "对比搜索结果页",
            "research_goal": "页面参考",
            "target_page": "搜索结果页",
            "regions": ["CN"],
            "specified_products": ["产品A"],
            "assumptions": [],
            "needs_clarification": False,
            "task_status": "ready",
            "planning_strategy": "user_only",
            "competitors": [{
                "product_name": "产品A", "region": "CN", "product_type": "社区", "platform": "Web",
                "target_page": "搜索结果页", "planning_source": "user_specified", "priority": "high", "reason": "指定",
            }],
        }

    def attempt(self, attempt_id="att-1"):
        return {
            "id": attempt_id,
            "source_type": "ui_database",
            "source_provider": "UI Notes",
            "entry_url": "https://uinotes.com/search",
            "query_mapping": {
                "raw_page_intent": "搜索结果页",
                "mapped_terms": ["Search", "Results"],
                "source_taxonomy_terms": ["search results"],
            },
            "actual_query": "Search Results",
            "search_mode": "tag_search",
            "discovery_batch": 1,
            "web_text_accessible": "unknown",
            "browser_accessible": True,
            "browser_interactive": True,
            "content_available": True,
            "access_status": "accessible",
            "observed_scope": "首屏并下滑两批",
            "attempt_status": "completed",
            "failure_reason": "",
        }

    def candidate(self, candidate_id="cand-1", attempt_id="att-1", **overrides):
        value = {
            "id": candidate_id,
            "source_attempt_id": attempt_id,
            "product_name": "产品A",
            "target_page": "搜索结果页",
            "source_entry_url": "https://uinotes.com/search",
            "source_detail_url": "https://uinotes.com/apps/product-a/screen-1",
            "source_asset_url": "https://cdn.example.com/product-a.png",
            "candidate_rank": 1,
            "candidate_status": "accepted",
            "disposition_reason": "页面主体与目标路径匹配，进入截图审核",
        }
        value.update(overrides)
        return value

    def payload(self, attempts=None, candidates=None, pool=None, limit=None):
        candidates = candidates or [self.candidate()]
        return {
            "source_attempts": attempts or [self.attempt()],
            "candidates": candidates,
            "candidate_pool": pool or [item["id"] for item in candidates if item["candidate_status"] == "accepted"],
            "candidate_limit": limit or {
                "max": 50,
                "unit": "candidate_records",
                "applies_to": "candidate_pool",
                "ordering_basis": "Agent 按页面匹配度与来源可追溯性排序",
                "truncated_candidate_ids": [],
            },
        }

    def test_formal_discovery_keeps_attempts_and_candidates_independent(self):
        result = validate_discovery_payload(self.task(), self.payload())
        self.assertEqual(result["source_attempts"][0]["id"], "att-1")
        self.assertEqual(result["candidates"][0]["source_attempt_id"], "att-1")
        self.assertEqual(result["candidate_pool"], ["cand-1"])

    def test_unknown_access_state_is_valid_and_preserved(self):
        attempt = self.attempt()
        attempt.update({
            "browser_accessible": "unknown",
            "browser_interactive": "unknown",
            "content_available": "unknown",
            "access_status": "unknown",
            "attempt_status": "not_verified",
        })
        result = validate_discovery_payload(self.task(), self.payload(attempts=[attempt]))
        self.assertEqual(result["source_attempts"][0]["access_status"], "unknown")

    def test_candidate_limit_preserves_overflow_dispositions(self):
        candidates = []
        for index in range(52):
            candidates.append(self.candidate(
                candidate_id=f"cand-{index}",
                candidate_rank=index + 1,
                candidate_status="accepted" if index < 50 else "not_reviewed",
                disposition_reason="进入候选池" if index < 50 else "超过候选池 50 条容量，保留登记但未进入截图池",
            ))
        result = validate_discovery_payload(self.task(), self.payload(
            candidates=candidates,
            pool=[f"cand-{index}" for index in range(50)],
            limit={
                "max": 50,
                "unit": "candidate_records",
                "applies_to": "candidate_pool",
                "ordering_basis": "页面匹配度降序",
                "truncated_candidate_ids": ["cand-50", "cand-51"],
            },
        ))
        self.assertEqual(len(result["candidates"]), 52)
        self.assertEqual(result["candidate_limit"]["truncated_candidate_ids"], ["cand-50", "cand-51"])

    def test_missing_source_attempt_is_an_explicit_error(self):
        with self.assertRaisesRegex(DiscoveryContractError, "source_attempt_id"):
            validate_discovery_payload(self.task(), self.payload(candidates=[self.candidate(attempt_id="missing")]))

    def test_capture_links_require_registered_candidate_and_preserve_url_roles(self):
        registry = validate_discovery_payload(self.task(), self.payload())
        capture = {
            "id": "cap-1",
            "source_candidate_id": "cand-1",
            "source_attempt_id": "att-1",
            "product_name": "产品A",
            "target_page": "搜索结果页",
            "requested_url": "https://uinotes.com/apps/product-a/screen-1",
            "source_entry_url": "https://uinotes.com/search",
            "source_detail_url": "https://uinotes.com/apps/product-a/screen-1",
            "source_asset_url": "https://cdn.example.com/product-a.png",
        }
        validate_capture_links(registry, [capture])
        capture["source_candidate_id"] = "not-registered"
        with self.assertRaisesRegex(EvidenceLinkError, "候选"):
            validate_capture_links(registry, [capture])

    def test_capture_cannot_bypass_rejected_candidate(self):
        rejected = self.candidate(candidate_status="rejected", disposition_reason="页面角色不匹配")
        registry = validate_discovery_payload(
            self.task(),
            self.payload(candidates=[rejected], pool=[], limit={
                "max": 50, "unit": "candidate_records", "applies_to": "candidate_pool",
                "ordering_basis": "页面匹配度", "truncated_candidate_ids": [],
            }),
        )
        capture = {
            "id": "cap-1", "source_candidate_id": "cand-1", "source_attempt_id": "att-1",
            "product_name": "产品A", "target_page": "搜索结果页",
            "requested_url": "https://uinotes.com/apps/product-a/screen-1",
            "source_entry_url": "https://uinotes.com/search",
            "source_detail_url": "https://uinotes.com/apps/product-a/screen-1",
            "source_asset_url": "https://cdn.example.com/product-a.png",
        }
        with self.assertRaisesRegex(EvidenceLinkError, "accepted"):
            validate_capture_links(registry, [capture])

    def test_material_handoff_rejects_wrong_capture_reference(self):
        registry = validate_discovery_payload(self.task(), self.payload())
        capture = {
            "id": "cap-1", "source_candidate_id": "cand-1", "source_attempt_id": "att-1",
            "product_name": "产品A", "target_page": "搜索结果页",
            "requested_url": "https://uinotes.com/apps/product-a/screen-1",
            "source_entry_url": "https://uinotes.com/search",
            "source_detail_url": "https://uinotes.com/apps/product-a/screen-1",
            "source_asset_url": "https://cdn.example.com/product-a.png",
            "capture_status": "captured",
        }
        material = {
            "id": "mat-1", "capture_id": "cap-1", "source_candidate_id": "cand-1",
            "source_attempt_id": "wrong-attempt", "product_name": "产品A", "target_page": "搜索结果页",
            "source_type": "browser", "source_detail_url": "https://uinotes.com/apps/product-a/screen-1",
        }
        with self.assertRaisesRegex(EvidenceLinkError, "source_attempt_id"):
            validate_reviewed_material_links(registry, [capture], [{"target_id": "cap-1"}], [material])
        material["source_attempt_id"] = "att-1"
        material["source_detail_url"] = "https://uinotes.com/apps/product-a/other-screen"
        with self.assertRaisesRegex(EvidenceLinkError, "source_detail_url"):
            validate_reviewed_material_links(registry, [capture], [{"target_id": "cap-1"}], [material])

    def test_statistics_separate_candidate_material_and_fallback_counts(self):
        stats = build_evidence_statistics(
            task={"competitors": [{"product_name": "产品A"}, {"product_name": "产品B"}]},
            source_attempts=[self.attempt()],
            candidates=[
                self.candidate(candidate_id="cand-1", candidate_status="accepted"),
                self.candidate(candidate_id="cand-2", candidate_status="rejected", disposition_reason="页面角色不匹配"),
                self.candidate(candidate_id="cand-3", candidate_status="not_reviewed", disposition_reason="来源权限未知"),
            ],
            reviews=[
                {"target_id": "cap-1", "semantic_status": "accepted"},
                {"target_id": "cap-2", "semantic_status": "rejected"},
            ],
            materials=[
                {"product_name": "产品A", "collection_status": "collected"},
                {"product_name": "产品B", "collection_status": "rejected"},
            ],
            fallback_requests=[
                {"product_name": "产品A", "status": "resolved"},
                {"product_name": "产品B", "status": "open"},
            ],
            capture_targets=[{}, {}, {}],
        )
        self.assertEqual(stats["candidates"]["accepted"], 1)
        self.assertEqual(stats["candidates"]["rejected"], 1)
        self.assertEqual(stats["candidates"]["not_reviewed"], 1)
        self.assertEqual(stats["semantic_reviews"]["accepted"], 1)
        self.assertEqual(stats["semantic_reviews"]["rejected"], 1)
        self.assertEqual(stats["fallback"]["open"], 1)
        self.assertEqual(stats["coverage"]["products_without_collected_material"], 1)

    def test_formal_sources_pipeline_persists_the_full_registry(self):
        payload = self.payload()
        payload["candidates"][0]["product_name"] = "产品A"
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); source_path = root / "sources-input.json"
            source_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
            result = run_pipeline(self.full_task(), root / "out", sources_file=source_path)
            saved = json.loads(result["sources_json"].read_text(encoding="utf-8"))
            self.assertEqual(saved["source_attempts"][0]["id"], "att-1")
            self.assertEqual(saved["candidates"][0]["source_attempt_id"], "att-1")
            self.assertEqual(saved["candidate_pool"], ["cand-1"])

    def test_formal_semantic_stage_rejects_historical_capture_without_registry(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            captures_path = root / "captures.json"
            reviews_path = root / "reviews.json"
            captures_path.write_text(json.dumps({"captures": [{
                "id": "cap-old", "source_candidate_id": "src-old", "source_attempt_id": "att-old",
                "product_name": "产品A", "target_page": "搜索结果页", "capture_status": "failed",
            }]}), encoding="utf-8")
            reviews_path.write_text(json.dumps({"reviews": []}), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "缺少 source_attempts/candidates"):
                run_pipeline(self.full_task(), root / "out", captures_file=captures_path, semantic_reviews_file=reviews_path)


if __name__ == "__main__":
    unittest.main()
