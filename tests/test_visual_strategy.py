"""Regression tests for visual relevance and zero-network fallback."""
import unittest
from visual_strategy import select_visual, compare_visual_options

class VisualStrategyTests(unittest.TestCase):
    def test_train_story_never_shows_parcels(self):
        vis, reason = select_visual({"say": "ट्रेन की सीट नहीं मिली"}, {"title": "रेलवे टिकट नियम"})
        self.assertEqual(reason, "animated-stage:train")
        self.assertTrue(all("scene" not in item for item in vis))

    def test_delivery_story_shows_matching_parcel(self):
        vis, reason = select_visual({"say": "पार्सल घर आ गया"}, {"title": "COD पार्सल"})
        self.assertEqual(reason, "illustrated:delivery")
        self.assertEqual(vis[0]["scene"], "delivery")

    def test_laddoo_punch_matches_visual(self):
        vis, reason = select_visual({"say": "लड्डू में HDMI लगा दिया"}, {"title": "COD पार्सल"})
        self.assertEqual(reason, "illustrated:laddoo_hdmi")

    def test_cod_story_without_matching_props_uses_kinetic(self):
        vis, reason = select_visual({"say": "चाचा ने कहा कि ये बहुत अजीब है"}, {"title": "COD पार्सल"})
        self.assertEqual(reason, "animated-stage:parcel")
        self.assertTrue(all("scene" not in item for item in vis))

    def test_non_delivery_line_uses_own_caption(self):
        vis, reason = select_visual(
            {"say": "रेलवे का नियम बदला", "caption": "टिकट वाला नया झटका"},
            {"title": "रेलवे टिकट"})
        self.assertEqual(reason, "animated-stage:train")
        self.assertEqual(vis[0]["caption"], "टिकट वाला नया झटका")

    def test_unknown_news_fallback(self):
        vis, reason = select_visual({"say": "क्या हुआ?"}, {})
        self.assertEqual(reason, "animated-stage:news")
        self.assertTrue(vis[0]["caption"])

    def test_comparison_is_not_retention_claim(self):
        result = compare_visual_options({"say": "बिल आया"}, {"title": "COD पार्सल"})
        self.assertIn("chosen", result)
        self.assertNotIn("retention", result)

if __name__ == "__main__":
    unittest.main()
