from dataclasses import asdict, dataclass
import re


@dataclass
class ResearchTask:
    request: str
    research_goal: str
    target_page: str
    regions: list[str]
    product_scope: list[str]
    specified_products: list[str]
    platforms: list[str]
    constraints: list[str]
    collection_status: str = "planned"

    def to_dict(self):
        return asdict(self)


def parse_request(request: str) -> ResearchTask:
    target_page = "搜索结果页" if re.search(r"搜索结果|search results|search page", request, re.I) else "待确认页面"
    regions = ["CN", "Global"] if re.search(r"海内外|国内外|全球|海外", request) else ["Global"]
    products = re.findall(r"(?:产品|竞品)[：:]\s*([^。；;]+)", request)
    return ResearchTask(request, "为产品设计提供页面参考", target_page, regions, products, [], [], [], "planned")

