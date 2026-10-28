"""Protect the 3D character stage from media-policy regressions.

A licensed-media sourcing setting must not silently revert the COD episode to
static cards/split screens. Tests do not claim human editorial approval.
"""
import unittest
from talk_episode import pick_shot


class StoryShotPolicyTests(unittest.TestCase):
    def test_hybrid_policy_keeps_story_shot(self):
        ep = {"visual_policy": "news_hybrid", "style": "v2"}
        for i, scene in enumerate(("sweets", "arrival", "bill", "freight", "house")):
            with self.subTest(scene=scene):
                self.assertEqual(pick_shot(ep, i, {"scene": scene, "shot": "story", "say": "पार्सल आया"}), "story")

    def test_news_first_no_longer_needed(self):
        ep = {"visual_policy": "news_images_clips", "style": "v2"}
        self.assertEqual(pick_shot(ep, 0, {"scene": "arrival", "shot": "story", "say": "डिलीवरी"}), "story")


if __name__ == "__main__":
    unittest.main()
