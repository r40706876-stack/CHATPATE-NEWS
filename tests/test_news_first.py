import unittest
from unittest.mock import patch
import news_first as nf

class NewsFirst(unittest.TestCase):
    def setUp(self):
        source_patch = patch('news_sources.collect', return_value=[
            {'id':'s1','name':'विभाग','url':'https://example.org/notice','text':'राष्ट्रीय सूचना का स्रोत'}])
        source_patch.start()
        self.addCleanup(source_patch.stop)

    def responses(self):
        facts = {'scope_class':'national','national_relevance':'देशभर के बैंक ग्राहकों पर लागू', 'publishable': True, 'topic': 'जरूरी सूचना', 'facts': [
            {'id':'f1','text':'विभाग ने सूचना जारी की','source_ids':['s1']}],
            'sources':[{'id':'s1','name':'विभाग','url':'https://example.org/notice'}]}
        # Deliberately long, single-speaker, no punch, tag or loop; all lines must survive.
        ep = {'topic':'जरूरी सूचना','lines':[{'who':'bablu','say':'जरूरी जानकारी ' * 25,
            'fact_ids':['f1']} for _ in range(12)]}
        return [[{'topic':'जरूरी सूचना','scope_class':'national','national_relevance':'देशभर के बैंक ग्राहक'}],facts,ep,{'ok':True,'national_scope_ok':True,'issues':[]}]

    def test_long_serious_news_preserved(self):
        with patch.object(nf.gemini,'ask_json',side_effect=self.responses()):
            ep = nf.write({'important_news':[]})[0]
        self.assertEqual(len(ep['lines']),12)
        self.assertEqual(len(ep['lines'][0]['say'].split()),50)
        self.assertEqual(ep['editorial_mode'],'news_first')
        self.assertNotIn('_loose',ep)
        self.assertIn('https://example.org/notice',ep['caption_post'])

    def test_unconfirmed_facts_block(self):
        with patch.object(nf.gemini,'ask_json',side_effect=[[{'topic':'x'}],{'publishable':False}]):
            with self.assertRaises(ValueError): nf.write({})

    def test_unsupported_line_blocks(self):
        data=self.responses();data[2]['lines'][0]['fact_ids']=['invented']
        with patch.object(nf.gemini,'ask_json',side_effect=data):
            with self.assertRaises(ValueError): nf.write({})

    def test_editorial_failure_blocks(self):
        data=self.responses();data[-1]={'ok':False,'issues':['तारीख गलत']}
        with patch.object(nf.gemini,'ask_json',side_effect=data):
            with self.assertRaises(ValueError): nf.write({})

    def test_local_or_route_only_news_rejected(self):
        for scope in ['local', 'regional', 'route_only', None]:
            with self.subTest(scope=scope), self.assertRaises(ValueError):
                nf.require_national({'scope_class':scope,'national_relevance':'एक रूट के यात्री'})

    def test_research_can_reject_initial_national_claim(self):
        data=self.responses()
        data[1]['scope_class']='route_only'
        with patch.object(nf.gemini,'ask_json',side_effect=data):
            with self.assertRaises(ValueError): nf.write({})

    def test_reviewer_rejects_national_scope(self):
        data=self.responses()
        data[-1]['national_scope_ok']=False
        with patch.object(nf.gemini,'ask_json',side_effect=data):
            with self.assertRaises(ValueError): nf.write({})

class ProductionRouting(unittest.TestCase):
    def test_default_writer_uses_news_first(self):
        import run_daily
        with patch.object(nf, 'write', return_value=['news']) as write:
            self.assertEqual(run_daily.write_scripts({'important_news':[]}, 1), ['news'])
            write.assert_called_once_with({'important_news':[]}, 1)

    def test_legacy_finish_does_not_truncate_news(self):
        import news_writer
        ep = NewsFirst().responses()[2]
        ep['editorial_mode'] = 'news_first'
        self.assertEqual(len(news_writer.finish(ep)['lines']), 12)

    def test_duration_report_has_no_target(self):
        import qa
        from types import SimpleNamespace
        with patch.object(qa.subprocess, 'run', return_value=SimpleNamespace(stdout='130.0')):
            report = qa.targets('long-news.mp4')
        self.assertIn('130.0', report)
        self.assertNotIn('⚠️', report)

if __name__=='__main__': unittest.main()
