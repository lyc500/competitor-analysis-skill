from html import escape
from urllib.parse import urlsplit
from .report_content import anchor, content_parts, source_tables

PAGE_SIZE = 20


def _collected(task, assets):
    target_surface = task.get("target_surface", "user_specified")
    result = []
    for material in assets:
        valid = (
            material.get("collection_status") == "collected"
            and material.get("semantic_status") == "accepted"
            and material.get("quality_status") == "accepted"
            and isinstance(material.get("image_path"), str)
            and material["image_path"].strip()
        )
        if target_surface == "mobile_app":
            platform = material.get("platform", "").casefold()
            valid = valid and (
                material.get("target_surface") == "mobile_app"
                and material.get("target_surface_match") == "matched"
                and ("ios" in platform or "android" in platform)
                and "web" not in platform
            )
        if valid:
            result.append(material)
    return result


def _visible_badges(material, material_labels):
    badges = []

    def add(text, critical=False):
        if text and not any(item[0] == text for item in badges):
            badges.append((text, critical))

    add(str(material.get("platform", "")).strip())
    add(str(material.get("region", "")).strip())
    login = material_labels.get("login_state")
    if login == "logged_out":
        add("未登录", True)
    elif login == "guest":
        add("访客", True)
    interaction = material_labels.get("interaction_stage", "")
    path = material_labels.get("path_stage", "")
    role = material_labels.get("page_role", "")
    if "drawer" in interaction or "drawer" in path or role == "services_drawer":
        add("抽屉", True)
    if "scroll" in interaction or "scrolled" in path or path.endswith("_lower") or role.endswith("_lower"):
        add("下段", True)
    if "subtab" in interaction or "_tab" in path:
        add("子页", True)
    if role == "own_profile":
        add("本人主页", True)
    render_state = material_labels.get("render_state", "")
    if render_state and render_state != "loaded_complete":
        add("加载状态受限", True)
    if material_labels.get("version_status") in ("historical", "historical_version"):
        add("历史版本", True)
    if material_labels.get("annotation_status") in ("annotated", "original_annotated"):
        add("原图带标注", True)
    caveats = material.get("display_caveats", [])
    if isinstance(caveats, list):
        for caveat in caveats:
            if isinstance(caveat, str):
                add(caveat.strip(), True)
    return badges


def _link(value):
    text = str(value or "")
    try:
        safe = urlsplit(text).scheme in ("http", "https")
    except ValueError:
        safe = False
    shown = escape(text)
    return f'<a href="{escape(text, quote=True)}" target="_blank" rel="noopener noreferrer">{shown}</a>' if safe else shown

def render_report(task, assets, classification, fallback_requests=None, evidence_statistics=None, analysis=None, generation=None, source_evidence=None):
    assets = _collected(task, assets); by_id = {m["id"]: m for m in assets}
    parts = content_parts(task, assets, classification, analysis, generation or {})
    labels = {x["material_id"]: x.get("labels", {}) for x in classification.get("material_labels", [])}
    sections = []
    for group_index, group in enumerate(classification.get("groups", [])):
        cards = []
        for mid in group.get("material_ids", group.get("asset_ids", [])):
            m = by_id.get(mid)
            if not m: continue
            material_labels = labels.get(mid, {})
            label_html = " ".join(f'<span class="label">{escape(str(k))}: {escape(str(v))}</span>' for k, v in material_labels.items())
            badges = "".join(
                f'<span class="status-chip{" critical" if critical else ""}">{escape(text)}</span>'
                for text, critical in _visible_badges(m, material_labels)
            )
            evidence_refs = []
            for key, label in (("id", "material"), ("capture_id", "capture"), ("source_candidate_id", "candidate"), ("source_attempt_id", "attempt")):
                if m.get(key):
                    evidence_refs.append(f'{label}: {escape(str(m[key]))}')
            evidence_html = f'<p class="evidence-ref">证据链：{" · ".join(evidence_refs)}</p>' if evidence_refs else ""
            index = len(cards)
            hidden = " hidden" if index >= PAGE_SIZE else ""
            review_html = "".join(
                f'<p><strong>{label}：</strong>{escape(str(m[field]))}</p>'
                for field, label in (("semantic_reason", "语义审核"), ("quality_reason", "机械质量"),
                                     ("notes", "素材说明")) if m.get(field)
            )
            source_meta = " · ".join(str(m.get(field, "")) for field in
                                     ("source_type", "source_provider", "collection_method") if m.get(field))
            source_meta_html = f'<p><strong>来源类型：</strong>{escape(source_meta)}</p>' if source_meta else ""
            dates = "".join(
                f'<p><strong>{label}：</strong>{escape(str(m[field]))}</p>'
                for field, label in (("version", "版本"), ("app_version", "版本"),
                                     ("source_date", "来源日期"), ("captured_at", "采集日期"))
                if m.get(field)
            )
            urls = "".join(
                f'<p><strong>{label}：</strong>{_link(m[field])}</p>'
                for field, label in (("source_url", "来源页面"), ("source_asset_url", "原图资源"))
                if m.get(field)
            )
            page_meta = "".join(
                f'<p><strong>{label}：</strong>{escape(str(m[field]))}</p>'
                for field, label in (("page_name", "页面"), ("product_type", "产品类型")) if m.get(field)
            )
            detail = (f'{parts["material_details"].get(mid, "")}{page_meta}<div class="labels">{label_html}</div>'
                      f'{review_html}{evidence_html}{source_meta_html}{dates}{urls}')
            image_alt = f'{m["product_name"]} {m.get("page_name", "")}'.strip()
            cards.append(
                f'<article class="gallery-card" id="{anchor("material", mid)}" data-index="{index}"{hidden} '
                f'data-material-id="{escape(str(m.get("id", "")))}" data-capture-id="{escape(str(m.get("capture_id", "")))}" '
                f'data-source-candidate-id="{escape(str(m.get("source_candidate_id", "")))}" '
                f'data-source-attempt-id="{escape(str(m.get("source_attempt_id", "")))}">'
                f'<div class="meta"><strong>{escape(m["product_name"])}</strong></div>'
                f'<div class="card-badges">{badges}</div>'
                f'<button class="image-button" type="button" aria-label="放大查看 {escape(image_alt)}" '
                f'onclick="showModal(this.querySelector(\'img\'))"><img class="asset-image" '
                f'src="{escape(m["image_path"], quote=True)}" alt="{escape(image_alt)}"></button>'
                f'{parts["materials"].get(mid, "")}<details class="card-details"><summary>页面详情</summary>{detail}</details>'
                f'</article>'
            )
        gallery_id = f"gallery-{group_index}"
        more = ""
        if len(cards) > PAGE_SIZE:
            more = f'<div class="more-wrap"><button class="more-button" type="button" data-more-for="{gallery_id}">更多</button></div>'
        if not cards:
            continue
        gid = group.get("id", group["name"])
        layout_size = min(len(cards), 5)
        sections.append(f'<section class="gallery-group" data-module="gallery" data-layout-size="{layout_size}" data-group-order="{group_index}" id="{anchor("group", gid)}"><div class="gallery-group-header"><h2>{escape(group["name"])}</h2>{parts["groups"].get(gid, "")}</div><div id="{gallery_id}" class="grid" data-gallery data-page-size="{PAGE_SIZE}">{"".join(cards)}</div>{more}</section>')
    open_items = [x for x in (fallback_requests or []) if x.get("status") == "open"]
    fallback_html = "" if not open_items else '<section class="fallback"><h2>待补充素材</h2><ul>' + ''.join(f'<li><strong>{escape(x.get("product_name", ""))}</strong>：{escape(x.get("reason", ""))}（{escape(", ".join(x.get("allowed_methods", [])))}）</li>' for x in open_items) + '</ul></section>'
    empty = "" if assets else '<section class="unavailable"><h2>unavailable</h2><p>当前没有通过语义审核和机械质量校验的有效页面素材。</p></section>'
    stats = evidence_statistics or {}
    sources_stats = stats.get("sources", {})
    candidate_stats = stats.get("candidates", {})
    review_stats = stats.get("semantic_reviews", {})
    material_stats = stats.get("materials", {})
    fallback_stats = stats.get("fallback", {})
    coverage_stats = stats.get("coverage", {})
    access_status = sources_stats.get("access_status", {})
    access_summary = " · ".join(f"{status} {access_status.get(status, 0)}" for status in ("accessible", "login_required", "paywall", "empty", "error", "blocked", "unknown"))
    stats_html = "" if not evidence_statistics else f'''<section class="evidence-stats"><h2>证据与覆盖统计</h2><div class="stat-grid"><div><strong>来源访问</strong><p>尝试 {sources_stats.get("attempted", 0)} · {access_summary} · unknown_access {sources_stats.get("unknown_access", 0)}</p></div><div><strong>候选处置</strong><p>accepted {candidate_stats.get("accepted", 0)} · rejected {candidate_stats.get("rejected", 0)} · not_reviewed {candidate_stats.get("not_reviewed", 0)}</p></div><div><strong>素材审核</strong><p>accepted {review_stats.get("accepted", 0)} · rejected {review_stats.get("rejected", 0)} · 未审核 {review_stats.get("not_reviewed", 0)}</p></div><div><strong>素材流水线</strong><p>collected {material_stats.get("collected", 0)} · rejected {material_stats.get("rejected", 0)} · pending {material_stats.get("pending", 0)}</p></div><div><strong>产品 fallback</strong><p>resolved {fallback_stats.get("resolved", 0)} · open {fallback_stats.get("open", 0)}</p></div><div><strong>产品覆盖缺口</strong><p>无有效素材 {coverage_stats.get("products_without_collected_material", 0)} · 待审核候选 {coverage_stats.get("pending_candidate_count", 0)} · 来源边界未知 {coverage_stats.get("source_access_boundary_count", 0)}</p></div></div></section>'''
    coverage_bits = []
    without_material = coverage_stats.get("products_without_collected_material", 0)
    unknown_boundary = coverage_stats.get("source_access_boundary_count", 0)
    if without_material:
        coverage_bits.append(f"{without_material} 个产品没有有效截图")
    if unknown_boundary:
        coverage_bits.append(f"{unknown_boundary} 个来源的可见范围仍不确定")
    if open_items:
        coverage_bits.append(f"{len(open_items)} 个产品仍待补充素材")
    coverage_alert = (f'<p class="coverage-alert">覆盖限制：{"；".join(coverage_bits)}。完整记录见“来源与筛选说明”。</p>'
                      if coverage_bits else "")
    analysis_coverage = (analysis or {}).get("coverage_assessment", {})
    if analysis_coverage.get("status") in ("limited", "insufficient"):
        prefix = "小样本方向参考" if analysis_coverage["status"] == "limited" else "样本不足"
        coverage_alert = f'<p class="coverage-alert"><strong>{prefix}：</strong>{escape(analysis_coverage["summary"])}。完整缺口见“来源与筛选说明”。</p>'
    css = '''*{box-sizing:border-box}body{margin:0;background:#f6f7f9;color:#17212b;font:15px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}main{max-width:1280px;margin:auto;padding:40px 24px}header{border-bottom:1px solid #dce1e7;padding-bottom:22px;margin-bottom:28px}h1{font-size:30px;margin:0 0 8px}h2{font-size:21px;line-height:1.3;margin:0;overflow-wrap:anywhere}.reason{color:#64707d;margin:4px 0 16px}section{margin:30px 0}.gallery-layout{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:36px 16px;align-items:start;margin:30px 0}.gallery-group{min-width:0;grid-column:span 5;margin:0;padding-top:14px;border-top:2px solid #dce1e7}.gallery-group[data-layout-size="1"]{grid-column:span 1}.gallery-group[data-layout-size="2"]{grid-column:span 2}.gallery-group[data-layout-size="3"]{grid-column:span 3}.gallery-group[data-layout-size="4"]{grid-column:span 4}.gallery-group[data-layout-size="5"]{grid-column:span 5}.gallery-group-header{min-width:0;margin-bottom:14px}.gallery-group-header .analysis-claim{margin:6px 0}.evidence-stats{padding:22px;background:#fff;border:1px solid #e0e5eb;border-radius:8px}.stat-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px;margin-top:14px}.stat-grid>div{padding:12px;background:#f6f7f9;border-radius:6px}.stat-grid p{margin:4px 0 0;color:#64707d;font-size:13px}.grid{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));justify-content:start;align-items:start;gap:16px}.gallery-group[data-layout-size="1"] .grid{grid-template-columns:minmax(0,1fr)}.gallery-group[data-layout-size="2"] .grid{grid-template-columns:repeat(2,minmax(0,1fr))}.gallery-group[data-layout-size="3"] .grid{grid-template-columns:repeat(3,minmax(0,1fr))}.gallery-group[data-layout-size="4"] .grid{grid-template-columns:repeat(4,minmax(0,1fr))}.gallery-card{width:100%;min-width:0;background:#fff;border:1px solid #e0e5eb;border-radius:8px;padding:12px}.gallery-card[hidden]{display:none}.meta{min-width:0;margin-bottom:7px}.meta strong{display:block;overflow-wrap:anywhere}.card-badges{display:flex;flex-wrap:wrap;gap:5px;margin:0 0 10px}.status-chip{display:inline-block;padding:2px 6px;border-radius:999px;background:#edf3f7;color:#4d5c68;font-size:11px;line-height:1.45}.status-chip.critical{background:#f5efe2;color:#6b5427}.image-button{display:block;width:100%;min-height:40px;margin:0;padding:0;border:0;border-radius:4px;background:#edf0f3;cursor:zoom-in}.image-button:focus-visible,.more-button:focus-visible,summary:focus-visible,dialog>button:focus-visible{outline:3px solid #4d88a3;outline-offset:2px}.asset-image{display:block;width:auto;max-width:100%;height:auto;max-height:720px;object-fit:contain;margin:0 auto;background:#edf0f3;border-radius:4px}.gallery-card p{color:#64707d;font-size:12px;overflow-wrap:anywhere}.gallery-card .card-focus{margin:10px 0 4px}.gallery-card .card-focus .claim-statement{color:#394956;font-weight:600}.gallery-card .card-recommendation{margin:5px 0;color:#52616d}.card-details{border-top:1px solid #e7eaee;padding-top:9px}.card-details p,.card-details a{overflow-wrap:anywhere;word-break:break-word}.evidence-ref{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;color:#64707d;font-size:11px}.label{display:inline-block;margin:8px 4px 0 0;padding:2px 6px;background:#edf3f7;border-radius:4px;font-size:12px}.unavailable,.fallback{padding:22px;background:#fff;border:1px solid #e0e5eb;border-radius:8px}.coverage-alert{padding:10px 12px;border-left:3px solid #a58136;background:#f7f2e8;color:#66542f;font-size:13px}.more-wrap{display:flex;justify-content:center;margin-top:16px}.more-button{border:1px solid #c7d0d9;border-radius:999px;background:#fff;color:#17212b;padding:8px 20px;font-size:14px;cursor:pointer}.more-button:hover{background:#edf3f7}dialog{border:0;border-radius:8px;padding:0;max-width:95vw;max-height:95vh;background:#111}dialog::backdrop{background:#000b}dialog img{max-width:92vw;max-height:90vh;display:block}dialog>button{position:absolute;right:10px;top:10px;border:0;border-radius:50%;width:34px;height:34px;font-size:22px;cursor:pointer}
@media(max-width:1100px){.gallery-layout{grid-template-columns:repeat(4,minmax(0,1fr))}.gallery-group[data-layout-size="5"]{grid-column:span 4}.gallery-group[data-layout-size="5"] .grid{grid-template-columns:repeat(4,minmax(0,1fr))}}
@media(max-width:900px){.gallery-layout{grid-template-columns:repeat(3,minmax(0,1fr))}.gallery-group[data-layout-size="4"],.gallery-group[data-layout-size="5"]{grid-column:span 3}.gallery-group[data-layout-size="4"] .grid,.gallery-group[data-layout-size="5"] .grid{grid-template-columns:repeat(3,minmax(0,1fr))}.stat-grid{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media(max-width:700px){.gallery-layout{grid-template-columns:repeat(2,minmax(0,1fr))}.gallery-group[data-layout-size="3"],.gallery-group[data-layout-size="4"],.gallery-group[data-layout-size="5"]{grid-column:span 2}.gallery-group[data-layout-size="3"] .grid,.gallery-group[data-layout-size="4"] .grid,.gallery-group[data-layout-size="5"] .grid{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media(max-width:600px){main{padding:24px 14px}.gallery-layout{grid-template-columns:minmax(0,1fr);gap:30px}.gallery-group{grid-column:span 1!important}.gallery-group .grid{grid-template-columns:minmax(0,1fr)!important}.stat-grid{grid-template-columns:minmax(0,1fr)}.asset-image{max-height:none}}'''
    script = """function showModal(image){const viewer=document.getElementById('viewer');document.getElementById('viewer-image').src=image.src;document.getElementById('viewer-image').alt=image.alt;viewer.showModal()}
const PAGE_SIZE=20;
function initGalleries(){document.querySelectorAll('[data-gallery]').forEach(gallery=>{const cards=[...gallery.querySelectorAll('.gallery-card')];const button=document.querySelector(`[data-more-for=\"${gallery.id}\"]`);let visible=Math.min(PAGE_SIZE,cards.length);const apply=()=>{cards.forEach((card,index)=>{card.hidden=index>=visible});if(button)button.hidden=visible>=cards.length};apply();if(button)button.addEventListener('click',()=>{visible=Math.min(visible+PAGE_SIZE,cards.length);apply()})})}
document.addEventListener('DOMContentLoaded',initGalleries);
document.addEventListener('click',event=>{const link=event.target.closest('[data-evidence-target]');if(!link)return;const target=document.getElementById(link.dataset.evidenceTarget);if(!target)return;const gallery=target.closest('[data-gallery]');if(gallery){const button=document.querySelector(`[data-more-for="${gallery.id}"]`);while(target.hidden&&button&&!button.hidden)button.click()}let parent=target;while(parent){if(parent.tagName==='DETAILS')parent.open=true;parent=parent.parentElement}});"""
    css += 'nav[data-module]{display:flex;flex-wrap:wrap;gap:10px;margin:20px 0}nav a{padding:6px 10px;border:1px solid #dce1e7;border-radius:4px}a{color:#235c75;overflow-wrap:anywhere}.analysis-claim{margin:12px 0;overflow-wrap:anywhere}.claim-statement{font-weight:600;margin:6px 0}.claim-evidence,.sample-count{font-size:12px;color:#64707d}.report-notice,.information-gap{font-size:13px;color:#65562d}details{margin:16px 0}summary{cursor:pointer;font-weight:600}.current-image-button{display:block;max-width:100%;padding:0;border:0;background:transparent;cursor:zoom-in}.current-image-button:focus-visible{outline:3px solid #4d88a3;outline-offset:2px}.current-image{display:block;max-width:100%;width:auto;height:auto;max-height:560px;object-fit:contain}figure{margin:16px 0}details[data-module]{padding:16px;border:1px solid #dce1e7;border-radius:6px}.gallery-card .analysis-claim p{font-size:13px}h3{font-size:17px}section,article,details{scroll-margin-top:16px}'
    process = parts["methodology"] + stats_html + source_tables(source_evidence) + fallback_html
    methodology = f'<details data-module="methodology"><summary>来源与筛选说明</summary>{process}</details>' if process else ''
    galleries = f'<div class="gallery-layout">{"".join(sections)}</div>' if sections else ""
    return f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{escape(parts["title"])}</title><style>{css}</style></head><body><main>{parts["overview"]}{parts["navigation"]}{parts["current"]}{empty}{galleries}{coverage_alert}{methodology}{parts["synthesis"]}</main><dialog id="viewer" onclick="if(event.target===this)this.close()"><button aria-label="关闭" onclick="this.closest('dialog').close()">×</button><img id="viewer-image" alt=""></dialog><script>{script}</script></body></html>'''
