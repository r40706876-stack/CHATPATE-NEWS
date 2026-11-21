from concurrent.futures import ThreadPoolExecutor
import json
import importlib.util
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("existing_voices", HERE.parent / "postal_recruitment_two_voices" / "render.py")
generator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(generator)

if len(sys.argv) == 2:
    generator.OUT = Path.cwd() / "reel-work" / "voices"
    generator.OUT.mkdir(parents=True, exist_ok=True)
    generator.DIALOGUE = json.loads((HERE/"dialogue.json").read_text())
    generator.voice_parts(sys.argv[1])
else:
    with ThreadPoolExecutor(max_workers=2) as executor:
        list(executor.map(lambda role: subprocess.run([sys.executable, __file__, role], check=True), ("golu","bhaiya")))
