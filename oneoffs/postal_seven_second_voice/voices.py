import sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import subprocess

folder = Path(__file__).resolve().parent
sys.path.insert(0, str(folder.parent / "postal_recruitment_two_voices"))
import render as voices

if len(sys.argv) == 2:
    voices.OUT.mkdir(exist_ok=True)
    voices.DIALOGUE = [
        ("golu", "भैया, तीन साल पूरे। अब एम टी एस पढ़ूँ या पोस्टमैन?"),
        ("bhaiya", "पोस्टमैन का रास्ता देख। तीन साल वाली बात अभी ड्राफ्ट में है।"),
    ]
    voices.voice_parts(sys.argv[1])
else:
    with ThreadPoolExecutor(max_workers=2) as pool:
        list(pool.map(lambda role: subprocess.run([sys.executable, __file__, role], check=True), ("golu", "bhaiya")))
