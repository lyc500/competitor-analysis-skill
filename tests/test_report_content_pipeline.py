import json
import hashlib
from pathlib import Path
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest

from report_content_fixtures import analysis, analysis_v2, classification_v2, inputs

ROOT = Path(__file__).resolve().parents[1]


class ReportContentPipelineTests(unittest.TestCase):
    def cli(self, *args):
        return subprocess.run([sys.executable, "-B", "-m", "competitor_analysis_skill", *map(str, args)], cwd=ROOT, text=True, capture_output=True)

    def formal(self, source, out, content=True):
        args = ["--task-file", source/"task.json", "--reviewed-materials-file", source/"reviewed.json", "--classification-plan-file", source/"classification.json", "--output", out]
        if content:
            args += ["--analysis-file", source/"analysis.json"]
        return self.cli(*args)

    def test_two_scenarios_share_order_and_optional_current_state(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp); source = root/"input"; inputs(source)
            for detailed in (False, True):
                data = analysis_v2(detailed)
                (source/"analysis.json").write_text(json.dumps(data, ensure_ascii=False))
                out = root/str(detailed)
                run = self.formal(source, out)
                self.assertEqual(run.returncode, 0, run.stderr)
                html = (out/"report.html").read_text()
                markers = ['data-module="overview"', 'data-module="navigation"']
                if detailed:
                    markers.append('data-module="current-state"')
                markers += ['data-module="gallery"', 'data-module="methodology"', 'data-module="synthesis"']
                positions = [html.index(marker) for marker in markers]
                self.assertEqual(positions, sorted(positions))
                self.assertEqual('data-module="current-state"' in html, detailed)
                report = json.loads((out/"report_data.json").read_text())
                self.assertEqual(len(report["materials"]), 1)
                self.assertEqual(report["evidence_statistics"]["coverage"]["products_with_collected_material"], 1)
                self.assertEqual(report["analysis"]["overall"], data["overall"])
                self.assertEqual(report["generation"]["mode"], "formal")
                if detailed:
                    self.assertTrue((out/report["analysis"]["current_state"]["images"][0]["image_path"]).exists())
                self.assertNotIn("归组审核理由，不是读者结论</p><div", html)
                self.assertIn('class="asset-image"', html)
                self.assertIn('id="viewer"', html)
                detail = html[html.index('<details class="card-details">'):html.index('</details></article>')]
                self.assertIn("语义审核依据", detail)
                self.assertIn("机械质量依据", detail)
                self.assertIn("历史与版本说明", detail)

    def test_snapshot_can_move_replay_and_change_from_input_without_html_edits(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp); source = root/"input"; inputs(source)
            (source/"analysis.json").write_text(json.dumps(analysis_v2(True), ensure_ascii=False))
            first = root/"first"; run = self.formal(source, first)
            self.assertEqual(run.returncode, 0, run.stderr)
            moved = root/"moved"; shutil.move(first, moved)
            for name in ("replay", "same"):
                run = self.cli("--report-data-file", moved/"report_data.json", "--output", root/name)
                self.assertEqual(run.returncode, 0, run.stderr)
            self.assertEqual((root/"replay/report.html").read_bytes(), (root/"same/report.html").read_bytes())
            report = json.loads((moved/"report_data.json").read_text())
            report["analysis"]["overall"]["statement"] = "更新后的总判断"
            (moved/"report_data.json").write_text(json.dumps(report, ensure_ascii=False))
            run = self.cli("--report-data-file", moved/"report_data.json", "--output", root/"updated")
            self.assertEqual(run.returncode, 0, run.stderr)
            html = (root/"updated/report.html").read_text()
            self.assertIn("更新后的总判断", html)
            self.assertIn("重放", html)
            snapshot = json.loads((root/"updated/report_data.json").read_text())
            self.assertEqual(snapshot["generation"]["mode"], "replay")
            for m in snapshot["materials"] + snapshot["analysis"]["current_state"]["images"]:
                self.assertTrue((root/"updated"/m["image_path"]).is_file())

    def test_unknown_reference_fails_without_publishing_report(self):
        with TemporaryDirectory() as tmp:
            root=Path(tmp); source=root/"input"; inputs(source)
            data=analysis_v2(); data["overall"]["evidence_refs"][0]["id"]="missing"
            (source/"analysis.json").write_text(json.dumps(data))
            run=self.formal(source,root/"out")
            self.assertNotEqual(run.returncode,0)
            self.assertIn("引用",run.stderr)
            self.assertFalse((root/"out/report.html").exists())

    def test_legacy_missing_analysis_is_explicit_and_has_no_empty_sections(self):
        with TemporaryDirectory() as tmp:
            root=Path(tmp); source=root/"input"; inputs(source)
            run=self.formal(source,root/"out",content=False)
            self.assertEqual(run.returncode,0,run.stderr)
            data=json.loads((root/"out/report_data.json").read_text())
            self.assertEqual(data.get("generation",{}).get("analysis_status"),"missing")
            html=(root/"out/report.html").read_text()
            self.assertNotIn('data-module="synthesis"',html)
            self.assertNotIn('data-module="current-state"',html)
            self.assertNotIn("暂无分析",html)
            self.assertIn("未提供结构化分析",html)

    def test_historical_replay_does_not_weaken_formal_evidence_gate(self):
        with TemporaryDirectory() as tmp:
            root=Path(tmp); source=root/"input"; data=inputs(source)
            data["reviewed"]["materials"][0]["source_type"]="ui_database"
            (source/"reviewed.json").write_text(json.dumps(data["reviewed"]))
            self.assertNotEqual(self.formal(source,root/"formal").returncode,0)
            data["snapshot"]["materials"][0]["source_type"]="ui_database"
            (source/"snapshot.json").write_text(json.dumps(data["snapshot"]))
            run=self.cli("--report-data-file",source/"snapshot.json","--analysis-file",source/"analysis.json","--output",root/"replay")
            self.assertEqual(run.returncode,0,run.stderr)
            self.assertIn("重放",(root/"replay/report.html").read_text())

    def test_partial_analysis_explains_missing_judgment_without_empty_modules(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp); source = root/"input"; inputs(source)
            data = analysis(); del data["overall"]; del data["synthesis"]
            (source/"analysis.json").write_text(json.dumps(data))
            (source/"snapshot.json").write_text(json.dumps({**json.loads((source/"snapshot.json").read_text()), "analysis": data}))
            run = self.cli("--report-data-file",source/"snapshot.json","--output",root/"out")
            self.assertEqual(run.returncode, 0, run.stderr)
            html = (root/"out/report.html").read_text()
            self.assertIn("本报告未提供：总判断、综合小结", html)
            self.assertNotIn('data-module="synthesis"', html)
            data["information_gaps"] = [{"section": "overall", "status": "unknown", "reason": "缺少相同状态的对照图"},
                                        {"section": "synthesis", "status": "not_applicable", "reason": "本次只整理单图观察"}]
            (source/"analysis.json").write_text(json.dumps(data))
            (source/"snapshot.json").write_text(json.dumps({**json.loads((source/"snapshot.json").read_text()), "analysis": data}))
            run = self.cli("--report-data-file",source/"snapshot.json","--output",root/"explained")
            self.assertEqual(run.returncode, 0, run.stderr)
            html = (root/"explained/report.html").read_text()
            self.assertNotIn("本报告未提供：", html)
            self.assertIn("缺少相同状态的对照图", html)

    def test_analysis_flag_cannot_be_silently_ignored_by_other_stages(self):
        with TemporaryDirectory() as tmp:
            source=Path(tmp); inputs(source)
            run=self.cli("--task-file",source/"task.json","--analysis-file",source/"analysis.json","--output",source/"out")
            self.assertNotEqual(run.returncode,0)
            self.assertIn("--analysis-file",run.stderr)

    def test_current_image_cannot_escape_input_or_be_missing(self):
        with TemporaryDirectory() as tmp:
            root=Path(tmp); source=root/"input"; inputs(source)
            for path in ("../outside.png","missing.png"):
                data=analysis_v2(True); data["current_state"]["images"][0]["image_path"]=path
                (source/"analysis.json").write_text(json.dumps(data))
                run=self.formal(source,root/("bad-"+Path(path).name))
                self.assertNotEqual(run.returncode,0)

    def test_asset_destination_symlink_cannot_escape_assets(self):
        with TemporaryDirectory() as tmp:
            root=Path(tmp); source=root/"input"; inputs(source)
            out=root/"out"; (out/"assets").mkdir(parents=True)
            outside=root/"keep.png"; outside.write_bytes(b"do not overwrite")
            digest=hashlib.sha256(b"mat-a").hexdigest()[:16]
            (out/"assets"/(digest+".png")).symlink_to(outside)
            run=self.formal(source,out)
            self.assertNotEqual(run.returncode,0)
            self.assertEqual(outside.read_bytes(),b"do not overwrite")

    def test_replay_can_replace_classification_and_analysis_as_structured_inputs(self):
        with TemporaryDirectory() as tmp:
            root=Path(tmp); source=root/"input"; inputs(source)
            plan=classification_v2(name="按设计问题重分组")
            (source/"classification-v2.json").write_text(json.dumps(plan,ensure_ascii=False))
            (source/"analysis-v2.json").write_text(json.dumps(analysis_v2(),ensure_ascii=False))
            run=self.cli("--report-data-file",source/"snapshot.json",
                         "--classification-plan-file",source/"classification-v2.json",
                         "--analysis-file",source/"analysis-v2.json","--output",root/"out")
            self.assertEqual(run.returncode,0,run.stderr)
            report=json.loads((root/"out/report_data.json").read_text())
            self.assertEqual(report["classification"]["groups"][0]["name"],"按设计问题重分组")
            self.assertEqual(report["analysis"]["schema_version"],2)
            self.assertEqual(report["generation"]["analysis_standard"],"v2_agent_self_review")

    def test_v2_renders_compact_group_takeaway_and_keeps_workbench_folded(self):
        with TemporaryDirectory() as tmp:
            root=Path(tmp); source=root/"input"; inputs(source)
            (source/"classification.json").write_text(json.dumps(classification_v2(),ensure_ascii=False))
            (source/"analysis.json").write_text(json.dumps(analysis_v2(),ensure_ascii=False))
            run=self.formal(source,root/"out")
            self.assertEqual(run.returncode,0,run.stderr)
            html=(root/"out/report.html").read_text()
            header=html[html.index('<header'):html.index('</header>')]
            self.assertNotIn("主要操作位于辅助入口之前",header)
            self.assertIn("主要操作独立成行，适合先处理当前任务再浏览辅助入口",header)
            self.assertIn("<strong>结论：</strong>",header)
            self.assertNotIn('class="key-findings"',header)
            self.assertEqual(header.count("按当前研究目标选择该做法"),1)
            self.assertNotIn("适用条件",header)
            self.assertNotIn("限制",header)
            self.assertNotIn("设计判断",header)
            gallery=html[html.index('data-module="gallery"'):html.index('data-module="methodology"')]
            subtitle=gallery[:gallery.index('<div id="gallery-0"')]
            self.assertIn("重点比较主操作是否与当前任务一致",subtitle)
            self.assertNotIn("按当前研究目标选择该做法",subtitle)
            self.assertNotIn("设计判断",subtitle)
            card=gallery[gallery.index('<article class="gallery-card"'):gallery.index('</article>')]
            visible,detail=card.split('<details class="card-details">',1)
            self.assertIn("主操作独立成行，可用于验证当前任务是否需要一级入口",visible)
            self.assertNotIn("可见任务和页面状态与证据一致时",visible)
            self.assertNotIn("静态截图不能证明使用频率或行为效果",visible)
            self.assertIn("可见任务和页面状态与证据一致时",detail)
            self.assertIn("静态截图不能证明使用频率或行为效果",detail)
            methodology=html[html.index('data-module="methodology"'):html.index('data-module="synthesis"')]
            self.assertIn("主要操作与辅助入口的组织机制",methodology)
            self.assertIn("Agent 自查",methodology)
            self.assertIn("不是独立质量验证",methodology)
            report=json.loads((root/"out/report_data.json").read_text())
            self.assertIn("analysis_process",report["analysis"])

    def test_reader_summary_is_generic_for_non_profile_page(self):
        with TemporaryDirectory() as tmp:
            root=Path(tmp); source=root/"input"; inputs(source)
            task=json.loads((source/"task.json").read_text())
            task["target_page"]="搜索结果页"; task["raw_request"]="比较搜索结果页的筛选方式"
            task["research_goal"]="决定筛选项和结果卡片的层级"
            for competitor in task["competitors"]: competitor["target_page"]="搜索结果页"
            reviewed=json.loads((source/"reviewed.json").read_text()); reviewed["task"]=task
            reviewed["materials"][0]["page_name"]="搜索结果页"
            data=analysis_v2(); data["title"]="搜索结果页筛选参考"
            data["research"]["question"]="搜索结果页如何区分常用筛选与更多筛选？"
            data["overall"]["statement"]="常用筛选直接显示，更多条件按需展开。"
            data["overall"]["recommendation"]="先确认用户最常比较的条件，再决定首层筛选项。"
            cov=data["coverage_assessment"]; cov["research_question"]=data["research"]["question"]
            cov["user_decision"]["research_question"]=data["research"]["question"]
            (source/"task.json").write_text(json.dumps(task,ensure_ascii=False))
            (source/"reviewed.json").write_text(json.dumps(reviewed,ensure_ascii=False))
            (source/"analysis.json").write_text(json.dumps(data,ensure_ascii=False))
            run=self.formal(source,root/"out")
            self.assertEqual(run.returncode,0,run.stderr)
            header=(root/"out/report.html").read_text().split("</header>",1)[0]
            self.assertIn("搜索结果页筛选参考",header)
            self.assertIn("<strong>结论：</strong>常用筛选直接显示",header)
            self.assertNotIn("会员",header); self.assertNotIn("任务中心",header); self.assertNotIn("虎牙",header)

    def test_limited_coverage_is_visible_but_full_coverage_notes_stay_folded(self):
        with TemporaryDirectory() as tmp:
            root=Path(tmp); source=root/"input"; inputs(source)
            (source/"classification.json").write_text(json.dumps(classification_v2(),ensure_ascii=False))
            data=analysis_v2()
            data["coverage_assessment"]={
                "status":"limited", "summary":"当前只有一个任务入口案例",
                "research_question":data["research"]["question"],
                "questions":[{"id":"q-entry","question":"入口可发现性","material_ids":["mat-a"],
                              "comparison_ids":[],"strategies":["主入口独立成行"],"status":"single_case"}],
                "gaps":[{"reason":"discovery_insufficient","detail":"缺少第二个任务案例",
                         "question_ids":["q-entry"],"source_attempt_ids":[]}],
                "user_decision":{"status":"not_required","research_question":data["research"]["question"],
                                 "provenance":"not_required"},
            }
            (source/"analysis.json").write_text(json.dumps(data,ensure_ascii=False))
            run=self.formal(source,root/"out")
            self.assertEqual(run.returncode,0,run.stderr)
            html=(root/"out/report.html").read_text()
            self.assertIn("小样本方向参考",html)
            self.assertIn("当前只有一个任务入口案例",html)
            header=html[html.index('<header'):html.index('</header>')]
            self.assertNotIn("缺少第二个任务案例",header)
            methodology=html[html.index('data-module="methodology"'):html.index('data-module="synthesis"')]
            self.assertIn("缺少第二个任务案例",methodology)

    def test_insufficient_coverage_cannot_publish_when_user_chose_more_sources(self):
        with TemporaryDirectory() as tmp:
            root=Path(tmp); source=root/"input"; inputs(source)
            (source/"classification.json").write_text(json.dumps(classification_v2(),ensure_ascii=False))
            data=analysis_v2()
            data["coverage_assessment"]={
                "status":"insufficient", "summary":"核心任务缺少可比较案例",
                "research_question":data["research"]["question"],
                "questions":[{"id":"q-entry","question":"任务入口如何组织","material_ids":[],
                              "comparison_ids":[],"strategies":[],"status":"missing"}],
                "gaps":[{"reason":"discovery_insufficient","detail":"没有任务入口案例",
                         "question_ids":["q-entry"],"source_attempt_ids":[]}],
                "user_decision":{"status":"supplement_sources","research_question":data["research"]["question"],
                                 "provenance":"user_explicit"},
            }
            (source/"analysis.json").write_text(json.dumps(data,ensure_ascii=False))
            run=self.formal(source,root/"out")
            self.assertNotEqual(run.returncode,0)
            self.assertIn("不能提前生成正式报告",run.stderr)
            self.assertFalse((root/"out/report.html").exists())

    def test_v2_current_state_renders_specific_problem_region(self):
        with TemporaryDirectory() as tmp:
            root=Path(tmp); source=root/"input"; inputs(source)
            (source/"classification.json").write_text(json.dumps(classification_v2(),ensure_ascii=False))
            (source/"analysis.json").write_text(json.dumps(analysis_v2(True),ensure_ascii=False))
            run=self.formal(source,root/"out")
            self.assertEqual(run.returncode,0,run.stderr)
            html=(root/"out/report.html").read_text()
            current=html[html.index('data-module="current-state"'):html.index('data-module="gallery"')]
            self.assertIn("功能入口区",current)
            self.assertIn("多个入口以相同尺寸连续排列",current)
