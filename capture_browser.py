#!/usr/bin/env python3
"""Render explicitly selected public pages using Playwright CLI; keep captures private."""
import argparse
import base64
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess

import search_lab as lab
from validation.snapshot import public_url


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', required=True)
    parser.add_argument('--cache', required=True)
    args = parser.parse_args()
    entries = [e for e in json.loads(Path(args.manifest).read_text())['sources'] if e.get('capture_mode') == 'browser']
    prefix = ['npx', '--yes', '--package', '@playwright/cli', 'playwright-cli', '--session=corpus-capture']
    opened = subprocess.run(prefix + ['open', 'about:blank'], capture_output=True, text=True)
    if opened.returncode:
        raise SystemExit('Could not launch Playwright CLI; install Node/npm and Chrome first.')
    cache = Path(args.cache) / 'browser'
    cache.mkdir(parents=True, exist_ok=True)
    failures = []
    for entry in entries:
        url = entry['url']
        public_url(url)
        key = hashlib.sha256(url.encode()).hexdigest()
        target = cache / (key + '.json')
        if target.exists():
            continue
        if url.split('?')[0].endswith('.pdf'):
            code = 'async (page) => { const r = await page.request.get(' + json.dumps(url) + '); return {url:r.url(),status:r.status(),pdf:(await r.body()).toString("base64")}; }'
        else:
            # DOM captures keep source markup after client rendering. No application,
            # login, cookie-consent, CAPTCHA or account-opening actions are performed.
            code = ('async (page) => { const r = await page.goto(' + json.dumps(url) +
                    ', {waitUntil:"domcontentloaded"}); await page.waitForLoadState("networkidle",{timeout:10000}).catch(()=>{}); '
                    'return {url:page.url(),status:r.status(),html:await page.content()}; }')
        result = subprocess.run(prefix + ['run-code', code], capture_output=True, text=True, timeout=100)
        try:
            if result.returncode or '### Result\n' not in result.stdout:
                raise ValueError('Browser did not return a capture')
            data = json.JSONDecoder().raw_decode(result.stdout.split('### Result\n', 1)[1])[0]
            public_url(data['url'])
            if data['status'] != 200:
                raise ValueError('Browser HTTP status ' + str(data['status']))
            raw = base64.b64decode(data['pdf']) if 'pdf' in data else data['html'].encode()
            if 'pdf' in data and not raw.startswith(b'%PDF'):
                raise ValueError('Response is not a PDF')
            meta = {'url':url, 'resolved_url':data['url'], 'content_type':'application/pdf' if 'pdf' in data else 'text/html',
                    'capture_method':'playwright_browser_response' if 'pdf' in data else 'playwright_rendered_dom',
                    'retrieved_at':datetime.now(timezone.utc).isoformat(),
                    'content_sha256':hashlib.sha256(raw).hexdigest()}
            (cache / (key + '.bin')).write_bytes(raw)
            lab.save(target, meta)
            print(json.dumps({'url':url, 'captured_bytes':len(raw)}), flush=True)
        except (ValueError, KeyError) as exc:
            failures.append({'url':url, 'error':str(exc)})
            print(json.dumps(failures[-1]), flush=True)
    subprocess.run(prefix + ['close'], capture_output=True, text=True)
    lab.save(cache / 'capture-status.json', {'failures':failures})
    if failures:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
