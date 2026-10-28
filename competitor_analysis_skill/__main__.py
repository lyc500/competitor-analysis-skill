import argparse
from pathlib import Path

from .pipeline import run_pipeline
from .report_bundle import replay_report
from .task_contract import load_task_file


def main():
    parser = argparse.ArgumentParser(
        description="竞品分析正式入口使用 --task-file；自然语言位置参数仅为固定示例 legacy/demo",
    )
    parser.add_argument("request", nargs="?", help="仅旧离线演示：固定示例自然语言需求，不用于正式分析")
    parser.add_argument("--task-file", help="正式入口：Agent 生成的结构化任务 JSON")
    parser.add_argument("--output", default="reports/latest", help="报告输出目录")
    parser.add_argument("--offline", action="store_true", help="只生成结构，不访问公开来源")
    parser.add_argument("--materials-file", help="Agent/来源适配器提供的素材 JSON")
    parser.add_argument("--sources-file", help="Agent 提供的公开来源候选 JSON；正式采集须含访问准备、来源尝试与候选登记")
    parser.add_argument("--capture-sources", action="store_true", help="校验正式来源与访问准备后，使用真实 Chromium 截取来源页面")
    parser.add_argument("--captures-file", help="阶段 3B 已持久化的截图记录")
    parser.add_argument("--semantic-reviews-file", help="Agent 结构化语义审核结果")
    parser.add_argument("--manual-captures-file", help="用户/人工提供的截图记录")
    parser.add_argument("--reviewed-materials-file", help="Stage 3C reviewed_materials.json")
    parser.add_argument("--classification-plan-file", help="Agent Classification Plan JSON")
    parser.add_argument("--analysis-file", help="Agent 结构化报告分析 JSON")
    parser.add_argument("--report-data-file", help="重放已有 report_data.json；不代表新的来源验收")
    args = parser.parse_args()
    if args.report_data_file:
        if any((args.request, args.task_file, args.materials_file, args.sources_file, args.capture_sources,
                args.captures_file, args.semantic_reviews_file, args.manual_captures_file,
                args.reviewed_materials_file, args.offline)):
            parser.error("--report-data-file 只能搭配 --classification-plan-file、--analysis-file 和 --output")
        result = replay_report(args.report_data_file, Path(args.output), args.analysis_file,
                               args.classification_plan_file)
        print(f"重放报告（非新采集验收）：{result['report_html']}")
        return
    if args.analysis_file and not args.reviewed_materials_file:
        parser.error("--analysis-file 必须搭配 --reviewed-materials-file 或 --report-data-file")
    if bool(args.request) == bool(args.task_file):
        parser.error("必须提供 request（legacy/demo）或 --task-file 之一")
    if args.sources_file and not args.task_file:
        parser.error("--sources-file 必须与 --task-file 一起使用")
    if args.capture_sources and (not args.task_file or not args.sources_file):
        parser.error("--capture-sources 必须与 --task-file 和 --sources-file 一起使用")
    if args.capture_sources and (args.offline or args.materials_file):
        parser.error("--capture-sources 不得与 --offline 或 --materials-file 同时使用")
    if args.semantic_reviews_file and not args.task_file:
        parser.error("--semantic-reviews-file 必须与 --task-file 一起使用")
    if args.semantic_reviews_file and not (args.captures_file or args.manual_captures_file):
        parser.error("--semantic-reviews-file 必须搭配 --captures-file 或 --manual-captures-file")
    if args.semantic_reviews_file and (args.capture_sources or args.offline or args.materials_file):
        parser.error("阶段 3C 不得与 --capture-sources、--offline 或 --materials-file 同时使用")
    if any((args.captures_file, args.manual_captures_file)) and not args.semantic_reviews_file:
        parser.error("--captures-file/--manual-captures-file 必须搭配 --semantic-reviews-file")
    if args.reviewed_materials_file and not args.task_file:
        parser.error("--reviewed-materials-file 必须与 --task-file 一起使用")
    if args.classification_plan_file and not args.reviewed_materials_file:
        parser.error("--classification-plan-file 必须搭配 --reviewed-materials-file")
    if args.reviewed_materials_file and any((args.materials_file, args.sources_file, args.capture_sources, args.captures_file, args.semantic_reviews_file, args.manual_captures_file, args.offline)):
        parser.error("Stage 4 输入不得与其他阶段参数或 --offline 同时使用")
    task_input = load_task_file(args.task_file) if args.task_file else args.request
    result = run_pipeline(task_input, Path(args.output), fetch=not args.offline, materials_file=args.materials_file, sources_file=args.sources_file, capture_sources_flag=args.capture_sources, captures_file=args.captures_file, semantic_reviews_file=args.semantic_reviews_file, manual_captures_file=args.manual_captures_file, reviewed_materials_file=args.reviewed_materials_file, classification_plan_file=args.classification_plan_file, analysis_file=args.analysis_file)
    if result.get("reviewed_materials_json"):
        print(f"审核素材：{result['reviewed_materials_json']}")
        print(f"回退请求：{result['fallback_requests_json']}")
        return
    if result.get("classification_json"):
        print(f"分类结果：{result['classification_json']}")
        print(f"报告数据：{result['report_data_json']}")
        print(f"HTML 报告：{result['report_html']}")
        return
    print(f"报告：{result['report_html']}")
    print(f"素材池：{result['assets_json']}")
    if result.get("captures_json"):
        print(f"浏览器截图记录：{result['captures_json']}")


if __name__ == "__main__":
    main()
