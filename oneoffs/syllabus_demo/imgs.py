"""Post-office backgrounds for the syllabus reel: Gemini image first, free Pollinations FLUX as fallback."""
import base64, os, time, urllib.parse
from pathlib import Path
import requests

OUT = Path(os.environ["OUT_DIR"]); OUT.mkdir(parents=True, exist_ok=True)
STYLE = ("photorealistic, cinematic, warm golden light, shallow depth of field, high detail, "
         "no people, no text, no letters, no watermark, vertical 9:16")
SCENES = {
 "counter": "Interior of a grand old Indian head post office: long polished wooden public counter with brass grille windows, "
            "red India Post colour accents, ceiling fans, tall arched windows with sunlight beams, marble floor, brass queue posts",
 "outside": "Exterior of a heritage red-brick Indian post office building with arches and steps, a classic red cylindrical "
            "Indian letter box in front, trees, clear blue morning sky",
 "verandah": "Arched verandah corridor of a heritage red-brick Indian post office, terracotta arches, potted plants, "
             "soft daylight, stone floor, a red letter box at the far end",
 "desk": "Indian post office back-office sorting desk with stacks of letters, parcels, rubber stamps, ink pad, "
         "postal scale and pigeon-hole sorting rack, warm lamp light",
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
            r = requests.get(url, params={"width": 1080, "height": 1920, "model": "flux", "nologo": "true",
                                          "seed": seed, "enhance": "false"}, timeout=240)
            if r.status_code == 200 and len(r.content) > 20000: return r.content
            print("poll", r.status_code, len(r.content))
        except requests.RequestException as e:
            print("poll err", e)
        time.sleep(8)
    return None

for name, desc in SCENES.items():
    prompt = f"{desc}. {STYLE}"
    data = gemini(prompt)
    if data:
        (OUT / f"{name}_gemini.png").write_bytes(data); print("gemini ok", name)
    for seed in (11, 29):
        data = pollinations(prompt, seed)
        if data: (OUT / f"{name}_flux_{seed}.jpg").write_bytes(data); print("flux ok", name, seed)
