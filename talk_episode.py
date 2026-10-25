"""
पूरी episode: कई किरदार, हर line अलग GitHub job में (एक साथ) SadTalker से हिलता चेहरा → जोड़कर पुराना TV look.
    python talk_episode.py prep episodes/x.json   → st_in/<i>/source.png + talk.wav, st_in/audio/NN.wav, st_in/lines.json
    python talk_episode.py post                   → episode.mp4 (+ preview_episode.jpg, Telegram)
"""
import json
import re
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

import talk_test as tt

ROOT = Path(__file__).parent
IN, OUT = ROOT / "st_in", ROOT / "st_out"
W, H, FPS = 1080, 1920, 25
TV_X, TV_Y = 60, 250
CHARS = {   # किरदार: (तस्वीर, नाम, पद) — सब काल्पनिक AI किरदार
    "bablu": ("assets/real/bablu.png", "बबलू", "गाँव संवाददाता • सीधे खेत से"),
    "chacha": ("assets/real/chacha.png", "चाचा", "वरिष्ठ विशेषज्ञ • 1975 से नाराज़"),
    "dadi": ("assets/real/dadi.png", "दादी", "तकनीकी सलाहकार • WhatsApp विभाग"),
    "pinky": ("assets/real/pinky.png", "पिंकी", "नई पीढ़ी • अभी-अभी 18 की"),
    "ramesh": ("assets/real/ramesh.png", "रमेश", "आम आदमी • रोज़ का परेशान"),
}


_cut = {}


EXPRS = ("hasi", "hairan", "gussa", "tanz")       # assets/real/<who>_<expr>.png हो तो वही भाव वाली फ़ोटो


def source_img(who, path, expr=""):
    """किरदार की फ़ोटो 960x1280 (line के भाव वाली, अगर है); assets/bg/<who>.jpg हो तो गाँव वाली पृष्ठभूमि."""
    ep = ROOT / f"assets/real/{who}_{expr}.png"
    im = Image.open(ep if expr and ep.exists() else ROOT / CHARS[who][0]).convert("RGB")
    s = max(960 / im.width, 1280 / im.height)
    im = im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS)
    x0, y0 = (im.width - 960) // 2, int((im.height - 1280) * 0.25)
    im = im.crop((x0, y0, x0 + 960, y0 + 1280))
    bgp = ROOT / f"assets/bg/{who}.jpg"
    if bgp.exists():
        try:
            if (who, expr) not in _cut:
                from rembg import new_session, remove
                _cut[(who, expr)] = remove(im, session=new_session("u2net_human_seg"))
            bg = Image.open(bgp).convert("RGB")
            k = max(960 / bg.width, 1280 / bg.height)
            bg = bg.resize((int(bg.width * k), int(bg.height * k)), Image.LANCZOS)
            bx, by = (bg.width - 960) // 2, (bg.height - 1280) // 2
            from PIL import ImageEnhance, ImageFilter
            bg = ImageEnhance.Brightness(bg.crop((bx, by, bx + 960, by + 1280)).filter(ImageFilter.GaussianBlur(5))).enhance(0.9)
            bg.paste(_cut[(who, expr)], (0, 0), _cut[(who, expr)])
            im = bg
        except Exception as e:                            # noqa: BLE001
            print("  पृष्ठभूमि नहीं बदली:", who, e)
    im.save(path)


def tighten(wav):
    """शुरू/आख़िर की चुप्पी हटाओ + थोड़ा तेज़ (reel की रफ़्तार)."""
    tmp = wav.with_suffix(".t.wav")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(wav), "-af",
                    "silenceremove=start_periods=1:start_threshold=-45dB,areverse,"
                    "silenceremove=start_periods=1:start_threshold=-45dB,areverse,atempo=1.1,apad=pad_dur=0.05",
                    str(tmp)], check=True)
    tmp.replace(wav)


def prep(script_path):
    ep = json.load(open(ROOT / script_path, encoding="utf-8"))
    import tts
    ep["_voice"] = tts.speak_script(ep, IN / "audio")             # कौन-सी आवाज़ लगी (gemini / edge / kokoro)
    ep["_voice_err"] = tts.LAST_ERR[:300]
    for i, ln in enumerate(ep["lines"]):
        tighten(IN / f"audio/{i:02d}.wav")
        pause = float(ln.get("pause_after") or 0)
        pause = min(pause, 0.5)                                # virality skill: 0.5 सेकंड से लंबा सन्नाटा = लोग scroll कर देते हैं
        if 0 < pause <= 1.5:                                   # "और अगर माँग नहीं मानी गई…" के बाद जानबूझकर सन्नाटा (suspense)
            w = IN / f"audio/{i:02d}.wav"
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(w), "-af", f"apad=pad_dur={pause}",
                            str(w.with_suffix(".p.wav"))], check=True)
            w.with_suffix(".p.wav").replace(w)
    for i, ln in enumerate(ep["lines"]):
        d = IN / str(i)
        d.mkdir(parents=True, exist_ok=True)
        sprite = (ep.get("sprite") or {}).get(ln["who"])
        if sprite:                                             # 3D किरदार: नीले studio में, line के भाव वाली फ़ोटो
            import reel_studio
            st = ln.get("set") or ("studio" if ln["who"] == "bablu" else "village")
            ln["shot"] = pick_shot(ep, i, ln)
            src_shot = "close" if ln["shot"] == "close" else "band"
            reel_studio.source_for(sprite, ln.get("expr", ""), d / "source.png", d / "still.png", st, src_shot)
            rp = ln.get("react_pose") if ep.get("react") else None    # reaction ठहराव बंद (flow टूटता था); ep["react"] से चालू
            if rp:
                reel_studio.source_for(sprite, rp, IN / f"react_{i}_small.png", IN / f"react_{i}.png", st, src_shot)
        else:
            source_img(ln["who"], d / "source.png", ln.get("expr", ""))
            Image.open(d / "source.png").save(d / "still.png")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(IN / f"audio/{i:02d}.wav"), "-ar", "16000",
                        "-ac", "1", str(d / "talk.wav")], check=True)
    import shutil
    import visuals                                             # हर line के लिए 2 तक पक्की तस्वीरें (भारत की, बात से जुड़ी)
    (IN / "broll").mkdir(exist_ok=True)
    for ln in ep["lines"]:
        ln["_need_vis"] = ln.get("shot") != "close" and bool(ln.get("visuals") or ln.get("photo_hi") or ln.get("topic")
                                                            or len(ln.get("say", "").split()) >= 8)
        # intro/outro जैसी lines (न खोज, न खबर) पर नई तस्वीर नहीं — पिछली चलती रहती है (वरना बेमेल फ़ोटो आती थी)
    if ep["lines"]:                                            # पहली line (hook) पर हमेशा तस्वीर — पहला सेकंड ही सब तय करता है
        ep["lines"][0]["_need_vis"] = ep["lines"][0].get("shot") != "close"
    got = visuals.pick_for_lines(ep["lines"], topic=ep.get("breaking") or ep.get("topic", ""),
                                 strict=True)                    # बिना AI जाँच कोई तस्वीर नहीं (cartoon/model वाली ग़लती)
    for i, paths in got.items():
        for j, path in enumerate(paths):
            shutil.copy(path, IN / f"broll/{i}_{j}{Path(path).suffix}")
            if Path(path).with_suffix(".txt").exists():          # photo वाले का नाम (CC license)
                shutil.copy(Path(path).with_suffix(".txt"), IN / f"broll/{i}_{j}.txt")
    if not ep.get("no_clips"):                                 # असली खबर के छोटे video clips (पहले सेकंड में हरकत)
        try:
            import clips
            qs = [q for ln in ep["lines"] for q in (ln.get("photo_hi") or [])][:6]
            got_c = clips.for_topic(ep.get("topic") or ep.get("breaking", ""), qs, want=3)
            for k, (cp, _, title) in enumerate(got_c):        # हर clip उसी line पर जिसकी बात उसके title से मिले
                tw = visuals._stems(title)

                def fit(i):
                    ln = ep["lines"][i]
                    return len(tw & visuals._stems(ln.get("say", "") + " " + " ".join(ln.get("photo_hi") or [])))
                free = [i for i in range(len(ep["lines"])) if not list((IN / "broll").glob(f"{i}_clip*"))]
                if not free:
                    break
                li = max(free, key=lambda i: (fit(i), -i))
                # A clip must match BOTH the underlying news story and this
                # dialogue; a common word like "मोबाइल" alone is not enough.
                topic_words = visuals._stems(ep.get("topic") or ep.get("breaking") or "")
                story_overlap = len(tw & topic_words)
                min_story = 2 if len(topic_words) >= 3 else 1
                if fit(li) == 0 or story_overlap < min_story:
                    print(f"  clip rejected (dialogue/story mismatch): {title[:70]}")
                    continue
                shutil.copy(cp, IN / f"broll/{li}_clip{k}.mp4")
                shutil.copy(cp.with_suffix(".txt"), IN / f"broll/{li}_clip{k}.txt")
                print(f"  🎬 clip → line {li + 1}: {title[:50]}")
        except Exception as e:                                 # noqa: BLE001
            print("  clips वाला हिस्सा छोड़ा:", repr(e)[:150])
    fill_sets(ep)
    json.dump(ep, open(IN / "episode.json", "w", encoding="utf-8"), ensure_ascii=False)
    sprite_lips = ep.get("sprite") and ep.get("lips", "sadtalker") == "sprite"
    print(json.dumps([] if sprite_lips else list(range(len(ep["lines"])))))   # sprite वाले होंठ = SadTalker की ज़रूरत नहीं


def pick_shot(ep, i, ln):
    """style: v2 = पूरी screen तस्वीर/close-up/split बदलते रहें; nochar = बिना किरदार (सिर्फ़ तस्वीर/clip + बड़े अक्षर);
    बाकी = पुराना हमेशा split."""
    import reel_studio
    style = ep.get("style")
    if style in ("v2", "nochar"):
        m = re.match(r"\s*(हर [^…,।!?]{2,30} में एक [^…,।!?]{2,25})", ln.get("say", ""))
        if m:
            ln["tag_text"] = m.group(1) + "…"
    if style == "nochar":
        return "full"
    return reel_studio.shot_v2(i, ln) if style == "v2" else reel_studio.shot_for(i, ln)


def fill_sets(ep):
    """जिस line को न जाँची हुई तस्वीर मिली न clip: उसकी बात वाली अपनी AI तस्वीर (आँगन, रसोई, स्टेशन, बैंक…).
    बेमेल फ़ोटो कभी नहीं; ठीक न बैठे (गाँव/studio) तो कुछ नहीं — screen पर उस line का card चलेगा."""
    import shutil
    import news_writer as nw
    topic = str(ep.get("topic") or ep.get("breaking") or "")
    for i, ln in enumerate(ep["lines"]):
        if list((IN / "broll").glob(f"{i}_*")):
            continue
        scene = nw.pick_set("x", ln.get("say", ""), topic)
        src = ROOT / f"assets/sets/{scene}.png"
        if scene not in ("village", "studio") and src.exists():
            shutil.copy(src, IN / f"broll/{i}_set.png")


def quality(ep):
    """video के साथ Telegram पर: कौन-सी आवाज़ लगी, कितनी lines पर असली तस्वीर/clip — ताकि चुपचाप ख़राब video न जाए."""
    n = len(ep["lines"])
    files = [p for p in (IN / "broll").glob("*") if p.suffix != ".txt"] if (IN / "broll").exists() else []
    real = {p.name.split("_")[0] for p in files if "_set" not in p.name}
    sets = {p.name.split("_")[0] for p in files if "_set" in p.name}
    clips_n = sum("clip" in p.name for p in files)
    v, err = ep.get("_voice") or "?", str(ep.get("_voice_err") or "")
    json.dump({"voice": v, "voice_err": err, "lines": n, "real_visual_lines": len(real), "set_lines": len(sets),
               "clips": clips_n, "format": ep.get("format", "")}, open(ROOT / "last_quality.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    msg = (f"📋 Video जाँच — आवाज़: {'Gemini ✅' if v == 'gemini' else v + ' (backup) ⚠️'}"
           + (f"\n   Gemini आवाज़ क्यों नहीं: {err[:160]}" if v != "gemini" and err else "")
           + f"\n🖼 असली तस्वीर/clip वाली lines: {len(real)}/{n} (YouTube clip: {clips_n})"
           + (f", अपनी AI तस्वीर: {len(sets)}" if sets else ""))
    if v != "gemini" or len(real) * 2 < n:
        msg += "\n⚠️ ये video पूरी quality का नहीं — Gemini का कोटा दोपहर 12:30 के बाद नया होता है, तब दोबारा बनवाना बेहतर।"
    return msg


def vischeck(script_path):
    """सिर्फ़ तस्वीरें चुनकर एक contact sheet (visual_check.jpg) — Telegram पर कुछ नहीं जाता. हर तस्वीर के नीचे
    line, खोज और स्रोत, ताकि जाँच सकें कि भारत की और बात से जुड़ी है."""
    import visuals
    from PIL import ImageDraw
    ep = json.load(open(ROOT / script_path, encoding="utf-8"))
    got = visuals.pick_for_lines(ep["lines"], topic=ep.get("breaking") or ep.get("topic", ""))
    tiles = []
    for i, ln in enumerate(ep["lines"]):
        paths = got.get(i) or [None]
        for p in paths:
            t = Image.new("RGB", (360, 330), (30, 30, 30))
            if p:
                src = p
                if p.suffix == ".mp4":
                    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", "1", "-i", str(p), "-frames:v", "1",
                                    str(p.with_suffix(".thumb.jpg"))])
                    src = p.with_suffix(".thumb.jpg")
                try:
                    im = Image.open(src).convert("RGB")
                    im.thumbnail((360, 240))
                    t.paste(im, ((360 - im.width) // 2, 0))
                except Exception:                     # noqa: BLE001
                    pass
            d = ImageDraw.Draw(t)
            f = tt.font(18)
            d.text((6, 250), f"{i + 1}. " + ln["say"][:32], font=f, fill="white")
            d.text((6, 276), ln["say"][32:64], font=f, fill="white")
            cred = (p.with_suffix(".txt").read_text(encoding="utf-8")[:36] if p.with_suffix(".txt").exists() else p.name) if p else "कोई नहीं — पिछली तस्वीर चलेगी"
            d.text((6, 302), cred, font=f, fill=(180, 220, 255) if p else (255, 120, 120))
            tiles.append(t)
    cols = 6
    sheet = Image.new("RGB", (360 * cols, 330 * ((len(tiles) + cols - 1) // cols)), (0, 0, 0))
    for i, t in enumerate(tiles):
        sheet.paste(t, ((i % cols) * 360, (i // cols) * 330))
    sheet.save(ROOT / "visual_check.jpg", quality=85)
    print(f"{sum(1 for v in got.values() if v)}/{len(got)} lines को तस्वीर मिली")


def _secs(p):
    with wave.open(str(p)) as w:
        return w.getnframes() / w.getframerate()


def _frames(video):
    rd = subprocess.Popen(["ffmpeg", "-loglevel", "error", "-i", str(video), "-vf",
                           f"fps={FPS},scale=960:1280:force_original_aspect_ratio=increase,crop=960:1280",
                           "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    while True:
        raw = rd.stdout.read(960 * 1280 * 3)
        if len(raw) < 960 * 1280 * 3:
            return
        yield Image.frombuffer("RGB", (960, 1280), raw)


def _wrap(text, f, width):
    lines, cur = [], ""
    for w in text.split():
        t = (cur + " " + w).strip()
        if f.getlength(t) <= width:
            cur = t
        else:
            lines.append(cur)
            cur = w
    return lines + [cur] if cur else lines


RED, YEL = (220, 30, 40), (255, 214, 0)
VH = 1440                                                   # ऊपर का video हिस्सा 1080x1440, नीचे caption


def _cover(path, w, h):
    rd = subprocess.Popen(["ffmpeg", "-loglevel", "error", "-stream_loop", "-1", "-i", str(path), "-vf",
                           f"fps={FPS},scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h}",
                           "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    while True:
        raw = rd.stdout.read(w * h * 3)
        if len(raw) < w * h * 3:
            return
        yield Image.frombuffer("RGB", (w, h), raw)


def _kenburns(path, w, h, n):
    im = Image.open(path).convert("RGB")
    k = max(w / im.width, h / im.height) * 1.15
    im = im.resize((int(im.width * k), int(im.height * k)), Image.LANCZOS)
    for t in range(n):
        z = 1 + 0.12 * (1 - t / max(1, n))                    # धीरे-धीरे zoom out
        cw, ch = w * 1.15 / z, h * 1.15 / z
        x0, y0 = (im.width - cw) / 2, (im.height - ch) / 2
        yield im.crop((int(x0), int(y0), int(x0 + cw), int(y0 + ch))).resize((w, h), Image.BILINEAR)


def chrome(ep, ln, k, total, broll):
    """ऊपर-नीचे की पट्टियाँ (RGBA, पूरे frame की)."""
    o = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(o)
    d.rounded_rectangle((36, 40, 330, 104), 14, fill=RED + (255,))
    d.text((183, 72), "बकरा न्यूज़", font=tt.font(40), fill="white", anchor="mm")
    d.rounded_rectangle((346, 48, 470, 96), 12, fill=(0, 0, 0, 170))
    d.ellipse((362, 64, 378, 80), fill=RED + (255,))
    d.text((424, 72), "LIVE", font=tt.font(28), fill="white", anchor="mm")
    d.text((W - 36, 72), "AI किरदार", font=tt.font(26), fill=(255, 255, 255, 200), anchor="rm")
    if k < FPS * 3 and ep.get("hook"):                          # पहले 3 सेकंड: hook
        rows = _wrap(ep["hook"], tt.font(64), 960)[:3]
        y0 = 190
        d.rounded_rectangle((30, y0 - 20, W - 30, y0 + 80 * len(rows) + 4), 22, fill=(0, 0, 0, 175))
        for r, t in enumerate(rows):
            d.text((W / 2, y0 + 40 + r * 80), t, font=tt.font(64), fill=YEL, anchor="mm")
    _, name, role = CHARS[ln["who"]]
    if broll:                                                    # b-roll पर: खबर वाली पट्टी
        d.rectangle((0, VH - 150, W, VH - 90), fill=RED + (240,))
        d.text((40, VH - 120), "मुख्य खबर", font=tt.font(36), fill="white", anchor="lm")
    else:                                                        # किरदार पर: नाम-पट्टी
        d.rectangle((0, VH - 170, 520, VH - 105), fill=RED + (245,))
        d.text((36, VH - 138), name, font=tt.font(46), fill="white", anchor="lm")
        d.rectangle((0, VH - 105, 640, VH - 55), fill=(255, 255, 255, 240))
        d.text((36, VH - 80), role, font=tt.font(30), fill=(20, 20, 20), anchor="lm")
    cap = ln.get("caption") or ln["say"]
    rows = _wrap(cap, tt.font(58), 980)[:4]
    yc = VH + (H - VH - 40) / 2 - (len(rows) - 1) * 40
    for r, t in enumerate(rows):
        d.text((W / 2, yc + r * 80), t, font=tt.font(58), fill="white" if r % 2 == 0 else YEL, anchor="mm",
               stroke_width=3, stroke_fill="black")
    d.rectangle((0, H - 14, int(W * k / total), H), fill=YEL + (255,))
    return o


def post_studio(ep):
    import reel_studio
    segs = []
    for i, ln in enumerate(ep["lines"]):
        clips = sorted((OUT / str(i)).rglob("*.mp4"))
        still = Image.open(IN / f"{i}/still.png").convert("RGB")
        vis = sorted((p for p in (IN / "broll").glob(f"{i}_*") if p.suffix != ".txt"),   # असली clip सबसे पहले
                     key=lambda p: ("clip" not in p.name, p.name)) if (IN / "broll").exists() else []
        shot = ln.get("shot") or pick_shot(ep, i, ln)
        talk = None
        sprite = (ep.get("sprite") or {}).get(ln["who"])
        if sprite and ep.get("lips", "sadtalker") == "sprite":
            talk = {"folder": sprite, "expr": ln.get("expr", ""), "wav": IN / f"audio/{i:02d}.wav",
                    "set": ln.get("set") or ("studio" if ln["who"] == "bablu" else "village")}
        segs.append({"ln": ln, "wav": IN / f"audio/{i:02d}.wav", "face": None if talk else (clips[-1] if clips else None),
                     "talk": talk, "still": still, "vis": vis, "shot": shot})
        if ep.get("react") and (IN / f"react_{i}.png").exists():
            rw = IN / f"audio/{i:02d}_r.wav"
            dur = "0.7"                                       # छोटा reaction, साथ में मज़ेदार आवाज़ (सन्नाटा नहीं)
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono",
                            "-t", dur, "-c:a", "pcm_s16le", str(rw)], check=True)
            segs.append({"ln": {"who": ln["who"], "say": ""}, "wav": rw, "face": None, "react": True, "shot": shot,
                         "still": Image.open(IN / f"react_{i}.png").convert("RGB"), "vis": []})
    out = ROOT / "episode.mp4"
    import qa
    import telegram
    issues, tries = None, 0
    for tries in range(3):                                # बनाओ → जाँचो → कमी हो तो ख़ुद ठीक करके दोबारा (2 बार तक)
        if tries:
            ep["_fix"] = tries                            # reel_studio: तस्वीरें और जल्दी बदलें, card ज़्यादा
            print(f"  ♻️ कमी मिली ({'; '.join(issues)}) — ठीक करके दोबारा बना रहे ({tries}/2)")
        secs = reel_studio.render(ep, segs, CHARS, out, ROOT / "preview_episode.jpg")
        try:
            issues = qa.check(out)
        except Exception as e:                            # noqa: BLE001
            print("  जाँच नहीं हुई:", repr(e)[:100])
            issues = ["QA जाँच नहीं चल पाई: " + type(e).__name__]
        print("  जाँच:", issues or "पास ✅")
        if not issues:
            break
    if issues:
        raise RuntimeError("Video QA failed; delivery blocked: " + "; ".join(issues))
    import memes                                          # पंच के बाद मशहूर meme (अपनी आवाज़ के साथ)
    used = memes.add(ep, segs, out)
    # Validate the final file, including any inserted meme clips.
    issues = qa.check(out)
    if issues:
        raise RuntimeError("Final video QA failed; delivery blocked: " + "; ".join(issues))
    report = quality(ep)
    try:                                                  # virality skill के लक्ष्य: लंबाई, पहला frame, पहला शब्द
        report += "\n" + qa.targets(out, segs[0]["wav"] if segs else None)
    except Exception as e:                                # noqa: BLE001
        print("  लक्ष्य-जाँच नहीं हुई:", repr(e)[:100])
    if used:
        report += "\n😂 Memes: " + ", ".join(used)
    print(report)
    print(f"बन गया: {out} ({secs:.1f}s)")
    cap = ep.get("caption_post") if ep.get("production") else f"🎬 3D demo: {ep.get('title', '')}"
    if ep.get("no_send"):                                 # जाँच वाला video: Telegram पर नहीं, सिर्फ़ repo में
        print("  (no_send) Telegram पर नहीं भेजा")
        return
    telegram.send_video(out, cap or ep.get("breaking", ""))
    if issues:
        report += "\n❌ 2 बार ठीक करने के बाद भी कमी बची — इसे post मत करना:\n• " + "\n• ".join(issues)
    else:
        report += "\n✅ अपने-आप जाँच पास" + (f" ({tries} बार ख़ुद ठीक किया)" if tries else "") + " — post कर सकते हो"
    telegram.send_text(report)


def post():
    import reel_v3
    ep = json.load(open(IN / "episode.json", encoding="utf-8"))
    if ep.get("sprite"):
        return post_studio(ep)
    n = len(ep["lines"])
    audio = [IN / f"audio/{i:02d}.wav" for i in range(n)]
    lens = [_secs(a) for a in audio]
    faces, stills, vis = [], [], []
    for i in range(n):
        clips = sorted((OUT / str(i)).rglob("*.mp4"))
        faces.append(_frames(clips[-1]) if clips else None)
        stills.append(Image.open(IN / f"{i}/source.png").convert("RGB"))
        vis.append(sorted((IN / "broll").glob(f"{i}_*")) if (IN / "broll").exists() else [])
    out = ROOT / "episode.mp4"
    secs = reel_v3.render(ep, lens, faces, stills, vis, CHARS, out, ROOT / "preview_episode.jpg", audio)
    print(f"बन गया: {out} ({secs:.1f}s)")
    import qa
    issues = qa.check(out)
    if issues:
        raise RuntimeError("v3 video QA failed; delivery blocked: " + "; ".join(issues))
    if ep.get("no_send"):
        print("  (no_send) v3 QA passed, Telegram पर नहीं भेजा")
        return
    import telegram
    telegram.send_video(out, f"🎬 v3 test: {ep.get('title', '')} — हर 2-3 सेकंड नया नज़ारा, poll के साथ")


_cc = {}


def chrome_cache(ep, ln, k, total, broll):
    key = (id(ln), k < FPS * 3, broll, k * 100 // max(1, total))
    if key not in _cc:
        _cc.clear()
        _cc[key] = chrome(ep, ln, k, total, broll)
    return _cc[key]


def _ring():
    m = Image.new("L", (312, 312), 0)
    ImageDraw.Draw(m).ellipse((0, 0, 311, 311), fill=255)
    return m


if __name__ == "__main__":
    if sys.argv[1] == "prep":
        prep(sys.argv[2])
    elif sys.argv[1] == "vischeck":
        vischeck(sys.argv[2])
    else:
        post()
