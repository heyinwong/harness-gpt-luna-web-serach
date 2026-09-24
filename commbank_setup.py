#!/usr/bin/env python3
"""Build the CommBank experiment inputs; this command never calls the model API."""
import argparse
import json
from pathlib import Path
import subprocess
import sys

import search_lab as lab


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cache',default='results/commbank-cache')
    parser.add_argument('--out-dir',required=True)
    parser.add_argument('--offline',action='store_true')
    args=parser.parse_args()
    directory=Path(args.out_dir).resolve()
    if directory.exists():
        parser.error('Output already exists; use a new versioned directory')
    manifest=lab.ROOT/'corpora/commbank/sources.json'
    def run(script,arguments):
        subprocess.run([sys.executable,str(lab.ROOT/script)]+arguments,check=True)
    if not args.offline:
        run('capture_browser.py',['--manifest',str(manifest),'--cache',args.cache])
    run('corpus_builder.py',['--manifest',str(manifest),'--cache',args.cache,'--out-dir',str(directory)]+
        (['--offline'] if args.offline else []))
    profile=json.loads((lab.ROOT/'corpora/commbank/calibration.json').read_text())
    profile['snapshot_urls']=[p['url'] for p in json.loads((directory/'reference.json').read_text())['pages']]
    lab.save(directory/'calibration.json',profile)
    for name in ('award_questions.json','discovery_questions.json','validation.json'):
        (directory/name).write_bytes((lab.ROOT/'corpora/commbank'/name).read_bytes())
    print(json.dumps({'output':str(directory),'paid_calls':0,
                     'next':'Read COMMBANK_RUNBOOK.md. Successful setup is not a Luna equivalence pass.'}))


if __name__=='__main__':
    main()
