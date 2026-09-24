import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

import corpus_builder as builder
import search_lab as lab
from discover import sources


class CorpusTests(unittest.TestCase):
    def test_declared_rate_page_cannot_pass_without_rendered_rate(self):
        url='https://example.org/rates'
        raw=('<main><h1>Savings rate</h1><p>Standard variable rate. '+('Conditions apply. '*30)+
             '</p><a href="https://example.org/apply?tracking=123%23abc">Apply</a></main>').encode()
        entry={'url':url,'provider':'Example','category':'rates','require_numeric_rate':True,
               'quality_reviews':[{'flag':'declared_rate_page_has_no_numeric_percentage','content_sha256':'stale','reason':'Old review'}]}
        with tempfile.TemporaryDirectory() as temp:
            cache=Path(temp);key=hashlib.sha256(url.encode()).hexdigest()
            (cache/(key+'.bin')).write_bytes(raw)
            lab.save(cache/(key+'.json'),{'url':url,'resolved_url':url,'content_type':'text/html',
                     'content_sha256':hashlib.sha256(raw).hexdigest(),'retrieved_at':'fixture'})
            result=builder.capture(entry,cache,offline=True)
            self.assertIn('declared_rate_page_has_no_numeric_percentage',result['quality_flags'])
            self.assertFalse(result['quality_reviews'])

    def test_structured_extraction_keeps_table_and_external_footnotes(self):
        html = '''<main><h1>Save</h1><p>Rate <b>5%</b>.</p>
        <table><tr><th>Account</th><th>Condition</th></tr><tr><td>Grow</td><td>No withdrawals</td></tr></table>
        <a href="/terms#bonus">Read conditions</a></main>
        <div class="lower-section-container"><p id="terms">Award footnote</p></div>
        <nav>Menu noise</nav>'''
        page = builder.html_page(html, 'https://example.org/save')
        self.assertIn('# Save', page['text'])
        self.assertIn('| Grow | No withdrawals |', page['text'])
        self.assertIn('[Read conditions](https://example.org/terms#bonus)', page['text'])
        self.assertIn('Award footnote', page['text'][page['anchors']['terms']:])
        self.assertNotIn('Menu noise', page['text'])

    def test_nested_selected_roots_do_not_duplicate_award(self):
        page = builder.html_page('<div id="skipmaincontent"><h1>Save</h1><div class="lower-section-container">Award</div></div>',
                                 'https://example.org', ['#skipmaincontent', '.lower-section-container'])
        self.assertEqual(page['text'].count('Award'), 1)

    def test_multiple_article_cards_are_not_truncated_to_first_card(self):
        page = builder.html_page('<body><h1>Savings</h1><article>Features</article><article>Bonus conditions</article><aside>Footnote</aside></body>',
                                 'https://example.org')
        for phrase in ('# Savings', 'Features', 'Bonus conditions', 'Footnote'):
            self.assertIn(phrase, page['text'])

    def test_ambiguous_alias_fails_instead_of_opening_wrong_page(self):
        pages = [{'url':'https://example.org/a','title':'A','text':'A','aliases':['https://example.org/x']},
                 {'url':'https://example.org/b','title':'B','text':'B','aliases':['https://example.org/x']}]
        with self.assertRaisesRegex(ValueError, 'Ambiguous'):
            lab.Browser({'pages':pages}, 'reference')

    def test_footnote_arm_requires_an_observed_original(self):
        import json
        corpus = json.loads((lab.ROOT/'sample_corpus.json').read_text())
        with self.assertRaisesRegex(ValueError, 'original_snapshot'):
            lab.make_pages(corpus, 'current_footnote')

    def test_tracking_alias_preserves_fragment_and_functional_query(self):
        page = {'url': 'https://example.org/save', 'title': 'Save', 'text': 'Start ' + 'x'*200 + 'Terms',
                'anchors': {'terms': 206}, 'aliases': ['https://example.org/save?ei=related']}
        browser = lab.Browser({'pages': [page]}, 'reference')
        opened = browser.call('open', {'url': 'https://example.org/save?ei=related#terms'})
        self.assertEqual(opened['text'], 'Terms')
        self.assertEqual(browser.call('open', {'url': 'https://example.org/save?version=old'})['error'], 'not_in_corpus')
        self.assertEqual(builder.clean_url('https://example.org/save?ei=a&version=old#terms'),
                         'https://example.org/save?version=old')

    def fixture(self):
        award = 'Canstar 2024 Digital Banking Bank of the Year.'
        text = '# Savings\n\nAccount details.\n\n## Things you should know\n\n3 ' + award + '\n\nOther terms.'
        page = {'url': 'https://www.commbank.com.au/savings-accounts.html', 'title': 'Savings', 'text': text,
                'anchors': {'terms': text.index('## Things'), 'after': text.index('Other terms.')}}
        reference = {'pages': [page], 'failures': []}
        return reference, page['url'], award

    def test_six_conditions_preserve_original_and_adjust_anchors(self):
        reference, url, award = self.fixture()
        before = copy.deepcopy(reference)
        corpus = builder.treatments(reference, url, award)
        self.assertEqual(reference, before)
        current = lab.make_pages(corpus, 'current_footnote')[url]
        self.assertEqual(current['text'], reference['pages'][0]['text'])
        self.assertEqual(current['anchors'], reference['pages'][0]['anchors'])
        for arm in lab.EXPERIMENT_ARMS:
            page = lab.make_pages(corpus, arm)[url]
            self.assertEqual(page['text'][page['anchors']['after']:], 'Other terms.')
            self.assertNotIn('{{AWARD_BLOCK}}', page['text'])
            if arm in ('baseline', 'no_link', 'link_vague'):
                self.assertNotIn(award, page['text'])
            else:
                self.assertEqual(page['text'].count(award), 1)
        self.assertLess(lab.make_pages(corpus, 'inline')[url]['text'].index(award),
                        lab.make_pages(corpus, 'inline')[url]['text'].index('Account details'))

    def test_changed_award_context_fails_closed(self):
        reference, url, award = self.fixture()
        reference['pages'][0]['text'] += '\n\n' + award
        with self.assertRaisesRegex(ValueError, 'exactly one'):
            builder.treatments(reference, url, award)

    def test_discovery_distinguishes_reported_cited_and_opened_urls(self):
        observed = sources({'responses':[{'output':[
            {'type':'web_search_call','action':{'type':'search','sources':[{'url':'https://example.org/a'}]}},
            {'type':'web_search_call','action':{'type':'open_page','url':'https://example.org/b'}},
            {'type':'message','content':[{'annotations':[{'type':'url_citation','url':'https://example.org/a'}]}]}
        ]}]})
        self.assertEqual(observed['https://example.org/a'], {'reported_source','answer_citation'})
        self.assertEqual(observed['https://example.org/b'], {'open_page'})


if __name__ == '__main__':
    unittest.main()
