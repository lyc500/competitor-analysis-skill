from html import escape

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

def render_report(task, assets, classification, fallback_requests=None):
    assets = _collected(task, assets); by_id = {m["id"]: m for m in assets}
    labels = {x["material_id"]: x.get("labels", {}) for x in classification.get("material_labels", [])}
    sections = []
    for group in classification.get("groups", []):
        cards = []
        for mid in group.get("material_ids", group.get("asset_ids", [])):
            m = by_id.get(mid)
            if not m: continue
            meta = " · ".join(str(m.get(k, "")) for k in ("region", "product_type", "platform"))
            label_html = " ".join(f'<span class="label">{escape(str(k))}: {escape(str(v))}</span>' for k, v in labels.get(mid, {}).items())
            cards.append(f'<article><div class="meta"><strong>{escape(m["product_name"])}</strong><span>{escape(meta)}</span></div><img class="asset-image" src="{escape(m["image_path"])}" alt="{escape(m["product_name"])} {escape(m["page_name"])}" onclick="showModal(this)"><div class="labels">{label_html}</div><p>{escape(m.get("source_url", ""))}</p></article>')
        sections.append(f'<section><h2>{escape(group["name"])}</h2><p class="reason">{escape(group["reason"])}</p><div class="grid">{"".join(cards)}</div></section>')
    open_items = [x for x in (fallback_requests or []) if x.get("status") == "open"]
    fallback_html = "" if not open_items else '<section class="fallback"><h2>待补充素材</h2><ul>' + ''.join(f'<li><strong>{escape(x.get("product_name", ""))}</strong>：{escape(x.get("reason", ""))}（{escape(", ".join(x.get("allowed_methods", [])))}）</li>' for x in open_items) + '</ul></section>'
    empty = "" if assets else '<section class="unavailable"><h2>unavailable</h2><p>当前没有通过语义审核和机械质量校验的有效页面素材。</p></section>'
    return f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>竞品页面报告</title><style>*{{box-sizing:border-box}}body{{margin:0;background:#f6f7f9;color:#17212b;font:15px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}}main{{max-width:1280px;margin:auto;padding:40px 24px}}header{{border-bottom:1px solid #dce1e7;padding-bottom:22px;margin-bottom:28px}}h1{{font-size:30px;margin:0 0 8px}}h2{{font-size:21px;margin:0}}.reason{{color:#64707d;margin:4px 0 16px}}section{{margin:30px 0}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:16px}}article{{background:#fff;border:1px solid #e0e5eb;border-radius:8px;padding:12px}}.meta{{display:flex;justify-content:space-between;gap:8px;margin-bottom:10px}}.meta span{{font-size:12px;color:#64707d}}.asset-image{{display:block;width:100%;height:360px;object-fit:contain;background:#edf0f3;border-radius:4px;cursor:zoom-in}}article p{{color:#64707d;font-size:12px;overflow-wrap:anywhere}}.label{{display:inline-block;margin:8px 4px 0 0;padding:2px 6px;background:#edf3f7;border-radius:4px;font-size:12px}}.unavailable,.fallback{{padding:22px;background:#fff;border:1px solid #e0e5eb;border-radius:8px}}dialog{{border:0;border-radius:8px;padding:0;max-width:95vw;max-height:95vh;background:#111}}dialog::backdrop{{background:#000b}}dialog img{{max-width:92vw;max-height:90vh;display:block}}button{{position:absolute;right:10px;top:10px;border:0;border-radius:50%;width:34px;height:34px;font-size:22px;cursor:pointer}}@media(max-width:600px){{main{{padding:24px 14px}}.grid{{grid-template-columns:1fr}}.asset-image{{height:300px}}}}</style></head><body><main><header><h1>{escape(task.get("target_page", "竞品页面报告"))}</h1><p>{escape(task.get("research_goal", ""))}</p><p class="reason">分类维度：{escape(classification.get("classification_dimension", ""))} · {escape(classification.get("classification_reason", ""))} · 有效样本：{len(assets)}</p></header>{empty}{"".join(sections)}{fallback_html}</main><dialog id="viewer" onclick="if(event.target===this)this.close()"><button aria-label="关闭" onclick="this.closest('dialog').close()">×</button><img id="viewer-image" alt=""></dialog><script>function showModal(image){{const viewer=document.getElementById('viewer');document.getElementById('viewer-image').src=image.src;document.getElementById('viewer-image').alt=image.alt;viewer.showModal()}}</script></body></html>'''
