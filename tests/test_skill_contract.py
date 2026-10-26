from pathlib import Path
import unittest


SKILL_PATH = Path(__file__).resolve().parents[1] / "SKILL.md"


class SkillContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.skill = SKILL_PATH.read_text(encoding="utf-8")

    def test_open_ended_discovery_requires_high_recall_candidate_protocol(self):
        for phrase in (
            "高召回",
            "标签搜图",
            "OCR 搜图",
            "候选登记",
            "not_reviewed",
            "连续两批",
        ):
            self.assertIn(phrase, self.skill)

    def test_auth_state_distinguishes_complete_logged_out_page_from_intercept(self):
        self.assertIn("logged_out_complete", self.skill)
        self.assertIn("login_intercept", self.skill)

    def test_competitor_count_has_only_a_fifty_item_upper_bound(self):
        for phrase in ("最多 50 个", "不设 3–5 个的小范围上限"):
            self.assertIn(phrase, self.skill)

    def test_report_uses_progressive_twenty_card_expansion(self):
        for phrase in ("一行 5 张", "初始展示 20 张", "更多", "每次展开 20 张"):
            self.assertIn(phrase, self.skill)

    def test_foreign_sources_translate_page_intent_to_local_naming_vocabulary(self):
        for phrase in (
            "海外页面命名映射",
            "Profile",
            "You",
            "Me",
            "Account",
            "My Page",
            "app.pttrns.com/patterns?categories=profile-account",
            "refero.design/apps/search?page_types",
            "mobbin.com/search/apps/ios?content_type=screens",
        ):
            self.assertIn(phrase, self.skill)

    def test_dynamic_ui_databases_use_browser_access_as_separate_source_status(self):
        for phrase in (
            "浏览器优先",
            "web_text_accessible",
            "browser_accessible",
            "browser_interactive",
            "文本抓取失败不等于来源不可用",
        ):
            self.assertIn(phrase, self.skill)

    def test_formal_entry_is_structured_and_legacy_is_bounded(self):
        for phrase in (
            "结构化 Task",
            "legacy/demo",
            "阶段中间产物",
            "正式报告",
            "离线演示",
            "--task-file",
            "--sources-file",
        ):
            self.assertIn(phrase, self.skill)

    def test_evidence_registry_and_cross_stage_links_are_explicit(self):
        for phrase in (
            "source_attempts",
            "source_candidate_id",
            "source_attempt_id",
            "source_entry_url",
            "source_detail_url",
            "source_asset_url",
            "缺失或错误引用",
            "不编造 ID",
        ):
            self.assertIn(phrase, self.skill)

    def test_report_statistics_and_historical_gap_are_explicit(self):
        for phrase in (
            "来源访问",
            "候选处置",
            "素材审核",
            "产品 fallback",
            "覆盖边界",
            "历史证据缺口",
        ):
            self.assertIn(phrase, self.skill)


if __name__ == "__main__":
    unittest.main()
