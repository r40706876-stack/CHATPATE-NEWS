"""
असली खबर के छोटे video clips (YouTube से, yt-dlp) — reel के पहले सेकंड में हरकत के लिए.
  • सिर्फ़ वो video जिसका title इसी खबर के कम से कम 2 असली शब्दों से मिले, और हाल का (7 दिन)
  • हर clip ~3 सेकंड, बिना आवाज़, 720p तक; screen पर स्रोत (channel का नाम) लिखा जाता है
  • YouTube अक्सर GitHub के servers को "bot" मानकर रोकता है — तब secret YT_COOKIES (cookies.txt का पूरा text) काम आता है;
    न चले तो चुपचाप कुछ नहीं (तस्वीरें चलती रहेंगी)
  • Instagram: secret IG_COOKIES हो तो वहाँ से भी कोशिश (login के बिना Instagram देता नहीं)
चेतावनी: दूसरों के video का हिस्सा लगाना copyright के दायरे में आ सकता है — मालिक ने ये ख़तरा जानकर चालू किया है.
"""
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).parent
CACHE = ROOT / "visuals_cache" / "clips"
CLIP_SECS = 3.2


def _ytdlp():
    try:
        import yt_dlp  # noqa: F401
    except ImportError:
        subprocess.run([sys.executable, "-m", "pip", "install", "-q", "--break-system-packages", "-U", "yt-dlp[default]"],
                       capture_output=True)
        subprocess.run([sys.executable, "-m", "pip", "install", "-q", "yt-dlp"], capture_output=True)
    return [sys.executable, "-m", "yt_dlp"]


def _cookies(env):
    txt = os.getenv(env, "")
    if not txt.strip():
        return []
    rows = ["# Netscape HTTP Cookie File"]                # email/Telegram से copy हुआ हो तो tab → space और "#" बिगड़ जाते हैं —
    for ln in txt.replace("\r", "").splitlines():       # हर cookie line फिर से tab वाली बनाओ
        p = ln.split()
        if len(p) >= 7 and p[0].lstrip("#").startswith(".") or (len(p) >= 7 and "." in p[0] and p[1] in ("TRUE", "FALSE")):
            rows.append("\t".join(p[:6] + [" ".join(p[6:])]))
    f = Path(tempfile.gettempdir()) / f"{env.lower()}.txt"
    f.write_text("\n".join(rows) + "\n", encoding="utf-8")
    print(f"  {env}: {len(rows) - 1} cookies")
    return ["--cookies", str(f)]


def search(query, n=8):
    """YouTube खोज: [(url, title, channel, duration, upload_date)] — बिना download."""
    data = {}
    for pre in ("ytsearch",):                             # (ytsearchdate इस yt-dlp में नहीं चलता)
        cmd = _ytdlp() + ["--flat-playlist", "-J", "--no-warnings", f"{pre}{n}:{query}"] + _cookies("YT_COOKIES")
        err = ""
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=45)
            err = r.stderr or ""
            data = json.loads(r.stdout or "{}") or {}
        except Exception as e:                            # noqa: BLE001
            print(f"  YouTube खोज ({pre}) नहीं चली:", repr(e)[:120], err[-200:])
            data = {}
        if data.get("entries"):
            break
        print(f"  YouTube खोज ({pre}) ख़ाली:", err.strip()[-200:])
    out = []
    for e in data.get("entries") or []:
        url = e.get("url") or (f"https://www.youtube.com/watch?v={e['id']}" if e.get("id") else "")
        if url:
            out.append((url, e.get("title") or "", e.get("channel") or e.get("uploader") or "YouTube",
                        e.get("duration") or 0))
    return out


def cut(url, out, start, secs=CLIP_SECS):
    """url के start सेकंड से secs सेकंड का बिना-आवाज़ clip (720p तक)."""
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_suffix(".src.mp4")
    cmd = _ytdlp() + ["-q", "--no-warnings", "--no-playlist", "-f", "bv*[height<=720][ext=mp4]/bv*[height<=720]/b[height<=720]",
                      "--download-sections", f"*{start:.1f}-{start + secs + 0.5:.1f}", "--force-keyframes-at-cuts",
                      "-o", str(tmp)] + _cookies("YT_COOKIES" if "youtu" in url else "IG_COOKIES") + [url]
    try:
        subprocess.run(cmd, capture_output=True, timeout=180)
        got = next((p for p in tmp.parent.glob(tmp.stem + "*") if p.suffix in (".mp4", ".webm", ".mkv")), None)
        if not got:
            return None
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(got), "-t", f"{secs}", "-an", "-vf",
                        "fps=25,scale='min(1280,iw)':-2", "-c:v", "libx264", "-preset", "veryfast", "-crf", "23", str(out)],
                       check=True, timeout=120)
        got.unlink(missing_ok=True)
        return out if out.exists() and out.stat().st_size > 20000 else None
    except Exception as e:                                # noqa: BLE001
        print("  clip नहीं कटा:", repr(e)[:120])
        return None


INDIAN = ("aaj tak", "abp", "ndtv", "zee", "india tv", "news18", "tv9", "republic", "times now", "lallantop", "bhaskar",
          "navbharat", "amar ujala", "jagran", "hindustan", "dd news", "ani news", "india today", "the print", "news24",
          "news nation", " tak", "bharat", "ibc24", "first india", "punjab kesari", "etv", "zee news", "good news today")


def indian(title, ch):
    """भारत का video: title में देवनागरी, या जाना-पहचाना भारतीय channel (विदेशी clip कभी नहीं — paramotor वाली ग़लती)."""
    return bool(re.search(r"[\u0900-\u097F]", title)) or any(k in f" {ch.lower()}" for k in INDIAN)


def vision_ok(path, topic):
    """clip में असल में क्या दिखता है — 3 frames Gemini को: anchor का बोलता चेहरा, दूसरे चैनल का बैनर/'FOLLOW US',
    सिर्फ़ लिखाई, या ख़बर से अलग दृश्य = नहीं (Jaipur demo: बोलती anchor पर Bablu की आवाज़ = होंठ बेमेल लगे)."""
    import base64
    import io
    import gemini
    from PIL import Image
    tiles = []
    for frac in (0.2, 0.5, 0.8):
        jpg = path.with_suffix(f".{int(frac * 10)}.jpg")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{CLIP_SECS * frac:.2f}", "-i", str(path),
                        "-frames:v", "1", "-vf", "scale=320:-2", str(jpg)])
        if jpg.exists():
            tiles.append(Image.open(jpg).convert("RGB"))
            jpg.unlink()
    if not tiles:
        return False
    W_ = sum(t.width for t in tiles)
    sheet = Image.new("RGB", (W_, max(t.height for t in tiles)))
    x = 0
    for t in tiles:
        sheet.paste(t, (x, 0))
        x += t.width
    buf = io.BytesIO()
    sheet.save(buf, "JPEG", quality=80)
    part = {"inline_data": {"mime_type": "image/jpeg", "data": base64.b64encode(buf.getvalue()).decode()}}
    q = (f"ये एक news video clip के 3 frames हैं. खबर: \"{topic}\". reel में ये clip बिना आवाज़ चलेगा और ऊपर हमारे anchor की "
         "आवाज़ होगी. सिर्फ़ JSON: {\"ok\": true/false, \"why\": \"...\"}. ok=false अगर: कोई anchor/रिपोर्टर/इंसान कैमरे की तरफ़ "
         "बोलता दिखे (होंठ बेमेल लगेंगे), channel का logo-बैनर/subscribe/FOLLOW US/promo भरा हो, सिर्फ़ लिखाई/graphic हो, "
         "या दृश्य इस खबर से जुड़ा न हो. ok=true सिर्फ़ तब जब असली घटना/जगह/चीज़ दिख रही हो.")
    try:
        r = gemini.json_from(gemini.ask([{"text": q}, part], json_mode=True, temperature=0.1))
        print(f"  👁 clip जाँच: {'✅' if r.get('ok') else '❌'} {str(r.get('why', ''))[:80]}")
        return bool(r.get("ok"))
    except Exception as e:                                # noqa: BLE001  जाँच न हो सके तो clip नहीं (फ़ोटो चलेंगी)
        print("  clip जाँच नहीं हुई:", repr(e)[:100])
        return False


def for_topic(topic, queries=(), want=2):
    """इसी खबर के `want` clips: [(path, credit)]. title में खबर के 2+ असली शब्द हों, video 15 सेकंड-20 मिनट का."""
    import visuals
    seen, got = set(), []
    for q in [*queries, topic, " ".join(str(topic).split()[:5])]:
        if not q or len(got) >= want:
            continue
        tw = visuals._stems(q)                            # title उसी खोज (Hindi या English) के 2+ शब्दों से मिले
        need = 2 if len(tw) >= 3 else 1
        for url, title, ch, dur in search(q):
            if url in seen or len(got) >= want:
                continue
            seen.add(url)
            if len(tw & visuals._stems(title)) < need or not (15 <= (dur or 60) <= 1200) or not indian(title, ch):
                continue
            start = max(2.0, min((dur or 60) * 0.25, 40.0))   # शुरू का intro/logo छोड़कर, असली हिस्से से
            path = cut(url, CACHE / f"clip_{len(seen)}.mp4", start)
            if path and not vision_ok(path, topic):
                path.unlink(missing_ok=True)
                continue
            if path:
                credit = f"वीडियो: {ch[:30]} (YouTube)"
                path.with_suffix(".txt").write_text(credit, encoding="utf-8")
                got.append((path, credit, title))
                print(f"  🎬 असली clip: {title[:60]} — {ch}")
    if not got:
        print("  असली clip नहीं मिला (YouTube ने रोका या मेल वाला video नहीं) — तस्वीरें चलेंगी")
    return got


if __name__ == "__main__":
    for p, c, t in for_topic(" ".join(sys.argv[1:]) or "उड़कर ऑफिस वायरल वीडियो"):
        print(p, c, t)
