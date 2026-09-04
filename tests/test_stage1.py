import unittest

from competitor_analysis_skill.requirements import parse_request
from competitor_analysis_skill.planning import plan_competitors
from competitor_analysis_skill.task_contract import ContractError, validate_task


class Stage1ContractTests(unittest.TestCase):
    def test_search_task_has_structured_target_and_agent_plan(self):
        task = parse_request("帮我搜集一下海内外热门产品的搜索结果页")
        self.assertEqual(task["raw_request"], "帮我搜集一下海内外热门产品的搜索结果页")
        self.assertEqual(task["target_page"], "搜索结果页")
        self.assertEqual(task["task_status"], "ready")
        competitors = plan_competitors(task)
        self.assertTrue(competitors)
        self.assertTrue(all(row["planning_source"] == "agent_planned" for row in competitors))

    def test_gifts_task_preserves_four_user_products_before_agent_additions(self):
        task = parse_request("帮我看看虎牙、斗鱼、抖音和 Twitch 的直播礼物面板")
        self.assertEqual(task["target_page"], "直播礼物面板")
        self.assertEqual(task["specified_products"], ["虎牙", "斗鱼", "抖音", "Twitch"])
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
