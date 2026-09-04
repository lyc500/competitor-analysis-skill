import json
import tempfile
import unittest
from pathlib import Path

from competitor_analysis_skill.pipeline import run_pipeline
from competitor_analysis_skill.requirements import parse_request
from competitor_analysis_skill.quality import assess_image
from competitor_analysis_skill.classification import classify_assets
from competitor_analysis_skill.collector import PublicSourceCollector
from competitor_analysis_skill.report import render_report


class MvpTests(unittest.TestCase):
  def test_parse_search_results_request(self):
    task = parse_request("帮我搜集一下海内外热门产品的搜索结果页。")
    self.assertEqual(task.target_page, "搜索结果页")
    self.assertEqual(task.regions, ["CN", "Global"])


  def test_quality_filter_rejects_non_image_and_accepts_clear_image(self):
    with tempfile.TemporaryDirectory() as directory:
      tmp_path = Path(directory)
      bad = tmp_path / "bad.txt"
      bad.write_text("not an image")
      good = tmp_path / "good.png"
      good.write_bytes(b"\x89PNG\r\n\x1a\n" + b"0" * 100)
      self.assertEqual(assess_image(bad).status, "rejected")
      self.assertEqual(assess_image(good).status, "rejected")


  def test_classification_uses_collected_page_structure(self):
    assets = [
        {"id": "a", "page_name": "搜索结果页", "product_type": "电商", "region": "CN", "notes": "分栏筛选"},
        {"id": "b", "page_name": "搜索结果页", "product_type": "内容社区", "region": "Global", "notes": "连续内容流"},
    ]
    result = classify_assets(assets)
    self.assertEqual(result["classification_dimension"], "页面结构模式")
    self.assertEqual({g["name"] for g in result["groups"]}, {"分栏筛选", "连续内容流"})

  def test_classification_can_choose_region_when_that_is_the_stronger_difference(self):
    assets = [
        {"id": "a", "page_name": "搜索结果页", "product_type": "综合搜索", "region": "CN", "notes": ""},
        {"id": "b", "page_name": "搜索结果页", "product_type": "综合搜索", "region": "Global", "notes": ""},
    ]
    result = classify_assets(assets)
    self.assertEqual(result["classification_dimension"], "地区")

  def test_public_collector_is_separate_from_builtin_candidate_catalog(self):
    self.assertTrue(PublicSourceCollector().source_type == "web")
    self.assertNotIn("target_url", PublicSourceCollector.__dict__)


  def test_report_embeds_assets_and_has_click_to_zoom(self):
    html = render_report(
        {"request": "搜索结果页", "research_goal": "页面参考"},
        [{"id": "a", "product_name": "产品 A", "image_path": "assets/a.png", "page_name": "搜索结果页", "region": "CN", "product_type": "电商", "notes": "分栏筛选"}],
        {"classification_dimension": "页面结构模式", "groups": [{"name": "分栏筛选", "reason": "", "asset_ids": ["a"]}]},
    )
    self.assertIn('class="asset-image"', html)
    self.assertIn("showModal", html)
    self.assertIn("assets/a.png", html)


  def test_pipeline_writes_json_and_html(self):
    with tempfile.TemporaryDirectory() as directory:
      result = run_pipeline("帮我搜集一下海内外热门产品的搜索结果页。", Path(directory), fetch=False)
      self.assertTrue(result["assets_json"].exists())
      self.assertTrue(result["report_html"].exists())
      payload = json.loads(result["assets_json"].read_text())
      self.assertEqual(payload["task"]["target_page"], "搜索结果页")
      self.assertTrue(payload["competitors"])


if __name__ == "__main__":
  unittest.main()
