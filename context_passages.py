"""Context-preserving passage candidate: no standalone headings or inferred hierarchy."""
import math
import re

from passage_retrieval import passages, STOP
from search_lab import Browser, LINK, tokens


def merge_spans(spans):
    merged=[]
    for start,end in sorted(spans):
        if merged and start <= merged[-1][1] + 2:
            merged[-1]=(merged[-1][0],max(end,merged[-1][1]))
        else:
            merged.append((start,end))
    return merged


def evidence_units(text):
    raw=passages(text,maximum=1000)
    result=[]
    for index,unit in enumerate(raw):
        body=text[unit['start']:unit['end']].strip()
        plain=LINK.sub(lambda m:m[1],body)
        if re.fullmatch(r'#{1,6}\s+[^\n]+',body) or (plain.endswith('?') and '\n' not in plain):
            continue
        # A list of navigation questions contains no answer evidence.
        if plain.count('?')>=3 and all(line.strip().endswith('?') for line in plain.splitlines() if line.strip()):
            continue
        start,end=unit['start'],unit['end'];context_terms=set()
        if index:
            before=raw[index-1]
            context=text[before['start']:before['end']].strip()
            clean=LINK.sub(lambda m:m[1],context)
            if len(context)<600 and (context.startswith('#') or clean.endswith(('?',':'))):
                start=before['start']
                context_terms=set(tokens(clean))
        if index+1<len(raw):
            after=raw[index+1]
            following=text[after['start']:after['end']].lstrip()
            if (plain.endswith(':') or re.search(r'\b(following|criteria|conditions)\b',plain,re.I)) and re.match(r'(?:[-•]|\d+[.)])\s',following):
                if after['end']-start<=1800:
                    end=after['end']
        result.append({'start':start,'end':end,'terms':set(tokens(plain)),
                       'context_terms':context_terms,
                       'identity':re.sub(r'\s+',' ',plain).strip().lower()})
    return result


class ContextPassageBrowser(Browser):
    backend_name='context_passages_v2'

    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.evidence_index={url:evidence_units(p['text']) for url,p in self.pages.items()}

    def search_excerpt(self,url,terms):
        text=self.pages[url]['text'];query=terms-STOP
        candidates=self.evidence_index[url]
        if not query or not candidates:
            return super().search_excerpt(url,terms)
        weights={t:math.log(1+(len(self.pages)+1)/(self.df[t]+1)) for t in query}
        selected=[];seen=set();covered=set();ranges=[]
        for _ in range(8):
            def score(u):
                body=sum(weights[t]*(1 if t not in covered else .15) for t in query & u['terms'])
                context=sum(weights[t] for t in query & u['context_terms'])*.12
                return (body+context) / max(u['end']-u['start'],200)**.15
            options=sorted((u for u in candidates if u['identity'] not in seen),key=lambda u:(-score(u),u['start']))
            choice=None
            for unit in options:
                spans=merge_spans(ranges+[(unit['start'],unit['end'])])
                cost=sum(end-start for start,end in spans)+2*max(0,len(spans)-1)
                if score(unit)>0 and cost<=self.snippet_chars:
                    choice=unit;ranges=spans;break
            if choice is None:
                break
            selected.append(choice);seen.add(choice['identity']);covered.update(choice['terms'] & query)
        if not selected:
            return super().search_excerpt(url,terms)
        return {'text':'\n\n'.join(text[start:end] for start,end in ranges),
                'passages':[{'start':start,'end':end} for start,end in ranges],
                'selection':'Source passages with adjacent question/heading context; gaps are omitted.'}
