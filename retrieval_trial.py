#!/usr/bin/env python3
"""Matched window-versus-passages calibration on one frozen corpus; reuses hosted traces."""
import argparse
import hashlib
import json
from pathlib import Path
import random
from types import SimpleNamespace

import search_lab as lab
from benchmark import code_hashes
from passage_retrieval import PassageBrowser
from context_passages import ContextPassageBrowser
from validation.budget import BudgetedTransport
from validation.metrics import extract
from validation.protocol import fingerprint, observations
from validation.statistics import mean


def summarize(profile, cases, source, candidates):
    rows=[]
    for name,spec in profile['metrics'].items():
        values={key:[] for key in ('window','passages','hosted')}
        for case in cases:
            groups={key:[candidates.get((case['id'],r,key)) for r in range(profile['repeats'])]
                    for key in ('window','passages')}
            groups['hosted']=[source.get((case['id'],r,'live')) for r in range(profile['repeats'])]
            if all(g and name in g['scalar'] for group in groups.values() for g in group):
                for key,group in groups.items():
                    values[key].append(mean([g['scalar'][name] for g in group]))
        rows.append({'metric':name,'n_matched_questions':len(values['hosted']),
                     **{k:mean(v) if v else None for k,v in values.items()},'registered_margin':spec['margin']})
    distributions=[]
    for name,spec in profile['distributions'].items():
        values={key:[] for key in ('window','passages','hosted')}
        for case in cases:
            groups={key:[candidates.get((case['id'],r,key)) for r in range(profile['repeats'])]
                    for key in ('window','passages')}
            groups['hosted']=[source.get((case['id'],r,'live')) for r in range(profile['repeats'])]
            if all(g and name in g['vectors'] for group in groups.values() for g in group):
                for key,group in groups.items():
                    vectors=[g['vectors'][name] for g in group]
                    values[key].append([mean([v[i] for v in vectors]) for i in range(len(vectors[0]))])
        averages={k:[mean([v[i] for v in vs]) for i in range(len(vs[0]))] if vs else None for k,vs in values.items()}
        distributions.append({'metric':name,'n_matched_questions':len(values['hosted']),
                              'window_vs_hosted_tv':sum(abs(x-y) for x,y in zip(averages['window'],averages['hosted']))/2 if averages['hosted'] else None,
                              'passages_vs_hosted_tv':sum(abs(x-y) for x,y in zip(averages['passages'],averages['hosted']))/2 if averages['hosted'] else None,
                              'registered_margin':spec['margin'],'means':averages})
    return {'verdict':'EXPLORATORY_ONLY','rows':rows,'distributions':distributions,
            'notice':'Fresh custom window and passage trials use the same corpus and character allowance. Hosted responses are reused, not a new holdout. Means use question clusters with all repetitions measurable in all three groups. No equivalence certificate or automatic adoption.',
            'candidate_statuses':{method:{status:sum(m==method and v['details']['status']==status for (_,_,m),v in candidates.items())
                                        for status in {v['details']['status'] for v in candidates.values()}}
                                  for method in ('window','passages')}}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--baseline-dir',required=True)
    p.add_argument('--corpus',required=True)
    p.add_argument('--out-dir',required=True)
    p.add_argument('--case-ids',nargs='+')
    p.add_argument('--snippet-chars',type=int,default=3000)
    p.add_argument('--passage-version',type=int,choices=(1,2),default=1)
    p.add_argument('--budget-usd',type=float,default=2)
    p.add_argument('--allow-paid',action='store_true')
    args=p.parse_args()
    if not 100<=args.snippet_chars<=20000 or not 0<args.budget_usd<=100:
        p.error('Invalid excerpt allowance or budget')
    source_dir=Path(args.baseline_dir)
    baseline=json.loads((source_dir/'manifest.json').read_text())
    profile=baseline['profile']
    if profile['split']=='validation':
        p.error('Do not tune retrieval on a confirmatory holdout')
    traces=[json.loads(f.read_text()) for f in sorted((source_dir/'traces').glob('*.json'))]
    source,errors=observations(baseline,traces)
    if errors:
        p.error('Baseline trace provenance failed: '+', '.join(errors))
    corpus=Path(args.corpus)
    corpus_data=json.loads(corpus.read_text())
    if corpus_data.get('failures') or corpus_data.get('quality_flags'):
        p.error('Resolve corpus capture/extraction failures first')
    passage_factory=PassageBrowser if args.passage_version==1 else ContextPassageBrowser
    passage_factory(corpus_data,'reference',snippet_chars=args.snippet_chars)
    cases=[c for c in profile['cases'] if not args.case_ids or c['id'] in args.case_ids]
    if args.case_ids and set(args.case_ids)!={c['id'] for c in cases}:
        p.error('Unknown calibration case')
    config=profile['runner']|{'snippet_chars':args.snippet_chars}
    hashes=code_hashes()|{f:hashlib.sha256((lab.ROOT/f).read_bytes()).hexdigest() for f in ('passage_retrieval.py','context_passages.py','retrieval_trial.py')}
    spec={'baseline_manifest':fingerprint(baseline),'hosted_trace_hashes':[fingerprint(t) for t in traces if t['mode']=='live'],
          'corpus_sha256':hashlib.sha256(corpus.read_bytes()).hexdigest(),'config':config,'code_hashes':hashes,
          'cases':cases,'repeats':profile['repeats'],'methods':['window','passages'],'passage_version':args.passage_version,
          'notice':'Post-hoc retrieval calibration; the historical reference uses the same model, prompts and native search settings.'}
    jobs=[{'case_id':c['id'],'repeat':r,'method':method} for c in cases for r in range(profile['repeats']) for method in spec['methods']]
    random.Random(profile['seed']).shuffle(jobs)
    print(json.dumps({'planned_custom_runs':len(jobs),'paid_enabled':args.allow_paid,'budget_usd':args.budget_usd}),flush=True)
    if not args.allow_paid:
        return
    directory=Path(args.out_dir);mf=directory/'manifest.json'
    if mf.exists() and json.loads(mf.read_text())!=spec:
        p.error('Trial inputs or code changed; use a new directory')
    lab.save(mf,spec)
    frozen=directory/'corpus.json'
    if frozen.exists() and hashlib.sha256(frozen.read_bytes()).hexdigest()!=spec['corpus_sha256']:
        p.error('Frozen trial corpus changed')
    if not frozen.exists():
        frozen.write_bytes(corpus.read_bytes())
    budget=BudgetedTransport(directory/'budget.json',args.budget_usd)
    by_id={c['id']:c for c in cases};results={}
    for job in jobs:
        path=directory/'traces'/(fingerprint(job)[:20]+'.json');case=by_id[job['case_id']]
        if path.exists():
            trace=json.loads(path.read_text())
            if trace.get('retrieval_trial_manifest')!=fingerprint(spec):
                p.error('Existing trace has different provenance')
        else:
            values=config|{'model':profile['model'],'instructions':profile['instructions'],'allow_paid':True,
                           'mode':'custom','arm':'reference','question':case['question'],'corpus':str(frozen),'out':str(path)}
            factory=passage_factory if job['method']=='passages' else lab.Browser
            trace=lab.run(SimpleNamespace(**values),transport=budget,browser_factory=factory)
            trace.update(retrieval_trial_job=job,retrieval_trial_manifest=fingerprint(spec))
            lab.save(path,trace)
            print(json.dumps(job|{'status':trace['status'],'accounted_usd':round(budget.ledger['reserved_or_charged_usd'],5)}),flush=True)
        results[(job['case_id'],job['repeat'],job['method'])]=extract(trace,case,profile)
        if trace['status']=='failed':
            break
    report=summarize(profile,cases,source,results)
    report.update(planned_runs=len(jobs),recorded_runs=len(results),manifest=spec)
    lab.save(directory/'report.json',report)
    lines=['# Complementary passage calibration','',report['notice'],'',
           '| Metric | Window | Passages | Hosted | Matched questions |','|---|---:|---:|---:|---:|']
    for row in report['rows']:
        values=['—' if row[k] is None else f"{row[k]:.3f}" for k in ('window','passages','hosted')]
        lines.append('| '+row['metric']+' | '+' | '.join(values)+f" | {row['n_matched_questions']} |")
    (directory/'report.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps({'report':str(directory/'report.md'),'verdict':report['verdict']}),flush=True)


if __name__=='__main__':
    main()
