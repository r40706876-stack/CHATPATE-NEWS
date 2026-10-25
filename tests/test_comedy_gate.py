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


if __name__ == "__main__":
    unittest.main()
