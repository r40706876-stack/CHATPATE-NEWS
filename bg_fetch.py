"""हर किरदार के लिए गाँव वाली पृष्ठभूमि के विकल्प (Pixabay photos) → assets/bg_options + preview_bg.jpg"""
import json, os, urllib.parse, urllib.request
from pathlib import Path
from PIL import Image, ImageDraw
Q = {"bablu": ["indian village street", "village road india"],
     "ramesh": ["indian village shop", "rural india house wall"],
     "chacha": ["indian tea stall", "village courtyard india"],
     "dadi": ["indian village house courtyard", "rural kitchen india"],
     "pinky": ["indian village field", "mustard field india"]}
key = os.environ["PIXABAY_API_KEY"]
out = Path("assets/bg_options"); out.mkdir(parents=True, exist_ok=True)
sheet = Image.new("RGB", (6 * 240, 5 * 200), "black"); d = ImageDraw.Draw(sheet)
for r, (who, qs) in enumerate(Q.items()):
    got = []
    for q in qs:
        u = f"https://pixabay.com/api/?key={key}&q={urllib.parse.quote(q)}&image_type=photo&per_page=10&safesearch=true&min_width=1200"
        hits = json.load(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"}), timeout=30))["hits"]
        got += [h for h in hits[:3]]
    for c, h in enumerate(got[:6]):
        p = out / f"{who}_{c}.jpg"
        p.write_bytes(urllib.request.urlopen(urllib.request.Request(h["largeImageURL"], headers={"User-Agent": "Mozilla/5.0"}), timeout=60).read())
        im = Image.open(p).convert("RGB"); im.thumbnail((240, 180))
        sheet.paste(im, (c * 240, r * 200)); d.text((c * 240 + 4, r * 200 + 182), f"{who}_{c}", fill="yellow")
sheet.save("preview_bg.jpg")
