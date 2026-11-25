"""Post-office backgrounds for the syllabus reel: Gemini image first, free Pollinations FLUX as fallback."""
import base64, os, time, urllib.parse
from pathlib import Path
import requests

OUT = Path(os.environ["OUT_DIR"]); OUT.mkdir(parents=True, exist_ok=True)
STYLE = ("photorealistic, cinematic, warm golden light, shallow depth of field, high detail, "
         "no people, no text, no letters, no watermark, vertical 9:16")
SCENES = {
 "counter": "Inside a busy-looking but empty Indian government post office: a long wooden public counter with several brass-grille "
            "teller windows, rubber stamps and ink pads on the counter, a red cylindrical Indian letter box standing beside the counter, "
            "parcels on a weighing scale, old wall clock, ceiling fans, cream walls with red trim, sunlight through arched windows",
 "outside": "Front of a small Indian town post office building painted cream and red, a red cylindrical Indian letter box on the "
            "footpath in front, bicycle parked near the gate, steps and veranda, neem tree, bright morning",
 "sorting": "Indian post office sorting room: wooden pigeon-hole sorting rack full of letters and postcards, khaki mail bags with "
            "drawstrings, a wooden table with bundles of letters tied with string, rubber stamps, warm window light",
 "letterbox": "Close view of a classic red cylindrical Indian post box with a dome top on a village street outside a post office, "
              "soft golden evening light, blurred background",
}
keys = [k for k in (os.environ.get(f"K{n}", "") for n in (1, 2, 3, 4)) if k.strip()]

def gemini(prompt):
    for model in ("gemini-2.5-flash-image", "gemini-2.0-flash-preview-image-generation"):
        for key in keys:
            body = {"contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {"responseModalities": ["IMAGE", "TEXT"], "imageConfig": {"aspectRatio": "9:16"}}}
            try:
                r = requests.post(f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
                                  params={"key": key}, json=body, timeout=180)
            except requests.RequestException as e:
                print("gemini err", e); continue
            if r.status_code != 200:
                print("gemini", model, r.status_code, r.text[:160]); continue
            for c in r.json().get("candidates", []):
                for p in c.get("content", {}).get("parts", []):
                    d = p.get("inlineData") or p.get("inline_data")
                    if d: return base64.b64decode(d["data"])
    return None

def pollinations(prompt, seed):
    url = "https://image.pollinations.ai/prompt/" + urllib.parse.quote(prompt)
    for attempt in range(4):
        try:
            r = requests.get(url, params={"width": 864, "height": 1536, "model": "flux", "nologo": "true",
                                          "seed": seed, "enhance": "false"}, timeout=240)
            if r.status_code == 200 and len(r.content) > 20000: return r.content
            print("poll", r.status_code, len(r.content))
        except requests.RequestException as e:
            print("poll err", e)
        time.sleep(8)
    return None

for name, desc in SCENES.items():
    prompt = f"{desc}. {STYLE}"
    for seed in (3, 17, 41, 77):
        data = pollinations(prompt, seed)
        if data: (OUT / f"{name}_flux_{seed}.jpg").write_bytes(data); print("flux ok", name, seed)
