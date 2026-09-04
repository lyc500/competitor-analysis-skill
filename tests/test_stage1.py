import json
import subprocess
from unittest.mock import patch
import tempfile
import unittest
from pathlib import Path

from competitor_analysis_skill.requirements import parse_request
from competitor_analysis_skill.planning import plan_competitors
from competitor_analysis_skill.task_contract import ContractError, load_task, load_task_file, validate_task
from competitor_analysis_skill.pipeline import run_pipeline


class Stage1ContractTests(unittest.TestCase):
    def _task(self, target_page, products, sources=None):
        sources = sources or ["user_specified"] * len(products)
        competitors = [{
            "product_name": name, "region": "CN", "product_type": "电商",
            "platform": "Web", "target_page": target_page, "planning_source": source,
            "priority": "high" if source == "user_specified" else "medium", "reason": "Agent 计划",
        } for name, source in zip(products, sources)]
        return {
            "raw_request": "Agent structured task", "research_goal": "页面参考",
            "target_page": target_page, "regions": ["CN"], "specified_products": products,
            "assumptions": [], "needs_clarification": False, "task_status": "ready",
            "planning_strategy": "user_only" if all(s == "user_specified" for s in sources) else "mixed",
            "competitors": competitors,
        }

    def test_arbitrary_product_detail_task_is_preserved(self):
        task = load_task(self._task("商品详情页", ["淘宝", "京东"]))
        planned = plan_competitors(task)
        self.assertEqual([row["product_name"] for row in planned], ["淘宝", "京东"])
        self.assertEqual([row["target_page"] for row in planned], ["商品详情页", "商品详情页"])

    def test_arbitrary_live_gift_task_is_not_replaced(self):
        task = load_task(self._task("直播礼物面板", ["B站", "快手直播"]))
        self.assertEqual([row["product_name"] for row in plan_competitors(task)], ["B站", "快手直播"])

    def test_arbitrary_page_does_not_require_keyword_table(self):
        task = load_task(self._task("新型空间面板", ["产品甲"]))
        self.assertEqual(task["target_page"], "新型空间面板")

    def test_missing_specified_product_fails(self):
        task = self._task("商品详情页", ["淘宝", "京东"])
        task["competitors"] = task["competitors"][:1]
        with self.assertRaises(ContractError):
            validate_task(task)

    def test_user_products_are_sorted_first_and_must_be_high_priority(self):
        task = self._task("商品详情页", ["淘宝"], ["user_specified"])
        task["competitors"].append({**task["competitors"][0], "product_name": "京东", "planning_source": "agent_planned", "priority": "medium"})
        task["planning_strategy"] = "mixed"
        self.assertEqual([r["product_name"] for r in plan_competitors(task)], ["淘宝", "京东"])
        bad = self._task("商品详情页", ["淘宝"])
        bad["competitors"][0]["priority"] = "medium"
        with self.assertRaises(ContractError):
            validate_task(bad)

    def test_target_page_mismatch_fails(self):
        task = self._task("商品详情页", ["淘宝"])
        task["competitors"][0]["target_page"] = "搜索结果页"
        with self.assertRaises(ContractError):
            validate_task(task)

    def test_task_file_entry_and_pipeline_use_agent_competitors(self):
        task = self._task("商品详情页", ["淘宝", "京东"])
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "task.json"
            path.write_text(json.dumps(task, ensure_ascii=False), encoding="utf-8")
            loaded = load_task_file(path)
            result = run_pipeline(loaded, Path(directory) / "report", fetch=False)
            self.assertEqual([r["product_name"] for r in result["payload"]["competitors"]], ["淘宝", "京东"])

    def test_cli_task_file_is_formal_entry(self):
        task = self._task("商品详情页", ["淘宝", "京东"])
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "task.json"
            output = Path(directory) / "report"
            path.write_text(json.dumps(task, ensure_ascii=False), encoding="utf-8")
            completed = subprocess.run(["python3", "-m", "competitor_analysis_skill", "--task-file", str(path), "--offline", "--output", str(output)], capture_output=True, text=True)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            payload = json.loads((output / "materials.json").read_text(encoding="utf-8"))
            self.assertEqual([r["product_name"] for r in payload["competitors"]], ["淘宝", "京东"])

    def test_formal_planning_does_not_call_builtin_catalog(self):
        task = load_task(self._task("商品详情页", ["淘宝"]))
        with patch("competitor_analysis_skill.catalog.builtin_search_candidates", side_effect=AssertionError("fixture catalog called")):
            self.assertEqual([r["product_name"] for r in plan_competitors(task)], ["淘宝"])
    def test_search_task_has_structured_target_and_agent_plan(self):
        task = parse_request("帮我搜集一下海内外热门产品的搜索结果页")
        self.assertEqual(task["raw_request"], "帮我搜集一下海内外热门产品的搜索结果页")
        self.assertEqual(task["target_page"], "搜索结果页")
        self.assertEqual(task["task_status"], "planned")
        self.assertEqual(plan_competitors(task), [])

    def test_gifts_task_preserves_four_user_products_before_agent_additions(self):
        task = load_task(self._task("直播礼物面板", ["虎牙", "斗鱼", "抖音", "Twitch"], ["user_specified"] * 4 + []))
        task["competitors"].extend([
            {"product_name": "快手直播", "region": "CN", "product_type": "直播产品", "platform": "Web", "target_page": "直播礼物面板", "planning_source": "agent_planned", "priority": "medium", "reason": "补充"},
        ])
        task["planning_strategy"] = "mixed"
        task = load_task(task)
        competitors = plan_competitors(task)
        self.assertEqual([c["product_name"] for c in competitors[:4]], ["虎牙", "斗鱼", "抖音", "Twitch"])
        self.assertTrue(all(c["planning_source"] == "user_specified" for c in competitors[:4]))
        self.assertTrue(all(c["priority"] == "high" for c in competitors[:4]))
        self.assertEqual(task["planning_strategy"], "mixed")

    def test_ambiguous_target_needs_clarification(self):
        task = parse_request("帮我看看热门产品怎么做")
        self.assertEqual(task["task_status"], "needs_clarification")
        self.assertTrue(task["needs_clarification"])
        self.assertEqual(plan_competitors(task), [])

    def test_ready_task_without_competitors_is_invalid(self):
        with self.assertRaises(ContractError):
            validate_task({
                "raw_request": "x", "research_goal": "y", "target_page": "页面",
                "regions": [], "specified_products": [], "assumptions": [],
                "needs_clarification": False, "task_status": "ready",
                "planning_strategy": "agent_only", "competitors": [],
            })

    def test_fixture_requires_explicit_strategy(self):
        fixture = {
            "raw_request": "fixture", "research_goal": "test", "target_page": "搜索结果页",
            "regions": ["CN"], "specified_products": [], "assumptions": [],
            "needs_clarification": False, "task_status": "ready",
            "planning_strategy": "fixture_demo", "competitors": [{
                "product_name": "百度", "region": "CN", "product_type": "搜索",
                "platform": "Web", "target_page": "搜索结果页", "planning_source": "fixture_demo",
                "priority": "high", "reason": "fixture",
            }],
        }
        self.assertIs(validate_task(fixture), fixture)
        fixture["planning_strategy"] = "agent_only"
        with self.assertRaises(ContractError):
            validate_task(fixture)

    def test_missing_region_is_recorded_as_assumption_or_clarification(self):
        task = parse_request("帮我搜集热门产品的搜索结果页")
        self.assertEqual(task["regions"], [])
        self.assertTrue(task["assumptions"] or task["task_status"] == "needs_clarification")


if __name__ == "__main__":
    unittest.main()
