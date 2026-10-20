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

    def test_mobile_report_excludes_collected_desktop_web_material(self):
        task = {**self.task(), "target_surface": "mobile_app"}
        mobile = self.material(
            id="mobile",
            product_name="Mobile App",
            platform="iOS",
            target_surface="mobile_app",
            target_surface_match="matched",
        )
        desktop = self.material(
            id="desktop",
            product_name="Desktop Web",
            platform="Web",
            image_path="assets/desktop.png",
            target_surface="mobile_app",
            target_surface_match="matched",
        )
        classification = self.classification()
        classification["groups"][0]["material_ids"] = ["mobile", "desktop"]
        html = render_report(task, [mobile, desktop], classification)
        self.assertIn("Mobile App", html)
        self.assertNotIn("Desktop Web", html)
        self.assertNotIn("assets/desktop.png", html)

    def test_gallery_uses_five_columns_on_desktop(self):
        html = render_report(self.task(), [self.material()], self.classification())
        self.assertNotIn("repeat(auto-fit,minmax(240px,1fr))", html)
        self.assertRegex(
            html,
            r"\.grid\{[^}]*grid-template-columns:repeat\(5,minmax\(0,1fr\)\)",
        )
        self.assertIn("justify-content:start", html)

    def test_large_group_uses_progressive_more_button(self):
        materials = [
            self.material(
                id=f"a{i}",
                product_name=f"产品{i}",
                image_path=f"assets/{i}.png",
            )
            for i in range(25)
        ]
        classification = self.classification()
        classification["groups"][0]["material_ids"] = [m["id"] for m in materials]
        html = render_report(self.task(), materials, classification)
        self.assertIn('data-page-size="20"', html)
        self.assertIn('data-index="19"', html)
        self.assertIn('data-index="20" hidden', html)
        self.assertIn('class="more-button"', html)
        self.assertIn(">更多<", html)
        self.assertIn("function initGalleries", html)
        self.assertIn("visible+PAGE_SIZE", html)

    def test_group_with_at_most_twenty_cards_has_no_more_button(self):
        materials = [
            self.material(
                id=f"a{i}",
                product_name=f"产品{i}",
                image_path=f"assets/{i}.png",
            )
            for i in range(20)
        ]
        classification = self.classification()
        classification["groups"][0]["material_ids"] = [m["id"] for m in materials]
        html = render_report(self.task(), materials, classification)
        self.assertNotIn('class="more-button"', html)

    def test_portrait_images_keep_intrinsic_ratio_and_lightbox(self):
        html = render_report(self.task(), [self.material()], self.classification())
        self.assertNotIn("width:100%;height:360px", html)
        self.assertNotIn(".asset-image{height:300px}", html)
        self.assertRegex(
            html,
            r"\.asset-image\{[^}]*width:auto;[^}]*max-width:100%;[^}]*height:auto;[^}]*max-height:720px;[^}]*object-fit:contain",
        )
        self.assertIn('onclick="showModal(this)"', html)
        self.assertIn('<dialog id="viewer"', html)
        self.assertIn("function showModal", html)
