import json, os, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
import news_first as nf
import scheduled_production as sp

PICK={'topic':'राष्ट्रीय बैंकिंग सूचना','query':'राष्ट्रीय बैंकिंग सूचना','scope_class':'national','national_relevance':'देशभर के बैंक ग्राहक'}
SOURCE={'id':'s1','name':'विभाग','url':'https://example.gov.in/notice','text':'देशभर के बैंक ग्राहकों की सूचना'}
FACTS={'publishable':True,'topic':PICK['topic'],'scope_class':'national','national_relevance':PICK['national_relevance'],
       'sources':[{k:v for k,v in SOURCE.items() if k!='text'}],
       'facts':[{'id':'f1','text':'देशभर के ग्राहकों की सूचना','source_ids':['s1']}]}
EP={'topic':PICK['topic'],'lines':[{'who':'bablu','say':'देशभर के बैंक ग्राहकों के लिए सूचना।','fact_ids':['f1']}]}
REVIEW={'ok':True,'national_scope_ok':True,'issues':[]}

class SourcePipeline(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.scope=patch.dict(os.environ,{'NEWS_CACHE_KEY':'2026-11-03_13'})
        self.scope.start();self.addCleanup(self.scope.stop)
        self.file=patch.object(nf,'__file__',str(Path(self.tmp.name)/'news_first.py'))
        self.file.start();self.addCleanup(self.file.stop)
        self.collect=patch('news_sources.collect',return_value=[SOURCE])
        self.collect.start();self.addCleanup(self.collect.stop)

    def test_direct_source_evidence_no_grounding_call(self):
        with patch.object(nf.gemini,'ask_json',side_effect=[[PICK],FACTS,EP,REVIEW]) as ask:
            ep=nf.write({'important_news':[]})[0]
        self.assertEqual(ep['scope_class'],'national')
        self.assertTrue(all(not c.kwargs.get('search') for c in ask.call_args_list))
        self.assertIn('example.gov.in',ask.call_args_list[1].args[0])

    def test_retry_reuses_selected_topic(self):
        with patch.object(nf.gemini,'ask_json',side_effect=[[PICK],RuntimeError('quota')]):
            with self.assertRaises(RuntimeError): nf.write({})
        with patch.object(nf.gemini,'ask_json',side_effect=[FACTS,EP,REVIEW]) as ask:
            nf.write({})
        self.assertEqual(ask.call_count,3)

    def test_completed_checkpoint_does_not_generate_again(self):
        with patch.object(nf.gemini,'ask_json',side_effect=[[PICK],FACTS,EP,REVIEW]):
            nf.write({})
        with patch.object(nf.gemini,'ask_json',side_effect=AssertionError('Duplicate generation')):
            self.assertEqual(nf.write({})[0]['scope_class'],'national')

    def test_invented_source_url_rejected(self):
        bad=json.loads(json.dumps(FACTS));bad['sources'][0]['url']='https://invented.example/x'
        with patch.object(nf.gemini,'ask_json',side_effect=[[PICK],bad]):
            with self.assertRaisesRegex(ValueError,'exact articles'): nf.write({})

    def test_failure_message_does_not_claim_missing_script(self):
        with patch.object(sp,'ROOT',Path(self.tmp.name)):
            text=sp.failure_message('https://example.org/run')
        self.assertIn('पूरी स्क्रिप्ट नहीं बन पाई',text)
        self.assertNotIn('स्क्रिप्ट सुरक्षित',text)

if __name__=='__main__': unittest.main()
