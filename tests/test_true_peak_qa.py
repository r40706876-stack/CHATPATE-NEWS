"""Ensure a real decoded AAC true-peak failure is never silently accepted."""
import unittest
from qa import _true_peak_dbfs, _integrated_lufs

class TruePeakQATests(unittest.TestCase):
    def test_ffmpeg_multiline_summary(self):
        log = "  True peak:\n    Peak:        0.2 dBFS\n"
        self.assertEqual(_true_peak_dbfs(log), 0.2)
    def test_safe_headroom(self):
        self.assertEqual(_true_peak_dbfs("True peak:\n Peak: -1.8 dBFS"), -1.8)
    def test_integrated_loudness_summary(self):
        log = "Integrated loudness:\\n    I: -17.8 LUFS\\n    Threshold: -28.3 LUFS"
        self.assertEqual(_integrated_lufs(log), -17.8)

    def test_integrated_loudness_missing_fails_closed(self):
        self.assertIsNone(_integrated_lufs("no summary"))

    def test_missing_meter_fails_closed(self):
        self.assertIsNone(_true_peak_dbfs("audio finished but no true peak"))

if __name__ == "__main__":
    unittest.main()
