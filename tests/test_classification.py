import unittest
from competitor_analysis_skill.classification import classify_assets, ClassificationError

def mat(mid, status="collected", semantic="accepted", quality="accepted"):
    return {"id":mid,"collection_status":status,"semantic_status":semantic,"quality_status":quality,"image_path":f"assets/{mid}.png"}

class ClassificationStage4Tests(unittest.TestCase):
    def plan(self, ids=("a","b")):
        return {"classification_dimension":"结果组织方式","classification_reason":"Agent 根据样本观察制定","groups":[{"name":"双栏卡片","reason":"双栏布局","material_ids":list(ids)}],"material_labels":[{"material_id":ids[0],"labels":{"布局":"双栏","筛选入口":"顶部"}}]}
    def test_agent_plan_is_preserved_and_labels_are_dynamic(self):
        result=classify_assets([mat("a"),mat("b")],self.plan())
        self.assertEqual(result["classification_dimension"],"结果组织方式"); self.assertEqual(result["groups"][0]["name"],"双栏卡片"); self.assertEqual(result["material_labels"][0]["labels"]["布局"],"双栏")
    def test_collected_materials_must_be_classified_exactly_once(self):
        with self.assertRaises(ClassificationError): classify_assets([mat("a"),mat("b")],self.plan(("a",)))
        with self.assertRaises(ClassificationError): classify_assets([mat("a"),mat("b")],{"classification_dimension":"x","classification_reason":"y","groups":[{"name":"g1","reason":"r","material_ids":["a"]},{"name":"g2","reason":"r","material_ids":["a","b"]}]})
    def test_invalid_and_unknown_material_references_rejected(self):
        with self.assertRaises(ClassificationError): classify_assets([mat("a"),mat("bad", "rejected", "rejected", "rejected")],self.plan(("a","bad")))
        with self.assertRaises(ClassificationError): classify_assets([mat("a")],self.plan(("a","x")))
    def test_zero_collected_is_unavailable_without_plan(self):
        result=classify_assets([mat("x","pending","pending","pending")])
        self.assertEqual(result["classification_status"],"unavailable"); self.assertEqual(result["groups"],[])
    def test_no_heuristic_overrides_agent_names(self):
        result=classify_assets([dict(mat("a"),product_type="电商",notes="分栏筛选 feed")],{"classification_dimension":"自定义","classification_reason":"来自 Agent","groups":[{"name":"自定义结构A","reason":"Agent","material_ids":["a"]}]})
        self.assertEqual(result["groups"][0]["name"],"自定义结构A")
