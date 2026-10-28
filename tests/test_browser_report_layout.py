from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from PIL import Image
from playwright.sync_api import sync_playwright

from competitor_analysis_skill.report import render_report


class BrowserReportLayoutTests(unittest.TestCase):
    def make_report(self, root, sizes, *, long_content=False):
        root = Path(root)
        assets = root / "assets"
        assets.mkdir(parents=True)
        Image.new("RGB", (180, 360), "white").save(assets / "portrait.png")
        Image.new("RGB", (360, 140), "white").save(assets / "landscape.png")
        materials = []
        groups = []
        labels = []
        for group_index, size in enumerate(sizes):
            ids = []
            for index in range(size):
                mid = f"g{group_index}-m{index}"
                ids.append(mid)
                materials.append({
                    "id": mid,
                    "product_name": ("很长的产品名称用于检查换行与卡片边界" if long_content and not materials else f"产品 {group_index}-{index}"),
                    "page_name": "目标页", "region": "CN", "product_type": "工具", "platform": "iOS",
                    "image_path": "assets/landscape.png" if index % 2 else "assets/portrait.png",
                    "source_url": "https://example.com/" + ("very-long-segment-" * 30),
                    "semantic_status": "accepted", "quality_status": "accepted", "collection_status": "collected",
                    "semantic_reason": "语义审核说明", "quality_reason": "机械质量说明", "notes": "历史与版本说明",
                })
                labels.append({"material_id": mid, "labels": {
                    "page_role": "services_drawer", "path_stage": "personal_center_drawer_lower",
                    "interaction_stage": "drawer_open_scrolled", "render_state": "loaded_complete",
                    "login_state": "logged_in",
                }})
            groups.append({
                "id": f"group-{group_index}",
                "name": ("很长的分类名称用于验证标题不会造成横向溢出" if long_content and group_index == 0 else f"组 {group_index}"),
                "reason": "测试布局", "material_ids": ids,
            })
        task = {"target_page": "目标页", "research_goal": "布局验证"}
        classification = {"classification_status": "ready", "classification_dimension": "测试",
                          "classification_reason": "测试", "groups": groups, "material_labels": labels}
        (root / "report.html").write_text(render_report(task, materials, classification), encoding="utf-8")
        return root / "report.html"

    def test_small_groups_pack_as_units_without_dense_backfill(self):
        with TemporaryDirectory() as tmp, sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            for sizes, same_row in (((2, 2), True), ((3, 2), True), ((4, 2), False)):
                report = self.make_report(Path(tmp) / ("-".join(map(str, sizes))), sizes)
                page = browser.new_page(viewport={"width": 1440, "height": 900})
                page.goto(report.as_uri())
                groups = page.locator(".gallery-group")
                first, second = groups.nth(0).bounding_box(), groups.nth(1).bounding_box()
                if same_row:
                    self.assertAlmostEqual(first["y"], second["y"], delta=2)
                    self.assertLessEqual(first["x"] + first["width"], second["x"] + 2)
                else:
                    self.assertGreater(second["y"], first["y"] + 2)
                for group_index, size in enumerate(sizes):
                    cards = groups.nth(group_index).locator(".gallery-card:not([hidden])")
                    self.assertEqual(cards.count(), size)
                    self.assertEqual(len({round(cards.nth(i).bounding_box()["y"]) for i in range(size)}), 1)
                page.close()
            browser.close()

    def test_single_and_large_groups_keep_readable_rows(self):
        with TemporaryDirectory() as tmp, sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            for size, expected_rows in ((1, 1), (2, 1), (3, 1), (5, 1), (6, 2), (20, 4)):
                report = self.make_report(Path(tmp) / str(size), (size,))
                page = browser.new_page(viewport={"width": 1440, "height": 900})
                page.goto(report.as_uri())
                cards = page.locator(".gallery-card:not([hidden])")
                rows = {round(cards.nth(i).bounding_box()["y"]) for i in range(size)}
                self.assertEqual(len(rows), expected_rows)
                self.assertGreater(cards.nth(0).bounding_box()["width"], 190)
                page.close()
            browser.close()

    def test_long_content_ratios_details_and_keyboard_lightbox(self):
        with TemporaryDirectory() as tmp, sync_playwright() as p:
            report = self.make_report(Path(tmp), (2,), long_content=True)
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1440, "height": 900})
            page.goto(report.as_uri())
            details = page.locator(".card-details").first
            self.assertFalse(details.get_attribute("open") is not None)
            self.assertFalse(page.locator(".card-details a").first.is_visible())
            details.locator("summary").click()
            self.assertTrue(details.locator("a").first.is_visible())
            self.assertEqual(page.locator("dialog[open]").count(), 0)
            details.locator("summary").click()
            image_button = page.locator(".image-button").first
            image_button.focus()
            page.keyboard.press("Enter")
            self.assertEqual(page.locator("dialog[open]").count(), 1)
            page.keyboard.press("Escape")
            self.assertEqual(page.locator("dialog[open]").count(), 0)
            image_button.focus()
            page.keyboard.press("Enter")
            close = page.locator('button[aria-label="关闭"]')
            close.focus()
            page.keyboard.press("Enter")
            self.assertEqual(page.locator("dialog[open]").count(), 0)
            image = page.locator(".asset-image").first
            ratio = image.bounding_box()["width"] / image.bounding_box()["height"]
            self.assertAlmostEqual(ratio, 0.5, delta=0.03)
            self.assertTrue(image.evaluate("i => i.complete && i.naturalWidth === 180 && i.naturalHeight === 360"))
            for width in (1440, 1280, 390):
                page.set_viewport_size({"width": width, "height": 844})
                self.assertLessEqual(page.evaluate("document.documentElement.scrollWidth"), width + 2)
            browser.close()
