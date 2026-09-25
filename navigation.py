"""Public-page navigation with an append-only, untreated response cache.

Search remains on its frozen seed index. Each redirect is intercepted before its
body is requested, so an experiment page cannot bypass its local treatment.
"""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlsplit, unquote
from urllib.request import Request, build_opener, HTTPRedirectHandler

from search_lab import canonical

MAX_BYTES = 8_000_000
MAX_REDIRECTS = 10


def control_key(url):
    """Controlled documents are invariant to scheme, www, trailing slash and query.

    Apply this only to explicitly registered experimental pages/aliases. Ordinary
    background URLs retain functional query parameters.
    """
    p = urlsplit(canonical(url))
    if p.port not in (None, 80, 443):
        raise ValueError('Only standard HTTP(S) ports are supported')
    return p.hostname.removeprefix('www.'), p.path.rstrip('/') or '/'


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def fetch_response(url):
    from validation.snapshot import public_url
    public_url(url)  # Validate every hop; never send cookies or credentials.
    request = Request(url, headers={'User-Agent': 'LunaSearchHarness/1.0 (public page capture)',
                                   'Accept': 'text/html,application/pdf,text/plain'})
    try:
        response = build_opener(NoRedirect()).open(request, timeout=25)
    except HTTPError as exc:
        response = exc  # Preserve real HTTP errors and Location without auto-following.
    with response:
        status = response.code
        raw = response.read(MAX_BYTES + 1) if 200 <= status < 300 else b''
        if len(raw) > MAX_BYTES:
            raise ValueError('response_too_large')
        return {'status': status, 'location': response.headers.get('Location'),
                'content_type': response.headers.get_content_type(),
                'charset': response.headers.get_content_charset() or 'utf-8', 'body': raw}


def parse_response(response, url):
    from corpus_builder import html_page, pdf_page
    raw = response['body']; kind = response['content_type']
    if kind in ('text/html', 'application/xhtml+xml'):
        page = html_page(raw.decode(response['charset'], errors='replace'), url)
    elif kind == 'application/pdf':
        page = pdf_page(raw, url)
    elif kind in ('text/plain', 'text/markdown'):
        page = {'title': url, 'text': raw.decode(response['charset'], errors='replace'), 'anchors': {}}
    else:
        raise ValueError('unsupported_content_type')
    if len(page['text'].strip()) < 80:
        raise ValueError('insufficient_extracted_text')
    page.update(url=url, retrieved_at=datetime.now(timezone.utc).isoformat(),
                content_sha256=hashlib.sha256(raw).hexdigest())
    return page


class PublicNavigator:
    def __init__(self, cache, mode, local_lookup, fetcher=fetch_response):
        if mode not in ('live', 'replay'):
            raise ValueError('Unknown navigation mode')
        self.cache = Path(cache); self.mode = mode; self.lookup = local_lookup
        self.fetcher = fetcher; self.reads = []
        self.parser_hash = hashlib.sha256(Path(__file__).with_name('corpus_builder.py').read_bytes()).hexdigest()
        if mode == 'live':
            self.cache.mkdir(parents=True, exist_ok=True)

    def record(self, url):
        key = hashlib.sha256(url.encode()).hexdigest()
        path = self.cache / (key + '.json'); raw_path = self.cache / (key + '.bin')
        if not path.exists():
            if self.mode == 'replay':
                return {'error': 'cache_miss', 'url': url}
            lock = self.cache / (key + '.lock')
            try:
                lock.mkdir()
            except FileExistsError:
                return {'error': 'cache_busy', 'url': url}
            try:
                # Recheck after acquiring the per-URL writer lock.
                if not path.exists():
                    entry = {'version': 1, 'url': url, 'parser_sha256': self.parser_hash,
                             'captured_at': datetime.now(timezone.utc).isoformat()}
                    try:
                        response = self.fetcher(url)
                        entry.update({k: v for k, v in response.items() if k != 'body'})
                        raw = response['body']
                        entry['raw_sha256'] = hashlib.sha256(raw).hexdigest()
                        if response['status'] in (301, 302, 303, 307, 308):
                            if not response.get('location'):
                                entry['error'] = 'redirect_without_location'
                        elif not 200 <= response['status'] < 300:
                            entry['error'] = 'http_error'
                        else:
                            try:
                                entry['page'] = parse_response(response, url)
                            except Exception as exc:
                                entry.update(error='extraction_error', error_type=type(exc).__name__)
                        raw_path.write_bytes(raw)
                    except (URLError, TimeoutError, OSError) as exc:
                        entry.update(error='network_error', error_type=type(exc).__name__)
                    except ValueError as exc:
                        entry.update(error='fetch_rejected', error_type=str(exc))
                    temp = path.with_suffix('.tmp')
                    temp.write_text(json.dumps(entry, ensure_ascii=False, sort_keys=True))
                    temp.replace(path)
            finally:
                lock.rmdir()
        data = path.read_bytes(); entry = json.loads(data)
        if entry.get('url') != url or entry.get('version') != 1 or entry.get('parser_sha256') != self.parser_hash:
            raise RuntimeError('Navigation cache format/parser mismatch; use its frozen code or a new cache')
        if entry.get('raw_sha256') and (not raw_path.exists() or hashlib.sha256(raw_path.read_bytes()).hexdigest() != entry['raw_sha256']):
            raise RuntimeError('Navigation cache body hash mismatch')
        digest = hashlib.sha256(data).hexdigest()
        self.reads.append({'url': url, 'record': key + '.json', 'record_sha256': digest,
                           'raw_sha256': entry.get('raw_sha256')})
        return entry | {'record_sha256': digest}

    def load(self, requested):
        url = canonical(requested); fragment = unquote(urlsplit(requested).fragment)
        visited = set(); hops = []
        for _ in range(MAX_REDIRECTS + 1):
            local = self.lookup(url)  # Also intercept cached redirects before returning text.
            if local is not None:
                return local | {'navigation': {'requested_url': requested, 'hops': hops}, 'fragment': fragment}
            if url in visited:
                return {'error': 'redirect_loop', 'url': url, 'navigation': {'hops': hops}}
            visited.add(url)
            entry = self.record(url)
            hops.append({'url': url, 'status': entry.get('status'), 'record_sha256': entry.get('record_sha256')})
            if entry.get('error'):
                return {'error': entry['error'], 'url': url, 'http_status': entry.get('status'),
                        'navigation': {'requested_url': requested, 'hops': hops}}
            if entry['status'] in (301, 302, 303, 307, 308):
                destination = urljoin(url, entry['location'])
                if urlsplit(destination).fragment:
                    fragment = unquote(urlsplit(destination).fragment)
                url = canonical(destination)
                continue
            page = dict(entry['page'])
            page['navigation_source'] = {'kind': 'cached_public_page', 'record_sha256': entry['record_sha256'],
                                         'content_sha256': page['content_sha256']}
            return {'page': page, 'fragment': fragment,
                    'navigation': {'requested_url': requested, 'hops': hops}}
        return {'error': 'redirect_limit', 'url': url, 'navigation': {'hops': hops}}


def navigation_summary(traces):
    """Diagnostic counts; hosted completion metadata does not prove HTTP success."""
    from collections import Counter
    custom = [t for t in traces if t.get('mode') == 'custom']
    events = [e for t in custom for e in t.get('tool_events', []) if e['tool'] in ('open', 'click')]
    errors = Counter(e['output']['error'] for e in events if 'error' in e['output'])
    records = {r['record_sha256'] for t in custom for r in t.get('navigation_reads', [])}
    # The first frozen pilot recorded per-hop hashes before the dedicated trace field.
    records.update(h['record_sha256'] for e in events
                   for h in e['output'].get('navigation', {}).get('hops', []) if h.get('record_sha256'))
    return {'custom_answers': len(custom), 'open_attempts': len(events),
            'successful_opens': sum('error' not in e['output'] for e in events),
            'failure_types': dict(errors),
            'unexposed_url_attempts': sum(e.get('url_provenance') == 'unexposed_url' for e in events),
            'http_404_opens': sum(e['output'].get('http_status') == 404 for e in events),
            'public_response_records_read': len(records),
            'notice': 'Open-attempt equivalence is not successful-read equivalence. The search seed is fixed; live navigation can grow the shared untreated cache. Hosted HTTP success is not assumed from tool completion.'}
