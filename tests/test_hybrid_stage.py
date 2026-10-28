"""Static visual QA for the hybrid stage, independent of TTS/network."""
import unittest
import numpy as np
from hybrid_stage import stage_frames, concept_of


def gray_small(image):
    return np.asarray(image.convert("L").resize((132, 101)), dtype=np.float32)


class HybridStageTests(unittest.TestCase):
    def test_cod_punchline_concepts(self):
        self.assertEqual(concept_of("लड्डू में HDMI लगाऊँ?"), "laddoo_hdmi")
        self.assertEqual(concept_of("टीवी का बिल ₹1.69 लाख"), "receipt")
        self.assertEqual(concept_of("अब डिलीवरी वाला कह रहा"), "delivery")

    def test_opening_has_visible_cut_before_half_second(self):
        frames = stage_frames({"topic": "parcel", "concept": "television", "caption": "टीवी का झटका"}, (1056, 810))
        first = gray_small(next(frames))
        half = None
        later = None
        for t in range(1, 76):
            frame = next(frames)
            if t == 13:
                half = gray_small(frame)
            if t == 45:
                later = gray_small(frame)
        self.assertGreater(float(np.abs(first - half).mean()), 2.0)
        self.assertGreater(float(np.abs(first - later).mean()), 10.0)


if __name__ == "__main__":
    unittest.main()
