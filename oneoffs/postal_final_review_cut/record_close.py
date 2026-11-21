from pathlib import Path
import importlib.util

folder = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("voices", folder.parent / "postal_recruitment_two_voices" / "render.py")
voices = importlib.util.module_from_spec(spec)
spec.loader.exec_module(voices)
voices.OUT = Path.cwd() / "reel-work"
voices.DIALOGUE = [("golu", "कोई साथी पोस्टमैन की तैयारी कर रहा है? उसे ये वीडियो भेज देना, ताकि उसे भी सही बात पता चले।")]
voices.voice_parts("golu")
