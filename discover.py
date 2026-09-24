#!/usr/bin/env python3
"""Use hosted Luna for corpus discovery only; never a validation sample."""
import argparse
import json
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import urlsplit

import search_lab as lab
from validation.budget import BudgetedTransport
from validation.protocol import fingerprint


def sources(trace):
    found = {}
    def add(url, kind):
        if isinstance(url, str) and urlsplit(url).scheme in ('http', 'https'):
            found.setdefault(url, set()).add(kind)
    for response in trace.get('responses', []):
        for item in response.get('output', []):
            if item.get('type') == 'web_search_call':
                action = item.get('action', {})
                for source in action.get('sources', []):
                    add(source.get('url'), 'reported_source')
                if action.get('type') in ('open_page', 'find_in_page'):
                    add(action.get('url'), action['type'])
            for content in item.get('content', []):
                for annotation in content.get('annotations', []):
                    if annotation.get('type') == 'url_citation':
                        add(annotation.get('url'), 'answer_citation')
    return found


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--questions', required=True)
    parser.add_argument('--out-dir', required=True)
    parser.add_argument('--budget-usd', type=float, default=2)
    parser.add_argument('--allow-paid', action='store_true')
    args = parser.parse_args()
    questions = json.loads(Path(args.questions).read_text())
    if not questions or len({q['id'] for q in questions}) != len(questions):
        parser.error('Questions need unique IDs')
    if not 0 < args.budget_usd <= 100:
        parser.error('Use an explicit budget between zero and US$100')
    config = dict(model='gpt-5.6-luna', reasoning='medium', web_tool='web_search_preview',
                  snippet_chars=1200, page_chars=8000, top_k=5, max_rounds=12,
                  max_output_tokens=4096, instructions=lab.INSTRUCTIONS)
    manifest = {'purpose': 'corpus_discovery_not_validation', 'questions': questions, 'config': config}
    directory = Path(args.out_dir)
    print(json.dumps({'planned_calls': len(questions), 'paid_enabled': args.allow_paid,
                      'budget_usd': args.budget_usd}), flush=True)
    if not args.allow_paid:
        return
    path = directory / 'manifest.json'
    if path.exists() and json.loads(path.read_text()) != manifest:
        parser.error('Discovery configuration changed; use a new directory')
    lab.save(path, manifest)
    budget = BudgetedTransport(directory / 'budget.json', args.budget_usd)
    traces = []
    for question in questions:
        output = directory / 'traces' / (fingerprint(question)[:20] + '.json')
        if output.exists():
            trace = json.loads(output.read_text())
        else:
            trace = lab.run(SimpleNamespace(**config, allow_paid=True, mode='live', arm='reference',
                            question=question['question'], out=str(output), corpus=None), transport=budget)
        traces.append((question['id'], trace))
        print(json.dumps({'case': question['id'], 'status': trace['status'],
                          'reported_urls': len(sources(trace)),
                          'accounted_usd': round(budget.ledger['reserved_or_charged_usd'], 6)}), flush=True)
        if trace['status'] == 'failed':
            break
    urls = {}
    for case, trace in traces:
        for url, kinds in sources(trace).items():
            record = urls.setdefault(url, {'url': url, 'cases': [], 'observation_types': set()})
            record['cases'].append(case)
            record['observation_types'].update(kinds)
    records = [r | {'observation_types': sorted(r['observation_types'])} for _, r in sorted(urls.items())]
    lab.save(directory / 'sources.json', {'purpose': manifest['purpose'], 'sources': records,
             'planned_calls': len(questions), 'recorded_calls': len(traces),
             'completed_calls': sum(t['status'] == 'completed' for _, t in traces),
             'accounted_usd': budget.ledger['reserved_or_charged_usd'],
             'estimated_usd': sum(t['usage']['estimated_usd'] for _, t in traces),
             'notice': 'Reported sources and citations are observations, not the complete candidate set or proof of reading. Discovery questions are excluded from confirmatory validation.'})


if __name__ == '__main__':
    main()
