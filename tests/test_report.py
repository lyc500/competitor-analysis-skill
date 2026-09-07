import unittest
from competitor_analysis_skill.report import render_report

class ReportStage4Tests(unittest.TestCase):
    def task(self): return {"target_page":"搜索结果页","research_goal":"参考 <目标>"}
    def classification(self): return {"classification_status":"ready","classification_dimension":"结果组织方式","classification_reason":"Agent 观察","groups":[{"name":"双栏 <A>","reason":"原因 & 说明","material_ids":["a"]}],"material_labels":[{"material_id":"a","labels":{"布局":"双栏"}}]}
    def material(self, **kw): return dict({"id":"a","product_name":"产品 <A>","page_name":"搜索结果页","region":"CN","product_type":"社区","platform":"Web","image_path":"assets/a.png","source_url":"https://example.com/?a=1&b=2","collection_status":"collected","semantic_status":"accepted","quality_status":"accepted"},**kw)
    def test_only_collected_is_rendered_and_labels_escape(self):
        html=render_report(self.task(),[self.material(),self.material(id="bad",image_path="assets/b.png",collection_status="rejected")],self.classification())
        self.assertIn('class="asset-image"',html); self.assertIn("assets/a.png",html); self.assertNotIn("assets/b.png",html); self.assertIn("&lt;A&gt;",html); self.assertIn("布局: 双栏",html)
    def test_fallback_and_unavailable(self):
        fallback=[{"product_name":"产品A","status":"open","reason":"缺少素材","allowed_methods":["user_upload"]},{"product_name":"产品B","status":"resolved","reason":"已有","allowed_methods":[]}]
        html=render_report(self.task(),[],{"classification_status":"unavailable","classification_dimension":"","classification_reason":"当前没有有效 collected 素材","groups":[],"material_labels":[]},fallback)
        self.assertIn("unavailable",html); self.assertIn("产品A",html); self.assertNotIn("产品B",html); self.assertNotIn('class="asset-image"',html)
