"""Browser check for reports regenerated during the second remediation."""

import json
from datetime import datetime, timezone
from pathlib import Path

from playwright.sync_api import sync_playwright


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
CASES = {
    "scenario-a-my-pages": {
        "images": 9,
        "groups": [2, 3, 2, 1, 1],
        "current": False,
        "required": [
            "账户切换、Settings 和 Help 构成简短管理列表",
            "根层关系待验证",
            "Airbuds 可看身份与个人内容表达",
        ],
        "forbidden": ["账户切换、安全", "帮助和退出", "关系资料可看 Duolingo 与 Airbuds"],
    },
    "scenario-b-redesign": {
        "images": 6,
        "groups": [2, 2, 2],
        "current": True,
        "required": ["金币商城与任务中心入口卡先于通用列表；登录后内容尚未展示"],
        "forbidden": ["任务对象清楚"],
    },
}


def inspect(page, name, expected):
    report = ROOT / name / "report" / "report.html"
    page.goto(report.as_uri(), wait_until="load")
    page.wait_for_function("[...document.images].every(image => image.complete)")
    images = page.locator(".asset-image")
    assert images.count() == expected["images"]
    assert all(images.nth(i).evaluate("image => image.naturalWidth > 0") for i in range(images.count()))
    assert page.locator(".card-details[open]").count() == 0
    assert page.locator('[data-module="methodology"][open]').count() == 0
    assert bool(page.locator('[data-module="current-state"]').count()) == expected["current"]
    if expected["current"]:
        assert page.locator('[data-module="current-state"][open]').count() == 0
    assert page.locator("main > [data-module]").last.get_attribute("data-module") == "synthesis"

    sizes = [
        page.locator(".gallery-group").nth(i).locator(".gallery-card").count()
        for i in range(page.locator(".gallery-group").count())
    ]
    assert sizes == expected["groups"]
    boxes = [page.locator(".gallery-group").nth(i).bounding_box() for i in range(len(sizes))]
    assert abs(boxes[0]["y"] - boxes[1]["y"]) <= 2

    detail = page.locator(".card-details").first
    detail.locator("summary").click()
    assert detail.get_attribute("open") is not None
    assert page.locator("dialog[open]").count() == 0
    detail.locator("summary").click()

    page.locator(".image-button").first.focus()
    page.keyboard.press("Enter")
    assert page.locator("dialog[open]").count() == 1
    page.keyboard.press("Escape")
    assert page.locator("dialog[open]").count() == 0

    methodology = page.locator('[data-module="methodology"]')
    methodology.locator("summary").click()
    audit_text = methodology.inner_text()
    for phrase in expected["required"]:
        assert phrase in audit_text or phrase in page.locator("body").inner_text()
    for phrase in expected["forbidden"]:
        assert phrase not in page.locator("body").inner_text()
    methodology.locator("summary").click()

    desktop_width = page.evaluate("document.documentElement.scrollWidth")
    assert desktop_width <= 1442
    page.screenshot(path=str(HERE / f"{name}-desktop.png"), full_page=True)

    page.set_viewport_size({"width": 390, "height": 844})
    page.evaluate("window.scrollTo(0, 0)")
    mobile_width = page.evaluate("document.documentElement.scrollWidth")
    assert mobile_width <= 392
    mobile_boxes = [page.locator(".gallery-group").nth(i).bounding_box() for i in range(len(sizes))]
    assert all(mobile_boxes[i + 1]["y"] > mobile_boxes[i]["y"] for i in range(len(sizes) - 1))
    page.screenshot(path=str(HERE / f"{name}-mobile.png"), full_page=True)
    return {
        "report": str(report.relative_to(ROOT)),
        "asset_images": images.count(),
        "group_sizes": sizes,
        "details_default_closed": True,
        "methodology_default_closed": True,
        "current_state_present": expected["current"],
        "synthesis_is_last_module": True,
        "keyboard_lightbox": True,
        "corrected_content_in_body_and_folded_audit": True,
        "desktop_scroll_width": desktop_width,
        "mobile_scroll_width": mobile_width,
    }


def main():
    output = {
        "checked_at": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "browser": "Playwright Chromium",
        "evidence_type": "second_remediation_local_report_browser_check",
        "cases": {},
    }
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        for name, expected in CASES.items():
            page = browser.new_page(viewport={"width": 1440, "height": 1000})
            output["cases"][name] = inspect(page, name, expected)
            page.close()
        browser.close()
    (HERE / "browser-validation.json").write_text(
        json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"browser cases passed: {len(CASES)}")


if __name__ == "__main__":
    main()
