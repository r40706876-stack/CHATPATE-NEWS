# जाँच: YouTube खोज + meme लाइब्रेरी (memes/*.mp4, memes/_sheet.jpg)
import clips, memes, json
r = clips.search("jio ipo", n=3)
print("खोज jio ipo →", len(r), [t[1][:40] for t in r], flush=True)
memes.build()
s = json.load(open("memes/status.json")); print("memes बने:", len(s), "/", len(memes.LIB))
