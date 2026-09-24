import unittest

from passage_retrieval import PassageBrowser, passages
from context_passages import ContextPassageBrowser, evidence_units
from retrieval_trial import summarize
from search_lab import Browser


class PassageTests(unittest.TestCase):
    def test_context_candidate_pairs_questions_with_answers(self):
        text='# Accounts\n\n## What is the Alpha bonus condition?\n\nDeposit $100 and grow your balance.\n\n## What is the Beta condition?\n\nNo deposits required.'
        corpus={'pages':[{'url':'https://example.org','title':'Accounts','text':text}]}
        browser=ContextPassageBrowser(corpus,'reference',snippet_chars=250)
        result=browser.search(['Alpha bonus condition'])['searches'][0]['results'][0]
        self.assertIn('What is the Alpha bonus condition?',result['text'])
        self.assertIn('Deposit $100',result['text'])
        self.assertNotIn('[Section:',result['text'])
        self.assertLessEqual(len(result['text']),250)
        for span in result['passages']:
            self.assertIn(text[span['start']:span['end']],result['text'])
        self.assertTrue(all(not text[u['start']:u['end']].strip().endswith('?') for u in evidence_units(text)))

    def fixture(self):
        text=('# Savings\n\n## Rate\n\nBonus interest rate is 5.00%.\n\n## Archive\n\n' +
              '\n\n'.join(('Unrelated historical information '+str(i)+' ')*12 for i in range(20)) +
              '\n\n## Bonus eligibility\n\n- Deposit $100 each month.\n\n- Grow the balance.\n\n- Withdrawals are allowed if the balance still grows.\n\n'+
              '[Bonus conditions](https://example.org/conditions#eligibility)\n\n## Archive links\n\n'+
              '[Unrelated archive](https://example.org/archive)')
        return {'pages':[{'url':'https://example.org/save','title':'Savings','text':text},
                         {'url':'https://example.org/conditions','title':'Bonus conditions','text':'Eligibility terms'}]}

    def test_complementary_passages_keep_distant_evidence_and_offsets(self):
        corpus=self.fixture();browser=PassageBrowser(corpus,'reference',snippet_chars=1200)
        result=browser.call('search',{'queries':['bonus interest deposit balance eligibility']})
        page=next(p for p in result['searches'][0]['results'] if p['url'].endswith('/save'))
        self.assertIn('5.00%',page['text'])
        self.assertIn('Deposit $100',page['text'])
        self.assertIn('Withdrawals are allowed',page['text'])
        self.assertLessEqual(len(page['text']),1200)
        self.assertNotIn('start',page)  # No misleading single contiguous span.
        for span in page['passages']:
            self.assertIn(corpus['pages'][0]['text'][span['start']:span['end']],page['text'])
        self.assertIn('Bonus eligibility',page['text'])

    def test_page_ranking_and_link_exposure_remain_observable(self):
        corpus=self.fixture();query=['bonus interest deposit eligibility']
        window=Browser(corpus,'reference',snippet_chars=1200)
        browser=PassageBrowser(corpus,'reference',snippet_chars=1200)
        a=window.call('search',{'queries':query})['searches'][0]['results']
        b=browser.call('search',{'queries':query})['searches'][0]['results']
        self.assertEqual([p['url'] for p in a],[p['url'] for p in b])
        for p in b:
            for link in p['links']:
                self.assertIn(link['text'],p['text'])
                self.assertNotEqual(link['url'],'https://example.org/archive')
        self.assertEqual(browser.metrics()['open_attempts'],0)

    def test_condition_bullets_are_one_passage(self):
        text='## Rules\n\n- Deposit.\n\n- Grow balance.\n\n- No withdrawals.\n\nOther paragraph.'
        chunks=passages(text)
        groups=[text[p['start']:p['end']] for p in chunks]
        self.assertTrue(any('Deposit.' in g and 'No withdrawals.' in g for g in groups))

    def test_summary_averages_repetitions_inside_questions(self):
        profile={'repeats':2,'metrics':{'open_actions':{'margin':.35}},
                 'distributions':{'opens':{'margin':.1}}}
        cases=[{'id':'a'},{'id':'b'}];source={};candidates={}
        for case in cases:
            for r in range(2):
                value={'scalar':{'open_actions':1},'vectors':{'opens':[0,1]},'details':{'status':'completed'}}
                source[(case['id'],r,'live')]=value
                for method in ('window','passages'):
                    candidates[(case['id'],r,method)]=value
        result=summarize(profile,cases,source,candidates)
        self.assertEqual(result['rows'][0]['n_matched_questions'],2)
        self.assertEqual(result['distributions'][0]['passages_vs_hosted_tv'],0)
        self.assertEqual(result['verdict'],'EXPLORATORY_ONLY')


if __name__=='__main__':
    unittest.main()
