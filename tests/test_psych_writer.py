"""psych_writer की plumbing (Gemini नकली): premise → 2 scripts → दर्शक-जज → punch-up → finish."""
import json
import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault("PSYCH", "1")
import gemini  # noqa: E402
import news_writer as nw  # noqa: E402

LINES = [{"who": "bablu", "say": "SBI ने फिर कहा है, हम कभी आपका डेटा नहीं माँगते.", "caption": "SBI: हम डेटा नहीं माँगते",
          "expr": "gambhir", "set": "studio", "visuals": ["sbi bank branch"], "photo_hi": ["SBI डेटा लीक"]},
         {"who": "bablu", "say": "माँगने की ज़रूरत भी नहीं. चार हज़ार ग्राहकों का डेटा डार्क वेब पर है.",
          "caption": "4000 ग्राहकों का डेटा डार्क वेब पर", "expr": "gambhir", "set": "bank", "visuals": ["laptop hacker"]},
         {"who": "ramesh", "say": "मैं पासबुक अपडेट कराने तीन बार लाइन में लगा.", "caption": "पासबुक के लिए 3 बार लाइन",
          "expr": "gussa", "set": "bank", "visuals": ["bank queue india"], "tag": True, "tag_screen": "वो जो पासबुक लेकर खड़ा"},
         {"who": "dadi", "say": "मैं अपना OTP पोते को नहीं बताती.", "caption": "मैं OTP पोते को नहीं बताती",
          "expr": "tanz", "set": "aangan", "visuals": ["old woman phone"]},
         {"who": "bablu", "say": "SBI की अपील है, अपना डेटा किसी को मत दीजिए. जो बचा है.", "caption": "डेटा मत दीजिए… जो बचा है",
          "expr": "gambhir", "set": "studio", "visuals": ["sbi logo board"], "punch": True, "stamp": "जो बचा है"}]


def fake(prompt, **kw):
    p = prompt if isinstance(prompt, str) else ""
    if "6 premise" in p:
        return json.dumps([{"topic": "SBI डेटा लीक", "premises": [
            {"premise": "डेटा माँगते नहीं क्योंकि बिक रहा है", "hook": "SBI ने फिर कहा…", "hasi": 8, "pehchaan_score": 7, "hook_score": 9},
            {"premise": "पासबुक की लाइन", "hook": "…", "hasi": 6, "pehchaan_score": 9, "hook_score": 5}]}])
    if "2 अलग scripts" in p:
        v = {"premise": "x", "breaking": "4000 SBI ग्राहकों का डेटा लीक", "source": "NDTV", "tag_who": "पापा",
             "lines": LINES}
        return json.dumps([{"topic": "SBI डेटा लीक", "versions": [v, dict(v, premise="y")]}])
    if "22 साल" in p:
        allok = {k: {"ok": True, "kyon": "x"} for k in ("pura", "hasi", "share", "daily", "follow", "like", "save", "ant", "khabar", "dhaga")}
        if p.count('"topic"') == 1:                                # punch-up के बाद दोबारा जाँच
            return json.dumps([{"id": 0, "score": 9, "jaanch": allok}])
        return json.dumps([{"id": 0, "score": 9, "kamzor": [3], "jaanch": dict(allok, share={"ok": False, "kyon": "किसे?"})},
                           {"id": 1, "score": 8, "kamzor": [], "jaanch": dict(allok, save={"ok": False, "kyon": ""})}])
    if "punch-up" in p:
        return json.dumps([{"id": 0, "lines": LINES}])
    raise AssertionError("अनजाना prompt")


class PsychWriter(unittest.TestCase):
    def test_pipeline(self):
        old = gemini.ask
        gemini.ask = fake
        try:
            packs = [{"topic": "SBI डेटा लीक", "facts": ["4000 ग्राहक"], "source": "NDTV"}]
            picks = [{"topic": "SBI डेटा लीक", "trend": {"score": 6, "why": "6 अख़बार"}, "cat": "bank"}]
            eps = nw._write_psych({}, packs, picks, 3)
        finally:
            gemini.ask = old
        self.assertEqual(len(eps), 1)
        # B जीता (core पास), फिर punch-up के बाद 7/7 → बदला गया
        self.assertEqual(eps[0]["connect"]["score"], 9)
        self.assertTrue(all(v["ok"] for v in eps[0]["jaanch"].values()))
        import run_daily
        self.assertIn("🧪 जाँच 10/10", run_daily.preview(eps))
        self.assertTrue(eps[0]["lines"][0]["say"].startswith("SBI"))
        self.assertTrue(any(l.get("tag_text") for l in eps[0]["lines"]))


if __name__ == "__main__":
    unittest.main()


class Fragments(unittest.TestCase):
    def test_fragment_fails_ending(self):
        import psych_writer as pw
        c = {"ep": {"lines": [{"say": "बॉलर डरा नहीं पाए."}, {"say": "जितना बलिया की चाची ने डरा दिया."}]},
             "vote": {"jaanch": {"ant": {"ok": True}}}}
        pw._code_check(c)
        self.assertIn("ant", pw._fails(c["vote"]))
        self.assertIn(1, c["vote"]["kamzor"])


class Copy(unittest.TestCase):
    def test_external_copy_flagged(self):
        import psych_writer as pw
        pw._EXT = ["वन विभाग ने मगरमच्छ होने से इंकार किया है"]
        c = {"ep": {"lines": [{"say": "वन विभाग ने मगरमच्छ होने से इनकार किया है."}, {"say": "वन विभाग ने मगरमच्छ होने से इनकार किया."},
                              {"say": "हमारी अपनी line है ये."}]},
             "vote": {"jaanch": {"hasi": {"ok": True}}}}
        pw._code_check(c)
        self.assertIn("hasi", pw._fails(c["vote"]))
        pw._EXT = None
