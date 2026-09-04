from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin
from urllib.request import Request, urlopen
import hashlib

from .quality import assess_image


class PublicSourceCollector:
    source_type = "public_web"

    def collect(self, competitor: dict, output_dir: Path) -> dict:
        return collect_candidate(competitor, output_dir, fetch=True)


class ImageMetaParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.images = []

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if tag == "meta" and values.get("property", values.get("name", "")).lower() in {"og:image", "twitter:image"}:
            if values.get("content"):
                self.images.append(values["content"])


def collect_candidate(competitor: dict, output_dir: Path, fetch: bool = True) -> dict:
    base = {"id": competitor["product_name"].lower().replace(" ", "-") + "-search-01",
            "product_name": competitor["product_name"], "page_name": competitor["reason"],
            "region": competitor["region"], "product_type": competitor["product_type"],
            "platform": "Web", "source_type": "public_web", "source_url": competitor["target_url"],
            "captured_at": "", "notes": "", "quality_status": "missing", "collection_status": "needs_manual_capture",
            "provenance": "online" if fetch else "builtin_candidate", "collection_method": "web_candidate",
            "semantic_status": "pending", "semantic_reason": "网页元数据候选，待语义确认", "quality_reason": "", "observed_structure": [], "observed_patterns": [], "image_path": "", "failure_reason": ""}
    if not fetch:
        base["notes"] = "内置候选离线结构验证，非真实在线采集"
        base["failure_reason"] = "offline_test"
        return base
    try:
        request = Request(competitor["target_url"], headers={"User-Agent": "Mozilla/5.0 competitor-analysis-skill/0.1"})
        with urlopen(request, timeout=12) as response:
            content_type = response.headers.get("Content-Type", "")
            body = response.read(2_000_000)
        image_url = competitor["target_url"] if content_type.startswith("image/") else _find_image(body, competitor["target_url"])
        if not image_url:
            raise ValueError("公开页面未提供可下载的页面图片")
        with urlopen(Request(image_url, headers={"User-Agent": "Mozilla/5.0 competitor-analysis-skill/0.1"}), timeout=12) as response:
            image = response.read(15_000_000)
        suffix = ".jpg" if "jpeg" in content_type.lower() or image_url.lower().split("?")[0].endswith((".jpg", ".jpeg")) else ".png"
        filename = hashlib.sha1(competitor["product_name"].encode()).hexdigest()[:10] + suffix
        path = output_dir / "assets" / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(image)
        quality = assess_image(path)
        if quality.status == "rejected":
            path.unlink(missing_ok=True)
            raise ValueError(quality.reason)
        base.update(image_path=str(path.relative_to(output_dir)), quality_status="accepted", quality_reason=quality.reason, collection_status="pending", notes="公开页面图片候选", provenance="online", content_sha256=quality.content_sha256, width=quality.width, height=quality.height, decode_format=quality.format)
    except Exception as exc:
        base["failure_reason"] = str(exc)
    return base


def _find_image(body: bytes, page_url: str):
    parser = ImageMetaParser()
    parser.feed(body.decode("utf-8", errors="ignore"))
    return urljoin(page_url, parser.images[0]) if parser.images else None
