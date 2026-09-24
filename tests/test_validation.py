import copy
import json
from pathlib import Path
import random
import tempfile
import unittest

import search_lab as lab
import calibrate
from validation.budget import BudgetedTransport
from validation.metrics import extract, bin_vector
from validation.planning import required_questions
from validation.protocol import analyze, fingerprint, observations
from validation.statistics import bounded_interval, equivalence, total_variation_interval

PROFILE = json.loads((lab.ROOT / 'benchmarks/public_web_pilot.json').read_text())


def fixture_manifest():
    p = copy.deepcopy(PROFILE)
    p['cases'] = p['cases'][:1]
    p['categories'] = ['lookup']
    return {'profile': p, 'corpus_sha256': 'test', 'code_hashes': {}}


def fixture_trace(manifest, mode='custom', repeat=0):
    p = manifest['profile']
    case = p['cases'][0]
    return {'mode': mode, 'status': 'completed', 'model': p['model'],
            'reasoning': p['runner']['reasoning'], 'instructions': p['instructions'],
            'question': case['question'], 'arm': 'reference' if mode == 'custom' else None,
            'corpus_sha256': 'test' if mode == 'custom' else None,
            'config': {k:v for k,v in p['runner'].items() if k != 'reasoning'},
            'benchmark_job': {'case_id': case['id'], 'repeat': repeat, 'mode': mode},
            'benchmark_manifest_sha256': fingerprint(manifest),
            'answer': 'Python JSON [docs](https://docs.python.org/3/library/json.html)',
            'tool_events': [], 'responses': [], 'metrics': {}, 'usage': {}}


class StatisticsTests(unittest.TestCase):
    def test_zero_variance_small_sample_is_not_certainty(self):
        ci = bounded_interval([0]*12, -10, 10, .0003)
        self.assertLess(ci['low'], -.35)
        self.assertEqual(equivalence(ci, .35), 'inconclusive')
        self.assertEqual(bounded_interval([], -1, 1, .05)['estimate'], None)

    def test_large_matching_and_mismatching_samples(self):
        self.assertEqual(equivalence(bounded_interval([0]*20000, -1, 1, .001), .1), 'equivalent')
        self.assertEqual(equivalence(bounded_interval([.5]*20000, -1, 1, .001), .1), 'different')

    def test_equal_means_can_hide_disjoint_distributions(self):
        # Custom always one open; live half zero, half two: both mean one.
        a = [0, 1, 0]
        b = [.5, 0, .5]
        intervals = [bounded_interval([x-y]*20000, -1, 1, .001) for x,y in zip(a,b)]
        tv = total_variation_interval(intervals)
        self.assertEqual(tv['estimate'], 1)
        self.assertGreater(tv['low'], .9)

    def test_seeded_coverage_simulation(self):
        rng = random.Random(79)
        covered = 0
        for _ in range(300):
            ci = bounded_interval([float(rng.random() < .2) for _ in range(300)], 0, 1, .05)
            covered += ci['low'] <= .2 <= ci['high']
        self.assertGreaterEqual(covered, 285)

    def test_planning_counts_questions_not_repetitions(self):
        self.assertGreater(required_questions(0, 20, .35, .0003), 1000)
        self.assertIsNone(required_questions(0, 20, 0, .05))


class MeasurementTests(unittest.TestCase):
    def test_calibration_uses_common_complete_question_clusters(self):
        m = fixture_manifest()
        source={}
        candidate={}
        for r in range(2):
            for mode in ('custom','live'):
                trace=fixture_trace(m,mode,r)
                source[(m['profile']['cases'][0]['id'],r,mode)]=extract(trace,m['profile']['cases'][0],m['profile'])
            candidate[(m['profile']['cases'][0]['id'],r)]=source[(m['profile']['cases'][0]['id'],r,'custom')]
        report=calibrate.compare(m['profile'],source,candidate)
        self.assertEqual(report['verdict'],'EXPLORATORY_ONLY')
        self.assertTrue(all(r['n_matched_questions']==1 for r in report['rows']))
        candidate.clear()
        report=calibrate.compare(m['profile'],source,candidate)
        self.assertTrue(all(r['n_matched_questions']==0 for r in report['rows']))

    def test_batch_queries_and_failed_opens(self):
        m = fixture_manifest()
        t = fixture_trace(m)
        t['tool_events'] = [{'tool':'search', 'arguments':{'queries':['one','site:python.org two']}},
                            {'tool':'open', 'arguments':{}, 'result':{'error':'not_in_corpus'}}]
        obs = extract(t, m['profile']['cases'][0], m['profile'])
        self.assertEqual(obs['scalar']['search_queries'], 2)
        self.assertEqual(obs['scalar']['search_actions'], 1)
        self.assertEqual(obs['scalar']['open_actions'], 1)
        self.assertEqual(obs['scalar']['site_query_share'], .5)

    def test_missing_hosted_queries_is_not_zero(self):
        m = fixture_manifest()
        t = fixture_trace(m, 'live')
        t['responses'] = [{'output':[{'type':'web_search_call','action':{'type':'search'}}]}]
        obs = extract(t, m['profile']['cases'][0], m['profile'])
        self.assertNotIn('search_queries', obs['scalar'])
        self.assertNotIn('search_count_distribution', obs['vectors'])
        self.assertEqual(obs['scalar']['search_actions'], 1)

    def test_mentions_ignore_link_targets_and_use_word_boundaries(self):
        m = fixture_manifest()
        t = fixture_trace(m)
        t['answer'] = '[documentation](https://example.org/Python) JSONified'
        obs = extract(t, m['profile']['cases'][0], m['profile'])
        self.assertEqual(obs['scalar']['target_mention'], 0)
        self.assertEqual(obs['scalar']['entity_mentions'], 0)

    def test_censored_answer_is_not_selected_as_valid_behaviour(self):
        m = fixture_manifest()
        t = fixture_trace(m)
        t['possibly_budget_limited'] = True
        obs = extract(t, m['profile']['cases'][0], m['profile'])
        self.assertEqual(obs['scalar'], {'completed':1, 'budget_limited':1})

    def test_bins_include_overflow(self):
        self.assertEqual(bin_vector(0, [0,1,2]), [1,0,0,0])
        self.assertEqual(bin_vector(3, [0,1,2]), [0,0,0,1])


class ProtocolTests(unittest.TestCase):
    def test_full_pipeline_can_pass_large_matching_fixture_and_reject_gap(self):
        m = fixture_manifest()
        p = m['profile']
        p.update(split='validation', sampling='independent_representative_holdout')
        p['metrics'] = {name:copy.deepcopy(p['metrics'][name]) for name in ('completed','budget_limited','any_open')}
        p['distributions'] = {'opens':{'kind':'count','field':'open_actions','edges':[0], 'margin':.1,'description':'open/no-open'}}
        first = p['cases'][0]
        p['cases'] = [dict(first, id='synthetic_'+str(i), question='Synthetic question '+str(i)) for i in range(800)]
        template = fixture_trace(m)
        digest = fingerprint(m)
        traces = []
        for case in p['cases']:
            for mode in ('custom','live'):
                for repeat in range(2):
                    trace = copy.deepcopy(template)
                    trace.update(mode=mode, question=case['question'], benchmark_manifest_sha256=digest,
                                 benchmark_job={'case_id':case['id'],'repeat':repeat,'mode':mode})
                    traces.append(trace)
        result = analyze(m,traces)
        self.assertEqual(result['verdict'],'equivalent')
        for trace in traces:
            if trace['mode']=='custom':
                trace['tool_events']=[{'tool':'open'}]
        self.assertEqual(analyze(m,traces)['verdict'],'different')

    def test_perfect_tiny_pilot_cannot_pass(self):
        m = fixture_manifest()
        traces = [fixture_trace(m, mode, r) for mode in ('custom','live') for r in range(2)]
        result = analyze(m, traces)
        self.assertEqual(result['observed_runs'], 4)
        self.assertEqual(result['verdict'], 'inconclusive')
        self.assertIn('exploratory_split_not_confirmatory', result['flags'])

    def test_repeated_runs_are_one_question_cluster(self):
        m = fixture_manifest()
        traces = [fixture_trace(m, mode, r) for mode in ('custom','live') for r in range(2)]
        result = analyze(m, traces)
        row = next(r for r in result['rows'] if r['name']=='open_actions')
        self.assertEqual(row['n_questions'], 1)

    def test_tampering_and_duplicate_traces_rejected(self):
        m = fixture_manifest()
        t = fixture_trace(m)
        t['question'] = 'changed'
        obs, errors = observations(m, [t])
        self.assertFalse(obs)
        self.assertIn('question_or_model_mismatch', errors)
        t = fixture_trace(m)
        with self.assertRaises(ValueError):
            observations(m, [t,t])

    def test_unfinished_or_cap_exceeding_run_blocks_certificate(self):
        m = fixture_manifest()
        t = fixture_trace(m)
        t['tool_events'] = [{'tool':'open'}]*11
        result = analyze(m, [t])
        self.assertIn('values_exceed_registered_caps', result['flags'])
        self.assertIn('planned_runs_missing', result['flags'])

    def test_reference_mode_needs_no_award_roles(self):
        corpus = {'pages':[{'url':'https://example.org','title':'Docs','text':'A documented fact.'}]}
        self.assertEqual(len(lab.Browser(corpus, 'reference').pages), 1)


class BudgetTests(unittest.TestCase):
    def payload(self):
        return {'model':'gpt-5.6-luna','tools':[{'type':'web_search_preview'}],
                'reasoning':{'effort':'medium'},'max_tool_calls':8,'max_output_tokens':4096}

    def test_reservation_blocks_before_paid_call(self):
        with tempfile.TemporaryDirectory() as d:
            calls = []
            budget = BudgetedTransport(Path(d)/'budget.json', .1, lambda p: calls.append(p))
            with self.assertRaisesRegex(RuntimeError, 'reservation_blocked'):
                budget(self.payload())
            self.assertEqual(calls, [])

    def test_settlement_and_unknown_billing_resume(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d)/'budget.json'
            response = {'id':'test', 'usage':{'input_tokens':100,'output_tokens':100},'output':[]}
            budget = BudgetedTransport(path, 2, lambda p: response)
            budget(self.payload())
            self.assertAlmostEqual(budget.ledger['reserved_or_charged_usd'], .00023)
            def fail(p):
                raise RuntimeError('network failed')
            budget.transport = fail
            with self.assertRaises(RuntimeError):
                budget(self.payload())
            with self.assertRaisesRegex(ValueError, 'unknown billing'):
                BudgetedTransport(path, 2)


if __name__ == '__main__':
    unittest.main()
