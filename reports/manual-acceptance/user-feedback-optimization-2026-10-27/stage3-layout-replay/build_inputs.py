"""Build Stage 3 replay inputs from the reviewed Stage 2 snapshots.

This acceptance-only script adds explicit presentation state labels. It is not a
production classifier and does not change group membership or analysis claims.
"""
from copy import deepcopy
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
STAGE2 = HERE.parent / "stage2-analysis-replay"


def main():
    for scenario in ("one-sentence-my-pages", "detailed-my-page-redesign"):
        plan = json.loads((STAGE2 / scenario / "classification-plan.json").read_text(encoding="utf-8"))
        plan = deepcopy(plan)
        if scenario == "detailed-my-page-redesign":
            labels = {row["material_id"]: row["labels"] for row in plan["material_labels"]}
            labels["mat-cap-tencent"]["annotation_status"] = "original_annotated"
            labels["mat-cap-bilibili"]["version_status"] = "historical_version"
        output = HERE / scenario / "classification-plan.json"
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
