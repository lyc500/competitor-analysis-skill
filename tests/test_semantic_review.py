import json
import os
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from competitor_analysis_skill.semantic_review import SemanticReviewError, process_semantic_reviews


class SemanticReviewTests(unittest.TestCase):
    FIXTURES = Path(__file__).parent / "fixtures" / "materials"

    def task(self, products=("产品A",)):
        competitors = []
        for product in products:
            competitors.append({
                "product_name": product,
                "region": "CN",
                "product_type": "社区",
                "platform": "Web",
                "target_page": "搜索结果页",
                "planning_source": "user_specified",
                "priority": "high",
                "reason": "用户指定",
            })
        return {
            "raw_request": "对比搜索结果页",
            "research_goal": "参考",
            "target_page": "搜索结果页",
            "regions": ["CN"],
            "specified_products": list(products),
            "assumptions": [],
            "needs_clarification": False,
            "task_status": "ready",
            "planning_strategy": "user_only",
            "competitors": competitors,
        }

    def capture(self, capture_id="cap-a", status="captured", product="产品A", image="valid.png"):
        return {
            "id": capture_id,
            "source_candidate_id": "src-a",
            "product_name": product,
            "target_page": "搜索结果页",
            "requested_url": "https://example.com/search",
            "final_url": "https://example.com/results",
            "captured_at": "2026-09-07T00:00:00Z",
            "capture_status": status,
            "screenshot_path": str(self.FIXTURES / image) if status == "captured" else "",
            "failure_reason": "capture failed" if status != "captured" else "",
        }

    def manual(self, capture_id="manual-a", source_type="user_upload", product="产品A", image="valid.png"):
        return {
            "id": capture_id,
            "product_name": product,
            "target_page": "搜索结果页",
            "source_type": source_type,
            "image_path": str(self.FIXTURES / image),
            "captured_at": "",
            "notes": "用户已提供",
        }

    def review(self, target_id="cap-a", target_kind="browser_capture", semantic_status="accepted", **changes):
        value = {
            "target_id": target_id,
            "target_kind": target_kind,
            "semantic_status": semantic_status,
            "product_identity": "matched",
            "target_page_match": "matched",
            "page_completeness": "complete",
            "asset_kind": "ui_page",
            "semantic_reason": "Agent 已确认产品、页面与主体完整性",
            "review_source": "agent_visual_review",
        }
        value.update(changes)
        return value

    def process(self, captures=None, manuals=None, reviews=None, products=("产品A",)):
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        output = Path(directory.name) / "output"
        return process_semantic_reviews(
            self.task(products), captures or [], manuals or [], reviews or [], output
        )

    def test_accepted_browser_capture_becomes_collected_after_quality_recheck(self):
        result = self.process(captures=[self.capture()], reviews=[self.review()])
        material = result["materials"][0]
        self.assertEqual((material["semantic_status"], material["quality_status"], material["collection_status"]), ("accepted", "accepted", "collected"))
        self.assertEqual((material["source_type"], material["collection_method"], material["provenance"]), ("browser", "browser_screenshot", "online"))
        self.assertEqual(material["capture_id"], "cap-a")

    def test_logo_marketing_and_wrong_target_reviews_stay_rejected(self):
        cases = [
            {"asset_kind": "logo"},
            {"asset_kind": "marketing_image"},
            {"target_page_match": "mismatched"},
        ]
        for changes in cases:
            with self.subTest(changes=changes):
                review = self.review(semantic_status="rejected", **changes)
                result = self.process(captures=[self.capture()], reviews=[review])
                self.assertEqual(result["materials"][0]["collection_status"], "rejected")

    def test_contradictory_accepted_review_is_rejected(self):
        with self.assertRaisesRegex(SemanticReviewError, "accepted"):
            self.process(captures=[self.capture()], reviews=[self.review(asset_kind="logo")])

    def test_mobile_app_task_requires_agent_surface_match(self):
        task = self.task()
        task["target_surface"] = "mobile_app"
        task["competitors"][0]["platform"] = "iOS / Android"
        with TemporaryDirectory() as directory:
            output = Path(directory) / "output"
            with self.assertRaisesRegex(SemanticReviewError, "target_surface_match"):
                process_semantic_reviews(task, [self.capture()], [], [self.review()], output)
            with self.assertRaisesRegex(SemanticReviewError, "accepted"):
                process_semantic_reviews(
                    task,
                    [self.capture()],
                    [],
                    [self.review(target_surface_match="mismatched")],
                    output,
                )
            result = process_semantic_reviews(
                task,
                [self.capture()],
                [],
                [self.review(target_surface_match="matched")],
                output,
            )
            material = result["materials"][0]
            self.assertEqual(material["target_surface"], "mobile_app")
            self.assertEqual(material["target_surface_match"], "matched")
            self.assertEqual(material["collection_status"], "collected")

    def test_captured_target_requires_exactly_one_review(self):
        with self.assertRaisesRegex(SemanticReviewError, "缺少"):
            self.process(captures=[self.capture()], reviews=[])
        with self.assertRaisesRegex(SemanticReviewError, "重复"):
            self.process(captures=[self.capture()], reviews=[self.review(), self.review()])

    def test_failed_and_blank_captures_cannot_be_accepted_and_leave_fallback_open(self):
        for status in ("failed", "blank"):
            with self.subTest(status=status):
                result = self.process(captures=[self.capture(status=status)], reviews=[])
                self.assertEqual(result["fallback_requests"][0]["status"], "open")
                with self.assertRaisesRegex(SemanticReviewError, "不可接受"):
                    self.process(captures=[self.capture(status=status)], reviews=[self.review()])
                with self.assertRaisesRegex(SemanticReviewError, "不可接受"):
                    self.process(captures=[self.capture(status=status)], reviews=[self.review(semantic_status="rejected", asset_kind="unknown")])

    def test_user_upload_and_device_capture_are_collected_with_strict_mapping(self):
        for source_type, method, provenance in (
            ("user_upload", "user_provided", "user_upload"),
            ("device_capture", "manual_device_capture", "device_capture"),
        ):
            with self.subTest(source_type=source_type):
                manual = self.manual(source_type=source_type)
                review = self.review(target_id="manual-a", target_kind="manual_capture")
                material = self.process(manuals=[manual], reviews=[review])["materials"][0]
                self.assertEqual((material["collection_method"], material["provenance"], material["collection_status"]), (method, provenance, "collected"))

    def test_manual_rejection_and_mechanical_failure_never_collect(self):
        rejected = self.review(target_id="manual-a", target_kind="manual_capture", semantic_status="rejected", asset_kind="cover")
        result = self.process(manuals=[self.manual()], reviews=[rejected])
        self.assertEqual(result["materials"][0]["collection_status"], "rejected")
        accepted = self.review(target_id="manual-a", target_kind="manual_capture")
        result = self.process(manuals=[self.manual(image="small.png")], reviews=[accepted])
        self.assertEqual(result["materials"][0]["quality_status"], "rejected")
        self.assertNotEqual(result["materials"][0]["collection_status"], "collected")

    def test_manual_success_resolves_failed_browser_fallback(self):
        review = self.review(target_id="manual-a", target_kind="manual_capture")
        result = self.process(captures=[self.capture(status="failed")], manuals=[self.manual()], reviews=[review])
        self.assertEqual(result["fallback_requests"][0]["status"], "resolved")

    def test_one_accepted_of_multiple_browser_captures_resolves_fallback(self):
        captures = [self.capture("cap-a"), self.capture("cap-b", image="valid.jpg")]
        reviews = [
            self.review("cap-a", semantic_status="rejected", asset_kind="share_card"),
            self.review("cap-b"),
        ]
        result = self.process(captures=captures, reviews=reviews)
        self.assertEqual(result["fallback_requests"][0]["status"], "resolved")

    def test_unknown_product_and_invalid_manual_source_are_rejected(self):
        review = self.review(target_id="manual-a", target_kind="manual_capture")
        with self.assertRaisesRegex(SemanticReviewError, "任务"):
            self.process(manuals=[self.manual(product="不存在")], reviews=[review])
        with self.assertRaisesRegex(SemanticReviewError, "source_type"):
            self.process(manuals=[self.manual(source_type="browser")], reviews=[review])

    def test_capture_ids_review_targets_and_paths_are_validated(self):
        with self.assertRaisesRegex(SemanticReviewError, "重复"):
            self.process(captures=[self.capture(), self.capture()], reviews=[self.review()])
        with self.assertRaisesRegex(SemanticReviewError, "不存在"):
            self.process(captures=[self.capture()], reviews=[self.review(target_id="cap-x")])
        with self.assertRaisesRegex(SemanticReviewError, "截图文件不存在"):
            self.process(captures=[self.capture(image="missing.png")], reviews=[self.review()])
        with self.assertRaisesRegex(SemanticReviewError, "capture_status"):
            self.process(captures=[self.capture(status="pending")], reviews=[])

    def test_formal_cli_writes_review_outputs_without_legacy_report(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            task_path = root / "task.json"
            captures_path = root / "captures.json"
            reviews_path = root / "reviews.json"
            output = root / "output"
            screenshot = root / "captures" / "valid.png"
            screenshot.parent.mkdir()
            screenshot.write_bytes((self.FIXTURES / "valid.png").read_bytes())
            capture = self.capture()
            capture["screenshot_path"] = "captures/valid.png"
            task_path.write_text(json.dumps(self.task(), ensure_ascii=False), encoding="utf-8")
            captures_path.write_text(json.dumps({"captures": [capture]}, ensure_ascii=False), encoding="utf-8")
            reviews_path.write_text(json.dumps({"reviews": [self.review()]}, ensure_ascii=False), encoding="utf-8")
            completed = subprocess.run([
                sys.executable, "-m", "competitor_analysis_skill",
                "--task-file", str(task_path), "--captures-file", str(captures_path),
                "--semantic-reviews-file", str(reviews_path), "--output", str(output),
            ], cwd=Path(__file__).parents[1], capture_output=True, text=True)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            payload = json.loads((output / "reviewed_materials.json").read_text(encoding="utf-8"))
            self.assertEqual(payload["materials"][0]["collection_status"], "collected")
            self.assertTrue((output / "fallback_requests.json").exists())
            self.assertFalse((output / "materials.json").exists())
            self.assertFalse((output / "report.html").exists())

    def test_formal_cli_resolves_relative_capture_file_from_working_directory(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            task_path = root / "task.json"
            captures_path = root / "captures.json"
            reviews_path = root / "reviews.json"
            output = root / "output"
            screenshot = root / "captures" / "valid.png"
            screenshot.parent.mkdir()
            screenshot.write_bytes((self.FIXTURES / "valid.png").read_bytes())
            capture = self.capture()
            capture["screenshot_path"] = "captures/valid.png"
            task_path.write_text(json.dumps(self.task(), ensure_ascii=False), encoding="utf-8")
            captures_path.write_text(json.dumps({"captures": [capture]}, ensure_ascii=False), encoding="utf-8")
            reviews_path.write_text(json.dumps({"reviews": [self.review()]}, ensure_ascii=False), encoding="utf-8")
            project_root = Path(__file__).parents[1]
            relative_captures = os.path.relpath(captures_path, project_root)
            completed = subprocess.run([
                sys.executable, "-m", "competitor_analysis_skill",
                "--task-file", str(task_path), "--captures-file", relative_captures,
                "--semantic-reviews-file", str(reviews_path), "--output", str(output),
            ], cwd=project_root, capture_output=True, text=True)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            payload = json.loads((output / "reviewed_materials.json").read_text(encoding="utf-8"))
            self.assertEqual(payload["materials"][0]["collection_status"], "collected")

    def test_cli_rejects_reviews_without_capture_or_manual_input(self):
        completed = subprocess.run([
            sys.executable, "-m", "competitor_analysis_skill",
            "--task-file", "task.json", "--semantic-reviews-file", "reviews.json",
        ], cwd=Path(__file__).parents[1], capture_output=True, text=True)
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("--captures-file", completed.stderr)


if __name__ == "__main__":
    unittest.main()
