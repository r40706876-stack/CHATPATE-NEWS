import copy
import unittest
from unittest.mock import patch
import news_writer as nw
import qa


def episode():
    texts = ['चाचा का पैसा कहाँ गया?', 'दुकान में आज फिर भीड़ लगी।', 'चाचा बोले सब कुछ सस्ता है।', 'पिंकी बोली आप तो उधार लेते हो।', 'दादी बोली पैसा दुकानदार का गया।']
    return {'topic': 'दुकान', 'lines': [dict(who=['chacha','bablu','chacha','pinky','dadi'][i], say=t, caption=t, tag=i==3) for i,t in enumerate(texts)]}

class Gates(unittest.TestCase):
    def test_valid_structure(self):
        self.assertEqual(len(nw.finish(episode())['lines']),5)
    def test_does_not_cut_context(self):
        ep=episode(); ep['lines'] *= 2
        with self.assertRaises(ValueError): nw.finish(ep)
    def test_invalid_script_not_rescued(self):
        ep=episode(); ep['lines'][0]['say']=' '.join(['बहुत']*20)
        with patch.object(nw,'LEAN',True), patch.object(nw.gemini,'ask',return_value='unused'), patch.object(nw.gemini,'json_from',return_value=[ep]):
            with self.assertRaises(nw.NoViral): nw.write_from({},[],[],1)
    def test_lean_does_not_invent_score(self):
        with patch.object(nw,'LEAN',True), patch.object(nw.gemini,'ask',return_value='unused'), patch.object(nw.gemini,'json_from',return_value=[episode()]):
            got=nw.write_from({},[],[{'topic':'दुकान','trend':{'score':5}}],1)[0]
            self.assertEqual(got['review_status'],'structure_only')
            self.assertNotIn('connect',got)
    def test_decode_failure_is_error(self):
        with self.assertRaises(Exception): qa.check('/nonexistent/bakra.mp4')

class DeliveryGates(unittest.TestCase):
    def test_failed_qa_never_sends(self):
        import talk_episode as te
        with patch('reel_studio.render', return_value=15), patch('qa.check', return_value=['frozen']), patch('telegram.send_video') as send:
            with self.assertRaises(RuntimeError): te.post_studio({'lines': []})
            send.assert_not_called()
    def test_qa_exception_never_sends(self):
        import talk_episode as te
        with patch('reel_studio.render', return_value=15), patch('qa.check', side_effect=ValueError('decode')), patch('telegram.send_video') as send:
            with self.assertRaises(RuntimeError): te.post_studio({'lines': []})
            send.assert_not_called()
    def test_final_meme_file_checked(self):
        import talk_episode as te
        with patch('reel_studio.render', return_value=15), patch('qa.check', side_effect=[[], ['bad final']]), patch('memes.add', return_value=['meme']), patch('telegram.send_video') as send:
            with self.assertRaises(RuntimeError): te.post_studio({'lines': []})
            send.assert_not_called()

if __name__ == '__main__': unittest.main()
