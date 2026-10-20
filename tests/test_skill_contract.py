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


if __name__ == "__main__":
    unittest.main()
