import json
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


class Stage2PipelineRegressionTests(unittest.TestCase):
    def test_materials_file_collected_material_does_not_require_classification_plan(self):
        with TemporaryDirectory() as d:
            root = Path(d)
            task = {
                "raw_request": "商品详情页参考",
                "research_goal": "验证 Stage 2 素材正式入口",
                "target_page": "商品详情页",
                "regions": ["CN"],
                "specified_products": ["产品A"],
                "assumptions": [],
                "needs_clarification": False,
                "task_status": "ready",
                "planning_strategy": "user_only",
                "competitors": [{
                    "product_name": "产品A",
                    "region": "CN",
                    "product_type": "电商",
                    "platform": "Web",
                    "target_page": "商品详情页",
                    "planning_source": "user_specified",
                    "priority": "high",
                    "reason": "用户指定",
                }],
            }
            fixture = Path(__file__).parent / "fixtures/materials/valid.png"
            material = {
                "id": "stage2-material",
                "product_name": "产品A",
                "page_name": "商品详情页",
                "region": "CN",
                "product_type": "电商",
                "platform": "Web",
                "image_path": str(fixture),
                "source_type": "user_upload",
                "source_url": "",
                "captured_at": "",
                "collection_method": "user_provided",
                "provenance": "user_upload",
                "semantic_status": "accepted",
                "semantic_reason": "Agent 已确认产品与目标页面匹配",
                "collection_status": "pending",
                "quality_status": "pending",
                "quality_reason": "",
                "observed_structure": [],
                "observed_patterns": [],
                "notes": "feed 流 分栏 筛选 电商",
                "failure_reason": "",
            }
            task_path = root / "task.json"
            materials_path = root / "materials-input.json"
            output = root / "output"
            task_path.write_text(json.dumps(task, ensure_ascii=False))
            materials_path.write_text(json.dumps({"materials": [material]}, ensure_ascii=False))

            completed = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "competitor_analysis_skill",
                    "--task-file",
                    str(task_path),
                    "--materials-file",
                    str(materials_path),
                    "--output",
                    str(output),
                ],
                cwd=Path(__file__).parents[1],
                capture_output=True,
                text=True,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            payload = json.loads((output / "materials.json").read_text(encoding="utf-8"))
            self.assertEqual(payload["assets"][0]["collection_status"], "collected")
            self.assertEqual(payload["classification"], {
                "classification_status": "unavailable",
                "classification_dimension": "",
                "classification_reason": "正式动态分类仅在 Stage 4 Agent Classification Plan 流程执行",
                "groups": [],
                "material_labels": [],
            })
            self.assertTrue((output / payload["assets"][0]["image_path"]).is_file())
            self.assertTrue((output / "report.html").is_file())


if __name__ == "__main__":
    unittest.main()
