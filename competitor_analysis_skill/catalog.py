"""Testable candidate providers. These are inputs to collection, not collection itself."""

SEARCH_CATALOG = [
    ("百度", "CN", "综合搜索", "百度搜索结果页", "https://www.baidu.com/s?wd=product+design"),
    ("小红书", "CN", "内容社区", "小红书搜索结果页", "https://www.xiaohongshu.com/search_result?keyword=design"),
    ("淘宝", "CN", "电商", "淘宝搜索结果页", "https://s.taobao.com/search?q=product+design"),
    ("Google", "Global", "综合搜索", "Google 搜索结果页", "https://www.google.com/search?q=product+design"),
    ("Bing", "Global", "综合搜索", "Bing 搜索结果页", "https://www.bing.com/search?q=product+design"),
    ("Amazon", "Global", "电商", "Amazon 搜索结果页", "https://www.amazon.com/s?k=product+design"),
    ("YouTube", "Global", "视频", "YouTube 搜索结果页", "https://www.youtube.com/results?search_query=product+design"),
    ("Pinterest", "Global", "灵感社区", "Pinterest 搜索结果页", "https://www.pinterest.com/search/pins/?q=product%20design"),
]


def builtin_search_candidates(regions):
    return [{"product_name": n, "region": r, "product_type": t, "reason": reason,
             "priority": "high" if n in {"Google", "百度"} else "medium", "target_url": url,
             "collection_status": "pending", "candidate_source": "builtin_candidate"}
            for n, r, t, reason, url in SEARCH_CATALOG if r in regions]

