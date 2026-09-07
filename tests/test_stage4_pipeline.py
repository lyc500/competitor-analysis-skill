import hashlib
import json, subprocess, sys, unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from competitor_analysis_skill.pipeline import run_pipeline

class Stage4PipelineTests(unittest.TestCase):
    def task(self):
        return {"raw_request":"x","research_goal":"参考","target_page":"搜索结果页","regions":["CN"],"specified_products":["产品A"],"assumptions":[],"needs_clarification":False,"task_status":"ready","planning_strategy":"user_only","competitors":[{"product_name":"产品A","region":"CN","product_type":"社区","platform":"Web","target_page":"搜索结果页","planning_source":"user_specified","priority":"high","reason":"指定"}]}
    def test_formal_cli_stage4_and_self_contained_assets(self):
        with TemporaryDirectory() as d:
            root=Path(d); stage=root/'stage3c'; (stage/'assets').mkdir(parents=True); (stage/'assets/a.png').write_bytes((Path(__file__).parent/'fixtures/materials/valid.png').read_bytes())
            reviewed={"task":self.task(),"materials":[{"id":"mat-a","product_name":"产品A","page_name":"搜索结果页","region":"CN","product_type":"社区","platform":"Web","image_path":"assets/a.png","source_type":"user_upload","collection_method":"user_provided","provenance":"user_upload","semantic_status":"accepted","quality_status":"accepted","collection_status":"collected"}],"fallback_requests":[]}
            taskp=root/'task.json'; reviewp=stage/'reviewed_materials.json'; planp=root/'plan.json'; taskp.write_text(json.dumps(self.task(),ensure_ascii=False)); reviewp.write_text(json.dumps(reviewed,ensure_ascii=False)); planp.write_text(json.dumps({"classification_dimension":"自定义","classification_reason":"Agent","groups":[{"name":"组","reason":"Agent","material_ids":["mat-a"]}]} ,ensure_ascii=False))
            out=root/'output'; done=subprocess.run([sys.executable,'-m','competitor_analysis_skill','--task-file',str(taskp),'--reviewed-materials-file',str(reviewp),'--classification-plan-file',str(planp),'--output',str(out)],cwd=Path(__file__).parents[1],capture_output=True,text=True); self.assertEqual(done.returncode,0,done.stderr); self.assertTrue((out/'classification.json').exists()); self.assertTrue((out/'report_data.json').exists()); self.assertTrue((out/'report.html').exists()); digest=hashlib.sha256(b"mat-a").hexdigest()[:16]; self.assertTrue((out/f'assets/{digest}.png').exists()); self.assertNotIn(str(stage), (out/'report.html').read_text()); self.assertFalse((out/'materials.json').exists())
    def test_collected_requires_plan(self):
        with TemporaryDirectory() as d:
            root=Path(d); stage=root/'stage'; stage.mkdir(); (stage/'a.png').write_bytes((Path(__file__).parent/'fixtures/materials/valid.png').read_bytes()); reviewed={"materials":[{"id":"a","product_name":"产品A","page_name":"搜索结果页","image_path":"a.png","collection_status":"collected","semantic_status":"accepted","quality_status":"accepted"}]}
            (stage/'reviewed.json').write_text(json.dumps(reviewed))
            with self.assertRaises(ValueError): run_pipeline(self.task(),root/'out',reviewed_materials_file=stage/'reviewed.json',classification_plan_file=None)

    def test_unsafe_material_ids_are_hashed_inside_assets_directory(self):
        unsafe_ids = ("../../../../escape", "nested/name", r"..\escape")
        with TemporaryDirectory() as d:
            root = Path(d)
            unsafe_ids += (str(root / "absolute-id"),)
            for index, material_id in enumerate(unsafe_ids):
                with self.subTest(material_id=material_id):
                    stage = root / f"stage3c-{index}"
                    (stage / "assets").mkdir(parents=True)
                    (stage / "assets/a.png").write_bytes(
                        (Path(__file__).parent / "fixtures/materials/valid.png").read_bytes()
                    )
                    reviewed = {
                        "task": self.task(),
                        "materials": [{
                            "id": material_id,
                            "product_name": "产品A",
                            "page_name": "搜索结果页",
                            "image_path": "assets/a.png",
                            "semantic_status": "accepted",
                            "quality_status": "accepted",
                            "collection_status": "collected",
                        }],
                        "fallback_requests": [],
                    }
                    reviewed_path = stage / "reviewed.json"
                    reviewed_path.write_text(json.dumps(reviewed, ensure_ascii=False))
                    plan_path = root / f"plan-{index}.json"
                    plan_path.write_text(json.dumps({
                        "classification_dimension": "自定义",
                        "classification_reason": "Agent",
                        "groups": [{
                            "name": "组",
                            "reason": "Agent",
                            "material_ids": [material_id],
                        }],
                    }, ensure_ascii=False))
                    output = root / f"case-{index}" / "nested" / "output"

                    result = run_pipeline(
                        self.task(),
                        output,
                        reviewed_materials_file=reviewed_path,
                        classification_plan_file=plan_path,
                    )

                    digest = hashlib.sha256(material_id.encode("utf-8")).hexdigest()[:16]
                    expected_relative = f"assets/{digest}.png"
                    self.assertEqual(
                        result["payload"]["materials"][0]["image_path"],
                        expected_relative,
                    )
                    self.assertTrue((output / expected_relative).is_file())
                    self.assertEqual(
                        [path.name for path in (output / "assets").iterdir()],
                        [f"{digest}.png"],
                    )
                    html = (output / "report.html").read_text(encoding="utf-8")
                    report_data = (output / "report_data.json").read_text(encoding="utf-8")
                    self.assertIn(expected_relative, html)
                    self.assertIn(expected_relative, report_data)
                    self.assertFalse((root / "escape.png").exists())
                    self.assertFalse((root / "absolute-id.png").exists())

    def _run_fallback_case(self, root, *, collected, fallback_status):
        stage = root / "stage3c"
        stage.mkdir()
        materials = []
        classification_plan_file = None
        if collected:
            (stage / "a.png").write_bytes(
                (Path(__file__).parent / "fixtures/materials/valid.png").read_bytes()
            )
            materials.append({
                "id": "mat-a",
                "product_name": "产品A",
                "page_name": "搜索结果页",
                "image_path": "a.png",
                "semantic_status": "accepted",
                "quality_status": "accepted",
                "collection_status": "collected",
            })
            classification_plan_file = root / "plan.json"
            classification_plan_file.write_text(json.dumps({
                "classification_dimension": "自定义",
                "classification_reason": "Agent",
                "groups": [{
                    "name": "组",
                    "reason": "Agent",
                    "material_ids": ["mat-a"],
                }],
            }, ensure_ascii=False))
        fallback_requests = [{
            "product_name": "产品A",
            "target_page": "搜索结果页",
            "status": fallback_status,
            "reason": "状态测试",
            "allowed_methods": ["user_upload"],
        }]
        reviewed_path = stage / "reviewed.json"
        reviewed_path.write_text(json.dumps({
            "task": self.task(),
            "materials": materials,
            "fallback_requests": fallback_requests,
        }, ensure_ascii=False))
        return run_pipeline(
            self.task(),
            root / "output",
            reviewed_materials_file=reviewed_path,
            classification_plan_file=classification_plan_file,
        )

    def test_collected_material_rejects_open_fallback(self):
        with TemporaryDirectory() as d:
            with self.assertRaisesRegex(ValueError, "fallback"):
                self._run_fallback_case(Path(d), collected=True, fallback_status="open")

    def test_missing_material_rejects_resolved_fallback(self):
        with TemporaryDirectory() as d:
            with self.assertRaisesRegex(ValueError, "fallback"):
                self._run_fallback_case(Path(d), collected=False, fallback_status="resolved")

    def test_collected_material_accepts_resolved_fallback(self):
        with TemporaryDirectory() as d:
            result = self._run_fallback_case(Path(d), collected=True, fallback_status="resolved")
            self.assertEqual(result["payload"]["fallback_requests"][0]["status"], "resolved")

    def test_missing_material_accepts_open_fallback(self):
        with TemporaryDirectory() as d:
            result = self._run_fallback_case(Path(d), collected=False, fallback_status="open")
            self.assertEqual(result["payload"]["fallback_requests"][0]["status"], "open")
