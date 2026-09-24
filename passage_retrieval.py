"""Experimental complementary passages; same page ranking and navigation as Browser."""
import math
import re

from search_lab import Browser, LINK, tokens

STOP = set('a an the and or to of in on at for from with is are be how what which when why do does can i me my you your their it its that this as'.split())


def passages(text, maximum=1100):
    """Contiguous source spans, with nearby heading paths and complete short lists."""
    units = []
    headings = []
    for match in re.finditer(r'\S[\s\S]*?(?=\n\s*\n|\Z)', text):
        body = match.group(0)
        heading = re.fullmatch(r'(#{1,6})\s+([^\n]+)', body.strip())
        if heading:
            depth = len(heading[1])
            headings = [h for h in headings if h[0] < depth] + [(depth, heading[2])]
        # Preserve entire paragraphs where possible. Split long ones at line/word
        # boundaries and expand over complete Markdown links, as the window tool does.
        start = match.start()
        while start < match.end():
            end = min(match.end(), start + maximum)
            if end < match.end():
                boundary = text.rfind('\n', start + maximum//2, end)
                if boundary < 0:
                    boundary = text.rfind(' ', start + maximum//2, end)
                if boundary > start:
                    end = boundary
            for link in LINK.finditer(text, start, match.end()):
                if link.start() < end < link.end():
                    end = link.end()
                    break
            if end <= start:
                end = match.end()
            units.append({'start': start, 'end': end, 'heading': ' > '.join(h[1] for h in headings),
                          'terms': set(tokens(LINK.sub(lambda m:m[1], text[start:end])))})
            start = end
            while start < match.end() and text[start].isspace():
                start += 1
    # Bullets in the structured extractor are separate paragraphs. Keep adjacent
    # qualifying conditions together instead of treating each as an isolated fact.
    merged = []
    for unit in units:
        if (merged and text[unit['start']:].startswith('- ') and
                text[merged[-1]['start']:].startswith('- ') and
                unit['end'] - merged[-1]['start'] <= maximum and
                not text[merged[-1]['end']:unit['start']].strip()):
            merged[-1]['end'] = unit['end']
            merged[-1]['terms'].update(unit['terms'])
        else:
            merged.append(unit)
    return merged


class PassageBrowser(Browser):
    backend_name = 'complementary_passages_v1'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.passage_index = {url:passages(page['text']) for url,page in self.pages.items()}

    def search_excerpt(self, url, terms):
        text = self.pages[url]['text']
        candidates = self.passage_index[url]
        query = terms - STOP
        if not query or not candidates:
            return super().search_excerpt(url, terms)
        weights = {t: math.log(1 + (len(self.pages)+1)/(self.df[t]+1)) for t in query}
        selected, covered, remaining = [], set(), self.snippet_chars
        # The character allowance includes heading context, not just passage body.
        # Page ranking, top-k, open windows, tool schema and action limits are unchanged.
        while candidates and len(selected) < 6:
            def score(unit):
                matched = query & unit['terms']
                novelty = sum(weights[t] * (1 if t not in covered else .18) for t in matched)
                context = sum(weights[t] for t in query & set(tokens(unit['heading']))) * .12
                length = unit['end'] - unit['start']
                return (novelty + context) / (max(length, 150) ** .2)
            ordered = sorted((u for u in candidates if u not in selected),
                             key=lambda u:(-score(u),u['start']))
            chosen = None
            for unit in ordered:
                header = '[Section: ' + unit['heading'] + ']\n' if unit['heading'] else ''
                cost = len(header) + unit['end'] - unit['start'] + 2
                if score(unit) > 0 and cost <= remaining:
                    chosen = unit
                    remaining -= cost
                    break
            if chosen is None:
                break
            selected.append(chosen)
            covered.update(query & chosen['terms'])
        if not selected:
            return super().search_excerpt(url, terms)
        selected.sort(key=lambda u:u['start'])
        blocks = [('['+'Section: '+u['heading']+']\n' if u['heading'] else '') + text[u['start']:u['end']] for u in selected]
        return {'text':'\n\n'.join(blocks),
                'passages':[{'start':u['start'],'end':u['end'],'heading':u['heading']} for u in selected],
                'selection':'Complementary source passages in document order; gaps are omitted.'}
