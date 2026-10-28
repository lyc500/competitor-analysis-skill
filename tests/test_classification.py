import unittest
from competitor_analysis_skill.classification import classify_assets, ClassificationError
from report_content_fixtures import classification_v2

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

    def test_v2_preserves_primary_basis_group_audit_and_member_reasons(self):
        result = classify_assets([mat("mat-a")], classification_v2())
        self.assertEqual(result["schema_version"], 2)
        self.assertEqual(result["comparison_basis"]["primary_dimension"], "主要操作与辅助入口的组织机制")
        self.assertEqual(result["groups"][0]["audit"]["member_reasons"][0]["material_id"], "mat-a")

    def test_v2_rejects_missing_member_reason_and_state_path_labels(self):
        missing_member = classification_v2(); missing_member["groups"][0]["audit"]["member_reasons"] = []
        with self.assertRaisesRegex(ClassificationError, "成员理由"):
            classify_assets([mat("mat-a")], missing_member)
        missing_state = classification_v2(); del missing_state["material_labels"][0]["labels"]["login_state"]
        with self.assertRaisesRegex(ClassificationError, "状态标签"):
            classify_assets([mat("mat-a")], missing_state)

    def test_v2_rejects_unknown_contract_fields_but_accepts_normalized_snapshot(self):
        typo = classification_v2(); typo["comparison_bais"] = {}
        with self.assertRaisesRegex(ClassificationError, "未知字段"):
            classify_assets([mat("mat-a")], typo)
        typo = classification_v2(); typo["groups"][0]["semantic_score"] = 1
        with self.assertRaisesRegex(ClassificationError, "未知字段"):
            classify_assets([mat("mat-a")], typo)
        normalized = classify_assets([mat("mat-a")], classification_v2())
        self.assertEqual(classify_assets([mat("mat-a")], normalized), normalized)

    def test_v2_does_not_infer_groups_from_product_names_or_broad_terms(self):
        plan = classification_v2(("x","y"), "共同机制")
        result = classify_assets([dict(mat("x"), product_name="任意甲", notes="会员 钱包 服务"),
                                  dict(mat("y"), product_name="任意乙", notes="文件 云盘")], plan)
        self.assertEqual(result["groups"][0]["material_ids"], ["x", "y"])
        self.assertEqual(result["groups"][0]["audit"]["shared_mechanism"], "用独立横排表达当前任务的主要操作")
