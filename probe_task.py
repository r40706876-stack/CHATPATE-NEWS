# जाँच: YouTube खोज चल रही है? + meme लाइब्रेरी बनाओ (memes/*.mp4, memes/_sheet.jpg)
import clips, memes
for q in ("भारत न्यूज़ीलैंड टी20", "jio ipo"):
    r = clips.search(q, n=3)
    print("खोज", q, "→", len(r), [t[1][:40] for t in r])
memes.build()
import json; s = json.load(open("memes/status.json")); print("memes बने:", len(s), "/", len(memes.LIB))
