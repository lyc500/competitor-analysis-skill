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
            out=root/'output'; done=subprocess.run([sys.executable,'-m','competitor_analysis_skill','--task-file',str(taskp),'--reviewed-materials-file',str(reviewp),'--classification-plan-file',str(planp),'--output',str(out)],cwd=Path(__file__).parents[1],capture_output=True,text=True); self.assertEqual(done.returncode,0,done.stderr); self.assertTrue((out/'classification.json').exists()); self.assertTrue((out/'report_data.json').exists()); self.assertTrue((out/'report.html').exists()); self.assertTrue((out/'assets/mat-a.png').exists()); self.assertNotIn(str(stage), (out/'report.html').read_text()); self.assertFalse((out/'materials.json').exists())
    def test_collected_requires_plan(self):
        with TemporaryDirectory() as d:
            root=Path(d); stage=root/'stage'; stage.mkdir(); (stage/'a.png').write_bytes((Path(__file__).parent/'fixtures/materials/valid.png').read_bytes()); reviewed={"materials":[{"id":"a","product_name":"产品A","page_name":"搜索结果页","image_path":"a.png","collection_status":"collected","semantic_status":"accepted","quality_status":"accepted"}]}
            (stage/'reviewed.json').write_text(json.dumps(reviewed))
            with self.assertRaises(ValueError): run_pipeline(self.task(),root/'out',reviewed_materials_file=stage/'reviewed.json',classification_plan_file=None)
