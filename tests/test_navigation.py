import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import URLError
from types import SimpleNamespace

import search_lab as lab
from navigation import PublicNavigator, fetch_response, navigation_summary

CORPUS = json.loads((lab.ROOT / 'sample_corpus.json').read_text())
PRODUCT = 'https://example-bank.test/savings'
HUB = 'https://example-bank.test/awards'
OTHER = 'https://background.test/article'


def html(text='A public background page with useful savings information. ' * 4):
    return {'status': 200, 'location': None, 'content_type': 'text/html', 'charset': 'utf-8',
            'body': ('<html><title>Background</title><main><h1>Details</h1><p>'+text+'</p></main></html>').encode()}


def redirect(url):
    return {'status': 302, 'location': url, 'content_type': 'text/html', 'charset': 'utf-8', 'body': b''}


class NavigationTests(unittest.TestCase):
    def browser(self, directory, arm='baseline', fetcher=None, mode='live'):
        corpus = copy.deepcopy(CORPUS)
        product = next(p for p in corpus['pages'] if p.get('role') == 'product')
        product['original_snapshot'] = {'text': product['text'].replace('{{AWARD_BLOCK}}', corpus['award_sentence']), 'anchors': {}}
        b = lab.browser_class('context')(corpus, arm, snippet_chars=6000, page_chars=32000)
        b.enable_navigation(directory, mode, fetcher)
        return b

    def test_fetch_unknown_then_shared_cache_replay_without_network(self):
        with tempfile.TemporaryDirectory() as d:
            calls=[]
            b=self.browser(d, fetcher=lambda u: calls.append(u) or html())
            result=b.call('open', {'url':OTHER,'offset':0})
            self.assertNotIn('error',result)
            self.assertEqual(result['source']['kind'],'cached_public_page')
            self.assertEqual(calls,[OTHER])
            self.assertEqual(b.events[0]['url_provenance'],'unexposed_url')
            fresh=self.browser(d,'inline',fetcher=lambda u:self.fail('replay fetched'),mode='replay')
            self.assertEqual(fresh.call('open',{'url':OTHER})['text'],result['text'])
            self.assertEqual(fresh.navigation.reads[0]['record_sha256'],b.navigation.reads[0]['record_sha256'])
            self.assertEqual(b.metrics()['successful_opens'],1)

    def test_fetch_does_not_change_search_ranking_or_index(self):
        with tempfile.TemporaryDirectory() as d:
            b=self.browser(d,fetcher=lambda u:html('superuniqueword ' * 20))
            before=b.search(['savings'])
            b.call('open',{'url':OTHER})
            self.assertEqual(b.search(['savings']),before)
            self.assertEqual(b.search(['superuniqueword'])['searches'][0]['results'],[])
            self.assertTrue(b.call('find',{'url':OTHER,'text':'superuniqueword'})['matches'])

    def test_every_condition_intercepts_direct_variants_and_redirects(self):
        with tempfile.TemporaryDirectory() as d:
            calls=[]
            def fetch(u):
                calls.append(u)
                return redirect('http://www.example-bank.test/savings/?utm_source=other')
            for arm in lab.EXPERIMENT_ARMS:
                b=self.browser(d,arm,fetcher=fetch)
                direct=b.call('open',{'url':PRODUCT+'/?variant=untreated'})
                via=b.call('open',{'url':OTHER})
                self.assertEqual(direct['text'],via['text'])
                self.assertEqual(CORPUS['award_sentence'] in via['text'],arm in ('inline','link_descriptive','current_footnote'))
            self.assertEqual(calls,[OTHER])
            # Cache holds only the untreated redirect, never a condition's page text.
            self.assertTrue(all('"page"' not in p.read_text() for p in Path(d).glob('*.json')))

    def test_absent_hub_cannot_be_fetched_directly_or_through_redirect(self):
        with tempfile.TemporaryDirectory() as d:
            calls=[]
            fetch=lambda u:calls.append(u) or redirect(HUB+'?from=elsewhere')
            for arm in ('baseline','inline','current_footnote'):
                b=self.browser(d,arm,fetcher=fetch)
                self.assertEqual(b.call('open',{'url':HUB})['error'],'not_available_in_condition')
                self.assertEqual(b.call('open',{'url':OTHER})['error'],'not_available_in_condition')
            b=self.browser(d,'link_descriptive',fetcher=fetch)
            self.assertNotIn('error',b.call('open',{'url':OTHER}))
            self.assertEqual(calls,[OTHER])

    def test_cached_original_controlled_body_cannot_leak(self):
        with tempfile.TemporaryDirectory() as d:
            nav=PublicNavigator(d,'live',lambda u:None,fetcher=lambda u:html('UNTREATEDSECRET ' * 12))
            nav.load(PRODUCT)
            b=self.browser(d,'baseline',fetcher=lambda u:self.fail('network'))
            self.assertNotIn('UNTREATEDSECRET',b.call('open',{'url':PRODUCT})['text'])

    def test_real_404_distinct_from_replay_cache_miss_and_condition_absence(self):
        with tempfile.TemporaryDirectory() as d:
            def missing(u):
                r=html();r.update(status=404,body=b'');return r
            b=self.browser(d,fetcher=missing)
            r=b.call('open',{'url':OTHER})
            self.assertEqual((r['error'],r['http_status']),('http_error',404))
            self.assertEqual(b.metrics()['http_404_opens'],1)
            self.assertEqual(b.metrics()['open_attempts'],1)
            replay=self.browser(d,mode='replay')
            self.assertEqual(replay.call('open',{'url':OTHER})['http_status'],404)
            self.assertEqual(replay.call('open',{'url':OTHER+'/new'})['error'],'cache_miss')

    def test_redirect_chain_and_click_then_find_are_usable(self):
        with tempfile.TemporaryDirectory() as d:
            dest=OTHER+'/final'
            def fetch(u):
                if u==OTHER:return redirect(dest)
                return html('<a href="/next">Follow details</a> '+('savings facts ' * 20))
            b=self.browser(d,fetcher=fetch)
            r=b.call('open',{'url':OTHER})
            self.assertEqual(r['url'],dest)
            self.assertEqual(len(r['navigation']['hops']),2)
            link=r['links'][0]
            clicked=b.call('click',{'page_url':dest,'link_id':link['id']})
            self.assertNotIn('error',clicked)
            self.assertEqual(b.events[-1]['url_provenance'],'previously_exposed_link')
            self.assertTrue(b.call('find',{'url':clicked['url'],'text':'savings'})['matches'])

    def test_reject_private_addresses_and_redirect_scheme(self):
        with patch('validation.snapshot.socket.getaddrinfo',return_value=[(None,None,None,None,('127.0.0.1',80))]):
            with self.assertRaises(ValueError):fetch_response('http://public-name.test/')
        with tempfile.TemporaryDirectory() as d:
            b=self.browser(d,fetcher=lambda u:redirect('file:///etc/passwd'))
            self.assertEqual(b.call('open',{'url':OTHER})['error'],'invalid_arguments')

    def test_redirect_loop_network_failure_and_bad_content(self):
        with tempfile.TemporaryDirectory() as d:
            b=self.browser(d,fetcher=lambda u:redirect(OTHER))
            self.assertEqual(b.call('open',{'url':OTHER})['error'],'redirect_loop')
        with tempfile.TemporaryDirectory() as d:
            def broken(u):raise URLError('offline')
            b=self.browser(d,fetcher=broken)
            self.assertEqual(b.call('open',{'url':OTHER})['error'],'network_error')
        with tempfile.TemporaryDirectory() as d:
            b=self.browser(d,fetcher=lambda u:html('tiny'))
            self.assertEqual(b.call('open',{'url':OTHER})['error'],'extraction_error')

    def test_run_persists_navigation_provenance_in_partial_and_final_traces(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / 'trace.json'
            args = SimpleNamespace(allow_paid=True, mode='custom', corpus=str(lab.ROOT/'sample_corpus.json'),
                arm='baseline', snippet_chars=6000, top_k=5, page_chars=32000,
                model='gpt-5.6-luna', reasoning='medium', question='Read the background page.',
                max_rounds=3, max_output_tokens=1024, web_tool='web_search_preview',
                retrieval='context', navigation='live', out=str(path), web_cache=str(Path(d)/'cache'))
            class FakeBrowser(lab.Browser):
                def enable_navigation(self, cache, mode):
                    super().enable_navigation(cache, mode, fetcher=lambda u: html())
            def transport(payload):
                if not path.exists() or not json.loads(path.read_text()).get('tool_events'):
                    return {'status':'completed','output':[{'type':'function_call','call_id':'nav',
                        'name':'open','arguments':json.dumps({'url':OTHER})}]}
                partial=json.loads(path.read_text())
                self.assertEqual(len(partial['navigation_reads']),1)
                return {'status':'completed','output':[{'type':'message','content':[
                    {'type':'output_text','text':'Background checked.'}]}]}
            trace=lab.run(args,transport=transport,browser_factory=FakeBrowser)
            saved=json.loads(path.read_text())
            self.assertEqual(trace['status'],'completed')
            self.assertEqual(saved['navigation_reads'],trace['navigation_reads'])
            self.assertEqual(navigation_summary([trace])['public_response_records_read'],1)
            # Frozen first pilot emitted hop hashes before adding the dedicated field.
            del trace['navigation_reads']
            self.assertEqual(navigation_summary([trace])['public_response_records_read'],1)
            self.assertEqual(navigation_summary([trace])['successful_opens'],1)

    def test_cache_tampering_fails_loudly(self):
        with tempfile.TemporaryDirectory() as d:
            self.browser(d,fetcher=lambda u:html()).call('open',{'url':OTHER})
            next(Path(d).glob('*.bin')).write_bytes(b'changed')
            b=self.browser(d,mode='replay')
            with self.assertRaisesRegex(RuntimeError,'hash mismatch'):b.call('open',{'url':OTHER})

if __name__=='__main__':unittest.main()
