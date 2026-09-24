import unittest

import report
import suite


class SuiteTests(unittest.TestCase):
    def test_same_questions_have_all_arms_and_one_live_per_repeat(self):
        questions = [{"id": "one", "question": "What conditions apply?", "category": "product"}]
        jobs = suite.plan(questions, ["baseline", "inline"], 2, True, 4)
        self.assertEqual(len(jobs), 6)
        self.assertEqual(sum(j["mode"] == "live" for j in jobs), 2)
        self.assertEqual(jobs, suite.plan(questions, ["baseline", "inline"], 2, True, 4))

    def test_duplicate_question_ids_rejected(self):
        with self.assertRaises(ValueError):
            suite.plan([{"id": "same", "question": "a"}, {"id": "same", "question": "b"}], ["baseline"], 1, False, 1)

    def test_report_marks_incomplete_hosted_query_count(self):
        trace = {"mode": "live", "status": "completed", "question": "q", "metrics": {
            "search_actions": 2, "search_queries_reported": 3, "search_actions_missing_query_list": 1}}
        rendered = report.render([("trace.json", trace)])
        self.assertIn(">= 3 (incomplete)", rendered)
        self.assertIn("Hosted-search excerpts are unavailable", rendered)


if __name__ == "__main__":
    unittest.main()
