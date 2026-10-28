"""असली data वाला loop: delivered → 'डेटा …' → lessons."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import results  # noqa: E402


class Loop(unittest.TestCase):
    def setUp(self):
        d = Path(tempfile.mkdtemp())
        results.FILE, results.LAST = d / "r.json", d / "l.json"

    def test_flow(self):
        ep = {"topic": "फ़ोन महंगे AI", "cold_open": {"kind": "phone"},
              "lines": [{"who": "bablu", "say": "नया फ़ोन लिया?"}, {"who": "ramesh", "say": "AI बोला मुझे बंद करो."}]}
        results.delivered(ep, 26.0)
        self.assertIsNone(results.record("2"))                       # नंबर वाला जवाब data नहीं
        ans = results.record("डेटा skip 40 watch 13 share 2")
        self.assertIn("याद रखा", ans)
        row = json.load(open(results.FILE, encoding="utf-8"))[0]
        self.assertEqual((row["skip"], row["watch"], row["cold_open"]), (40.0, 13.0, "phone"))
        self.assertIn("skip 40.0%", results.lessons())


if __name__ == "__main__":
    unittest.main()
