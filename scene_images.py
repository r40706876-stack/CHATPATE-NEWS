"""हर line की अपनी तस्वीर — उस line की बात वाला दृश्य, हमारे 3D अंदाज़ में (28 Oct: "image same same आ रहे").
असली खबर वाली line (बबलू का तथ्य) पर असली फ़ोटो/clip ही रहती है; ये तस्वीरें कल्पना/पंच वाली lines के लिए हैं
(फूफाजी काउंटर पर टॉफी लौटा रहे) — जिनकी कोई असली फ़ोटो हो ही नहीं सकती.
पहले Gemini (image model), न चले तो Pollinations (मुफ़्त FLUX, बिना key). दोनों न चलें तो कुछ नहीं — पुराना तरीका चलता रहे.
python scene_images.py probe   → दोनों आज़माकर probe_scene_*.png
"""
import base64
import json
import os
import random
import sys
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).parent
STYLE = ("semi-realistic 3D animated film still, Pixar-like but grounded, Indian small-town setting, Indian people and "
         "clothes, warm cinematic lighting, shallow depth of field, expressive faces, landscape composition, "
         "no text, no letters, no watermark, no logo")
GEMINI_IMG = [m for m in os.getenv("GEMINI_IMAGE_MODELS", "gemini-2.5-flash-image,gemini-2.0-flash-preview-image-generation"
                                   ).split(",") if m]
_dead = set()


def _gemini(prompt, out):
    keys = [os.getenv(k) for k in ("GEMINI_API_KEY", "GEMINI_API_KEY2", "GEMINI_API_KEY3") if os.getenv(k)]
    body = {"contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"responseModalities": ["TEXT", "IMAGE"]}}
    for model in GEMINI_IMG:
        for key in keys:
            if (model, key) in _dead:
                continue
            req = urllib.request.Request(
                f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}",
                data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
            try:
                data = json.loads(urllib.request.urlopen(req, timeout=120).read())
            except Exception as e:                        # noqa: BLE001  (429/404 = इस model/key पर नहीं)
                print(f"    Gemini image {model}: {repr(e)[:90]}")
                _dead.add((model, key))
                continue
            for part in (data.get("candidates") or [{}])[0].get("content", {}).get("parts", []):
                inl = part.get("inlineData") or part.get("inline_data")
                if inl and inl.get("data"):
                    out.write_bytes(base64.b64decode(inl["data"]))
                    return True
    return False


def _pollinations(prompt, out, seed):
    url = ("https://image.pollinations.ai/prompt/" + urllib.parse.quote(prompt) +
           f"?width=1056&height=810&nologo=true&model=flux&seed={seed}")
    try:
        data = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}),
                                      timeout=180).read()
    except Exception as e:                                # noqa: BLE001
        print("    Pollinations:", repr(e)[:90])
        return False
    if len(data) < 20000:
        return False
    out.write_bytes(data)
    return True


def make(scene, out, seed=None):
    """scene = अंग्रेज़ी में दृश्य. लौटाता है "gemini"/"pollinations"/None."""
    prompt = f"{scene}. {STYLE}"
    seed = seed if seed is not None else random.randint(1, 10 ** 6)
    if os.getenv("SCENE_GEMINI", "1") == "1" and _gemini(prompt, out):
        return "gemini"
    if _pollinations(prompt, out, seed):
        return "pollinations"
    return None


def scene_text(ln, topic=""):
    """line से दृश्य: writer ने "scene" दिया हो तो वही, वरना पहली visuals खोज."""
    s = ln.get("scene_en") or (ln.get("visuals") or [""])[0]
    return s or f"Indian common man reacting to news about {topic}"


def for_episode(ep, broll_dir, max_n=4):
    """कल्पना/पंच वाली lines (बबलू के तथ्य वाली नहीं) पर {i}_scene.png. पहले से clip वाली line छोड़ो."""
    broll_dir = Path(broll_dir)
    done = 0
    for i, ln in enumerate(ep["lines"]):
        if done >= max_n or ln.get("shot") == "close":
            continue
        if ln.get("who") == "bablu" and not ln.get("punch"):
            continue                                       # तथ्य = असली फ़ोटो
        if list(broll_dir.glob(f"{i}_clip*")):
            continue
        out = broll_dir / f"{i}_0scene.png"                # नाम ऐसा कि उस line में सबसे पहले आए
        how = make(scene_text(ln, ep.get("topic", "")), out, seed=1000 + i)
        if how:
            out.with_suffix(".txt").write_text("AI दृश्य (कल्पना)", encoding="utf-8")
            done += 1
            print(f"  🎨 दृश्य → line {i + 1} ({how}): {scene_text(ln)[:60]}")
    return done


if __name__ == "__main__" and sys.argv[1:] == ["probe"]:
    for k, s in enumerate(["an Indian uncle at a railway ticket counter window refusing a toffee offered as change by the clerk",
                           "a worried Indian grandmother holding a smartphone showing an OTP message"]):
        print(k, make(s, ROOT / f"probe_scene_{k}.png", seed=42 + k))
