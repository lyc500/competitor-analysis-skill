import ipaddress
import socket
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageStat
from playwright.sync_api import Error as PlaywrightError, TimeoutError as PlaywrightTimeoutError, sync_playwright

from .quality import assess_image


def _public_host(url, allow_private_network=False):
    from urllib.parse import urlsplit
    host = urlsplit(url).hostname
    if not host:
        raise ValueError("URL 缺少 hostname")
    if allow_private_network:
        return
    try:
        addresses = {item[4][0] for item in socket.getaddrinfo(host, None)}
    except socket.gaierror as exc:
        raise ValueError(f"DNS 解析失败: {exc}") from exc
    for address in addresses:
        ip = ipaddress.ip_address(address)
        if not ip.is_global:
            raise ValueError(f"目标地址不是公网地址: {address}")


def _blank(path):
    with Image.open(path) as image:
        image.thumbnail((32, 32))
        stat = ImageStat.Stat(image.convert("RGB"))
        return max(channel[1] - channel[0] for channel in stat.extrema) <= 2


def capture_sources(sources, output_dir, timeout_ms=15000, settle_ms=750, viewport_width=1440, viewport_height=1200, allow_private_network=False):
    output_dir = Path(output_dir).resolve(); capture_dir = output_dir / "captures"; capture_dir.mkdir(parents=True, exist_ok=True)
    results = []
    with sync_playwright() as playwright:
        try:
            browser = playwright.chromium.launch(headless=True)
        except Exception as exc:
            raise RuntimeError(f"Chromium 启动失败: {exc}") from exc
        try:
            version = browser.version
            for source in sources:
                results.append(_capture_one(browser, source, capture_dir, output_dir, timeout_ms, settle_ms, viewport_width, viewport_height, allow_private_network, version))
        finally:
            browser.close()
    return results


def _capture_one(browser, source, capture_dir, output_dir, timeout_ms, settle_ms, width, height, allow_private, browser_version):
    requested = source["normalized_url"]
    base = {"id": f"cap-{source['id']}", "source_candidate_id": source["id"], "product_name": source["product_name"], "target_page": source["target_page"], "target_surface": source.get("target_surface", "user_specified"), "discovered_source_type": source["source_type"], "source_provider": source.get("source_provider", ""), "source_asset_url": source.get("source_asset_url", ""), "requested_url": requested, "final_url": "", "page_title": "", "http_status": None, "content_type": "", "browser_name": "chromium", "browser_version": browser_version, "viewport_width": width, "viewport_height": height, "captured_at": datetime.now(timezone.utc).isoformat(), "capture_status": "failed", "screenshot_path": "", "quality_status": "missing", "quality_reason": "", "width": 0, "height": 0, "content_sha256": "", "failure_reason": ""}
    try:
        _public_host(requested, allow_private)
        context = browser.new_context(viewport={"width": width, "height": height})
        def guard(route):
            from urllib.parse import urlsplit
            target = route.request.url
            if urlsplit(target).scheme in {"http", "https"}:
                try:
                    _public_host(target, allow_private)
                except ValueError:
                    route.abort()
                    return
            route.continue_()
        context.route("**/*", guard)
        page = context.new_page()
        page.set_default_timeout(timeout_ms)
        response = page.goto(requested, wait_until="domcontentloaded", timeout=timeout_ms)
        try:
            page.wait_for_load_state("networkidle", timeout=min(timeout_ms, 3000))
        except PlaywrightTimeoutError:
            pass
        if settle_ms: page.wait_for_timeout(settle_ms)
        final_url = page.url; _public_host(final_url, allow_private)
        base.update(final_url=final_url, page_title=page.title(), http_status=response.status if response else None, content_type=(response.headers.get("content-type", "") if response else ""))
        if response and response.status >= 400:
            base["failure_reason"] = f"HTTP {response.status}"
            return base
        path = capture_dir / f"{base['id']}.png"; page.screenshot(path=str(path), type="png")
        quality = assess_image(path)
        base.update(quality_status=quality.status, quality_reason=quality.reason, width=quality.width, height=quality.height, content_sha256=quality.content_sha256)
        if quality.status != "accepted":
            base["failure_reason"] = quality.reason; return base
        if _blank(path):
            base.update(capture_status="blank", failure_reason="截图近似单色空白，未获得有效渲染结果")
            return base
        base.update(capture_status="captured", screenshot_path=path.relative_to(output_dir).as_posix())
        return base
    except PlaywrightTimeoutError as exc:
        base["failure_reason"] = f"浏览器超时: {exc}"
    except (PlaywrightError, ValueError, OSError) as exc:
        base["failure_reason"] = str(exc)
    finally:
        try: context.close()
        except Exception: pass
    return base
