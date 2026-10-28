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
        log = "Integrated loudness:\n    I: -17.8 LUFS\n    Threshold: -28.3 LUFS"
        self.assertEqual(_integrated_lufs(log), -17.8)

    def test_integrated_loudness_missing_fails_closed(self):
        self.assertIsNone(_integrated_lufs("no summary"))

    def test_missing_meter_fails_closed(self):
        self.assertIsNone(_true_peak_dbfs("audio finished but no true peak"))

    @unittest.skipUnless(__import__("shutil").which("ffmpeg"), "ffmpeg unavailable")
    def test_studio_final_audio_filter_survives_aac_true_peak_meter(self):
        """Run the actual production filter, encode AAC, and meter decoded true peak."""
        import subprocess
        import tempfile
        from pathlib import Path
        from reel_studio import STUDIO_AUDIO_FILTER

        self.assertIn("alimiter=limit=", STUDIO_AUDIO_FILTER)
        self.assertIn("level=0", STUDIO_AUDIO_FILTER)
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "delivery.m4a"
            subprocess.run([
                "ffmpeg", "-v", "error", "-y", "-f", "lavfi",
                "-i", "sine=frequency=440:duration=4:sample_rate=24000",
                "-af", STUDIO_AUDIO_FILTER, "-c:a", "aac", "-b:a", "160k",
                str(out)
            ], check=True)
            meter = subprocess.run([
                "ffmpeg", "-hide_banner", "-nostats", "-i", str(out), "-vn",
                "-af", "ebur128=peak=true", "-f", "null", "-"
            ], capture_output=True, text=True, check=True)
            peak = _true_peak_dbfs(meter.stderr)
            loudness = _integrated_lufs(meter.stderr)
            self.assertIsNotNone(peak)
            self.assertIsNotNone(loudness)
            self.assertLess(peak, -1.0, f"Decoded AAC true peak: {peak} dBTP")
            self.assertGreaterEqual(loudness, -21.0)
            self.assertLessEqual(loudness, -12.0)

    @unittest.skipUnless(__import__("shutil").which("ffmpeg"), "ffmpeg unavailable")
    def test_sfx_overlay_keeps_decoded_aac_peak_and_loudness_safe(self):
        """Catch clipping added AFTER the main reel's loudnorm pass."""
        import subprocess
        import tempfile
        from pathlib import Path
        from unittest.mock import patch
        import memes

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            base, sfx, out = (root / x for x in ("base.mp4", "boom.wav", "mixed.mp4"))
            subprocess.run([
                "ffmpeg", "-v", "error", "-y",
                "-f", "lavfi", "-i", "color=c=blue:s=160x288:r=12:d=4",
                "-f", "lavfi", "-i", "sine=frequency=440:duration=4:sample_rate=44100",
                "-af", "volume=0.65", "-c:v", "mpeg4", "-c:a", "aac",
                "-shortest", str(base)
            ], check=True)
            subprocess.run([
                "ffmpeg", "-v", "error", "-y", "-f", "lavfi",
                "-i", "sine=frequency=120:duration=0.5:sample_rate=44100",
                "-af", "volume=8", "-c:a", "pcm_s16le", str(sfx)
            ], check=True)
            with patch.object(memes, "_sfx_ok", return_value=sfx):
                self.assertEqual(memes.overlay_sfx(base, [(1.0, "sfx_vine_boom")], out), out)
            meter = subprocess.run([
                "ffmpeg", "-hide_banner", "-nostats", "-i", str(out), "-vn",
                "-af", "ebur128=peak=true", "-f", "null", "-"
            ], capture_output=True, text=True, check=True)
            peak = _true_peak_dbfs(meter.stderr)
            loudness = _integrated_lufs(meter.stderr)
            self.assertIsNotNone(peak)
            self.assertIsNotNone(loudness)
            self.assertLess(peak, -1.0, f"AAC true peak: {peak} dBTP")
            self.assertGreaterEqual(loudness, -21.0)
            self.assertLessEqual(loudness, -12.0)

if __name__ == "__main__":
    unittest.main()
