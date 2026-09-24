#!/usr/bin/env python3
"""Prepare blinded manual scoring, then summarize paired award-placement effects."""
import argparse
import json
from pathlib import Path

import search_lab as lab
from validation.protocol import fingerprint
from validation.statistics import bounded_interval, mean

CONTRASTS = [('inline', 'baseline'), ('no_link', 'baseline'), ('no_link', 'inline'),
             ('link_vague', 'inline'), ('link_descriptive', 'inline')]
RUBRIC = ('Score correct_relevant_award=1 only if the answer accurately identifies the target award '
          'and describes its relevance without presenting a service/bank award as a product-performance award. '
          'Otherwise score 0. Score unsupported_product_claim=1 if it makes that unsupported inference, else 0. '
          'Add a short evidence quote/reason. Do not infer correctness from a citation or an entity name alone. '
          'Use null until reviewed. Review without the trace-to-arm mapping; adjudicate disagreements before analysis.')


def load_suite(directory):
    directory = Path(directory)
    manifest = json.loads((directory/'manifest.json').read_text())
    expected = {fingerprint(j):j for j in manifest['jobs'] if j['mode']=='custom'}
    found = {}
    for path in directory.glob('*.json'):
        trace = json.loads(path.read_text())
        job = trace.get('suite_job')
        if not job or job['mode'] != 'custom':
            continue
        ident = fingerprint(job)
        if ident not in expected or trace.get('suite_config') != manifest['config']:
            raise ValueError('Trace does not match frozen suite')
        if ident in found:
            raise ValueError('Duplicate job trace')
        if trace.get('arm') != job['arm'] or trace.get('question') != job['question']:
            raise ValueError('Trace/job mismatch')
        found[ident] = trace
    return manifest, expected, found


def prepare(directory, corpus):
    manifest, expected, traces = load_suite(directory)
    import hashlib
    if hashlib.sha256(Path(corpus).read_bytes()).hexdigest() != manifest['config']['corpus_sha256']:
        raise ValueError('Corpus differs from the experiment snapshot')
    data = json.loads(Path(corpus).read_text())
    return {'suite_fingerprint':fingerprint(manifest), 'rubric':RUBRIC,
            'target_award':data['award_sentence'], 'planned_runs':len(expected),
            'items':[{'blind_id':key, 'question':trace['question'], 'answer':trace.get('answer',''),
                      'correct_relevant_award':None, 'unsupported_product_claim':None,
                      'reviewer':'', 'evidence':''}
                     for key,trace in sorted(traces.items())
                     if trace['status']=='completed' and not trace.get('possibly_budget_limited')]}


def summarize(directory, scores, confidence=.95):
    manifest, expected, traces = load_suite(directory)
    if scores['suite_fingerprint'] != fingerprint(manifest):
        raise ValueError('Scores belong to another suite')
    scored = {}
    for item in scores['items']:
        key = item['blind_id']
        if key in scored or key not in traces:
            raise ValueError('Duplicate or unknown scored item')
        if item.get('question') != traces[key]['question'] or item.get('answer') != traces[key].get('answer',''):
            raise ValueError('Scored answer changed')
        if any(type(item.get(field)) is not int or item[field] not in (0,1)
               for field in ('correct_relevant_award','unsupported_product_claim')):
            raise ValueError('Every included score must be manually completed as 0 or 1')
        if not item.get('reviewer','').strip() or not item.get('evidence','').strip():
            raise ValueError('Each score needs a reviewer and evidence/rationale')
        scored[key] = item
    valid = {key for key,t in traces.items() if t['status']=='completed' and not t.get('possibly_budget_limited')}
    flags = []
    if set(traces) != set(expected):
        flags.append('planned_runs_missing')
    if valid != set(expected):
        flags.append('failed_or_censored_runs')
    if set(scored) != valid:
        flags.append('scores_missing_or_ineligible')
    groups = {}
    for key, job in expected.items():
        groups.setdefault((job['id'],job['arm']), []).append(key)
    rows = []
    alpha = (1-confidence)/(len(CONTRASTS)*2)
    for left,right in CONTRASTS:
        for field in ('correct_relevant_award','unsupported_product_claim'):
            xs,ys = [],[]
            for question in sorted({j['id'] for j in expected.values()}):
                a,b = groups.get((question,left),[]),groups.get((question,right),[])
                if a and b and all(k in scored and k in valid for k in a+b):
                    xs.append(mean([scored[k][field] for k in a]))
                    ys.append(mean([scored[k][field] for k in b]))
            rows.append({'contrast':left+' minus '+right,'outcome':field,
                         'left_rate':mean(xs) if xs else None,'right_rate':mean(ys) if ys else None,
                         'difference':bounded_interval([x-y for x,y in zip(xs,ys)],-1,1,alpha)})
    return {'scope':'Effects within the controlled harness; not certified effects in ChatGPT.',
            'confidence':confidence,'assumptions':'Simultaneous bounded intervals over independent representative question clusters. Repetitions are averaged within question. Convenience samples are descriptive only.',
            'flags':flags,'planned_runs':len(expected),'recorded_runs':len(traces),'reviewed_runs':len(scored),
            'contrasts':rows,'notice':'No automatic non-inferiority claim. Prespecify a practically acceptable loss and validate the searching agent separately.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command',required=True)
    p = sub.add_parser('prepare')
    p.add_argument('--corpus',required=True)
    r = sub.add_parser('analyze')
    r.add_argument('--scores',required=True)
    for command in (p,r):
        command.add_argument('--suite-dir',required=True)
        command.add_argument('--out',required=True)
    args = parser.parse_args()
    if Path(args.out).exists():
        parser.error('Output exists; preserve the original and choose a new path')
    result = prepare(args.suite_dir,args.corpus) if args.command=='prepare' else summarize(args.suite_dir,json.loads(Path(args.scores).read_text()))
    lab.save(args.out,result)
    print(json.dumps({'output':args.out,'flags':result.get('flags',[])}))


if __name__=='__main__':
    main()
