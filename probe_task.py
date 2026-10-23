# जाँच: YouTube खोज + meme लाइब्रेरी (memes/*.mp4, memes/_sheet.jpg)
import time, json
t0 = time.time()
import clips, memes
print("deno:", __import__("shutil").which("deno"), flush=True)
r = clips.search("jio ipo", n=3)
print(f"खोज jio ipo → {len(r)} ({time.time()-t0:.0f}s)", [t[1][:40] for t in r], flush=True)
memes.build()
s = json.load(open("memes/status.json")); print("memes बने:", len(s), "/", len(memes.LIB), f"({time.time()-t0:.0f}s)")
