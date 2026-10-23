# जाँच: YouTube खोज + meme लाइब्रेरी (memes/*.mp4, memes/_sheet.jpg)
import time, json, subprocess
t0 = time.time()
import clips, memes
print("deno:", __import__("shutil").which("deno"), flush=True)
for pre in ("ytsearch", "ytsearchdate"):
    r = subprocess.run(clips._ytdlp() + ["--flat-playlist", "-J", f"{pre}3:jio ipo"] + clips._cookies("YT_COOKIES"),
                       capture_output=True, text=True, timeout=60)
    print(pre, "stdout:", r.stdout[:200].replace("\n", " "), "| stderr:", r.stderr[-600:], flush=True)
r = subprocess.run(clips._ytdlp() + ["--flat-playlist", "-J", "ytsearch3:jio ipo"], capture_output=True, text=True, timeout=60)
print("बिना cookies stdout:", r.stdout[:200].replace("\n", " "), "| stderr:", r.stderr[-400:], flush=True)
print("yt-dlp version:", subprocess.run(clips._ytdlp() + ["--version"], capture_output=True, text=True).stdout, flush=True)
memes.build()
s = json.load(open("memes/status.json")); print("memes बने:", len(s), "/", len(memes.LIB) + len(memes.SFX), f"({time.time()-t0:.0f}s)")
