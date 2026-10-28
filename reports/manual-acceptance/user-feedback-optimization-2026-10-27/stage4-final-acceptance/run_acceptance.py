"""Run the formal Stage 2 -> Stage 3C -> Stage 4 chain for each acceptance case."""
import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[3]
SCENARIOS = ("scenario-a-my-pages", "scenario-b-redesign", "generic-settings-validation")


def run(command):
    result = subprocess.run(command, cwd=REPO, text=True, capture_output=True)
    return {
        "command": " ".join(command), "returncode": result.returncode,
        "stdout": result.stdout, "stderr": result.stderr,
    }


def main():
    records = []
    for name in SCENARIOS:
        folder = ROOT / name
        input_dir = folder / "input"
        stages = [
            [sys.executable, "-B", "-m", "competitor_analysis_skill", "--task-file", str(input_dir / "task.json"),
             "--sources-file", str(input_dir / "sources-input.json"), "--output", str(folder / "stage2")],
            [sys.executable, "-B", "-m", "competitor_analysis_skill", "--task-file", str(input_dir / "task.json"),
             "--sources-file", str(folder / "stage2" / "sources.json"), "--captures-file", str(input_dir / "captures-input.json"),
             "--semantic-reviews-file", str(input_dir / "semantic-reviews.json"), "--output", str(folder / "stage3c")],
            [sys.executable, "-B", "-m", "competitor_analysis_skill", "--task-file", str(input_dir / "task.json"),
             "--reviewed-materials-file", str(folder / "stage3c" / "reviewed_materials.json"),
             "--classification-plan-file", str(input_dir / "classification-plan.json"),
             "--analysis-file", str(input_dir / "analysis.json"), "--output", str(folder / "report")],
        ]
        for command in stages:
            record = run(command)
            record["scenario"] = name
            records.append(record)
            if record["returncode"]:
                break
    (ROOT / "actual-command-log.json").write_text(json.dumps(records, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    failed = [record for record in records if record["returncode"]]
    if failed:
        print(failed[0]["stderr"] or failed[0]["stdout"], file=sys.stderr)
        raise SystemExit(failed[0]["returncode"])
    print(f"formal runs passed: {len(records)} commands")


if __name__ == "__main__":
    main()
