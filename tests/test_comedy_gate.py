"""Offline regression tests for comedy format and script quality gates."""
import unittest
import bakra_rules
import visuals


def episode(first="रिचार्ज ने जेब की छुट्टी कर दी!", fmt="news_roast"):
    return {"topic": "मोबाइल रिचार्ज", "comedy_format": fmt,
            "lines": [{"who": "bablu", "say": first},
                      {"who": "chacha", "say": "चाचा ने सिम अलमारी में रख दी!"},
                      {"who": "pinky", "say": "अब तो पड़ोसी भी दरवाजा बंद रखते हैं!"}]}


class ComedyGateTests(unittest.TestCase):
    def test_format_acceptance(self):
        for fmt in ("news_roast", "character_clash", "reverse_punch"):
            self.assertNotIn("अनजान comedy_format", bakra_rules.violations(episode(fmt=fmt)))

    def test_unknown_format_rejected(self):
        self.assertIn("अनजान comedy_format", bakra_rules.violations(episode(fmt="random")))

    def test_slow_intro_rejected(self):
        self.assertIn("धीमा introduction hook", bakra_rules.violations(episode(first="नमस्कार दोस्तों, खबर सुनिए")))


    def test_no_clips_blocks_fullscreen_meme_insertion(self):
        import memes
        from pathlib import Path
        from unittest.mock import patch
        with patch.object(memes, "DIR", Path(".")):
            self.assertEqual(memes.pick({"no_clips": True}, [2.0, 2.0]), [])



class VisualMatchingTests(unittest.TestCase):
    def test_gemini_quota_fallback_uses_only_same_news(self):
        options = [
            {"same_story": True, "tags": "बिहार ट्रेन स्टेशन पर यात्रियों की भीड़"},
            {"same_story": False, "tags": "बिहार ट्रेन स्टेशन पर यात्रियों की भीड़"},
            {"same_story": True, "stock": True, "tags": "बिहार ट्रेन स्टेशन पर यात्रियों की भीड़"},
            {"same_story": True, "tags": "बैंक में बिजली कटौती"},
        ]
        self.assertEqual(visuals.safe_story_indices(options, "बिहार ट्रेन स्टेशन"), [0])

    def test_empty_news_never_guesses_random_visual(self):
        self.assertEqual(visuals.safe_story_indices([{"same_story": True, "tags": "train"}], ""), [])



class KineticCardColorTests(unittest.TestCase):
    def test_named_and_hex_colors_render_without_numpy_type_crash(self):
        import reel_studio
        from PIL import Image
        for color in ("yellow", "#ffc400", (255, 204, 0), [255, 204, 0], "bad-color"):
            self.assertEqual(len(reel_studio._card_rgb(color)), 3)
            frame = reel_studio._kinetic({"color": color, "big": "टिकट"}, None, 2, (320, 240))
            self.assertIsInstance(frame, Image.Image)
            self.assertEqual(frame.size, (320, 240))


class VideoMotionGateTests(unittest.TestCase):
    def test_four_seconds_of_same_picture_is_rejected(self):
        import numpy as np
        import qa
        frames = np.full((42, 101, 132), 100, dtype=np.float32)
        longest, _, _ = qa.longest_unchanged(frames)
        self.assertGreater(longest, 32)

    def test_story_scene_cuts_with_shared_background_are_recognized(self):
        import numpy as np
        import qa
        # Reuse most of the backdrop; replace a significant illustrated prop
        # every 1.3 seconds. The old gate falsely labelled such shots frozen.
        frames = np.full((52, 101, 132), 120, dtype=np.float32)
        for t in range(52):
            beat = t // 13
            frames[t, 30:85, 12+beat*20:32+beat*20] = 230
        longest, _, _ = qa.longest_unchanged(frames)
        self.assertLessEqual(longest, 32)

if __name__ == "__main__":
    unittest.main()
