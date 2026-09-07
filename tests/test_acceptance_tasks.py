import unittest
from pathlib import Path

from competitor_analysis_skill.catalog import SEARCH_CATALOG
from competitor_analysis_skill.planning import plan_competitors
from competitor_analysis_skill.task_contract import load_task_file


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "acceptance"


class Stage5AcceptanceTaskTests(unittest.TestCase):
    def _load(self, filename):
        return load_task_file(FIXTURE_DIR / filename)

    def test_task_a_is_agent_only_cross_region_plan(self):
        task = self._load("task_a.json")
        competitors = plan_competitors(task)

        self.assertEqual(task["raw_request"], "帮我搜集一下海内外热门产品的搜索结果页。")
        self.assertEqual(task["target_page"], "搜索结果页")
        self.assertEqual(task["specified_products"], [])
        self.assertEqual(task["planning_strategy"], "agent_only")
        self.assertEqual(task["task_status"], "ready")
        self.assertGreaterEqual(len(competitors), 3)
        self.assertEqual({row["region"] for row in competitors}, {"CN", "Global"})
        self.assertEqual(len({row["product_name"] for row in competitors}), len(competitors))
        self.assertTrue(all(row["planning_source"] == "agent_planned" for row in competitors))
        self.assertTrue(all(row["reason"].strip() for row in competitors))
        self.assertNotIn("fixture_demo", {row["planning_source"] for row in competitors})

    def test_task_b_preserves_specified_products_before_agent_additions(self):
        task = self._load("task_b.json")
        competitors = plan_competitors(task)
        specified = ["虎牙", "斗鱼", "抖音直播", "Twitch"]

        self.assertEqual(
            task["raw_request"],
            "帮我搜集一下国内外热门直播产品的礼物面板，重点关注虎牙、斗鱼、抖音直播和 Twitch。",
        )
        self.assertEqual(task["target_page"], "直播产品礼物面板")
        self.assertEqual(task["specified_products"], specified)
        self.assertEqual(task["planning_strategy"], "mixed")
        self.assertEqual(task["task_status"], "ready")
        self.assertEqual([row["product_name"] for row in competitors[:4]], specified)
        self.assertTrue(all(row["planning_source"] == "user_specified" for row in competitors[:4]))
        self.assertTrue(all(row["priority"] == "high" for row in competitors[:4]))
        self.assertGreater(len(competitors), len(specified))
        self.assertTrue(all(row["planning_source"] == "agent_planned" for row in competitors[4:]))
        self.assertTrue(all(row["reason"].strip() for row in competitors))
        self.assertNotIn("fixture_demo", {row["planning_source"] for row in competitors})

    def test_acceptance_plans_are_distinct_and_task_a_is_not_the_fixed_catalog(self):
        task_a = self._load("task_a.json")
        task_b = self._load("task_b.json")
        task_a_names = {row["product_name"] for row in plan_competitors(task_a)}
        task_b_names = {row["product_name"] for row in plan_competitors(task_b)}
        catalog_names = {row[0] for row in SEARCH_CATALOG}

        self.assertNotEqual(task_a["target_page"], task_b["target_page"])
        self.assertNotEqual(task_a_names, task_b_names)
        self.assertNotEqual(task_a_names, catalog_names)
        self.assertTrue(task_a_names - catalog_names)


if __name__ == "__main__":
    unittest.main()
