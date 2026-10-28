import unittest
from competitor_analysis_skill.report import render_report

class ReportStage4Tests(unittest.TestCase):
    def task(self): return {"target_page":"搜索结果页","research_goal":"参考 <目标>"}
    def classification(self): return {"classification_status":"ready","classification_dimension":"结果组织方式","classification_reason":"Agent 观察","groups":[{"name":"双栏 <A>","reason":"原因 & 说明","material_ids":["a"]}],"material_labels":[{"material_id":"a","labels":{"布局":"双栏"}}]}
    def material(self, **kw): return dict({"id":"a","product_name":"产品 <A>","page_name":"搜索结果页","region":"CN","product_type":"社区","platform":"Web","image_path":"assets/a.png","source_url":"https://example.com/?a=1&b=2","collection_status":"collected","semantic_status":"accepted","quality_status":"accepted"},**kw)
    def test_only_collected_is_rendered_and_labels_escape(self):
        html=render_report(self.task(),[self.material(),self.material(id="bad",image_path="assets/b.png",collection_status="rejected")],self.classification())
        self.assertIn('class="asset-image"',html); self.assertIn("assets/a.png",html); self.assertNotIn("assets/b.png",html); self.assertIn("&lt;A&gt;",html); self.assertIn("布局: 双栏",html)

    def test_card_keeps_only_identity_status_and_focus_visible_before_details(self):
        classification=self.classification()
        classification["material_labels"][0]["labels"]={
            "page_role":"services_drawer", "path_stage":"personal_center_drawer_lower",
            "interaction_stage":"drawer_open_scrolled", "render_state":"loaded_complete",
            "login_state":"logged_out", "version_status":"historical_version",
            "annotation_status":"original_annotated",
        }
        html=render_report(self.task(),[self.material(
            notes="历史与版本说明", semantic_reason="语义审核说明", quality_reason="质量说明",
        )],classification)
        card=html[html.index('<article class="gallery-card"'):html.index('</article>')]
        visible,detail=card.split('<details class="card-details">',1)
        self.assertIn("产品 &lt;A&gt;",visible)
        self.assertIn("Web",visible)
        self.assertIn("未登录",visible)
        self.assertIn("抽屉",visible)
        self.assertIn("下段",visible)
        self.assertIn("历史版本",visible)
        self.assertIn("原图带标注",visible)
        for hidden in ("page_role", "services_drawer", "语义审核说明", "质量说明",
                       "历史与版本说明", "https://example.com/?a=1&amp;b=2", "证据链"):
            self.assertNotIn(hidden,visible)
            self.assertIn(hidden,detail)
        self.assertIn('<summary>页面详情</summary>',detail)

    def test_gallery_groups_are_layout_units_with_stable_span_hints(self):
        materials=[]; groups=[]
        for group_index,size in enumerate((4,2,6)):
            ids=[]
            for index in range(size):
                mid=f"g{group_index}-{index}"; ids.append(mid)
                materials.append(self.material(id=mid,product_name=mid,image_path=f"assets/{mid}.png"))
            groups.append({"id":f"group-{group_index}","name":f"组{group_index}","reason":"理由","material_ids":ids})
        classification={**self.classification(),"groups":groups,"material_labels":[]}
        html=render_report(self.task(),materials,classification)
        self.assertIn('class="gallery-layout"',html)
        self.assertIn('data-layout-size="4"',html)
        self.assertIn('data-layout-size="2"',html)
        self.assertIn('data-layout-size="5"',html)
        self.assertNotIn("grid-auto-flow:dense",html)
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
        self.assertIn('class="image-button"', html)
        self.assertIn('onclick="showModal(this.querySelector(\'img\'))"', html)
        self.assertIn('<dialog id="viewer"', html)
        self.assertIn("function showModal", html)

    def test_report_exposes_evidence_statistics_and_coverage_boundary(self):
        html = render_report(
            self.task(),
            [self.material()],
            self.classification(),
            evidence_statistics={
                "sources": {"attempted": 2, "unknown_access": 1, "access_status": {"accessible": 1, "blocked": 1}},
                "candidates": {"accepted": 1, "rejected": 3, "not_reviewed": 2},
                "semantic_reviews": {"accepted": 1, "rejected": 0, "not_reviewed": 1},
                "fallback": {"open": 1, "resolved": 0},
                "coverage": {"products_without_collected_material": 1, "pending_candidate_count": 2},
            },
        )
        self.assertIn("来源访问", html)
        self.assertIn("候选处置", html)
        self.assertIn("待审核候选", html)
        self.assertIn("unknown_access", html)
        self.assertIn("blocked 1", html)
        self.assertIn("产品覆盖缺口", html)
        self.assertIn("覆盖限制：1 个产品没有有效截图", html)

    def test_report_exposes_evidence_ids_for_traceability(self):
        html = render_report(self.task(), [self.material(
            capture_id="cap-a", source_candidate_id="cand-a", source_attempt_id="att-a",
        )], self.classification())
        self.assertIn('data-material-id="a"', html)
        self.assertIn('data-capture-id="cap-a"', html)
        self.assertIn('data-source-candidate-id="cand-a"', html)
        self.assertIn('data-source-attempt-id="att-a"', html)
        self.assertIn("证据链：material: a · capture: cap-a · candidate: cand-a · attempt: att-a", html)

    def test_source_access_preparation_is_preserved_inside_folded_process_section(self):
        preparation = {
            "id": "access-batch-1",
            "research_scope": "个人中心公开素材",
            "decision": {
                "status": "not_required",
                "summary": "三个来源的可见范围足以继续，付费墙边界保留记录。",
            },
            "resume": {"status": "not_needed"},
            "current_checks_by_source": {"att-ui": "check-ui"},
            "checks": [{
                "id": "check-ui", "source_attempt_id": "att-ui",
                "authentication_state": "authenticated", "access_barrier": "paywall",
                "page_open": True, "search_usable": True, "filter_usable": True,
                "detail_usable": True, "original_asset_usable": True,
                "pagination_usable": False, "visible_scope": "前 20 张可见",
                "coverage_impact": "minor", "notes": "非会员可访问首批结果",
            }],
        }
        html = render_report(
            self.task(), [self.material()], self.classification(),
            source_evidence={"access_preparation": preparation},
        )
        process = html[html.index('<details data-module="methodology"'):]
        self.assertIn("来源访问准备", process)
        self.assertIn("前 20 张可见", process)
        self.assertIn("登录状态：authenticated", process)
        self.assertIn("原图：可用", process)
        self.assertIn("继续浏览：不可用", process)
        self.assertIn("无需用户选择", process)
        self.assertNotIn("cookie", process.lower())
