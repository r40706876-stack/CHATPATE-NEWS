# memes दोबारा: हर meme का पूरा dialogue Gemini से सुनकर, चुप्पी पर कटा (पुराने 0-2.6 सेकंड वाले अधूरे clips की जगह)
import json, time
t0 = time.time()
import memes
memes.build()
s = json.load(open("memes/status.json"))
good = [m for m, *_ in memes.LIB if (s.get(m) or {}).get("verified")]
print(f"\nपूरे dialogue वाले memes: {len(good)} / {len(memes.LIB)}  ({time.time() - t0:.0f}s)")
for m, *_ in memes.LIB:
    x = s.get(m) or {}
    print(("✅" if x.get("verified") else "❌"), m, x.get("secs"), "|", x.get("heard", ""), "|", (x.get("title") or "")[:50])
