import subprocess, sys, json
subprocess.run([sys.executable, "-m", "pip", "install", "-q", "--break-system-packages", "yt-dlp"])
import clips
r = subprocess.run(clips._ytdlp() + ["--flat-playlist", "-J", "ytsearch5:paramotor office viral"], capture_output=True, text=True, timeout=120)
print("SEARCH rc", r.returncode, "| err:", r.stderr[-600:])
try:
    e = json.loads(r.stdout).get("entries") or []
    print("found", len(e), [x.get("title") for x in e][:3])
    url = e[0]["url"] if e else "https://www.youtube.com/watch?v=jNQXAC9IVRw"
except Exception as x:
    print("parse fail", x); url = "https://www.youtube.com/watch?v=jNQXAC9IVRw"
from pathlib import Path
p = clips.cut(url, Path("probe_clip.mp4"), 3)
print("CUT ->", p)
r = subprocess.run(clips._ytdlp() + ["-v", "--simulate", "-f", "bv*[height<=720]", url], capture_output=True, text=True, timeout=120)
print("DL rc", r.returncode, "| err tail:", r.stderr[-900:])
