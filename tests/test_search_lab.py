import copy
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest

import search_lab as lab


CORPUS = json.loads((lab.ROOT / "sample_corpus.json").read_text())
PRODUCT = "https://example-bank.test/savings"
HUB = "https://example-bank.test/awards"


class ToolTests(unittest.TestCase):
    def test_sibling_tool_calls_cannot_follow_not_yet_observed_links(self):
        browser = lab.Browser(CORPUS, "link_descriptive")
        observation = {"pages": set(), "links": {}}
        browser.call("open", {"url": PRODUCT}, observation)
        result = browser.call("click", {"page_url": PRODUCT, "link_id": "link_1"}, observation)
        self.assertEqual(result["error"], "link_not_previously_exposed")

    def test_treatments_do_not_mutate_source(self):
        source = copy.deepcopy(CORPUS)
        for arm in lab.ARMS:
            pages = lab.make_pages(source, arm)
            self.assertEqual(HUB in pages, arm not in ("baseline", "inline"))
            self.assertEqual(CORPUS["award_sentence"] in pages[PRODUCT]["text"], arm in ("inline", "link_descriptive"))
            self.assertEqual(HUB in pages[PRODUCT]["text"], arm in ("link_vague", "link_descriptive"))
        self.assertEqual(source, CORPUS)

    def test_search_index_uses_treatment(self):
        baseline = lab.Browser(CORPUS, "baseline")
        inline = lab.Browser(CORPUS, "inline")
        query = {"queries": ['"2026 Sample Savings Service Award"']}
        self.assertEqual(baseline.call("search", query)["searches"][0]["results"], [])
        self.assertEqual(inline.call("search", query)["searches"][0]["results"][0]["url"], PRODUCT)

    def test_site_filter_and_batch_query_count(self):
        browser = lab.Browser(CORPUS, "no_link")
        result = browser.call("search", {"queries": ["site:other-bank.test savings", "site:example-bank.test awards"]})
        self.assertTrue(all("other-bank.test" in r["url"] for r in result["searches"][0]["results"]))
        self.assertEqual(browser.metrics()["search_actions"], 1)
        self.assertEqual(browser.metrics()["search_queries"], 2)

    def test_missing_page_does_not_fetch_network(self):
        browser = lab.Browser(CORPUS)
        result = browser.call("open", {"url": "https://not-in-corpus.test", "offset": 0})
        self.assertEqual(result["error"], "not_in_corpus")
        self.assertEqual(browser.metrics()["failed_opens"], 1)

    def test_click_requires_actual_link_exposure(self):
        browser = lab.Browser(CORPUS, "link_descriptive", page_chars=100)
        browser.call("open", {"url": PRODUCT, "offset": 0})
        self.assertEqual(browser.call("click", {"page_url": PRODUCT, "link_id": "link_1"})["error"], "link_not_previously_exposed")
        browser.call("find", {"url": PRODUCT, "text": "Award details"})
        self.assertEqual(browser.call("click", {"page_url": PRODUCT, "link_id": "link_1"})["url"], HUB)
        self.assertTrue(browser.metrics()["explicit_product_to_hub_follow"])

    def test_direct_open_is_not_mislabelled_as_follow(self):
        browser = lab.Browser(CORPUS, "link_vague")
        browser.call("open", {"url": PRODUCT})
        browser.call("open", {"url": HUB})
        self.assertFalse(browser.metrics()["explicit_product_to_hub_follow"])

    def test_repeated_opens_count_separately_from_unique_urls(self):
        browser = lab.Browser(CORPUS)
        for _ in range(2):
            browser.call("open", {"url": PRODUCT})
        self.assertEqual(browser.metrics()["successful_opens"], 2)
        self.assertEqual(browser.metrics()["unique_open_urls"], 1)

    def test_find_requires_exposed_page(self):
        browser = lab.Browser(CORPUS)
        self.assertEqual(browser.call("find", {"url": PRODUCT, "text": "deposit"})["error"], "page_not_previously_exposed")

    def test_invalid_batch_does_not_expose_unreturned_results(self):
        browser = lab.Browser(CORPUS)
        self.assertIn("error", browser.call("search", {"queries": ["savings", 42]}))
        self.assertEqual(browser.visible_pages, set())

    def test_page_windows_retain_full_content(self):
        browser = lab.Browser(CORPUS, page_chars=100)
        offset, pieces = 0, []
        while offset is not None:
            result = browser.call("open", {"url": PRODUCT, "offset": offset})
            pieces.append(result)
            offset = result["next_offset"]
        covered = set()
        for piece in pieces:
            covered.update(range(piece["start"], piece["end"]))
        self.assertEqual(len(covered), len(browser.pages[PRODUCT]["text"]))


class RunnerTests(unittest.TestCase):
    def test_credentials_accept_key_only_and_assignment(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / ".env"
            # Deliberately invalid test fixture, never used for a network request.
            example = "sk-" + "unit-test-fixture-not-a-real-credential"
            path.write_text(example + "\n")
            self.assertEqual(lab.load_api_key(path), example)
            path.write_text('OPENAI_API_KEY="' + example + '"\n')
            self.assertEqual(lab.load_api_key(path), example)

    def test_malformed_credentials_error_does_not_echo_content(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / ".env"
            path.write_text("PRIVATE-TEST-CONTENT\nsecond-line")
            with self.assertRaises(RuntimeError) as raised:
                lab.load_api_key(path)
            self.assertNotIn("PRIVATE-TEST-CONTENT", str(raised.exception))

    def test_missing_usage_does_not_hide_failed_run(self):
        self.assertEqual(lab.cost_estimate([{"usage": None}], "custom")["estimated_usd"], 0)

    def args(self, path, **kwargs):
        values = dict(allow_paid=True, mode="custom", corpus=str(lab.ROOT / "sample_corpus.json"),
                      arm="link_vague", snippet_chars=1200, top_k=5, page_chars=8000,
                      model="gpt-5.6-luna", reasoning="medium", question="What conditions apply?",
                      max_rounds=3, max_output_tokens=1024, web_tool="web_search_preview", out=path)
        return SimpleNamespace(**(values | kwargs))

    def response(self, output):
        return {"status": "completed", "output": output,
                "usage": {"input_tokens": 100, "output_tokens": 20}}

    def test_paid_opt_in_precedes_transport(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "Paid requests disabled"):
                lab.run(self.args(str(Path(directory) / "trace.json"), allow_paid=False),
                        lambda payload: self.fail("Network transport must not run"))

    def test_loop_preserves_reasoning_and_returns_tool_results(self):
        requests = []
        reasoning = {"type": "reasoning", "id": "r_test", "encrypted_content": "fixture", "summary": []}
        call = {"type": "function_call", "id": "fc_test", "call_id": "c_test", "name": "search",
                "arguments": json.dumps({"queries": ["savings conditions"]})}
        def transport(payload):
            requests.append(copy.deepcopy(payload))
            if len(requests) == 1:
                return self.response([reasoning, call])
            return self.response([{"type": "message", "content": [{"type": "output_text", "text": "Fixture answer"}]}])
        with tempfile.TemporaryDirectory() as directory:
            result = lab.run(self.args(str(Path(directory) / "trace.json")), transport)
        self.assertEqual(result["status"], "completed")
        self.assertIn(reasoning, requests[1]["input"])
        self.assertEqual(requests[1]["input"][-1]["type"], "function_call_output")
        self.assertEqual(result["tool_events"][0]["submitted_in_response"], 1)

    def test_round_limit_is_incomplete_not_success(self):
        call = {"type": "function_call", "call_id": "c_test", "name": "search", "arguments": '{"queries":["savings"]}'}
        with tempfile.TemporaryDirectory() as directory:
            result = lab.run(self.args(str(Path(directory) / "trace.json"), max_rounds=1), lambda p: self.response([call]))
        self.assertEqual(result["status"], "round_limit_reached")
        self.assertTrue(result["possibly_budget_limited"])
        self.assertNotIn("submitted_in_response", result["tool_events"][0])

    def test_failure_persists_completed_work(self):
        with tempfile.TemporaryDirectory() as directory:
            path = str(Path(directory) / "trace.json")
            def failing(payload):
                raise RuntimeError("API request failed (HTTP 429)")
            result = lab.run(self.args(path), failing)
            self.assertEqual(result["status"], "failed")
            self.assertTrue(Path(path).is_file())

    def test_live_missing_queries_are_not_assumed_zero(self):
        response = self.response([
            {"type": "web_search_call", "action": {"type": "search", "sources": [{"url": PRODUCT}]}},
            {"type": "web_search_call", "action": {"type": "search", "queries": ["a", "b"]}},
            {"type": "web_search_call", "status": "completed", "action": {"type": "open_page", "url": PRODUCT}},
        ])
        result = lab.hosted_metrics([response])
        self.assertEqual(result["search_queries_reported"], 2)
        self.assertEqual(result["search_actions_missing_query_list"], 1)
        self.assertEqual(result["completed_open_actions"], 1)
        self.assertEqual(result["consulted_sources"], [PRODUCT])

    def test_live_needs_no_local_corpus(self):
        with tempfile.TemporaryDirectory() as directory:
            args = self.args(str(Path(directory) / "trace.json"), mode="live", corpus="nonexistent.json")
            result = lab.run(args, lambda p: self.response([{"type": "message", "content": [{"type": "output_text", "text": "answer"}]}]))
        self.assertEqual(result["status"], "completed")

    def test_cost_includes_cached_discount_and_not_double_reasoning(self):
        response = {"usage": {"input_tokens": 100000, "input_tokens_details": {"cached_tokens": 50000},
                              "output_tokens": 5000, "output_tokens_details": {"reasoning_tokens": 4000}}}
        self.assertAlmostEqual(lab.cost_estimate([response], "custom")["estimated_usd"], .017)


if __name__ == "__main__":
    unittest.main()
