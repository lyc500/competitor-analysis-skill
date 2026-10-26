from html import escape

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

def render_report(task, assets, classification, fallback_requests=None, evidence_statistics=None):
    assets = _collected(task, assets); by_id = {m["id"]: m for m in assets}
    labels = {x["material_id"]: x.get("labels", {}) for x in classification.get("material_labels", [])}
    sections = []
    for group_index, group in enumerate(classification.get("groups", [])):
        cards = []
        for mid in group.get("material_ids", group.get("asset_ids", [])):
            m = by_id.get(mid)
            if not m: continue
            meta = " · ".join(str(m.get(k, "")) for k in ("region", "product_type", "platform"))
            label_html = " ".join(f'<span class="label">{escape(str(k))}: {escape(str(v))}</span>' for k, v in labels.get(mid, {}).items())
            evidence_refs = []
            for key, label in (("id", "material"), ("capture_id", "capture"), ("source_candidate_id", "candidate"), ("source_attempt_id", "attempt")):
                if m.get(key):
                    evidence_refs.append(f'{label}: {escape(str(m[key]))}')
            evidence_html = f'<p class="evidence-ref">证据链：{" · ".join(evidence_refs)}</p>' if evidence_refs else ""
            index = len(cards)
            hidden = " hidden" if index >= PAGE_SIZE else ""
            cards.append(f'<article class="gallery-card" data-index="{index}"{hidden} data-material-id="{escape(str(m.get("id", "")))}" data-capture-id="{escape(str(m.get("capture_id", "")))}" data-source-candidate-id="{escape(str(m.get("source_candidate_id", "")))}" data-source-attempt-id="{escape(str(m.get("source_attempt_id", "")))}"><div class="meta"><strong>{escape(m["product_name"])}</strong><span>{escape(meta)}</span></div><img class="asset-image" src="{escape(m["image_path"])}" alt="{escape(m["product_name"])} {escape(m["page_name"])}" onclick="showModal(this)"><div class="labels">{label_html}</div>{evidence_html}<p>{escape(m.get("source_url", ""))}</p></article>')
        gallery_id = f"gallery-{group_index}"
        more = ""
        if len(cards) > PAGE_SIZE:
            more = f'<div class="more-wrap"><button class="more-button" type="button" data-more-for="{gallery_id}">更多</button></div>'
        sections.append(f'<section><h2>{escape(group["name"])}</h2><p class="reason">{escape(group["reason"])}</p><div id="{gallery_id}" class="grid" data-gallery data-page-size="{PAGE_SIZE}">{"".join(cards)}</div>{more}</section>')
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
    css = '*{box-sizing:border-box}body{margin:0;background:#f6f7f9;color:#17212b;font:15px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}main{max-width:1280px;margin:auto;padding:40px 24px}header{border-bottom:1px solid #dce1e7;padding-bottom:22px;margin-bottom:28px}h1{font-size:30px;margin:0 0 8px}h2{font-size:21px;margin:0}.reason{color:#64707d;margin:4px 0 16px}section{margin:30px 0}.evidence-stats{padding:22px;background:#fff;border:1px solid #e0e5eb;border-radius:8px}.stat-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px;margin-top:14px}.stat-grid>div{padding:12px;background:#f6f7f9;border-radius:6px}.stat-grid p{margin:4px 0 0;color:#64707d;font-size:13px}.grid{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));justify-content:start;align-items:start;gap:16px}.gallery-card{width:100%;min-width:0;background:#fff;border:1px solid #e0e5eb;border-radius:8px;padding:12px}.gallery-card[hidden]{display:none}.meta{display:flex;justify-content:space-between;gap:8px;margin-bottom:10px}.meta span{font-size:12px;color:#64707d}.asset-image{display:block;width:auto;max-width:100%;height:auto;max-height:720px;object-fit:contain;margin:0 auto;background:#edf0f3;border-radius:4px;cursor:zoom-in}.gallery-card p{color:#64707d;font-size:12px;overflow-wrap:anywhere}.evidence-ref{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;color:#64707d;font-size:11px}.label{display:inline-block;margin:8px 4px 0 0;padding:2px 6px;background:#edf3f7;border-radius:4px;font-size:12px}.unavailable,.fallback{padding:22px;background:#fff;border:1px solid #e0e5eb;border-radius:8px}.more-wrap{display:flex;justify-content:center;margin-top:16px}.more-button{border:1px solid #c7d0d9;border-radius:999px;background:#fff;color:#17212b;padding:8px 20px;font-size:14px;cursor:pointer}.more-button:hover{background:#edf3f7}dialog{border:0;border-radius:8px;padding:0;max-width:95vw;max-height:95vh;background:#111}dialog::backdrop{background:#000b}dialog img{max-width:92vw;max-height:90vh;display:block}dialog>button{position:absolute;right:10px;top:10px;border:0;border-radius:50%;width:34px;height:34px;font-size:22px;cursor:pointer}@media(max-width:1100px){.grid{grid-template-columns:repeat(4,minmax(0,1fr))}}@media(max-width:900px){.grid{grid-template-columns:repeat(3,minmax(0,1fr))}.stat-grid{grid-template-columns:repeat(2,minmax(0,1fr))}}@media(max-width:700px){.grid{grid-template-columns:repeat(2,minmax(0,1fr))}}@media(max-width:600px){main{padding:24px 14px}.grid{grid-template-columns:minmax(0,1fr)}.stat-grid{grid-template-columns:minmax(0,1fr)}.asset-image{max-height:none}}'
    script = """function showModal(image){const viewer=document.getElementById('viewer');document.getElementById('viewer-image').src=image.src;document.getElementById('viewer-image').alt=image.alt;viewer.showModal()}
const PAGE_SIZE=20;
function initGalleries(){document.querySelectorAll('[data-gallery]').forEach(gallery=>{const cards=[...gallery.querySelectorAll('.gallery-card')];const button=document.querySelector(`[data-more-for=\"${gallery.id}\"]`);let visible=Math.min(PAGE_SIZE,cards.length);const apply=()=>{cards.forEach((card,index)=>{card.hidden=index>=visible});if(button)button.hidden=visible>=cards.length};apply();if(button)button.addEventListener('click',()=>{visible=Math.min(visible+PAGE_SIZE,cards.length);apply()})})}
document.addEventListener('DOMContentLoaded',initGalleries);"""
    return f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>竞品页面报告</title><style>{css}</style></head><body><main><header><h1>{escape(task.get("target_page", "竞品页面报告"))}</h1><p>{escape(task.get("research_goal", ""))}</p><p class="reason">分类维度：{escape(classification.get("classification_dimension", ""))} · {escape(classification.get("classification_reason", ""))} · 有效样本：{len(assets)}</p></header>{stats_html}{empty}{"".join(sections)}{fallback_html}</main><dialog id="viewer" onclick="if(event.target===this)this.close()"><button aria-label="关闭" onclick="this.closest('dialog').close()">×</button><img id="viewer-image" alt=""></dialog><script>{script}</script></body></html>'''
