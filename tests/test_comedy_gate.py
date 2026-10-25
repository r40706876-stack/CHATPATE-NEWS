"""Offline regression tests for comedy format and script quality gates."""
import unittest
from unittest.mock import patch
import bakra_rules
import run_daily


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

    def test_rejected_scripts_never_escape_gate(self):
        with patch("news_writer._safe", return_value={}), \\
             patch("news_writer.gather", return_value=([], [])), \\
             patch("news_writer.write_from", return_value=[episode(first="नमस्कार दोस्तों, खबर सुनिए")]):
            self.assertEqual(run_daily.write_scripts({}, 1), [])


if __name__ == "__main__":
    unittest.main()
