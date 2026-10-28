"""Render and inspect the two Stage 2 historical replay reports in Chromium."""
from __future__ import annotations

import json
from pathlib import Path

from playwright.sync_api import sync_playwright


HERE = Path(__file__).resolve().parent
EVIDENCE = HERE / "evidence" / "rendered"


def verify(page, name, asset_count, group_count, expected_count, has_current):
    report = HERE / name / "generated" / "report.html"
    page.goto(report.as_uri())
    page.wait_for_load_state("load")
    result = {
        "report": str(report.relative_to(HERE)),
        "asset_images": page.locator(".asset-image").count(),
        "groups": page.locator('[data-module="gallery"]').count(),
        "sample_count": page.locator(".sample-count").inner_text(),
        "current_state_present": page.locator('[data-module="current-state"]').count() == 1,
        "current_state_default_closed": page.locator('[data-module="current-state"][open]').count() == 0,
        "methodology_default_closed": page.locator('[data-module="methodology"][open]').count() == 0,
        "card_details_default_closed": page.locator(".card-details[open]").count() == 0,
        "last_main_module": page.locator("main > [data-module]").last.get_attribute("data-module"),
        "desktop_no_horizontal_overflow": page.evaluate("document.documentElement.scrollWidth <= window.innerWidth + 2"),
    }
    assert result["asset_images"] == asset_count
    assert result["groups"] == group_count
    assert result["sample_count"] == expected_count
    assert result["current_state_present"] is has_current
    assert result["current_state_default_closed"]
    assert result["methodology_default_closed"]
    assert result["card_details_default_closed"]
    assert result["last_main_module"] == "synthesis"
    assert result["desktop_no_horizontal_overflow"]
    assert page.locator(".asset-image").first.evaluate("i => i.complete && i.naturalWidth > 0")
    page.locator(".asset-image").first.click()
    assert page.locator("dialog[open]").count() == 1
    page.keyboard.press("Escape")
    page.screenshot(path=str(EVIDENCE / f"{name}-desktop.png"), full_page=True)
    page.set_viewport_size({"width": 390, "height": 844})
    result["mobile_no_horizontal_overflow"] = page.evaluate("document.documentElement.scrollWidth <= window.innerWidth + 2")
    assert result["mobile_no_horizontal_overflow"]
    page.set_viewport_size({"width": 1440, "height": 1000})
    if has_current:
        page.locator('[data-module="current-state"] > summary').click()
        assert page.locator(".current-image").evaluate("i => i.complete && i.naturalWidth > 0")
        page.locator('[data-module="current-state"]').screenshot(path=str(EVIDENCE / f"{name}-current.png"))
    return result


def main():
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 1000})
        results = {
            "historical_replay": True,
            "new_source_collection": False,
            "reports": {
                "one-sentence-my-pages": verify(page, "one-sentence-my-pages", 26, 7, "20 个竞品 · 26 张竞品截图", False),
                "detailed-my-page-redesign": verify(page, "detailed-my-page-redesign", 10, 4, "9 个竞品 · 10 张竞品截图", True),
            },
        }
        browser.close()
    (EVIDENCE / "verification.json").write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
