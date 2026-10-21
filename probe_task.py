import subprocess, shutil
import clips
print("deno:", shutil.which("deno"))
url = clips.search("paramotor flies to work", 2)[0][0]
r = subprocess.run(clips._ytdlp() + ["--simulate", "-f", "bv*[height<=720]/b"] + clips._cookies("YT_COOKIES") + [url], capture_output=True, text=True, timeout=180)
print("DL rc", r.returncode, "| err:", r.stderr[-900:])
