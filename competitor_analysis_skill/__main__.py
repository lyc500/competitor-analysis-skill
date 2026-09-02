import argparse
from pathlib import Path

from .pipeline import run_pipeline


def main():
    parser = argparse.ArgumentParser(description="竞品分析 Skill V0.1")
    parser.add_argument("request", help="自然语言调研需求")
    parser.add_argument("--output", default="reports/latest", help="报告输出目录")
    parser.add_argument("--offline", action="store_true", help="只生成结构，不访问公开来源")
    args = parser.parse_args()
    result = run_pipeline(args.request, Path(args.output), fetch=not args.offline)
    print(f"报告：{result['report_html']}")
    print(f"素材池：{result['assets_json']}")


if __name__ == "__main__":
    main()

