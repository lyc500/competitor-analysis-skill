"""Inspect Stage 3 historical replay reports with behavioral geometry checks."""
from __future__ import annotations

import json
import hashlib
from pathlib import Path

from playwright.sync_api import sync_playwright


HERE = Path(__file__).resolve().parent
EVIDENCE = HERE / "evidence" / "rendered"


def box(locator):
    value = locator.bounding_box()
    assert value
    return value


def same_row(left, right):
    a, b = box(left), box(right)
    return abs(a["y"] - b["y"]) <= 2 and a["x"] + a["width"] <= b["x"] + 2


def verify_common(page, scenario, asset_count, group_count, sample_count, has_current):
    report = HERE / scenario / "generated" / "report.html"
    page.goto(report.as_uri())
    page.wait_for_load_state("load")
    result = {
        "report": str(report.relative_to(HERE)),
        "asset_images": page.locator(".asset-image").count(),
        "groups": page.locator(".gallery-group").count(),
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
    assert result["sample_count"] == sample_count
    assert result["current_state_present"] is has_current
    assert result["current_state_default_closed"]
    assert result["methodology_default_closed"]
    assert result["card_details_default_closed"]
    assert result["last_main_module"] == "synthesis"
    assert result["desktop_no_horizontal_overflow"]
    assert page.locator(".asset-image").first.evaluate("i => i.complete && i.naturalWidth > 0")
    detail = page.locator(".card-details").first
    detail.locator("summary").click()
    assert page.locator("dialog[open]").count() == 0
    assert detail.locator(".evidence-ref").is_visible()
    detail.locator("summary").click()
    image_button = page.locator(".image-button").first
    image_button.focus()
    page.keyboard.press("Enter")
    assert page.locator("dialog[open]").count() == 1
    assert page.locator("#viewer-image").evaluate("i => i.complete && i.naturalWidth > 0")
    page.keyboard.press("Escape")
    page.set_viewport_size({"width": 390, "height": 844})
    result["mobile_no_horizontal_overflow"] = page.evaluate("document.documentElement.scrollWidth <= window.innerWidth + 2")
    assert result["mobile_no_horizontal_overflow"]
    page.screenshot(path=str(EVIDENCE / f"{scenario}-mobile.png"), full_page=False)
    page.set_viewport_size({"width": 1440, "height": 1000})
    page.screenshot(path=str(EVIDENCE / f"{scenario}-desktop.png"), full_page=True)
    return result


def main():
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 1000})
        one = verify_common(page, "one-sentence-my-pages", 26, 7, "20 个竞品 · 26 张竞品截图", False)
        groups = page.locator(".gallery-group")
        assert same_row(groups.nth(1), groups.nth(2))
        assert same_row(groups.nth(5), groups.nth(6))
        assert box(groups.nth(4))["y"] > box(groups.nth(3))["y"]
        one["desktop_small_group_rows"] = ["2+2", "1+1"]
        one["large_group_starts_new_row_after_two"] = True

        detailed = verify_common(page, "detailed-my-page-redesign", 10, 4, "9 个竞品 · 10 张竞品截图", True)
        groups = page.locator(".gallery-group")
        assert same_row(groups.nth(1), groups.nth(2)) and same_row(groups.nth(2), groups.nth(3))
        detailed["desktop_small_group_row"] = "2+1+2"
        visible_text = page.locator("main").inner_text()
        assert "原图带标注" in visible_text and "历史版本" in visible_text and "抽屉" in visible_text
        detailed["critical_visible_flags"] = ["原图带标注", "历史版本", "抽屉", "下段"]
        page.locator('[data-module="current-state"] > summary').click()
        assert page.locator(".current-image").evaluate("i => i.complete && i.naturalWidth > 0")
        page.locator('[data-module="current-state"]').screenshot(path=str(EVIDENCE / "detailed-current-expanded.png"))
        browser.close()
    unchanged = {}
    stage2 = HERE.parent / "stage2-analysis-replay"
    for scenario in ("one-sentence-my-pages", "detailed-my-page-redesign"):
        before = json.loads((stage2 / scenario / "generated" / "report_data.json").read_text(encoding="utf-8"))
        after = json.loads((HERE / scenario / "generated" / "report_data.json").read_text(encoding="utf-8"))
        assert before["analysis"] == after["analysis"]
        for field in ("classification_dimension", "classification_reason", "comparison_basis", "groups"):
            assert before["classification"].get(field) == after["classification"].get(field)
        before_assets = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                         for p in (stage2 / scenario / "generated" / "assets").iterdir() if p.is_file()}
        after_assets = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                        for p in (HERE / scenario / "generated" / "assets").iterdir() if p.is_file()}
        assert before_assets == after_assets
        unchanged[scenario] = {"analysis_equal": True, "groups_equal": True,
                               "asset_files_equal": True, "asset_count": len(after_assets)}
    result = {
        "historical_replay": True,
        "new_source_collection": False,
        "analysis_and_group_membership_unchanged_from_stage2": True,
        "stage2_comparison": unchanged,
        "reports": {"one-sentence-my-pages": one, "detailed-my-page-redesign": detailed},
    }
    (EVIDENCE / "verification.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
