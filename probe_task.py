import subprocess, sys
from pathlib import Path
import clips
res = clips.search("paramotor flies to work", 3)
print("SEARCH:", [(t, d) for _, t, _, d in res])
url = res[0][0]
print("CUT:", clips.cut(url, Path("probe_clip.mp4"), 10))
r = subprocess.run(clips._ytdlp() + ["--simulate", "-f", "bv*[height<=720]/b"] + clips._cookies("YT_COOKIES") + [url], capture_output=True, text=True, timeout=180)
print("DL rc", r.returncode, "| err:", r.stderr[-700:])
