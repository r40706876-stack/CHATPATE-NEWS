"""Regression tests for the TTS fallback that previously blocked a render."""
import unittest
import numpy as np
from tts import SR, TEMPO, audio_length_issues, trim_boundary_silence


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

    def test_gemini_separator_pause_is_not_counted_as_speech(self):
        # 27 Oct: a 45-character line got 8s including a long generated pause.
        # Only remove silence at the boundaries, preserving the spoken waveform.
        lead = np.zeros(round(0.8 * SR), dtype=np.float32)
        speech = np.full(round(6.1 * SR), 0.10, dtype=np.float32)
        tail = np.zeros(round(1.1 * SR), dtype=np.float32)
        cleaned = trim_boundary_silence(np.concatenate([lead, speech, tail]))
        self.assertLess(len(cleaned) / SR, 6.4)
        self.assertGreater(len(cleaned) / SR, 6.1)
        self.assertEqual(audio_length_issues([{"say": "अ" * 45}], [cleaned], "gemini"), [])

    def test_gemini_sustained_speech_is_not_trimmed(self):
        raw = np.full(round(8.8 * SR), 0.1, dtype=np.float32)
        cleaned = trim_boundary_silence(raw)
        self.assertEqual(len(cleaned), len(raw))
        self.assertTrue(audio_length_issues([{"say": "अ" * 55}], [cleaned], "gemini"))

    def test_edge_unusually_long_line_still_rejected(self):
        line = {"say": "अ" * 56}
        audio = np.zeros(round(12.0 * SR), dtype=np.float32)
        self.assertTrue(audio_length_issues([line], [audio], "edge"))

    def test_tempo_and_tighten_remain_positive(self):
        self.assertGreater(TEMPO * 1.1, 1)


if __name__ == "__main__":
    unittest.main()
