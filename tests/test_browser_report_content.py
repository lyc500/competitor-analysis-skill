import json
from pathlib import Path
import shutil
from tempfile import TemporaryDirectory
import unittest

from playwright.sync_api import sync_playwright
from competitor_analysis_skill.pipeline import run_pipeline
from competitor_analysis_skill.report_bundle import replay_report
from competitor_analysis_skill.report_content import anchor
from report_content_fixtures import analysis, inputs, claim


class BrowserReportContentTests(unittest.TestCase):
    def test_closed_sections_citations_zoom_and_portable_bundle(self):
        with TemporaryDirectory() as tmp:
            root=Path(tmp); source=root/"input"; data=inputs(source)
            (source/"analysis.json").write_text(json.dumps(analysis(True),ensure_ascii=False))
            result=run_pipeline(data["task"],root/"output",reviewed_materials_file=source/"reviewed.json",
                                classification_plan_file=source/"classification.json",analysis_file=source/"analysis.json")
            moved=root/"moved"; shutil.move(root/"output",moved)
            with sync_playwright() as p:
                browser=p.chromium.launch(headless=True)
                page=browser.new_page(viewport={"width":1440,"height":1000})
                page.goto((moved/"report.html").as_uri())
                self.assertEqual(page.locator('[data-module="current-state"][open]').count(),0)
                self.assertEqual(page.locator('[data-module="methodology"][open]').count(),0)
                self.assertEqual(page.locator('.card-details[open]').count(),0)
                self.assertEqual(page.locator('main > [data-module]').last.get_attribute('data-module'),'synthesis')
                self.assertNotIn("用户原始长需求",page.locator('header').inner_text())
                self.assertNotIn("归组审核理由",page.locator('[data-module="gallery"]').inner_text())
                page.locator('[data-module="current-state"] > summary').focus()
                page.keyboard.press('Enter')
                self.assertEqual(page.locator('[data-module="current-state"][open]').count(),1)
                self.assertTrue(page.locator('.current-image').evaluate('i=>i.complete&&i.naturalWidth>0'))
                page.locator('.current-image-button').focus()
                page.keyboard.press('Enter')
                self.assertEqual(page.locator('dialog[open]').count(),1)
                page.keyboard.press('Escape')
                page.locator('.asset-image').click()
                page.wait_for_function("document.querySelector('#viewer-image').naturalWidth>0")
                page.keyboard.press('Escape')
                page.locator('[data-module="methodology"] > summary').click()
                self.assertIn("归组审核理由",page.locator('[data-module="methodology"]').inner_text())
                for width in (1440,390):
                    page.set_viewport_size({"width":width,"height":844})
                    self.assertLessEqual(page.evaluate('document.documentElement.scrollWidth'),width+2)
                browser.close()

    def test_evidence_link_reveals_progressively_hidden_material(self):
        with TemporaryDirectory() as tmp:
            root=Path(tmp); data=inputs(root/"input")
            snapshot=data["snapshot"]
            original=snapshot["materials"][0]
            snapshot["materials"]=[{**original,"id":f"mat-{i}"} for i in range(25)]
            snapshot["classification"]["groups"][0]["material_ids"]=[m["id"] for m in snapshot["materials"]]
            snapshot["classification"]["material_labels"]=[]
            snapshot["analysis"]={"schema_version":1,"title":"渐进展开引用测试","research":{"question":"测试引用","scope":"离线夹具"},
                                  "overall":claim("overall","定位最后一张",[{"kind":"material","id":"mat-24"}])}
            path=root/"input/snapshot.json"; path.write_text(json.dumps(snapshot,ensure_ascii=False))
            replay_report(path,root/"out")
            with sync_playwright() as p:
                browser=p.chromium.launch(headless=True)
                page=browser.new_page(); page.goto((root/"out/report.html").as_uri())
                self.assertEqual(page.locator('.gallery-card:not([hidden])').count(),20)
                page.locator('header [data-evidence-target]').click()
                self.assertEqual(page.locator('.gallery-card:not([hidden])').count(),25)
                self.assertTrue(page.locator('#'+anchor('material','mat-24')).is_visible())
                browser.close()
