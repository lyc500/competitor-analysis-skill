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

    def test_competitor_count_is_not_capped_at_three_to_five(self):
        self.assertIn("不再限制 3–5 个", self.skill)

    def test_report_uses_progressive_twenty_card_expansion(self):
        for phrase in ("一行 5 张", "初始展示 20 张", "更多", "每次展开 20 张"):
            self.assertIn(phrase, self.skill)


if __name__ == "__main__":
    unittest.main()
