#!/usr/bin/env python3
"""Measure corpus coverage without confusing source URLs, citations and reads."""
import argparse
from collections import Counter
import json
from pathlib import Path
from urllib.parse import urlsplit

import search_lab as lab
from corpus_builder import clean_url


def audit(corpus, discovery):
    pages = corpus['pages']
    known = {clean_url(u) for p in pages for u in [p['url'], p.get('resolved_url', p['url'])] + p.get('aliases', [])}
    def key(url):
        p = urlsplit(url)
        return (p.hostname or '').removeprefix('www.'), p.path.rstrip('/')
    paths = {key(u) for u in known}
    grouped = {}
    for source in discovery['sources']:
        normalized = clean_url(source['url'])
        row = grouped.setdefault(normalized, {'url':normalized, 'cases':set(), 'types':set()})
        row['cases'].update(source['cases'])
        row['types'].update(source['observation_types'])
    coverage = {}
    for kind in ('reported_source', 'answer_citation', 'open_page', 'find_in_page'):
        selected = [r for r in grouped.values() if kind in r['types']]
        coverage[kind] = {'unique_urls':len(selected),
                          'exact_or_declared_alias_matches':sum(r['url'] in known for r in selected),
                          'host_path_matches':sum(key(r['url']) in paths for r in selected),
                          'outside_host_path':sorted(r['url'] for r in selected if key(r['url']) not in paths)}
    return {'pages':len(pages), 'providers':dict(Counter(p['provider'] for p in pages)),
            'pdf_documents':sum(p['extraction']['format'].startswith('pdf') for p in pages),
            'pdf_pages':sum(p['extraction'].get('pdf_pages',0) for p in pages),
            'characters':sum(len(p['text']) for p in pages),
            'source_coverage':coverage,
            'notice':'Discovery-set diagnostic only. Host/path ignores query and cannot prove identical content. Reported sources are not the complete search candidate set; citations and opens have separate denominators. More pages alone do not establish sufficiency.',
            'excluded_sources':corpus.get('excluded_sources',[])}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--corpus',required=True)
    parser.add_argument('--discovery',required=True)
    parser.add_argument('--out',required=True)
    args=parser.parse_args()
    if Path(args.out).exists():
        parser.error('Choose a new audit path')
    result=audit(json.loads(Path(args.corpus).read_text()),json.loads(Path(args.discovery).read_text()))
    lab.save(args.out,result)
    print(json.dumps({k:v for k,v in result.items() if k not in ('source_coverage','notice','excluded_sources')}))
    print(json.dumps({k:{a:b for a,b in v.items() if a!='outside_host_path'} for k,v in result['source_coverage'].items()}))


if __name__=='__main__':
    main()
