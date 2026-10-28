"""Regenerate each final report from saved formal inputs and compare bytes."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[3]
SCENARIOS = ("scenario-a-my-pages", "scenario-b-redesign", "generic-settings-validation")


def file_hashes(folder: Path) -> dict[str, str]:
    return {
        str(path.relative_to(folder)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(folder.rglob("*"))
        if path.is_file()
    }


def manifest_hash(hashes: dict[str, str]) -> str:
    payload = json.dumps(hashes, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def main() -> None:
    results = []
    with tempfile.TemporaryDirectory(prefix="competitor-report-repro-") as temp:
        temporary_root = Path(temp)
        for name in SCENARIOS:
            folder = ROOT / name
            input_dir = folder / "input"
            regenerated = temporary_root / name
            command = [
                sys.executable,
                "-B",
                "-m",
                "competitor_analysis_skill",
                "--task-file",
                str(input_dir / "task.json"),
                "--reviewed-materials-file",
                str(folder / "stage3c" / "reviewed_materials.json"),
                "--classification-plan-file",
                str(input_dir / "classification-plan.json"),
                "--analysis-file",
                str(input_dir / "analysis.json"),
                "--output",
                str(regenerated),
            ]
            completed = subprocess.run(command, cwd=REPO, text=True, capture_output=True)
            expected = file_hashes(folder / "report")
            actual = file_hashes(regenerated) if completed.returncode == 0 else {}
            results.append({
                "scenario": name,
                "command": (
                    "python3 -B -m competitor_analysis_skill "
                    f"--task-file {name}/input/task.json "
                    f"--reviewed-materials-file {name}/stage3c/reviewed_materials.json "
                    f"--classification-plan-file {name}/input/classification-plan.json "
                    f"--analysis-file {name}/input/analysis.json "
                    f"--output <temporary-output>/{name}"
                ),
                "returncode": completed.returncode,
                "stderr": completed.stderr,
                "expected_file_count": len(expected),
                "actual_file_count": len(actual),
                "expected_manifest_sha256": manifest_hash(expected),
                "actual_manifest_sha256": manifest_hash(actual),
                "missing_files": sorted(set(expected) - set(actual)),
                "unexpected_files": sorted(set(actual) - set(expected)),
                "changed_files": sorted(
                    path for path in set(expected) & set(actual) if expected[path] != actual[path]
                ),
                "exact_match": expected == actual,
            })

    output = ROOT / "reproducibility.json"
    output.write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    failed = [item for item in results if item["returncode"] or not item["exact_match"]]
    if failed:
        print(json.dumps(failed, ensure_ascii=False, indent=2), file=sys.stderr)
        raise SystemExit(1)
    print(f"exact report regeneration passed: {len(results)} scenarios")


if __name__ == "__main__":
    main()
