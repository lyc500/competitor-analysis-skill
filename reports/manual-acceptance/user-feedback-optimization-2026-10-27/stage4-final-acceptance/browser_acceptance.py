"""Real Chromium checks for the newly generated local acceptance reports."""
import json
from pathlib import Path

from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parent
CASES = {
    "scenario-a-my-pages": {"images": 9, "groups": [2, 3, 2, 1, 1], "current": False},
    "scenario-b-redesign": {"images": 6, "groups": [2, 2, 2], "current": True},
    "generic-settings-validation": {"images": 1, "groups": [1], "current": False},
}


def inspect(page, name, expected):
    report = ROOT / name / "report" / "report.html"
    page.goto(report.as_uri(), wait_until="load")
    page.wait_for_function("[...document.images].every(image => image.complete)")
    images = page.locator(".asset-image")
    assert images.count() == expected["images"]
    assert all(images.nth(i).evaluate("image => image.naturalWidth > 0 && image.naturalHeight > 0") for i in range(images.count()))
    assert page.locator('.card-details[open]').count() == 0
    assert page.locator('[data-module="methodology"][open]').count() == 0
    assert bool(page.locator('[data-module="current-state"]').count()) == expected["current"]
    if expected["current"]:
        assert page.locator('[data-module="current-state"][open]').count() == 0
    assert page.locator('main > [data-module]').last.get_attribute('data-module') == 'synthesis'
    group_sizes = [page.locator('.gallery-group').nth(i).locator('.gallery-card').count()
                   for i in range(page.locator('.gallery-group').count())]
    assert group_sizes == expected["groups"]
    desktop_boxes = [page.locator('.gallery-group').nth(i).bounding_box() for i in range(len(group_sizes))]
    desktop_scroll_width = page.evaluate('document.documentElement.scrollWidth')
    assert desktop_scroll_width <= 1442
    image_button = page.locator('.image-button').first
    image_button.focus()
    page.keyboard.press('Enter')
    assert page.locator('dialog[open]').count() == 1
    page.keyboard.press('Escape')
    assert page.locator('dialog[open]').count() == 0
    detail = page.locator('.card-details').first
    detail.locator('summary').click()
    assert detail.get_attribute('open') is not None
    assert page.locator('dialog[open]').count() == 0
    detail.locator('summary').click()
    process = page.locator('[data-module="methodology"]')
    process.locator('summary').click()
    assert '来源访问准备' in process.inner_text()
    process.locator('summary').click()
    page.screenshot(path=str(ROOT / 'browser-evidence' / f'{name}-desktop.png'), full_page=True)
    page.set_viewport_size({"width": 390, "height": 844})
    page.evaluate('window.scrollTo(0, 0)')
    assert page.evaluate('document.documentElement.scrollWidth') <= 392
    mobile_boxes = [page.locator('.gallery-group').nth(i).bounding_box() for i in range(len(group_sizes))]
    page.screenshot(path=str(ROOT / 'browser-evidence' / f'{name}-mobile.png'), full_page=True)
    return {
        "report": str(report.relative_to(ROOT)), "asset_images": images.count(), "group_sizes": group_sizes,
        "current_state_present": expected["current"], "details_default_closed": True,
        "methodology_default_closed": True, "synthesis_is_last_module": True,
        "keyboard_lightbox_open_close": True,
        "desktop": {"viewport": [1440, 1000], "scroll_width": desktop_scroll_width,
                    "group_boxes_before_mobile": desktop_boxes},
        "mobile": {"viewport": [390, 844], "scroll_width": page.evaluate('document.documentElement.scrollWidth'),
                   "group_boxes": mobile_boxes},
    }


def main():
    (ROOT / 'browser-evidence').mkdir(parents=True, exist_ok=True)
    output = {"browser": "Playwright Chromium", "evidence_type": "local_report_browser_acceptance", "cases": {}}
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        for name, expected in CASES.items():
            page = browser.new_page(viewport={"width": 1440, "height": 1000})
            output["cases"][name] = inspect(page, name, expected)
            page.close()
        browser.close()
    (ROOT / 'browser-evidence' / 'browser-validation.json').write_text(
        json.dumps(output, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f"browser cases passed: {len(CASES)}")


if __name__ == '__main__':
    main()
