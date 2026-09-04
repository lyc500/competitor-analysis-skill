import argparse
from pathlib import Path

from .pipeline import run_pipeline
from .task_contract import load_task_file


def main():
    parser = argparse.ArgumentParser(description="竞品分析 Skill V0.1")
    parser.add_argument("request", nargs="?", help="legacy/demo 自然语言调研需求")
    parser.add_argument("--task-file", help="Agent 生成的结构化任务 JSON")
    parser.add_argument("--output", default="reports/latest", help="报告输出目录")
    parser.add_argument("--offline", action="store_true", help="只生成结构，不访问公开来源")
    parser.add_argument("--materials-file", help="Agent/来源适配器提供的素材 JSON")
    parser.add_argument("--sources-file", help="Agent 提供的公开来源候选 JSON")
    args = parser.parse_args()
    if bool(args.request) == bool(args.task_file):
        parser.error("必须提供 request（legacy/demo）或 --task-file 之一")
    if args.sources_file and not args.task_file:
        parser.error("--sources-file 必须与 --task-file 一起使用")
    task_input = load_task_file(args.task_file) if args.task_file else args.request
    result = run_pipeline(task_input, Path(args.output), fetch=not args.offline, materials_file=args.materials_file, sources_file=args.sources_file)
    print(f"报告：{result['report_html']}")
    print(f"素材池：{result['assets_json']}")


if __name__ == "__main__":
    main()
