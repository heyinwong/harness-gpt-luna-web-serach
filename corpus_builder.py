#!/usr/bin/env python3
"""Capture a declared HTML/PDF corpus with provenance; rebuild offline from its cache."""
import argparse
import concurrent.futures
import copy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import threading
from urllib.parse import parse_qsl, urlencode, urljoin, urlsplit, urlunsplit
from urllib.request import Request, build_opener

from bs4 import BeautifulSoup, NavigableString, Comment
import search_lab as lab
from validation.snapshot import PublicRedirect, public_url

VERSION = 'structured-corpus-v1'
TRACKING = {'ei', 'cid', 'ocid', 'gclid', 'fbclid'}
PDF_LOCK = threading.Lock()  # MuPDF/table extraction is not thread-safe.


def clean_url(url):
    """Only declared tracking parameters are removed; functional query values survive."""
    p = urlsplit(lab.canonical(url))
    query = urlencode([(k, v) for k, v in parse_qsl(p.query, keep_blank_values=True)
                       if k.lower() not in TRACKING and not k.lower().startswith('utm_')])
    return urlunsplit((p.scheme, p.netloc, p.path, query, ''))


def html_page(raw, url, selectors=None):
    soup = BeautifulSoup(raw, 'html.parser')
    title = soup.title.get_text(' ', strip=True) if soup.title else url
    for node in soup.select('script,style,noscript,nav,form,svg,iframe'):
        node.decompose()
    if selectors:
        roots = soup.select(','.join(selectors))
        if not roots:
            raise ValueError('Declared content selector no longer matches')
    else:
        # Preserve legal/footnote regions outside main; header/footer menus are not evidence.
        root = soup.find('main') or soup.find(attrs={'role': 'main'})
        # Product/award pages often contain many article cards. Selecting the first
        # article silently discards the rest of the document and its conditions.
        articles = soup.find_all('article')
        if root is None and len(articles) == 1 and soup.find('h1') in articles[0].descendants:
            root = articles[0]
        roots = [root] if root else [soup.body or soup]
        if root:
            roots += soup.select('[role="doc-endnotes"],.lower-section-container,#terms')
    roots = [r for r in roots if not any(parent is other for parent in r.parents for other in roots)]
    for root in roots:
        for node in root.select('header,footer,.commbank-header,.commbank-footer,.skip-links-module,.page-lockout'):
            node.decompose()
    anchors = []
    table_count = 0
    def render(node):
        nonlocal table_count
        if isinstance(node, Comment):
            return ''
        if isinstance(node, NavigableString):
            return re.sub(r'\s+', ' ', str(node))
        name = node.name
        anchor = node.get('id') or (node.get('name') if name == 'a' else None)
        prefix = ''
        if anchor:
            prefix = f'\ue000{len(anchors)}\ue001'
            anchors.append(anchor)
        if name == 'br':
            return prefix + '\n'
        if name == 'img':
            alt = node.get('alt', '').strip()
            return prefix + (f' [Image: {alt}] ' if alt else '')
        if name == 'table':
            table_count += 1
            rows = []
            for row in node.find_all('tr'):
                cells = []
                for cell in row.find_all(['th', 'td'], recursive=False):
                    value = ''.join(render(c) for c in cell.children).strip().replace('\n', ' / ').replace('|', '\\|')
                    span = int(cell.get('colspan', 1))
                    row_span = int(cell.get('rowspan', 1))
                    if span > 1 or row_span > 1:
                        value += f' [spans {span} columns, {row_span} rows]'
                    cells.append(value)
                if cells:
                    rows.append('| ' + ' | '.join(cells) + ' |')
            return prefix + '\n\n[Source table; row order preserved]\n' + '\n'.join(rows) + '\n\n'
        body = ''.join(render(c) for c in node.children)
        if name == 'a' and node.get('href'):
            target = urljoin(url, node['href'])
            if urlsplit(target).scheme in ('http', 'https') and body.strip():
                body = '[' + body.strip().replace(']', '\\]') + '](' + target.replace(' ', '%20').replace(')', '%29') + ')'
        if name in ('h1', 'h2', 'h3', 'h4', 'h5', 'h6'):
            body = '\n\n' + '#' * int(name[1]) + ' ' + body.strip() + '\n\n'
        elif name == 'li':
            body = '\n- ' + body.strip() + '\n'
        elif name in ('p', 'div', 'section', 'aside', 'article', 'main', 'ul', 'ol', 'details', 'summary', 'blockquote'):
            body = '\n\n' + body.strip() + '\n\n'
        return prefix + body
    text = '\n\n'.join(render(r) for r in roots)
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r' *\n *', '\n', text)
    text = re.sub(r'\n{3,}', '\n\n', text).strip()
    offsets, chunks, cursor, length = {}, [], 0, 0
    for match in re.finditer('\ue000(\\d+)\ue001', text):
        chunk = text[cursor:match.start()]
        chunks.append(chunk)
        length += len(chunk)
        offsets.setdefault(anchors[int(match.group(1))], length)
        cursor = match.end()
    chunks.append(text[cursor:])
    text = ''.join(chunks)
    return {'title': title, 'text': text, 'anchors': offsets,
            'extraction': {'format': 'html_structured_text', 'tables': table_count,
                           'notice': 'Includes static DOM and collapsed content; does not model viewport visibility or execute scripts.'}}


def pdf_page(raw, url, split_spreads=False):
    import fitz
    with fitz.open(stream=raw, filetype='pdf') as doc:
        text, anchors = '', {}
        warnings = []
        for index, page in enumerate(doc):
            anchors[f'page={index + 1}'] = len(text)
            clips = [page.rect]
            if split_spreads and page.rect.width > page.rect.height:
                clips = [fitz.Rect(0, 0, page.rect.width/2, page.rect.height),
                         fitz.Rect(page.rect.width/2, 0, page.rect.width, page.rect.height)]
            extracted_parts = []
            for part, clip in enumerate(clips):
                # Keep the PDF's text-block order within each printed page. Sorting
                # individual lines by y mixes adjacent columns on these booklets.
                extracted_parts.append(('### Printed page panel ' + str(part+1) + '\n\n' if len(clips)>1 else '') +
                                       page.get_text(clip=clip, sort=False).strip())
                finder = page.find_tables(clip=clip)
                for table in finder.tables:
                    rows = table.extract()
                    rendered = ['| ' + ' | '.join((cell or '[blank or graphical cell; check original PDF]').replace('\n', ' / ')
                                                for cell in row) + ' |' for row in rows]
                    extracted_parts.append('[Detected table; empty cells may contain graphics]\n' + '\n'.join(rendered))
            extracted = '\n\n'.join(extracted_parts)
            if len(extracted) < 40:
                warnings.append(f'pdf_page_{index+1}_sparse_text')
            text += f'\n\n## PDF page {index + 1}\n\n{extracted}\n'
            links = sorted({link['uri'] for link in page.get_links() if link.get('uri', '').startswith(('https://', 'http://'))})
            if links:
                text += '\n' + '\n'.join(f'[PDF hyperlink]({u})' for u in links) + '\n'
        return {'title': doc.metadata.get('title') or urlsplit(url).path.rsplit('/', 1)[-1],
                'text': text, 'anchors': anchors,
                'extraction': {'format': 'pdf_text_blocks_and_tables', 'pdf_pages': len(doc), 'split_spreads': split_spreads,
                               'warnings': warnings,
                               'notice': 'PDF text order is approximate; visually review tables before relying on numerical comparisons.'}}


def capture(entry, cache, offline=False):
    url = entry['url']
    if entry.get('capture_mode') == 'browser':
        cache = cache / 'browser'
        offline = True
    key = hashlib.sha256(url.encode()).hexdigest()
    metadata_path = cache / (key + '.json')
    raw_path = cache / (key + '.bin')
    try:
        if metadata_path.exists() and raw_path.exists():
            meta, raw = json.loads(metadata_path.read_text()), raw_path.read_bytes()
            if hashlib.sha256(raw).hexdigest() != meta['content_sha256']:
                raise ValueError('Cached response hash mismatch')
        elif offline:
            raise ValueError('Source is absent from offline cache')
        else:
            public_url(url)
            request = Request(url, headers={'User-Agent': 'LunaSearchValidation/1.0 (public research snapshot)'})
            with build_opener(PublicRedirect()).open(request, timeout=45) as response:
                resolved = public_url(response.url)
                raw = response.read(15000001)
                if len(raw) > 15000000:
                    raise ValueError('Source exceeds 15MB limit')
                meta = {'url': url, 'resolved_url': resolved, 'content_type': response.headers.get_content_type(),
                        'retrieved_at': datetime.now(timezone.utc).isoformat(),
                        'content_sha256': hashlib.sha256(raw).hexdigest()}
            cache.mkdir(parents=True, exist_ok=True)
            raw_path.write_bytes(raw)
            lab.save(metadata_path, meta)
        kind = meta['content_type']
        if raw.startswith(b'%PDF'):
            with PDF_LOCK:
                page = pdf_page(raw, meta['resolved_url'], entry.get('split_spreads', False))
        elif kind in ('text/html', 'application/xhtml+xml'):
            page = html_page(raw, meta['resolved_url'], entry.get('selectors'))
        else:
            raise ValueError('Unsupported content type: ' + kind)
        if len(page['text'].strip()) < 200:
            raise ValueError('Extracted content too short')
        for required in entry.get('required_text', []):
            if required.lower() not in page['text'].lower():
                raise ValueError('Required source phrase missing: ' + required)
        issues = list(page['extraction'].get('warnings', []))
        visible_text = lab.LINK.sub(lambda match: match.group(1), page['text'])
        if entry.get('require_numeric_rate') and not re.search(r'\d(?:[.\d]*)\s*%', visible_text):
            issues.append('declared_rate_page_has_no_numeric_percentage')
        if re.search(r'\{\{|\bBVAR[#_]|enable javascript to (?:continue|view)|rate of\s*%\s*p\.?a', page['text'], re.I):
            issues.append('unresolved_template_or_javascript_content')
        reviewed = []
        for review in entry.get('quality_reviews', []):
            if (review.get('content_sha256') == meta['content_sha256'] and review.get('reason')
                    and review.get('flag') in issues):
                issues.remove(review['flag'])
                reviewed.append(review)
        page.update(meta, provider=entry['provider'], category=entry['category'],
                    selection_reason=entry.get('reason', ''), aliases=entry.get('aliases', []),
                    fetch_status='ok', extraction_version=VERSION, quality_flags=issues, quality_reviews=reviewed)
        if meta['resolved_url'] != url:
            page['aliases'] = sorted(set(page['aliases'] + [meta['resolved_url']]))
        return page
    except Exception as exc:
        return {'url': url, 'provider': entry['provider'], 'fetch_status': 'failed',
                'error_type': type(exc).__name__, 'error': str(exc)}


def link_audit(pages):
    by_clean = {clean_url(p['url']): p for p in pages}
    for page in pages:
        for alias in page.get('aliases', []):
            by_clean.setdefault(clean_url(alias), page)
    counts, missing = {}, {}
    for page in pages:
        for match in lab.LINK.finditer(page['text']):
            target = urljoin(page['url'], match.group(2))
            if urlsplit(target).scheme not in ('http', 'https'):
                continue
            key = clean_url(target)
            if key in by_clean:
                dest = by_clean[key]
                alias = lab.canonical(target)
                if alias != dest['url'] and alias not in dest.setdefault('aliases', []):
                    dest['aliases'].append(alias)
                counts[page['url']] = counts.get(page['url'], 0) + 1
            else:
                missing.setdefault(key, set()).add(page['url'])
    return {'in_corpus_link_occurrences': sum(counts.values()),
            'outside_corpus_urls': [{'url': u, 'referring_pages': len(v)} for u, v in sorted(missing.items())],
            'notice': 'Navigation/application/unrelated links remain visible and can be outside scope. No silent network fallback.'}


def treatments(reference, target_url, award_text):
    result = copy.deepcopy(reference)
    product = next(p for p in result['pages'] if p['url'] == target_url)
    product['role'] = 'product'
    product['original_snapshot'] = {'text': product['text'], 'anchors': copy.deepcopy(product['anchors'])}
    if product['text'].count(award_text) != 1:
        raise ValueError('Expected exactly one existing target award footnote; review changed source')
    index = product['text'].index(award_text)
    # Remove its entire standalone footnote paragraph, including the superscript marker.
    start = product['text'].rfind('\n\n', 0, index) + 2
    end = product['text'].find('\n\n', index)
    if end < 0:
        end = len(product['text'])
    removed = product['text'][start:end]
    if re.sub(r'^\s*3\s*', '', removed).strip() != award_text.strip():
        raise ValueError('Award is no longer an isolated footnote; manual intervention design required')
    lab.replace_span(product, start, end, '')
    heading = re.search(r'^# [^\n]+\n', product['text'], re.M)
    if not heading:
        raise ValueError('No main heading found for declared prominent placement')
    lab.replace_span(product, heading.end(), heading.end(), '\n{{AWARD_BLOCK}}\n')
    hub_url = 'https://www.commbank.com.au/research-experiment-awards.html'
    if any(p['url'] == hub_url for p in result['pages']):
        raise ValueError('Counterfactual hub collides with a captured page')
    result['pages'].append({'url': hub_url, 'title': 'CommBank digital banking award', 'role': 'hub',
                           'provider': 'CommBank', 'category': 'counterfactual_award_hub',
                           'synthetic': True, 'anchors': {},
                           'text': '# CommBank digital banking award\n\n' + award_text +
                           '\n\nThis is a bank-level digital banking award, not a savings account interest-rate or product-performance award.',
                           'provenance': {'derived_from': target_url,
                                          'notice': 'Local counterfactual page; not claimed to exist on the public website.'}})
    result.update(kind='controlled_interventions', award_sentence=award_text,
                  description='Controlled CommBank award placements in an observed multi-provider corpus; includes a local counterfactual hub.',
                  intervention={'target_url': target_url, 'placement': 'immediately after source H1',
                                'original_footnote_offset': index, 'original_footnote_fraction': index / len(product['original_snapshot']['text']),
                                'arms': list(lab.EXPERIMENT_ARMS),
                                'notice': 'Only the target page award paragraph and hub availability change. Other source awards remain fixed; baseline is not globally award-free.'})
    for arm in lab.EXPERIMENT_ARMS:
        lab.Browser(result, arm)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', required=True)
    parser.add_argument('--cache', required=True)
    parser.add_argument('--out-dir', required=True)
    parser.add_argument('--offline', action='store_true')
    args = parser.parse_args()
    directory = Path(args.out_dir)
    if directory.exists():
        parser.error('Output exists; preserve frozen corpora and choose a new directory')
    manifest = json.loads(Path(args.manifest).read_text())
    entries = manifest['sources']
    if len({p['url'] for p in entries}) != len(entries):
        parser.error('Duplicate manifest URLs')
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        captured = list(pool.map(lambda e: capture(e, Path(args.cache), args.offline), entries))
    pages = [p for p in captured if p['fetch_status'] == 'ok']
    failed = [p for p in captured if p['fetch_status'] != 'ok']
    # Resolved duplicates are one search document, with all observed entry URLs as aliases.
    unique = {}
    for page in pages:
        key = clean_url(page['resolved_url'])
        if key in unique:
            unique[key]['aliases'] += [page['url']] + page.get('aliases', [])
        else:
            unique[key] = page
    pages = list(unique.values())
    links = link_audit(pages)
    reference = {'kind': 'observed_reference', 'description': manifest['scope'], 'pages': pages,
                 'failures': failed, 'manifest_sha256': hashlib.sha256(Path(args.manifest).read_bytes()).hexdigest(),
                 'quality_flags': [{'url':p['url'],'flags':p['quality_flags']} for p in pages if p['quality_flags']],
                 'excluded_sources': manifest.get('excluded_sources', []),
                 'extraction_version': VERSION}
    lab.Browser(reference, 'reference')
    lab.save(directory / 'reference.json', reference)
    audit = {'scope': manifest['scope'], 'pages': len(pages), 'requested_sources': len(entries),
             'excluded_sources': manifest.get('excluded_sources', []),
             'failures': failed, 'links': links,
             'sources': [{k: p[k] for k in ('url', 'resolved_url', 'provider', 'category', 'content_sha256', 'retrieved_at', 'quality_flags', 'quality_reviews', 'extraction')}
                         | {'characters': len(p['text']), 'anchors': len(p['anchors']),
                            'award_mentions': len(re.findall(r'\baward\w*\b', p['text'], re.I)),
                            'target_award_occurrences': p['text'].count(manifest['award_text'])}
                        for p in pages]}
    lab.save(directory / 'audit.json', audit)
    if failed:
        print(json.dumps({'pages': len(pages), 'failures': failed, 'ready': False}))
        raise SystemExit(1)
    if any(p['quality_flags'] for p in pages):
        print(json.dumps({'pages': len(pages), 'quality_flags': [{'url':p['url'],'flags':p['quality_flags']} for p in pages if p['quality_flags']], 'ready': False}))
        raise SystemExit(1)
    experimental = treatments(reference, manifest['target_url'], manifest['award_text'])
    lab.save(directory / 'experiment.json', experimental)
    print(json.dumps({'pages': len(pages), 'arms': list(lab.EXPERIMENT_ARMS), 'output': str(directory), 'ready': True}))


if __name__ == '__main__':
    main()
