"""Presentation of validated analysis. No domain-specific copy or inference."""
from html import escape
import hashlib


def anchor(kind, value):
    return kind + "-" + hashlib.sha256(str(value).encode("utf-8")).hexdigest()[:16]


def _claim_evidence(claim, names):
    refs = []
    for ref in claim["evidence_refs"]:
        kind, rid = ref["kind"], ref["id"]
        target = anchor(kind, rid)
        refs.append(f'<a href="#{target}" data-evidence-target="{target}">{escape(names.get((kind, rid), rid))}</a>')
    kind_label = {"observation": "可见观察", "inference": "设计判断", "question": "待验证"}[claim["kind"]]
    return f'<p class="claim-evidence"><span>{kind_label}</span> · {" / ".join(refs)}</p>'


def render_claim(claim, names, compact=False, show_evidence=True):
    detail = "" if compact else "".join(f'<p><strong>{label}：</strong>{escape(claim[field])}</p>'
                     for field, label in (("recommendation", "建议"), ("applicability", "适用条件"), ("limitations", "限制")) if field in claim)
    evidence = _claim_evidence(claim, names) if show_evidence else ""
    return f'<div class="analysis-claim" id="{anchor("claim", claim["id"])}"><p class="claim-statement">{escape(claim["statement"])}</p>{detail}{evidence}</div>'


def render_reader_claim(claim, names, show_recommendation=True):
    recommendation = ""
    if show_recommendation and claim.get("recommendation"):
        recommendation = f'<p class="reader-recommendation"><strong>建议：</strong>{escape(claim["recommendation"])}</p>'
    return (f'<div class="analysis-claim reader-claim" id="{anchor("claim", claim["id"])}">'
            f'<p class="claim-statement">{escape(claim["statement"])}</p>{recommendation}</div>')


def render_overview_claim(overall):
    """Render the Agent-authored reader summary without re-composing its workbench claims."""
    conclusion = overall["statement"].strip()
    recommendation = ""
    if overall.get("recommendation"):
        recommendation = (f'<p class="reader-recommendation"><strong>建议：</strong>'
                          f'{escape(overall["recommendation"])}</p>')
    return (f'<div class="analysis-claim reader-claim" id="{anchor("claim", overall["id"])}">'
            f'<p class="claim-statement"><strong>结论：</strong>{escape(conclusion)}</p>'
            f'{recommendation}</div>')


def render_card_claim(claim, show_recommendation):
    recommendation = ""
    if show_recommendation and claim.get("recommendation"):
        recommendation = f'<p class="card-recommendation"><strong>建议：</strong>{escape(claim["recommendation"])}</p>'
    return (f'<div class="analysis-claim card-focus" id="{anchor("claim", claim["id"])}">'
            f'<p class="claim-statement">{escape(claim["statement"])}</p>{recommendation}</div>')


def render_claim_detail(claim, names):
    detail = "".join(f'<p><strong>{label}：</strong>{escape(claim[field])}</p>'
                     for field, label in (("recommendation", "建议"), ("applicability", "适用条件"),
                                          ("limitations", "限制")) if field in claim)
    return f'<div class="claim-detail">{detail}{_claim_evidence(claim, names)}</div>'


def content_parts(task, materials, classification, analysis, generation):
    groups = classification.get("groups", [])
    names = {("material", m["id"]): m["product_name"] for m in materials}
    names.update({("group", g.get("id", g["name"])): g["name"] for g in groups})
    current = (analysis or {}).get("current_state", {})
    if current:
        names[("current_state", current["id"])] = "现状证据"
        names.update({("current_state", i["id"]): i["caption"] for i in current.get("images", [])})
        names.update({("current_state", i["id"]): i["label"] for i in current.get("regions", [])})
    render = lambda c: render_claim(c, names)
    title = analysis["title"] if analysis else task.get("target_page", "竞品页面报告")
    notice = '<p class="report-notice">历史数据重放 / 报告重渲染；未执行新的来源搜集或证据验收。</p>' if generation.get("mode") == "replay" else ""
    count = f'<p class="sample-count">{len({m["product_name"] for m in materials})} 个竞品 · {len(materials)} 张竞品截图</p>'
    if analysis:
        main = render_overview_claim(analysis["overall"]) if "overall" in analysis else ""
        explained = {g["section"] for g in analysis.get("information_gaps", [])}
        summary = analysis.get("synthesis", {})
        absent = []
        if "overall" not in analysis and "overall" not in explained:
            absent.append("总判断")
        if not (summary.get("findings") or summary.get("validation_questions")) and "synthesis" not in explained:
            absent.append("综合小结")
        if absent:
            main += f'<p class="information-gap">本报告未提供：{"、".join(absent)}；仅展示已有依据的分析。</p>'
    else:
        main = '<p class="report-notice">未提供结构化分析；保留已有截图与证据，未按新版分析标准验收。</p>'
    overview = f'<header data-module="overview"><h1>{escape(title)}</h1>{main}</header>'
    navigation = ""
    if groups:
        links = "".join(f'<a href="#{anchor("group", g.get("id", g["name"]))}">{escape(g["name"])}</a>' for g in groups)
        navigation = f'<nav data-module="navigation" aria-label="分类导航">{links}</nav>'
    baseline = ""
    if current:
        text = f'<p>{escape(current["description"])}</p>' if current.get("description") else ""
        for item in current.get("images", []):
            text += (f'<figure id="{anchor("current_state", item["id"])}">'
                     f'<button class="current-image-button" type="button" aria-label="放大查看 {escape(item["caption"])}" '
                     f'onclick="showModal(this.querySelector(\'img\'))"><img class="current-image" '
                     f'src="{escape(item["image_path"], quote=True)}" alt="{escape(item["caption"])}"></button>'
                     f'<figcaption>{escape(item["caption"])}</figcaption></figure>')
        for item in current.get("regions", []):
            text += (f'<div class="current-region" id="{anchor("current_state", item["id"])}">'
                     f'<p><strong>{escape(item["label"])}：</strong>{escape(item["visible_fact"])}</p></div>')
        text += "".join(render(c) for c in current.get("findings", []))
        baseline = f'<details data-module="current-state" id="{anchor("current_state", current["id"])}"><summary>现状与问题分析</summary>{text}<p>用户现状仅用于对照，不计入竞品数量。</p></details>'
    synthesis = ""
    summary = (analysis or {}).get("synthesis", {})
    findings = "".join(render_reader_claim(c, names) for c in summary.get("findings", []))
    questions = "".join(render_reader_claim(c, names, show_recommendation=False) for c in summary.get("validation_questions", []))
    if findings or questions:
        synthesis = '<section data-module="synthesis"><h2>竞品分析小结</h2>' + findings
        if questions:
            synthesis += '<h3>待验证事项</h3>' + questions
        synthesis += '</section>'
    group_text = {g["group_id"]: render_claim(g["takeaway"], names, compact=True, show_evidence=False)
                  for g in (analysis or {}).get("groups", [])}
    show_card_recommendation = bool((analysis or {}).get("research", {}).get("goals"))
    material_text = {m["material_id"]: render_card_claim(m["insight"], show_card_recommendation)
                     for m in (analysis or {}).get("materials", [])}
    material_details = {m["material_id"]: render_claim_detail(m["insight"], names)
                        for m in (analysis or {}).get("materials", [])}
    methodology = ""
    if analysis:
        methodology = notice + count
        research = analysis["research"]
        methodology += f'<h3>研究问题与范围</h3><p>{escape(research["question"])}</p><p>{escape(research["scope"])}</p>'
        for field, label in (("goals", "目标"), ("constraints", "约束")):
            if research.get(field):
                methodology += f'<h3>{label}</h3><ul>' + ''.join(f'<li>{escape(s)}</li>' for s in research[field]) + '</ul>'
        for note in analysis.get("methodology", []):
            methodology += f'<h3>{escape(note["title"])}</h3><p>{escape(note["text"])}</p>'
        for gap in analysis.get("information_gaps", []):
            label = "不适用" if gap["status"] == "not_applicable" else "信息缺口"
            methodology += f'<p>{label}：{escape(gap["reason"])}</p>'
        coverage = analysis.get("coverage_assessment")
        if coverage:
            decision_labels = {
                "not_required": "无需额外选择",
                "continue_limited": "用户选择按当前样本继续",
                "supplement_sources": "用户选择补充来源",
                "pending": "等待用户选择",
            }
            methodology += f'<h3>样本覆盖</h3><p>{escape(coverage["summary"])}</p>'
            questions = coverage.get("questions")
            covered = ([item["question"] for item in questions if item["status"] == "comparable"]
                       if questions else coverage.get("covered_questions", []))
            if covered:
                methodology += '<p><strong>已覆盖：</strong>' + '；'.join(escape(item) for item in covered) + '</p>'
            gaps = coverage.get("gaps", [])
            gap_text = [item["detail"] if isinstance(item, dict) else item for item in gaps]
            if gap_text:
                methodology += '<p><strong>仍缺：</strong>' + '；'.join(escape(item) for item in gap_text) + '</p>'
            raw_decision = coverage["user_decision"]
            decision_status = raw_decision.get("status") if isinstance(raw_decision, dict) else raw_decision
            decision = decision_labels.get(decision_status, decision_status)
            methodology += f'<p><strong>处理：</strong>{escape(decision)}</p>'
        traceable_claims = ([analysis["overall"]] if analysis.get("overall") else [])
        traceable_claims += analysis.get("key_findings", [])
        traceable_claims += analysis.get("synthesis", {}).get("findings", [])
        traceable_claims += analysis.get("synthesis", {}).get("validation_questions", [])
        if traceable_claims:
            methodology += '<h3>结论依据与边界</h3>' + ''.join(render(c) for c in traceable_claims)
    elif task.get("research_goal"):
        methodology += f'<h3>原始研究目标</h3><p>{escape(task["research_goal"])}</p>'
    if groups:
        methodology += f'<h3>分类审核依据</h3><p>{escape(classification.get("classification_dimension", ""))} · {escape(classification.get("classification_reason", ""))}</p>'
        basis = classification.get("comparison_basis")
        if basis:
            methodology += (f'<p><strong>主比较维度：</strong>{escape(basis["primary_dimension"])}</p>'
                            f'<p><strong>采用原因：</strong>{escape(basis["rationale"])}</p>'
                            f'<p><strong>比较范围：</strong>{escape(basis["scope"])}</p>')
        methodology += '<ul>'
        for group in groups:
            methodology += f'<li><strong>{escape(group["name"])}</strong>：{escape(group["reason"])}'
            audit = group.get("audit")
            if audit:
                methodology += (f'<p>纳入标准：{escape(audit["inclusion_criteria"])}</p>'
                                f'<p>共同机制：{escape(audit["shared_mechanism"])}</p>'
                                f'<p>相邻差异：{escape(audit["adjacent_difference"])}</p><ul>')
                methodology += ''.join(
                    f'<li>{escape(names.get(("material", row["material_id"]), row["material_id"]))}：{escape(row["reason"])}</li>'
                    for row in audit["member_reasons"])
                methodology += '</ul>'
            methodology += '</li>'
        methodology += '</ul>'
    review = (analysis or {}).get("quality_review")
    if review:
        process = analysis["analysis_process"]
        if review["review_type"] == "agent_self_review":
            methodology += '<h3>分析复核</h3><p>Agent 自查已覆盖最终结论；这是交付前辅助复核，不是独立质量验证。</p>'
        else:
            methodology += '<h3>分析复核</h3><p>记录为人工复核；Python 仅校验记录结构，不判断分析正确性。</p>'
        methodology += (f'<p>底稿包含 {len(process["material_observations"])} 条逐图观察、'
                        f'{len(process["comparisons"])} 组横向比较；完整推理保存在结构化数据中，不在正文铺开。</p>')
        if review.get("notes"):
            methodology += '<ul>' + ''.join(f'<li>{escape(note)}</li>' for note in review["notes"]) + '</ul>'
    return {"overview": overview, "navigation": navigation, "current": baseline, "synthesis": synthesis,
            "groups": group_text, "materials": material_text, "material_details": material_details,
            "methodology": methodology, "title": title}


def source_tables(registry):
    if not registry:
        return ""
    result = ""
    preparation = registry.get("access_preparation")
    if preparation:
        decision_labels = {
            "not_required": "无需用户选择",
            "pending_user_choice": "等待用户选择",
            "public_only": "用户选择仅使用公开内容",
            "login_then_continue": "用户选择登录后继续",
        }
        resume_labels = {
            "not_needed": "无需恢复",
            "waiting_for_login": "等待登录",
            "resumed": "已复查并恢复",
            "partial": "复查后部分恢复",
            "blocked": "复查后仍阻塞",
        }
        bool_labels = {True: "可用", False: "不可用", "unknown": "未确认"}
        result += '<h3>来源访问准备</h3>'
        result += f'<p>{escape(preparation.get("research_scope", ""))}</p>'
        decision = preparation.get("decision", {})
        result += (f'<p><strong>本批决定：</strong>{escape(decision_labels.get(decision.get("status"), str(decision.get("status", ""))))}'
                   f'。{escape(decision.get("summary", ""))}</p>')
        resume = preparation.get("resume", {})
        result += f'<p><strong>恢复状态：</strong>{escape(resume_labels.get(resume.get("status"), str(resume.get("status", ""))))}</p>'
        check_by_id = {check.get("id"): check for check in preparation.get("checks", [])}
        current = preparation.get("current_checks_by_source", {})
        current_checks = [check_by_id[check_id] for check_id in current.values() if check_id in check_by_id]
        if current_checks:
            result += '<ul>'
            for check in current_checks:
                capabilities = (
                    f'页面：{bool_labels.get(check.get("page_open"), "未确认")} · '
                    f'搜索：{bool_labels.get(check.get("search_usable"), "未确认")} · '
                    f'筛选：{bool_labels.get(check.get("filter_usable"), "未确认")} · '
                    f'详情：{bool_labels.get(check.get("detail_usable"), "未确认")} · '
                    f'原图：{bool_labels.get(check.get("original_asset_usable"), "未确认")} · '
                    f'继续浏览：{bool_labels.get(check.get("pagination_usable"), "未确认")}'
                )
                result += (f'<li><strong>{escape(str(check.get("source_attempt_id", "")))}</strong>：'
                           f'登录状态：{escape(str(check.get("authentication_state", "unknown")))}；'
                           f'访问边界：{escape(str(check.get("access_barrier", "unknown")))}；'
                           f'{escape(capabilities)}；可见范围：{escape(str(check.get("visible_scope", "")))}'
                           f'{"；" + escape(str(check.get("notes", ""))) if check.get("notes") else ""}</li>')
            result += '</ul>'
    for key, title, fields in (("source_attempts", "来源访问记录", ("source_provider", "access_status", "observed_scope")),
                               ("candidates", "候选处置记录", ("product_name", "candidate_status", "disposition_reason"))):
        rows = registry.get(key, [])
        if rows:
            result += f'<h3>{title}</h3><ul>'
            result += ''.join('<li>' + ' · '.join(escape(str(row.get(k, ""))) for k in fields) + '</li>' for row in rows)
            result += '</ul>'
    return result
