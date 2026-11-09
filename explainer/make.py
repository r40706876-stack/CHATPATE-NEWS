"""
"काम की बात" motion-graphics explainer (9 Nov 2026 demo) — LifeFixerTV जैसी शैली, पर हमारे अपने रंग/design.
पूरा automatic: topic → Gemini (Google Search से तथ्य) दृश्य-योजना JSON → हर दृश्य की Gemini आवाज़ →
HTML/CSS animated templates (explainer/scenes.html) Playwright से 30fps frames → ffmpeg → Telegram.
चलाना: python explainer/make.py "विषय"   (GitHub: explainer.yml)
"""
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import gemini  # noqa: E402

HERE = Path(__file__).resolve().parent
TYPES = {
    "hook": 'पहला दृश्य: {"title": "3-6 शब्द, बड़े अक्षर", "hl": ["title के 1-2 शब्द जो पीले हों"], "emoji": "1 emoji", "tag": "छोटा label जैसे ₹1,00,000 (वैकल्पिक)"}',
    "chat": '{"badge": "छोटा ऊपरी label (वैकल्पिक)", "title": "...", "header": "किससे बात", "msgs": [{"me": true, "text": "≤8 शब्द"}, {"me": false, "text": "..."}]} (2-3 msgs)',
    "dialer": '{"badge": "...", "title": "...", "number": "helpline नंबर", "label": "किसकी helpline"}',
    "question": '{"title": "...", "text": "सवाल ≤8 शब्द", "hl": ["..."]}',
    "steps": '{"badge": "...", "title": "...", "labels": ["2-3 शब्द", "...", "..."], "active": 1}  (2-4 रास्ते; active = अभी कौन सा)',
    "card": '{"badge": "...", "title": "...", "emoji": "1 emoji", "card_title": "...", "lines": ["≤7 शब्द", "..."]} (1-3 lines)',
    "deadline": '{"badge": "...", "title": "...", "big": "48", "unit": "घंटे", "note": "≤10 शब्द"}',
    "calendar": '{"badge": "...", "title": "...", "big": "30", "unit": "दिन", "note": "≤10 शब्द"}',
    "form": '{"badge": "...", "title": "...", "site": "website पता", "form_title": "...", "fields": [["label", "उदाहरण"], ...], "button": "Submit"} (2-3 fields)',
    "money": '{"badge": "...", "title": "...", "card_title": "...", "rows": [["मद", "₹..."], ...], "total": ["कुल", "₹..."]}',
    "news": '{"badge": "...", "title": "...", "source": "अख़बार/तारीख", "headline": "...", "body": "1-2 वाक्य", "stamp": "जीत/WIN (वैकल्पिक)"}',
    "outro": 'आख़िरी दृश्य: {"title": "...", "handle": "@page", "button": "Follow"}',
}

PLAN = """तुम एक Hindi "काम की बात" explainer reel की script और दृश्य-योजना बनाते हो (60 सेकंड, 9:16, motion graphics, कोई चेहरा नहीं).
विषय: {topic}

Google Search से असली, ताज़ा, सही जानकारी लो (helpline नंबर, नियम/धारा, समय-सीमा, website, कोई असली केस हो तो).
जो पक्का न हो वो मत लिखो.

बोलने का अंदाज़: आम बोलचाल की Hinglish (जैसे दोस्त समझा रहा हो), छोटे वाक्य, "आप" से बात. ढाँचा:
1. hook — रोज़ की ज़िंदगी की एक तकलीफ़ वाली स्थिति, पहले 3 सेकंड में ("एक लाख का फ़ोन मँगाया, डिब्बा खोला… साबुन!")
2. आम ग़लत रास्ता/उलझन → 3. "रास्ता 1, 2, 3" साफ़ steps (नंबर, website, समय-सीमा के साथ) → 4. कोई असली केस/नतीजा (अगर मिले)
→ 5. आख़िरी: "ऐसी और ज़रूरी बातों के लिए follow कर लीजिए".
कुल 9-11 दृश्य. हर दृश्य का "say" (बोली जाने वाली line) 8-20 शब्द; कुल 140-170 शब्द.
"say" और screen के शब्द मेल खाएँ (screen पर कम शब्द, बड़े).

दृश्य के प्रकार (हर दृश्य में "type", "say" और उस प्रकार के fields):
{types}

सिर्फ JSON: {{"topic": "...", "caption_post": "Instagram caption + 5 hashtag", "sources": ["..."], "scenes": [{{"type": "hook", "say": "...", ...}}, ...]}}"""


def plan(topic, handle):
    q = PLAN.format(topic=topic, types="\n".join(f"- {k}: {v}" for k, v in TYPES.items()))
    try:
        raw = gemini.ask(q, search=True, temperature=0.7)
    except gemini.QuotaOver:
        gemini._dead.clear()
        raw = gemini.ask(q.replace("Google Search से असली, ताज़ा, सही जानकारी लो", "अपनी पक्की जानकारी से लिखो"), temperature=0.7)
    p = gemini.json_from(raw)
    scenes = [s for s in p.get("scenes", []) if isinstance(s, dict) and str(s.get("say", "")).strip()]
    for s in scenes:
        if s.get("type") not in TYPES:
            s["type"] = "card"
        if s["type"] == "outro":
            s["handle"] = handle
    if len(scenes) < 6 or scenes[0]["type"] != "hook":
        raise ValueError(f"दृश्य-योजना अधूरी ({len(scenes)} दृश्य)")
    if scenes[-1]["type"] != "outro":
        scenes.append({"type": "outro", "title": "ऐसी और ज़रूरी बातों के लिए", "handle": handle, "button": "Follow",
                       "say": "ऐसी और ज़रूरी बातों के लिए follow कर लीजिए।"})
    p["scenes"] = scenes
    return p


def voice(scenes, out):
    """हर दृश्य की line → Gemini आवाज़ (बाकी reels वाला ही tts.py, एक ही आवाज़) → अवधि."""
    import tts
    from scipy.io import wavfile
    script = {"lines": [{"who": "bablu", "say": s["say"], "expr": "gambhir"} for s in scenes], "require_gemini_voice": True}
    tts.speak_script(script, out)
    t = 0.25
    for i, s in enumerate(scenes):
        sr, a = wavfile.read(out / f"{i:02d}.wav")
        s["start"], s["end"] = round(t, 3), round(t + len(a) / sr + 0.18, 3)
        t = s["end"]
    return t


def mux(scenes, audio_dir, frames, out):
    lst = audio_dir / "list.txt"
    parts = []
    gap = audio_dir / "gap.wav"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono", "-t", "0.18", str(gap)], check=True)
    lead = audio_dir / "lead.wav"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono", "-t", "0.25", str(lead)], check=True)
    parts.append(lead)
    for i in range(len(scenes)):
        parts += [audio_dir / f"{i:02d}.wav", gap]
    lst.write_text("".join(f"file '{p.resolve()}'\n" for p in parts), encoding="utf-8")
    voice_wav = audio_dir / "voice.wav"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(voice_wav)], check=True)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", "30", "-i", str(frames / "%05d.jpg"), "-i", str(voice_wav),
                    "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k",
                    "-shortest", "-movflags", "+faststart", str(out)], check=True)


def main(topic, handle):
    work = ROOT / "explainer_out"
    work.mkdir(exist_ok=True)
    p = plan(topic, handle)
    total = voice(p["scenes"], work / "audio")
    spec = {"handle": handle, "scenes": p["scenes"]}
    (work / "spec.json").write_text(json.dumps(spec, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"  दृश्य: {len(p['scenes'])}, अवधि {total:.1f}s —", ", ".join(s["type"] for s in p["scenes"]))
    subprocess.run(["node", str(HERE / "render.js"), str(work / "spec.json"), str(work / "frames")], check=True)
    out = work / "explainer.mp4"
    mux(p["scenes"], work / "audio", work / "frames", out)
    import telegram
    cap = "🧪 DEMO — काम की बात (motion graphics)\n" + p.get("topic", topic) + "\n\n" + str(p.get("caption_post", ""))[:700]
    if p.get("sources"):
        cap += "\n\nस्रोत: " + "; ".join(map(str, p["sources"]))[:250]
    telegram.send_video(out, cap[:1000])
    print("  ✅ Telegram पर भेजा:", out)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "ग़लत UPI ट्रांसफ़र हो जाए तो पैसा वापस कैसे पाएँ",
         os.getenv("PAGE_HANDLE", "@bakra_news"))
