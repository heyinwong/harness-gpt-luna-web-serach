import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import contextlib
import io

import award_report
import search_lab as lab
import suite
from validation.snapshot import extract_html
from validation.protocol import fingerprint
from validation.budget import BudgetedTransport


class RetrievalRegressionTests(unittest.TestCase):
    def test_semantic_aside_footnotes_are_evidence(self):
        _, text, anchors = extract_html("<main><p>Use newline=''.</p><aside class='footnote-list'><aside id='fn1' role='doc-footnote'><p>Otherwise embedded newlines are wrong.</p></aside></aside></main>", 'https://example.org/csv')
        self.assertIn('embedded newlines are wrong', text)
        self.assertIn('fn1', anchors)

    def test_inline_syntax_and_anchor_position_survive_html(self):
        title, text, anchors = extract_html("<title>CSV</title><main><p>Earlier text</p><p id='note'>If <code><span>newline</span><span>=</span><span>''</span></code> is not specified</p></main>", 'https://example.org/csv')
        self.assertIn("newline=''", text)
        corpus={'pages':[{'url':'https://example.org/csv','title':title,'text':text,'anchors':anchors}]}
        browser=lab.Browser(corpus,'reference',snippet_chars=100,page_chars=100)
        opened=browser.call('open',{'url':'https://example.org/csv#note','offset':0})
        self.assertGreater(opened['start'],0)
        self.assertNotIn('Earlier text',opened['text'])
        found=browser.call('find',{'url':'https://example.org/csv','text':"If newline='' is not specified"})
        self.assertEqual(found['total_matches'],1)

    def test_site_path_and_quoted_phrase_across_whitespace(self):
        corpus={'pages':[{'url':'https://example.org/docs/csv','title':'CSV','text':'embedded\nnewlines matter'},
                         {'url':'https://example.org/other','title':'CSV','text':'embedded newlines'}]}
        browser=lab.Browser(corpus,'reference')
        result=browser.call('search',{'queries':['site:example.org/docs "embedded newlines"']})
        self.assertEqual([p['url'] for p in result['searches'][0]['results']],['https://example.org/docs/csv'])

    def test_fragment_is_preserved_when_clicking_observed_link(self):
        corpus={'pages':[{'url':'https://example.org/docs','title':'Docs','text':'[Note](#note) '+'x'*200+'Footnote','anchors':{'note':214}}]}
        browser=lab.Browser(corpus,'reference',page_chars=100)
        opened=browser.call('open',{'url':'https://example.org/docs','offset':0})
        link=opened['links'][0]
        self.assertTrue(link['url'].endswith('#note'))
        result=browser.call('click',{'page_url':'https://example.org/docs','link_id':link['id']})
        self.assertEqual(result['start'],214)


class AwardScoringTests(unittest.TestCase):
    def test_suite_end_to_end_with_mock_transport_and_safe_resume(self):
        with tempfile.TemporaryDirectory() as temp:
            directory=Path(temp)/'suite'
            calls=[]
            def fake(payload):
                calls.append(payload)
                return {'model':'gpt-5.6-luna','status':'completed','id':'mock',
                        'output':[{'type':'message','content':[{'type':'output_text','text':'Fictional answer for plumbing only.'}]}],
                        'usage':{'input_tokens':100,'output_tokens':100}}
            def budget(path, maximum):
                return BudgetedTransport(path,maximum,transport=fake)
            argv=['suite.py','--out-dir',str(directory),'--max-runs','30','--repeats','2','--allow-paid']
            with patch('sys.argv',argv),patch('suite.BudgetedTransport',budget),contextlib.redirect_stdout(io.StringIO()):
                suite.main()
                self.assertEqual(len(calls),30)
                suite.main()
                self.assertEqual(len(calls),30)
            packet=award_report.prepare(directory,lab.ROOT/'sample_corpus.json')
            self.assertEqual(len(packet['items']),30)

    def test_blinded_packet_and_complete_paired_scoring(self):
        with tempfile.TemporaryDirectory() as temp:
            d=Path(temp)
            corpus=lab.ROOT/'sample_corpus.json'
            jobs=suite.plan([{'id':'q1','question':'Which account?'}],list(lab.ARMS),2,False,4)
            config={'corpus_sha256':hashlib.sha256(corpus.read_bytes()).hexdigest()}
            lab.save(d/'manifest.json',{'jobs':jobs,'config':config})
            for j in jobs:
                lab.save(d/(fingerprint(j)+'.json'),{'suite_job':j,'suite_config':config,
                         'question':j['question'],'arm':j['arm'],'status':'completed','answer':'Example answer'})
            packet=award_report.prepare(d,corpus)
            self.assertEqual(len(packet['items']),10)
            self.assertNotIn('arm',packet['items'][0])
            with self.assertRaisesRegex(ValueError,'manually completed'):
                award_report.summarize(d,packet)
            for item in packet['items']:
                item.update(correct_relevant_award=0,unsupported_product_claim=0,reviewer='Test reviewer',evidence='Fixture contains no award.')
            result=award_report.summarize(d,packet)
            self.assertFalse(result['flags'])
            self.assertEqual(len(result['contrasts']),10)
            self.assertTrue(all(r['difference']['n_questions']==1 for r in result['contrasts']))
            altered=copy.deepcopy(packet)
            altered['items'][0]['answer']='changed'
            with self.assertRaisesRegex(ValueError,'answer changed'):
                award_report.summarize(d,altered)


if __name__=='__main__':
    unittest.main()
