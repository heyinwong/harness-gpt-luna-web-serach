#!/usr/bin/env python3
"""Exploratory one-factor excerpt or corpus calibration; never a certificate."""
import argparse
import hashlib
import json
from pathlib import Path
import random
from types import SimpleNamespace

import search_lab as lab
from benchmark import code_hashes
from validation.budget import BudgetedTransport
from validation.metrics import extract
from validation.protocol import fingerprint, observations
from validation.statistics import mean


def compare(profile, source, candidate):
    rows=[]
    repeats=profile['repeats']
    for name,spec in profile['metrics'].items():
        values={'original_custom':[], 'candidate_custom':[], 'hosted':[]}
        for case in profile['cases']:
            groups=[source.get((case['id'],r,'custom')) for r in range(repeats)], [candidate.get((case['id'],r)) for r in range(repeats)], [source.get((case['id'],r,'live')) for r in range(repeats)]
            if all(g and name in g['scalar'] for group in groups for g in group):
                for key, group in zip(values,groups):
                    values[key].append(mean([g['scalar'][name] for g in group]))
        rows.append({'metric':name,'n_matched_questions':len(values['hosted']),
                     **{k:mean(v) if v else None for k,v in values.items()},'registered_margin':spec['margin']})
    distributions=[]
    for name,spec in profile['distributions'].items():
        values={key:[] for key in ('original_custom','candidate_custom','hosted')}
        for case in profile['cases']:
            groups=([source.get((case['id'],r,'custom')) for r in range(repeats)],
                    [candidate.get((case['id'],r)) for r in range(repeats)],
                    [source.get((case['id'],r,'live')) for r in range(repeats)])
            if all(g and name in g['vectors'] for group in groups for g in group):
                for key,group in zip(values,groups):
                    vectors=[g['vectors'][name] for g in group]
                    values[key].append([mean([v[i] for v in vectors]) for i in range(len(vectors[0]))])
        averages={k:[mean([v[i] for v in vs]) for i in range(len(vs[0]))] if vs else None for k,vs in values.items()}
        distances={k+'_vs_hosted_tv':sum(abs(x-y) for x,y in zip(averages[k],averages['hosted']))/2 if averages['hosted'] else None
                   for k in ('original_custom','candidate_custom')}
        distributions.append({'metric':name,'n_matched_questions':len(values['hosted']),
                              'registered_margin':spec['margin'],'means':averages,**distances})
    return {'verdict':'EXPLORATORY_ONLY', 'notice':'Reuses a recorded hosted reference. Selected after seeing pilot results; not a new holdout, confidence test or proof of transfer. Each row uses questions with all repetitions measurable in all three groups. Reliability rows include failures.',
            'rows':rows, 'distributions':distributions, 'candidate_runs':len(candidate),
            'candidate_statuses':{s:sum(v['details']['status']==s for v in candidate.values()) for s in {v['details']['status'] for v in candidate.values()}}}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--baseline-dir',required=True)
    p.add_argument('--out-dir',required=True)
    change=p.add_mutually_exclusive_group(required=True)
    change.add_argument('--snippet-chars',type=int)
    change.add_argument('--corpus',help='Use a repaired corpus with the original tool settings')
    change.add_argument('--runner-config',help='Explicit new-design runner settings; allows changed implementation and records its hashes')
    p.add_argument('--case-ids',nargs='+',help='Optional registered calibration cases for a targeted diagnostic')
    p.add_argument('--budget-usd',type=float,default=.25)
    p.add_argument('--allow-paid',action='store_true')
    args=p.parse_args()
    source_dir=Path(args.baseline_dir)
    source_manifest=json.loads((source_dir/'manifest.json').read_text())
    profile=source_manifest['profile']
    if profile['split']=='validation':
        p.error('Do not tune against a held-out validation set; use a pilot or calibration baseline')
    if (args.snippet_chars is not None and not 100<=args.snippet_chars<=20000) or not 0<args.budget_usd<=100:
        p.error('Invalid excerpt length or budget')
    traces=[json.loads(f.read_text()) for f in sorted((source_dir/'traces').glob('*.json'))]
    source,errors=observations(source_manifest,traces)
    if errors:
        p.error('Baseline provenance failed: '+', '.join(errors))
    corpus=source_dir/'corpus.json'
    if hashlib.sha256(corpus.read_bytes()).hexdigest()!=source_manifest['corpus_sha256']:
        p.error('Baseline corpus changed')
    config=profile['runner']|({'snippet_chars':args.snippet_chars} if args.snippet_chars is not None else {})
    if args.runner_config:
        replacement=json.loads(Path(args.runner_config).read_text())
        if set(replacement)-{'retrieval','reasoning','web_tool','snippet_chars','page_chars','top_k','max_rounds','max_output_tokens'}:
            p.error('Runner configuration contains unsupported fields')
        if any(replacement.get(k,config.get(k))!=config.get(k) for k in ('reasoning','web_tool')):
            p.error('A reused hosted reference must keep its reasoning and web tool settings')
        config.update(replacement)
    candidate_corpus=Path(args.corpus) if args.corpus else corpus
    candidate_data=json.loads(candidate_corpus.read_text())
    if candidate_data.get('failures') or candidate_data.get('quality_flags'):
        p.error('Resolve candidate corpus failures and quality flags before paid calibration')
    lab.browser_class(config.get('retrieval','window'))(candidate_data,'reference',config['snippet_chars'],config['top_k'],config['page_chars'])
    selected=[c for c in profile['cases'] if not args.case_ids or c['id'] in args.case_ids]
    if args.case_ids and set(args.case_ids)!={c['id'] for c in selected}:
        p.error('Unknown selected calibration case')
    spec={'baseline_manifest':fingerprint(source_manifest),'source_trace_hashes':[fingerprint(t) for t in traces],
          'candidate_config':config,'current_code_hashes':code_hashes(),
          'candidate_corpus_sha256':hashlib.sha256(candidate_corpus.read_bytes()).hexdigest(),
          'selected_case_ids':[c['id'] for c in selected],
          'calibration_code_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
          'notice':('One-factor snippet-length calibration; same frozen corpus and recorded hosted responses.' if not args.corpus else
                    'Corpus-repair diagnostic; original tool settings and recorded hosted responses. All changed source pages belong to this corpus factor.')}
    if args.runner_config:
        spec['notice']='New-design calibration on the same frozen corpus and questions, reusing hosted responses. Implementation and runner settings may change; this is not a one-factor causal ablation.'
    if not args.runner_config and spec['current_code_hashes']!=source_manifest['code_hashes']:
        p.error('Code differs from baseline: this command isolates excerpt length only')
    jobs=[(c,r) for c in selected for r in range(profile['repeats'])]
    random.Random(profile['seed']).shuffle(jobs)
    print(json.dumps({'paid_enabled':args.allow_paid,'candidate_runs':len(jobs),'snippet_chars':args.snippet_chars,'budget_usd':args.budget_usd}),flush=True)
    if not args.allow_paid:
        return
    directory=Path(args.out_dir)
    mf=directory/'manifest.json'
    if mf.exists() and json.loads(mf.read_text())!=spec:
        p.error('Calibration changed; use a new directory')
    lab.save(mf,spec)
    frozen_corpus=directory/'corpus.json'
    if frozen_corpus.exists() and hashlib.sha256(frozen_corpus.read_bytes()).hexdigest()!=spec['candidate_corpus_sha256']:
        p.error('Frozen candidate corpus changed')
    if not frozen_corpus.exists():
        frozen_corpus.write_bytes(candidate_corpus.read_bytes())
    budget=BudgetedTransport(directory/'budget.json',args.budget_usd)
    candidate={}
    for case,repeat in jobs:
        key={'case_id':case['id'],'repeat':repeat}
        path=directory/'traces'/(fingerprint(key)[:20]+'.json')
        if path.exists():
            trace=json.loads(path.read_text())
            if trace.get('calibration_manifest_sha256')!=fingerprint(spec):
                p.error('Candidate trace provenance mismatch')
        else:
            values=config|{'model':profile['model'],'instructions':profile['instructions'],'mode':'custom','arm':'reference',
                           'allow_paid':True,'question':case['question'],'corpus':str(frozen_corpus),'out':str(path)}
            trace=lab.run(SimpleNamespace(**values),transport=budget)
            trace.update(calibration_job=key,calibration_manifest_sha256=fingerprint(spec))
            lab.save(path,trace)
            print(json.dumps({'case':case['id'],'repeat':repeat,'status':trace['status'],'conservative_usd':round(budget.ledger['reserved_or_charged_usd'],4)}),flush=True)
        candidate[(case['id'],repeat)]=extract(trace,case,profile)
        if trace['status']=='failed':
            break
    result=compare(profile,source,candidate)
    result['manifest']=spec
    lab.save(directory/'report.json',result)
    lines=['# Exploratory calibration','',spec['notice'],'',result['notice'],'',f"Candidate statuses: {result['candidate_statuses']}",'',
           '| Metric | Original custom | Candidate custom | Hosted | Matched questions |','|---|---:|---:|---:|---:|']
    for row in result['rows']:
        numbers=['—' if row[k] is None else f"{row[k]:.3f}" for k in ('original_custom','candidate_custom','hosted')]
        lines.append('| '+row['metric']+' | '+' | '.join(numbers)+f" | {row['n_matched_questions']} |")
    (directory/'report.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps({'report':str(directory/'report.md'),'verdict':result['verdict']}),flush=True)


if __name__=='__main__':
    main()
