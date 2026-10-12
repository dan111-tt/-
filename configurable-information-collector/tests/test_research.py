import unittest
import json
from datetime import date
from pathlib import Path

from app.research_rules import build_general_queries, build_queries, draft_signal, extract_published_date, parse_date_value


class ResearchRulesTest(unittest.TestCase):
    def test_date_parsing_and_evidence(self):
        self.assertEqual(parse_date_value("2025-12-31T09:00:00Z"), date(2025, 12, 31))
        self.assertEqual(parse_date_value("31 décembre 2025"), date(2025, 12, 31))
        parsed, basis = extract_published_date("", "2025-12-24", "Updated 2026-01-02")
        self.assertEqual(parsed, date(2025, 12, 24))
        self.assertEqual(basis, "structured data")
        parsed, _ = extract_published_date("", "", "Published 2025-12-24; effective 2026-01-01")
        self.assertIsNone(parsed)  # two visible dates must not be guessed
        parsed, basis = extract_published_date("2025-12-24", "2025-12-25", "")
        self.assertIsNone(parsed)
        self.assertIn("conflicting", basis)

    def test_draft_signal_languages(self):
        self.assertTrue(draft_signal("Draft Bill on wage setting"))
        self.assertTrue(draft_signal("Projet de loi relatif au climat"))
        self.assertTrue(draft_signal("征求意见稿"))
        self.assertFalse(draft_signal("Income Tax Amendment Act, 2025"))

    def test_query_plan_covers_jurisdictions_and_clusters(self):
        requested = ["南非", "赞比亚"]
        sources = [
            {"country": "South Africa", "host": "gov.za", "level": "P0"},
            {"country": "Zambia", "host": "parliament.gov.zm", "level": "P0"},
        ]
        queries = build_queries(requested, sources, [], [], date(2025, 11, 30), date(2025, 12, 31))
        self.assertEqual(len(queries), 6)
        self.assertEqual({q["country"] for q in queries}, set(requested))
        self.assertEqual({q["cluster"] for q in queries}, {"laws_and_gazettes", "construction_telecom_procurement", "investment_labor_tax_compliance"})
        self.assertTrue(all("after:2025-11-29" in q["query"] and "before:2026-01-01" in q["query"] for q in queries))
        self.assertTrue(all(q.get("domains") for q in queries))
        sa_legal = next(q["query"] for q in queries if q["country"] == "南非" and q["cluster"] == "laws_and_gazettes")
        self.assertIn("Government Gazette", sa_legal)
        custom = build_queries(["南非"], sources[:1], ["建设工程行业、海外投资、金融、劳动等"], [], date(2025, 12, 1), date(2025, 12, 31))
        topical = [q for q in custom if q["cluster"] != "laws_and_gazettes"]
        self.assertTrue(all(any(term in q["query"] for term in ("construction", "foreign investment", "employment", "tax")) for q in topical))

    def test_general_query_plan_uses_only_user_task_values(self):
        regions = ["日本", "马来西亚"]
        industries = ["新能源", "储能"]
        scope = ["正式政策", "并网规定"]
        domains = ["energy.go.jp"]
        queries = build_general_queries(regions, industries, scope, ["battery storage"], date(2026, 9, 1), date(2026, 9, 30), domains)
        self.assertEqual(len(queries), 6)
        self.assertEqual({q["region"] for q in queries}, set(regions))
        self.assertEqual({q["cluster"] for q in queries}, {"industry_scope", "industry", "scope"})
        self.assertTrue(all(q["domains"] == domains for q in queries))
        all_queries = " ".join(q["query"] for q in queries)
        for term in [*regions, *industries, *scope, "battery storage"]:
            self.assertIn(term, all_queries)
        self.assertIn("after:2026-08-31", all_queries)
        self.assertIn("before:2026-10-01", all_queries)
        self.assertNotIn("通信工程", all_queries)

    def test_general_query_can_search_without_fixed_domain_or_sector_defaults(self):
        queries = build_general_queries(["肯尼亚"], ["农业"], ["灌溉政策"], [], date(2026, 1, 1), date(2026, 1, 2))
        self.assertTrue(all(q["domains"] == [] for q in queries))
        self.assertTrue(all('"肯尼亚"' in q["query"] for q in queries))
        self.assertTrue(any("农业" in q["query"] and "灌溉政策" in q["query"] for q in queries))

    def test_report_regression_cases(self):
        data=json.loads((Path(__file__).parent/"regression_cases.json").read_text(encoding="utf-8"))
        start,end=map(date.fromisoformat,data["window"])
        for item in data["expected_in_window"]:
            published=date.fromisoformat(item["published_date"])
            self.assertTrue(start <= published <= end, item["title"])
            self.assertFalse(draft_signal(item["title"]), item["title"])
        for item in data["expected_excluded"]:
            published=date.fromisoformat(item["published_date"])
            if item["reason"]=="draft":
                self.assertTrue(draft_signal(item["title"]), item["title"])
            else:
                self.assertFalse(start <= published <= end, item["title"])
                self.assertTrue(start <= date.fromisoformat(item["effective_date"]) <= end)


if __name__ == "__main__":
    unittest.main()
