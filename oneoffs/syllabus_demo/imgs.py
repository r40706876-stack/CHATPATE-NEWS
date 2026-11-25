"""Premium post-office backgrounds via Gemini/Imagen on all 4 Bakra keys (no free fallback)."""
import base64, os, requests
from pathlib import Path
OUT = Path(os.environ["OUT_DIR"]); OUT.mkdir(parents=True, exist_ok=True)
keys = [k for k in (os.environ.get(f"K{n}", "") for n in (1, 2, 3, 4)) if k.strip()]
BASE = "https://generativelanguage.googleapis.com/v1beta"
STYLE = ("Ultra-detailed photorealistic photograph, 35mm lens, cinematic warm golden-hour light, gentle depth of field, rich "
         "clean colours, premium editorial look. Strictly no people, no readable text, no logos, no watermark. Vertical 9:16.")
SCENES = {
 "counter": "Inside a grand heritage Indian head post office public hall: long polished teak counter with brass-grille teller "
            "windows, rubber stamps and ink pad on the counter, a red cylindrical Indian post box beside the counter, parcels on "
            "a weighing scale, ceiling fans, tall arched windows with sunbeams, marble floor with brass queue stands",
 "outside": "Front of a heritage red-brick Indian post office building with arches and steps, a red cylindrical Indian post box "
            "with dome top on the footpath in front, a postman's bicycle with khaki mail bag parked near the gate, neem tree, morning sky",
 "sorting": "Indian post office sorting room: tall wooden pigeon-hole sorting rack full of letters, khaki canvas mail bags with "
            "drawstrings, wooden table with bundled letters tied with string, rubber stamps, warm window light, dust in sunbeams",
 "verandah": "Arched verandah of a heritage red-brick Indian post office, terracotta arches in perspective, potted plants, "
             "stone floor, a red Indian post box at the far end, soft daylight",
}
# discover image-capable models on each key
models = []
for key in keys:
    r = requests.get(f"{BASE}/models", params={"key": key, "pageSize": 1000}, timeout=60)
    for m in r.json().get("models", []):
        n = m["name"].split("/")[-1]
        if ("image" in n or "imagen" in n) and n not in models: models.append(n)
print("image models:", models, flush=True)

def try_one(model, key, prompt):
    if model.startswith("imagen"):
        r = requests.post(f"{BASE}/models/{model}:predict", params={"key": key}, timeout=240,
                          json={"instances": [{"prompt": prompt}], "parameters": {"sampleCount": 1, "aspectRatio": "9:16"}})
        if r.status_code == 200:
            p = r.json().get("predictions", [])
            if p and p[0].get("bytesBase64Encoded"): return base64.b64decode(p[0]["bytesBase64Encoded"])
    else:
        r = requests.post(f"{BASE}/models/{model}:generateContent", params={"key": key}, timeout=240,
                          json={"contents": [{"parts": [{"text": prompt}]}],
                                "generationConfig": {"responseModalities": ["TEXT", "IMAGE"], "imageConfig": {"aspectRatio": "9:16"}}})
        if r.status_code == 200:
            for c in r.json().get("candidates", []):
                for part in c.get("content", {}).get("parts", []):
                    d = part.get("inlineData") or part.get("inline_data")
                    if d: return base64.b64decode(d["data"])
    print("  ", model, "key", keys.index(key) + 1, r.status_code, r.text[:600].replace("\n", " "), flush=True)
    return None

working = None
for name, desc in SCENES.items():
    prompt = f"{desc}. {STYLE}"
    order = [working] + [m for m in models if m != working] if working else models
    done = False
    for model in order:
        for key in keys:
            data = try_one(model, key, prompt)
            if data:
                (OUT / f"{name}.png").write_bytes(data); working = model; done = True
                print("OK", name, model, len(data), flush=True); break
        if done: break
    if not done: print("FAILED", name)
