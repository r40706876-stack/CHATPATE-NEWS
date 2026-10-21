import subprocess, shutil
from pathlib import Path
import clips
print("ffmpeg:", shutil.which("ffmpeg"))
res = clips.search("paramotor flies to work", 3)
url = [r for r in res if "Controller" in r[1]][0][0] if any("Controller" in r[1] for r in res) else res[0][0]
out = Path("probe_clip.mp4"); tmp = out.with_suffix(".src.mp4")
cmd = clips._ytdlp() + ["--no-playlist", "-f", "bv*[height<=720][ext=mp4]/bv*[height<=720]/b[height<=720]",
       "--download-sections", "*30.0-34.0", "--force-keyframes-at-cuts", "-o", str(tmp)] + clips._cookies("YT_COOKIES") + [url]
r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
print("rc", r.returncode, "| out:", r.stdout[-300:], "| err:", r.stderr[-900:])
print([ (p.name, p.stat().st_size) for p in Path(".").glob("probe_clip*")])
