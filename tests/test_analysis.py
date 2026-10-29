import copy
import importlib
import importlib.util
import unittest

from competitor_analysis_skill.classification import classify_assets, ClassificationError
from report_content_fixtures import analysis, analysis_v2, claim, classification_v2


class AnalysisContractTests(unittest.TestCase):
    def validate(self, value):
        self.assertIsNotNone(importlib.util.find_spec("competitor_analysis_skill.analysis"), "R4/R5 分析契约尚未实现")
        module = importlib.import_module("competitor_analysis_skill.analysis")
        materials = [{"id": "mat-a", "collection_status": "collected", "semantic_status": "accepted", "quality_status": "accepted", "image_path": "a.png"}]
        groups = {"groups": [{"id": "group-main", "material_ids": ["mat-a"]}]}
        return module.validate_analysis(value, materials, groups)

    def test_r5_preserves_reader_content_and_multiple_evidence_refs(self):
        data = analysis()
        data["overall"]["evidence_refs"].append({"kind": "group", "id": "group-main"})
        before = copy.deepcopy(data)
        result = self.validate(data)
        self.assertEqual(result, before)
        self.assertEqual(data, before)

    def test_r5_rejects_unknown_material_group_and_current_state_references(self):
        for kind in ("material", "group", "current_state"):
            with self.subTest(kind=kind):
                data = analysis()
                data["overall"]["evidence_refs"] = [{"kind": kind, "id": "missing"}]
                with self.assertRaisesRegex(ValueError, "引用"):
                    self.validate(data)

    def test_claim_ids_are_unique_across_modules(self):
        data = analysis()
        data["synthesis"]["findings"][0]["id"] = "overall"
        with self.assertRaisesRegex(ValueError, "重复"):
            self.validate(data)

    def test_empty_group_cannot_support_a_claim(self):
        from competitor_analysis_skill.analysis import validate_analysis
        data = analysis()
        data["overall"]["evidence_refs"] = [{"kind": "group", "id": "empty"}]
        materials = [{"id": "mat-a", "collection_status": "collected", "semantic_status": "accepted", "quality_status": "accepted", "image_path": "a.png"}]
        classification = {"groups": [{"id": "group-main", "material_ids": ["mat-a"]}, {"id": "empty", "material_ids": []}]}
        with self.assertRaisesRegex(ValueError, "引用"):
            validate_analysis(data, materials, classification)

    def test_current_state_requires_actual_text_or_image_evidence(self):
        data = analysis()
        data["current_state"] = {"id": "current", "images": [], "findings": []}
        with self.assertRaisesRegex(ValueError, "现状"):
            self.validate(data)

    def test_text_only_current_state_is_valid(self):
        data = analysis(True)
        data["current_state"]["images"] = []
        self.assertEqual(self.validate(data)["current_state"]["description"], data["current_state"]["description"])

    def test_unknown_missing_and_not_applicable_are_explicit_gaps(self):
        data = {"schema_version": 1, "title": "边界说明", "research": {"question": "比较入口", "scope": "尚无可比较的截图"},
                "information_gaps": [{"section": "overall", "status": "unknown", "reason": "未取得目标状态截图"},
                                     {"section": "current_state", "status": "not_provided", "reason": "用户未提供现状"},
                                     {"section": "recommendation", "status": "not_applicable", "reason": "本次仅记录可见差异"}]}
        self.assertEqual(self.validate(data), data)
        data["information_gaps"][0]["status"] = "guessed"
        with self.assertRaises(ValueError):
            self.validate(data)

    def test_malformed_content_and_unrendered_fields_are_rejected(self):
        for change in ({"schema_version": 2}, {"groups": "not an array"}, {"typo_findings": []}, {"overall": None}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                self.validate({**analysis(), **change})

    def test_group_and_material_insights_must_reference_their_subject(self):
        data = analysis()
        data["groups"][0]["takeaway"]["evidence_refs"] = [{"kind": "current_state", "id": "absent"}]
        with self.assertRaises(ValueError):
            self.validate(data)


class StableGroupIdTests(unittest.TestCase):
    def test_explicit_group_ids_survive_and_duplicates_fail(self):
        materials = [{"id": "a", "collection_status": "collected", "semantic_status": "accepted", "quality_status": "accepted", "image_path": "a.png"}]
        plan = {"classification_dimension": "维度", "classification_reason": "依据", "groups": [{"id": "stable-group", "name": "组", "reason": "理由", "material_ids": ["a"]}]}
        self.assertEqual(classify_assets(materials, plan)["groups"][0].get("id"), "stable-group")
        plan["groups"].append({"id": "stable-group", "name": "另一组", "reason": "理由", "material_ids": []})
        with self.assertRaises(ClassificationError):
            classify_assets(materials, plan)

    def test_legacy_ids_are_deterministic_and_not_position_based(self):
        materials = [{"id": x, "collection_status": "collected", "semantic_status": "accepted", "quality_status": "accepted", "image_path": x+".png"} for x in ("a", "b")]
        plan = {"classification_dimension": "维度", "classification_reason": "依据", "groups": [{"name": x, "reason": "理由", "material_ids": [x]} for x in ("a", "b")]}
        first = classify_assets(materials, plan)["groups"]
        plan["groups"].reverse()
        second = classify_assets(materials, plan)["groups"]
        self.assertTrue(all(g.get("id") for g in first))
        self.assertEqual({g["name"]: g["id"] for g in first}, {g["name"]: g["id"] for g in second})


class AnalysisV2WorkflowTests(unittest.TestCase):
    def validate(self, value, with_current=False):
        from competitor_analysis_skill.analysis import validate_analysis
        materials = [{"id": "mat-a", "collection_status": "collected", "semantic_status": "accepted",
                      "quality_status": "accepted", "image_path": "a.png"}]
        return validate_analysis(value, materials, classify_assets(materials, classification_v2()))

    def test_v2_persists_workbench_and_agent_review_without_claiming_independence(self):
        data = analysis_v2()
        self.assertEqual(self.validate(data), data)
        self.assertFalse(data["quality_review"]["independent"])

    def test_v2_coverage_assessment_requires_explicit_choice_when_insufficient(self):
        data = analysis_v2()
        data["coverage_assessment"] = {
            "status": "insufficient", "summary": "任务模块只有一个可用案例",
            "covered_questions": ["会员入口"], "gaps": ["任务模块缺少第二个可比较案例"],
            "user_decision": "pending",
        }
        with self.assertRaisesRegex(ValueError, "样本不足"):
            self.validate(data)
        data["coverage_assessment"]["user_decision"] = "continue_limited"
        self.assertEqual(self.validate(data)["coverage_assessment"]["status"], "insufficient")

    def test_detailed_coverage_requires_independent_cases_and_task_bound_choice(self):
        from competitor_analysis_skill.analysis import validate_analysis
        data = analysis_v2()
        question = data["research"]["question"]
        data["coverage_assessment"] = {
            "status": "limited", "summary": "单个产品只能支持案例观察", "research_question": question,
            "questions": [{"id": "q1", "question": "入口如何分层", "material_ids": ["mat-a"],
                           "comparison_ids": [], "strategies": ["主入口独立成行"], "status": "single_case"}],
            "gaps": [{"reason": "discovery_insufficient", "detail": "缺少第二个独立产品",
                      "question_ids": ["q1"], "source_attempt_ids": []}],
            "user_decision": {"status": "not_required", "research_question": question,
                              "provenance": "not_required"},
        }
        materials = [{"id": "mat-a", "product_name": "产品A", "collection_status": "collected",
                      "semantic_status": "accepted", "quality_status": "accepted", "image_path": "a.png"}]
        classification = classify_assets(materials, classification_v2())
        self.assertEqual(validate_analysis(data, materials, classification, True)["coverage_assessment"]["status"], "limited")
        data["coverage_assessment"]["research_question"] = "另一项研究"
        with self.assertRaisesRegex(ValueError, "研究问题"):
            validate_analysis(data, materials, classification, True)

    def test_detailed_coverage_does_not_count_duplicate_screens_as_independent_cases(self):
        from competitor_analysis_skill.analysis import validate_analysis
        materials = [{"id": mid, "product_name": "同一产品", "collection_status": "collected",
                      "semantic_status": "accepted", "quality_status": "accepted", "image_path": mid+".png"}
                     for mid in ("mat-a", "mat-b")]
        classification = classify_assets(materials, classification_v2(("mat-a", "mat-b")))
        data = analysis_v2()
        data["analysis_process"]["material_observations"].append({
            "id": "obs-b", "material_id": "mat-b", "visible_facts": ["同一产品另一张截图"],
            "evidence_boundaries": ["不能冒充独立案例"]})
        data["analysis_process"]["comparisons"] = [{
            "id": "cmp", "material_ids": ["mat-a", "mat-b"], "comparison_findings": ["同一产品两个状态"],
            "design_judgment": "只能比较状态", "recommendation": "补充其他产品", "applicability": "当前任务",
            "tradeoffs": ["缺少独立案例"], "evidence_boundaries": ["不支持普遍结论"]}]
        data["materials"].append({"material_id": "mat-b", "insight": {
            "id": "material-b", "kind": "inference", "statement": "补充同产品另一状态",
            "evidence_refs": [{"kind": "material", "id": "mat-b"}], "analysis_refs": ["obs-b"],
            "recommendation": "仅作状态对照", "applicability": "同产品比较", "limitations": "不是独立案例"}})
        data["quality_review"]["reviewed_claim_ids"].append("material-b")
        q=data["research"]["question"]
        data["coverage_assessment"]={"status":"sufficient","summary":"两张截图","research_question":q,
            "questions":[{"id":"q1","question":"入口如何分层","material_ids":["mat-a","mat-b"],
                          "comparison_ids":["cmp"],"strategies":["独立成行"],"status":"comparable"}],"gaps":[],
            "user_decision":{"status":"not_required","research_question":q,"provenance":"not_required"}}
        with self.assertRaisesRegex(ValueError, "独立产品"):
            validate_analysis(data, materials, classification, True)

    def test_v2_rejects_missing_observation_and_unknown_analysis_reference(self):
        missing = analysis_v2(); missing["analysis_process"]["material_observations"] = []
        with self.assertRaisesRegex(ValueError, "逐图观察"):
            self.validate(missing)
        unknown = analysis_v2(); unknown["overall"]["analysis_refs"] = ["missing-process"]
        with self.assertRaisesRegex(ValueError, "分析过程"):
            self.validate(unknown)

    def test_v2_review_must_cover_every_final_claim(self):
        data = analysis_v2(); data["quality_review"]["reviewed_claim_ids"].remove("summary")
        with self.assertRaisesRegex(ValueError, "复核"):
            self.validate(data)
        data = analysis_v2(); data["quality_review"]["independent"] = True
        with self.assertRaisesRegex(ValueError, "独立"):
            self.validate(data)

    def test_v2_current_state_links_specific_region_and_competitor_reference(self):
        data = analysis_v2(True)
        self.assertEqual(self.validate(data, True)["current_state"]["regions"][0]["id"], "current-actions")
        no_region = analysis_v2(True); no_region["current_state"]["regions"] = []
        with self.assertRaisesRegex(ValueError, "问题区域"):
            self.validate(no_region, True)
        no_reference = analysis_v2(True); no_reference["analysis_process"]["current_state"]["reference_claim_ids"] = []
        with self.assertRaisesRegex(ValueError, "竞品"):
            self.validate(no_reference, True)

    def test_v2_comparisons_cover_every_material_and_do_not_hide_exceptions(self):
        from competitor_analysis_skill.analysis import validate_analysis
        materials = [{"id": mid, "collection_status": "collected", "semantic_status": "accepted",
                      "quality_status": "accepted", "image_path": mid + ".png"} for mid in ("mat-a", "mat-b")]
        classification = classify_assets(materials, classification_v2(("mat-a", "mat-b")))
        data = analysis_v2()
        data["analysis_process"]["material_observations"].append({
            "id": "obs-b", "material_id": "mat-b",
            "visible_facts": ["第二张素材采用列表而不是横排"],
            "evidence_boundaries": ["只能比较当前可见结构"],
        })
        data["materials"].append({
            "material_id": "mat-b",
            "insight": {
                "id": "material-b", "kind": "inference", "statement": "列表适合承接较多辅助入口",
                "evidence_refs": [{"kind": "material", "id": "mat-b"}], "analysis_refs": ["obs-b"],
                "recommendation": "在入口较多时再采用列表", "applicability": "辅助入口需要清楚命名",
                "limitations": "不能据此判断入口低频",
            },
        })
        data["quality_review"]["reviewed_claim_ids"].append("material-b")
        with self.assertRaisesRegex(ValueError, "横向比较"):
            validate_analysis(data, materials, classification)
        data["analysis_process"]["comparisons"] = [{
            "id": "cmp-layout", "material_ids": ["mat-a", "mat-b"],
            "comparison_findings": ["一张用横排，一张用列表"],
            "design_judgment": "入口数量和任务关系决定组织方式",
            "recommendation": "先确认主要与辅助入口", "applicability": "需要组织多类入口",
            "tradeoffs": ["列表增加页面长度"], "evidence_boundaries": ["截图不能证明查找效率"],
        }]
        self.assertEqual(len(validate_analysis(data, materials, classification)["analysis_process"]["comparisons"]), 1)

        unrelated = copy.deepcopy(data)
        unrelated["materials"][0]["insight"]["analysis_refs"] = ["obs-b"]
        unrelated["materials"][0]["insight"]["evidence_refs"].append(
            {"kind": "material", "id": "mat-b"}
        )
        with self.assertRaisesRegex(ValueError, "本素材"):
            validate_analysis(unrelated, materials, classification)

        unrelated = copy.deepcopy(data)
        unrelated["overall"]["analysis_refs"] = ["obs-b"]
        with self.assertRaisesRegex(ValueError, "证据对象"):
            validate_analysis(unrelated, materials, classification)
