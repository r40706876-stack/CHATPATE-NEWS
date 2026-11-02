"""Regression tests for production-policy bypasses and truthful visual reporting."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import talk_episode as te
import tts

def national(**kw):
    return dict(production=True, scope_class='national', national_relevance='देशभर के बैंक ग्राहक', **kw)

class Reliability(unittest.TestCase):
    def test_legacy_local_production_cannot_enter_prep(self):
        with self.assertRaises(ValueError):
            te.normalize_visual_style({'production':True,'lines':[]})

    def test_national_production_requires_gemini(self):
        ep=te.normalize_visual_style(national(lines=[]))
        self.assertTrue(ep['require_gemini_voice'])

    def test_delivery_rejects_edge_before_render(self):
        with self.assertRaisesRegex(RuntimeError,'Gemini voice'):
            te.post_studio(national(_voice='edge',lines=[]))

    def test_delivery_rejects_local_before_render(self):
        with self.assertRaises(ValueError):
            te.post_studio({'production':True,'_voice':'gemini','lines':[]})

    def test_gemini_failure_never_falls_back(self):
        with tempfile.TemporaryDirectory() as d, patch('gemini.keys',return_value=['test-key']), patch.object(tts,'make_all',side_effect=RuntimeError('quota')) as make:
            with self.assertRaises(RuntimeError):
                tts.speak_script({'editorial_mode':'news_first','lines':[{'who':'bablu','say':'सूचना'}]},Path(d))
        self.assertEqual([c.args[1] for c in make.call_args_list],['gemini'])

    def test_graphic_is_not_reported_as_real_photo(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);broll=root/'st_in/broll';broll.mkdir(parents=True)
            (broll/'0_own.mp4').touch()
            (broll/'0_own.txt').write_text('तथ्य-आधारित ग्राफिक • स्रोत: PIB',encoding='utf-8')
            (broll/'1_photo.jpg').touch()
            with patch.object(te,'ROOT',root),patch.object(te,'IN',root/'st_in'):
                te.quality({'_voice':'gemini','lines':[{},{}]})
            report=json.loads((root/'last_quality.json').read_text())
            self.assertEqual(report['real_visual_lines'],1)
            self.assertEqual(report['fact_graphic_lines'],1)

    def test_missing_lipsync_never_becomes_static_face(self):
        from PIL import Image
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'st_in/0').mkdir(parents=True)
            Image.new('RGB',(4,4)).save(root/'st_in/0/still.png')
            ep=national(_voice='gemini',lips='sadtalker',lines=[{'who':'bablu','say':'खबर','shot':'close'}])
            with patch.object(te,'IN',root/'st_in'),patch.object(te,'OUT',root/'st_out'):
                with self.assertRaisesRegex(RuntimeError,'Missing SadTalker'):
                    te.post_studio(ep)

    def test_cached_local_script_rejected(self):
        import datetime as dt
        import scheduled_production as sp
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'episodes').mkdir()
            (root/'episodes/old.json').write_text(json.dumps({'topic':'एक रूट की ट्रेन','production':True,'lines':[]}))
            sp.save('2026-11-03_07',{'status':'prepared','script':'episodes/old.json'},root)
            with self.assertRaises(ValueError):
                sp.prepare(dt.datetime(2026,11,3,2,0,tzinfo=dt.timezone.utc),root)
            self.assertFalse((root/'studio_job.txt').exists())

if __name__=='__main__': unittest.main()

