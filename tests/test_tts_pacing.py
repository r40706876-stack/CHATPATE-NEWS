"""Regression tests for the TTS fallback that previously blocked a render."""
import unittest
import numpy as np
from tts import SR, TEMPO, audio_length_issues


class TTSPacingTests(unittest.TestCase):
    def test_edge_seven_point_two_seconds_is_fast_enough_after_processing(self):
        # 26 Oct failure: Edge produced 7.2s for a 56-char line and was rejected.
        line = {"say": "अ" * 56}
        audio = np.zeros(round(7.2 * SR), dtype=np.float32)
        self.assertEqual(audio_length_issues([line], [audio], "edge"), [])

    def test_gemini_normal_fifty_char_line_not_rejected_as_hallucination(self):
        line = {"say": "अ" * 50}
        audio = np.zeros(round(7.3 * SR), dtype=np.float32)
        self.assertEqual(audio_length_issues([line], [audio], "gemini"), [])

    def test_gemini_extra_speech_is_still_rejected(self):
        line = {"say": "अ" * 55}
        audio = np.zeros(round(8.8 * SR), dtype=np.float32)
        self.assertTrue(audio_length_issues([line], [audio], "gemini"))

    def test_edge_unusually_long_line_still_rejected(self):
        line = {"say": "अ" * 56}
        audio = np.zeros(round(12.0 * SR), dtype=np.float32)
        self.assertTrue(audio_length_issues([line], [audio], "edge"))

    def test_tempo_and_tighten_remain_positive(self):
        self.assertGreater(TEMPO * 1.1, 1)


if __name__ == "__main__":
    unittest.main()
