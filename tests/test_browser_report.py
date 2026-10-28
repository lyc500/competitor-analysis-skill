import json, shutil, threading, unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from tempfile import TemporaryDirectory
from playwright.sync_api import sync_playwright
from competitor_analysis_skill.pipeline import run_pipeline

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        body = Path(self.server.root, self.path.lstrip('/')).read_bytes()
        self.send_response(200); self.send_header('Content-Type','text/html' if self.path.endswith('.html') else 'image/png'); self.end_headers(); self.wfile.write(body)
    def log_message(self,*args): pass

class BrowserReportTests(unittest.TestCase):
    def test_chromium_loads_report_and_zoom_mobile(self):
        with TemporaryDirectory() as d:
            root=Path(d); src=root/'stage3c'; src.mkdir(); assets=src/'assets'; assets.mkdir()
            fixture=Path(__file__).parent/'fixtures/materials/valid.png'; (assets/'a.png').write_bytes(fixture.read_bytes())
            task={"raw_request":"x","research_goal":"参考","target_page":"搜索结果页","regions":["CN"],"specified_products":["产品A"],"assumptions":[],"needs_clarification":False,"task_status":"ready","planning_strategy":"user_only","competitors":[{"product_name":"产品A","region":"CN","product_type":"社区","platform":"Web","target_page":"搜索结果页","planning_source":"user_specified","priority":"high","reason":"指定"}]}
            reviewed={"task":task,"materials":[{"id":"mat-a","product_name":"产品A","page_name":"搜索结果页","region":"CN","product_type":"社区","platform":"Web","image_path":"assets/a.png","source_type":"user_upload","collection_method":"user_provided","provenance":"user_upload","semantic_status":"accepted","quality_status":"accepted","collection_status":"collected"}],"fallback_requests":[]}
            plan={"classification_dimension":"布局","classification_reason":"Agent 观察","groups":[{"name":"自定义组","reason":"Agent","material_ids":["mat-a"]}],"material_labels":[{"material_id":"mat-a","labels":{"布局":"单列"}}]}
            reviewed_path=src/'reviewed_materials.json'; reviewed_path.write_text(json.dumps(reviewed,ensure_ascii=False)); plan_path=root/'plan.json'; plan_path.write_text(json.dumps(plan,ensure_ascii=False))
            out=root/'out'; run_pipeline(task,out,reviewed_materials_file=reviewed_path,classification_plan_file=plan_path)
            report_data=json.loads((out/'report_data.json').read_text(encoding='utf-8')); asset_path=report_data['materials'][0]['image_path']
            moved=root/'new_location'; shutil.move(out,moved); self.assertFalse(out.exists())
            class S(ThreadingHTTPServer): pass
            S.root=moved; server=S(('127.0.0.1',0),Handler); thread=threading.Thread(target=server.serve_forever,daemon=True); thread.start(); self.addCleanup(server.shutdown)
            with sync_playwright() as p:
                browser=p.chromium.launch(headless=True); page=browser.new_page(viewport={"width":390,"height":844}); page.goto(f'http://127.0.0.1:{server.server_port}/report.html'); self.assertEqual(page.locator('.asset-image').count(),1); self.assertTrue(page.locator('.asset-image').evaluate('image => image.complete && image.naturalWidth > 0')); page.locator('.asset-image').click(); self.assertTrue(page.locator('dialog[open]').count()==1); self.assertTrue(page.locator('#viewer-image').get_attribute('src').endswith('/'+asset_path)); page.wait_for_function("document.getElementById('viewer-image').complete && document.getElementById('viewer-image').naturalWidth > 0"); self.assertGreater(page.locator('#viewer-image').evaluate('image => image.naturalWidth'),0); page.locator('button[aria-label="关闭"]').click(); self.assertEqual(page.locator('dialog[open]').count(),0); self.assertLessEqual(page.evaluate('document.documentElement.scrollWidth'), page.evaluate('window.innerWidth')+2); browser.close()

    def test_more_button_reveals_next_twenty_cards_in_chromium(self):
        with TemporaryDirectory() as d:
            root = Path(d); src = root / 'stage3c'; assets = src / 'assets'; assets.mkdir(parents=True)
            fixture = Path(__file__).parent / 'fixtures/materials/valid.png'
            materials = []
            for index in range(25):
                filename = f'{index}.png'
                (assets / filename).write_bytes(fixture.read_bytes())
                materials.append({
                    "id": f"mat-{index}", "product_name": f"产品{index}",
                    "page_name": "搜索结果页", "region": "CN", "product_type": "社区",
                    "platform": "Web", "image_path": f"assets/{filename}",
                    "source_type": "user_upload", "collection_method": "user_provided",
                    "provenance": "user_upload", "semantic_status": "accepted",
                    "quality_status": "accepted", "collection_status": "collected",
                })
            task = {"raw_request":"x","research_goal":"参考","target_page":"搜索结果页","regions":["CN"],"specified_products":["产品0"],"assumptions":[],"needs_clarification":False,"task_status":"ready","planning_strategy":"user_only","competitors":[{"product_name":"产品0","region":"CN","product_type":"社区","platform":"Web","target_page":"搜索结果页","planning_source":"user_specified","priority":"high","reason":"指定"}]}
            task["specified_products"] = [f"产品{index}" for index in range(25)]
            task["competitors"] = [{"product_name": f"产品{index}", "region": "CN", "product_type": "社区", "platform": "Web", "target_page": "搜索结果页", "planning_source": "user_specified", "priority": "high", "reason": "指定"} for index in range(25)]
            reviewed = {"task": task, "materials": materials, "fallback_requests": []}
            plan = {"classification_dimension":"布局","classification_reason":"Agent 观察","groups":[{"name":"自定义组","reason":"Agent","material_ids":[m["id"] for m in materials]}],"material_labels":[]}
            reviewed_path = src / 'reviewed_materials.json'; reviewed_path.write_text(json.dumps(reviewed, ensure_ascii=False)); plan_path = root / 'plan.json'; plan_path.write_text(json.dumps(plan, ensure_ascii=False))
            out = root / 'out'; run_pipeline(task, out, reviewed_materials_file=reviewed_path, classification_plan_file=plan_path)
            class S(ThreadingHTTPServer): pass
            S.root = out; server = S(('127.0.0.1', 0), Handler); thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start(); self.addCleanup(server.shutdown)
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True); page = browser.new_page(viewport={"width":1440,"height":900}); page.goto(f'http://127.0.0.1:{server.server_port}/report.html')
                self.assertEqual(page.locator('.gallery-card:not([hidden])').count(), 20)
                self.assertEqual(page.locator('.grid').evaluate("element => getComputedStyle(element).gridTemplateColumns.split(' ').length"), 5)
                more = page.locator('.more-button'); self.assertTrue(more.is_visible()); more.click()
                self.assertEqual(page.locator('.gallery-card:not([hidden])').count(), 25); self.assertFalse(more.is_visible()); browser.close()

    def test_multiple_groups_each_expand_in_independent_twenty_card_steps(self):
        with TemporaryDirectory() as d:
            root = Path(d); src = root / 'stage3c'; assets = src / 'assets'; assets.mkdir(parents=True)
            fixture = Path(__file__).parent / 'fixtures/materials/valid.png'
            materials = []
            groups = []
            competitors = []
            for group_index, size in enumerate((45, 21)):
                ids = []
                for index in range(size):
                    material_id = f'mat-{group_index}-{index}'; filename = f'{material_id}.png'
                    (assets / filename).write_bytes(fixture.read_bytes())
                    ids.append(material_id)
                    product = f'产品{group_index}-{index}'
                    competitors.append({"product_name": product, "region": "CN", "product_type": "社区", "platform": "Web", "target_page": "搜索结果页", "planning_source": "user_specified", "priority": "high", "reason": "指定"})
                    materials.append({"id": material_id, "product_name": product, "page_name": "搜索结果页", "region": "CN", "product_type": "社区", "platform": "Web", "image_path": f'assets/{filename}', "source_type": "user_upload", "collection_method": "user_provided", "provenance": "user_upload", "semantic_status": "accepted", "quality_status": "accepted", "collection_status": "collected"})
                groups.append({"name": f"组{group_index}", "reason": "独立展开测试", "material_ids": ids})
            task = {"raw_request":"x","research_goal":"参考","target_page":"搜索结果页","regions":["CN"],"specified_products":[c["product_name"] for c in competitors],"assumptions":[],"needs_clarification":False,"task_status":"ready","planning_strategy":"user_only","competitors":competitors}
            reviewed_path = src / 'reviewed_materials.json'; reviewed_path.write_text(json.dumps({"task": task, "materials": materials, "fallback_requests": []}, ensure_ascii=False)); plan_path = root / 'plan.json'; plan_path.write_text(json.dumps({"classification_dimension":"布局","classification_reason":"Agent 观察","groups":groups,"material_labels":[]}, ensure_ascii=False))
            out = root / 'out'; run_pipeline(task, out, reviewed_materials_file=reviewed_path, classification_plan_file=plan_path)
            class S(ThreadingHTTPServer): pass
            S.root = out; server = S(('127.0.0.1', 0), Handler); thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start(); self.addCleanup(server.shutdown)
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True); page = browser.new_page(viewport={"width":390,"height":844}); page.goto(f'http://127.0.0.1:{server.server_port}/report.html')
                galleries = page.locator('[data-gallery]')
                self.assertEqual(galleries.count(), 2)
                self.assertEqual(galleries.nth(0).locator('.gallery-card:not([hidden])').count(), 20)
                self.assertEqual(galleries.nth(1).locator('.gallery-card:not([hidden])').count(), 20)
                buttons = page.locator('.more-button'); self.assertEqual(buttons.count(), 2)
                buttons.nth(0).click(); self.assertEqual(galleries.nth(0).locator('.gallery-card:not([hidden])').count(), 40); self.assertTrue(buttons.nth(0).is_visible())
                page.set_viewport_size({"width": 1440, "height": 900})
                self.assertEqual(galleries.nth(0).locator('.gallery-card:not([hidden])').count(), 40)
                page.set_viewport_size({"width": 390, "height": 844})
                self.assertEqual(galleries.nth(0).locator('.gallery-card:not([hidden])').count(), 40)
                buttons.nth(0).click(); self.assertEqual(galleries.nth(0).locator('.gallery-card:not([hidden])').count(), 45); self.assertFalse(buttons.nth(0).is_visible())
                buttons.nth(1).click(); self.assertEqual(galleries.nth(1).locator('.gallery-card:not([hidden])').count(), 21); self.assertFalse(buttons.nth(1).is_visible())
                first_ids = galleries.nth(0).locator('.gallery-card:not([hidden])').evaluate_all("cards => cards.map(c => c.dataset.materialId)")
                second_ids = galleries.nth(1).locator('.gallery-card:not([hidden])').evaluate_all("cards => cards.map(c => c.dataset.materialId)")
                self.assertEqual(first_ids, [f'mat-0-{index}' for index in range(45)])
                self.assertEqual(second_ids, [f'mat-1-{index}' for index in range(21)])
                self.assertLessEqual(page.evaluate('document.documentElement.scrollWidth'), page.evaluate('window.innerWidth') + 2)
                browser.close()
