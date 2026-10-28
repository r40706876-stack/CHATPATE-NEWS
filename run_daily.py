"""
Bakra News — तुम चुनो, फिर video बने.

    python run_daily.py write     # topics → Gemini 3 scripts → Telegram पर text (pending.json)
    python run_daily.py check     # Telegram पर तुम्हारा जवाब देखो: 1/2/3 → choice.json, 0 → 3 नए
    python run_daily.py render    # choice.json → आवाज़ → video → Telegram
    python run_daily.py auto      # pending है तो check, नहीं तो write
    python run_daily.py --script examples_sale.json   # बना-बनाया script सीधे video

नतीजा: out/<तारीख-समय>/reel.mp4 + caption.txt (+ script.json)
"""
import argparse
import datetime as dt
import json
import os
import re
import shutil
import sys
import time
from pathlib import Path

ROOT = Path(__file__).parent
sys.stdout.reconfigure(line_buffering=True)            # GitHub log में हर कदम तुरंत दिखे
PENDING, CHOICE, OFFSET = ROOT / "pending.json", ROOT / "choice.json", ROOT / "tg_offset.txt"
NAME = {"bablu": "🎤 बबलू", "chacha": "👴 चाचा", "pinky": "📱 पिंकी", "dadi": "👵 दादी", "ramesh": "😤 रमेश"}
NUM = {"१": "1", "२": "2", "३": "3", "०": "0", "one": "1", "two": "2", "three": "3",
       "पहला": "1", "पहली": "1", "दूसरा": "2", "दूसरी": "2", "तीसरा": "3", "तीसरी": "3"}


def ist():
    return dt.datetime.utcnow() + dt.timedelta(hours=5, minutes=30)


def candidates(feed=None):
    import topics
    c = topics.collect(feed)
    # सुबह: खबर + Insta trend | शाम: पूरा viral/Insta वाला
    c["mode"] = "viral" if dt.datetime.utcnow().hour >= 9 else "news"
    if not c["news"]:
        c["mode"] = "viral"
    if not (c["viral"] or c["insta"]):
        c["mode"] = "news"
    print("  mode:", c["mode"])
    return c


def preview(eps):
    out = [f"🐐 बकरा न्यूज़ — आज की {len(eps)} scripts ({ist():%d %b, %I:%M %p})"]
    for i, ep in enumerate(eps, 1):
        out.append(f"\n━━━━━━━━━━  {i}  ━━━━━━━━━━")
        out.append("🔥 बकरा बहस" if ep.get("format") == "rant" else
                   "⚡ एक पंच (8-10 सेकंड, loop — retention experiment)" if ep.get("kind") == "punch" else
                   "📺 नकली ऐड (नया format — TV-shop वाला ऑफ़र → असली खबर → चाचा → loop)" if ep.get("kind") == "tvshop" else "📰 वायरल खबर")
        out.append(f"📰 {ep.get('topic') or ep.get('breaking', '')}")
        if ep.get("insta_used"):
            out.append(f"📱 Insta trend: {ep['insta_used']}")
        if ep.get("hook_text"):
            out.append(f"🪝 Hook: {ep['hook_text']}")
        if ep.get("_loose"):
            out.append("⚠️ ये script नए ढाँचे से बाहर है (लंबा hook या लंबी script) — दूसरा विकल्प हो तो वही चुनो")
        if ep.get("hasi"):
            out.append(f"😂 क्यों चुना: {ep['hasi']}")
        if ep.get("format") == "rant":
            out.append(f"👥 समाज: {ep.get('samaj', '')}")
            out.append(f"📢 माँग: {ep.get('maang', '')}")
            out.append(f"💣 Twist: {ep.get('twist', '')}")
        elif ep.get("cast_why"):
            out.append(f"🎭 किरदार: {ep['cast_why']}")
        import viral_check
        if viral_check.line(ep):
            out.append(viral_check.line(ep))
        if ep.get("source"):
            out.append(f"🔎 स्रोत: {ep['source']}  ← तथ्य एक बार ज़रूर जाँच लेना")
        for ln in ep.get("lines", []):
            mark = " 💥" if ln.get("punch") else ""
            c = ln.get("card")
            if c:
                out.append(f"   📋 [{c.get('tag', '')}] {c.get('big', '')} — {c.get('sub', '')}")
            out.append(f"{NAME.get(ln.get('who'), ln.get('who'))}: {ln.get('say', '')}{mark}")
        if ep.get("ticker"):
            out.append("📰 पट्टी: " + " • ".join(ep["ticker"]))
        poll = ep.get("poll") or []
        if len(poll) >= 2:
            out.append(f"🗳 Poll: 1) {poll[0]}  2) {poll[1]}")
    out.append(f"\n👉 जो पसंद हो उसका नंबर भेजो: 1 से {len(eps)}"
               "\n👉 कोई पसंद नहीं? 0 भेजो — नई scripts आएँगी"
               "\n(जवाब के 15-20 मिनट में video आ जाएगा)")
    return "\n".join(out)


def write_scripts(news, n):
    """दोनों format एक साथ (मालिक का फ़ैसला: दोनों डालकर देखेंगे, जो viral होगा उसी पर बढ़ेंगे):
    आधी "🔥 बकरा बहस" (भड़का anchor-rant) + आधी "📰 वायरल खबर" (पुराना काम-की-खबर ढाँचा). खबरें/तथ्य एक ही बार (Gemini बचे).
    FORMAT=rant या FORMAT=news हो तो सिर्फ़ वही."""
    import gemini
    import news_writer
    import rant_writer
    fmt = os.getenv("FORMAT", "both")
    c = news_writer._safe(news)
    packs, picks = news_writer.gather(c, n)
    n_rant = n if fmt == "rant" else 0 if fmt == "news" else (n + 1) // 2
    rants, newsy = [], []
    if n_rant:
        try:
            rants = rant_writer.write_from(c, packs, picks, n_rant)
        except gemini.QuotaOver:
            raise
        except (Exception, SystemExit) as e:               # noqa: BLE001
            print("  बकरा बहस नहीं बनी:", repr(e)[:200])
    if len(rants) < n:
        used = set(c.get("rant_topics") or [])
        rest = [p for p in packs if str(p.get("topic", "")) not in used]
        rest = rest if len(rest) >= 2 else packs            # अलग खबरें हों तो अलग, वरना वही खबर दूसरे अंदाज़ में
        try:
            newsy = news_writer.write_from(c, rest, picks, n - len(rants))
        except (gemini.QuotaOver, news_writer.NoViral):
            if not rants:
                raise
        except (Exception, SystemExit) as e:               # noqa: BLE001
            print("  वायरल खबर वाली नहीं बनी:", repr(e)[:200])
            if not rants:
                raise
    for e in newsy:
        e.setdefault("label", "वायरल खबर")
    out = []                                               # बारी-बारी: 🔥, 📰, 🔥, 📰…
    for k in range(max(len(rants), len(newsy))):
        out += rants[k:k + 1] + newsy[k:k + 1]
    punch = []                                             # ⚡ एक पंच (8-10 सेकंड, loop) — retention वाला experiment, रोज़ 1 विकल्प
    if os.getenv("PUNCH", "1") == "1" and fmt == "both" and n >= 3:
        try:
            import punch_writer
            punch = punch_writer.write_from(c, packs, picks, 1)
        except gemini.QuotaOver:
            pass
        except (Exception, SystemExit) as e:               # noqa: BLE001
            print("  एक पंच नहीं बना:", repr(e)[:200])
    tv = []                                                # 📺 नकली ऐड — मालिक का चुना नया format (25 Oct), रोज़ 1 विकल्प सबसे ऊपर
    if os.getenv("TVSHOP", "1") == "1" and fmt == "both":
        try:
            import tvshop_writer
            tv = tvshop_writer.write_from(c, packs, picks, 1)
        except gemini.QuotaOver:
            pass
        except (Exception, SystemExit) as e:               # noqa: BLE001
            print("  नकली ऐड नहीं बना:", repr(e)[:200])
    eps = (tv + punch + out)[:n]
    import bakra_rules                                     # मालिक के पक्के नियम: टूटी script Telegram तक नहीं (सब टूटीं तो ⚠️ के साथ)
    ok = [e for e in eps if not bakra_rules.violations(e)]
    for e in eps:
        v = bakra_rules.violations(e)
        if v:
            print("  ❌ नियम टूटा, हटाई:", e.get("topic"), v)
            e["_loose"] = True
    return ok or eps


def do_write(feed=None):
    import gemini
    import news_writer
    import telegram
    import topics
    try:                                               # काम की खबर, देसी अंदाज़ (Gemini के सिर्फ़ 3 call)
        news = topics.collect_news(feed)
        try:
            eps = write_scripts(news, 6)
        except (gemini.QuotaOver, news_writer.NoViral):
            raise
        except RuntimeError as e:                      # Gemini busy (503) — 4 मिनट रुककर एक बार और
            print("  Gemini busy, 4 मिनट बाद दोबारा:", str(e)[:120])
            time.sleep(240)
            try:
                eps = write_scripts(news, 6)
            except (gemini.QuotaOver, news_writer.NoViral):
                raise
            except RuntimeError:
                telegram.send_text("⚠️ Gemini अभी बहुत busy है, scripts नहीं बन पाईं। 0 भेजो तो थोड़ी देर में फिर कोशिश होगी।")
                return
    except gemini.QuotaOver:
        telegram.send_text("⏳ Gemini का free कोटा अभी ख़त्म है। ये रोज़ दोपहर ~12:30 पर नया होता है, उसके बाद वाली बारी अपने-आप चलेगी।")
        print("  आज का Gemini कोटा ख़त्म — रुक गया")
        return
    except news_writer.NoViral as e:
        rows = []
        for r in e.rejected[:6]:
            t, cn = r.get("trend") or {}, r.get("connect") or {}
            rows.append(f"❌ {r.get('topic')}\n   📈 {t.get('score', '?')}/10 {t.get('why', '')}"
                        + (f"\n   ❤️ {cn.get('score')}/10 — {cn.get('weak', '')}" if cn else ""))
        telegram.send_text("🔍 आज की कोई खबर viral पैमाने पर पास नहीं हुई, इसलिए script नहीं भेजी।\n\n" + "\n".join(rows)
                           + "\n\n👉 फिर भी नई कोशिश चाहिए तो 0 भेजो।")
        json.dump({"sent_at": int(time.time()), "eps": []}, open(PENDING, "w", encoding="utf-8"))
        return
    json.dump({"sent_at": int(time.time()), "eps": eps}, open(PENDING, "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)
    CHOICE.unlink(missing_ok=True)
    telegram.send_text(preview(eps))
    with open(ROOT / "shown.txt", "a", encoding="utf-8") as f:     # भेजी गई खबरें याद (अगली बार वही विषय दोबारा न आए)
        for e in eps:
            f.write(f"{ist().date().isoformat()}|{e.get('category', 'other')}|{str(e.get('topic', '')).replace('|', ' ')}\n")
    print(f"  {len(eps)} scripts Telegram पर भेजीं — जवाब का इंतज़ार")


def pick(text, n):
    t = text.strip().lower()
    for k, v in NUM.items():
        t = t.replace(k, v)
    m = re.match(r"^\D{0,12}?([0-9])\b", t) or re.fullmatch(r"([0-9])", t)
    if not m:
        return None
    k = int(m.group(1))
    return k if 0 <= k <= n else None


def do_check():
    import telegram
    if not PENDING.exists():
        print("  कोई script इंतज़ार में नहीं")
        return
    p = json.load(open(PENDING, encoding="utf-8"))
    n = len(p["eps"])
    k = None
    for when, text in replies():
        if when + 60 < p["sent_at"]:                  # scripts भेजने से पहले के पुराने messages नहीं
            continue
        got = pick(text, n)
        if got is None:
            telegram.send_text(f"समझ नहीं आया 🙂 सिर्फ़ नंबर भेजो: 1 से {n}, या 0 (नई scripts)")
        else:
            k = got                                    # आख़िरी वाला जवाब माना जाएगा
    if k is None:
        print("  अभी जवाब नहीं आया")
        return
    if k == 0:
        telegram.send_text("ठीक है! 3 नई scripts लिख रहा हूँ… ✍️")
        topics_seen = [e.get("topic", "") for e in p["eps"]]
        import topics
        topics.EXTRA_RECENT = topics_seen
        import writer
        writer.learn(p["eps"], liked=False)            # तीनों ठुकराईं → अगली बार ऐसा नहीं
        do_write()
        return
    ep = p["eps"][k - 1]
    import writer
    writer.learn([ep], liked=True)                     # तुम्हारी पसंद याद रहती है
    if ep.get("format") == "rant":                     # चुनी हुई "बकरा बहस" = Gemini का अगला नमूना (वो इसी से सीखता है)
        import rant_writer
        rant_writer.learn(ep)
    json.dump(ep, open(CHOICE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    telegram.send_text(f"✅ विकल्प {k} चुना: {ep.get('topic') or ep.get('breaking', '')}\n🎬 video बन रहा है, 10-15 मिनट…")
    print("  चुना:", k)


def log_done(script):
    with open(ROOT / "done.txt", "a", encoding="utf-8") as f:
        topic = str(script.get("topic") or script.get("breaking") or "").replace("|", " ").strip()
        f.write(f"{ist().date().isoformat()}|{script.get('category', 'other')}|{topic} {script.get('news_used', '')}".strip() + "\n")
        for k in ("insta_used", "trend"):
            if isinstance(script.get(k), str) and script[k]:
                f.write(str(script[k]).strip() + "\n")
        blob = json.dumps(script, ensure_ascii=False)
        tf = ROOT / "topics.txt"                       # topics.txt की इस्तेमाल हुई line भी done
        if tf.exists():
            for line in tf.read_text(encoding="utf-8").splitlines():
                if line.strip() and not line.startswith("#") and line.strip() in blob:
                    f.write(line.strip() + "\n")


TOON = {c: f"assets/toon/{c}" for c in ("bablu", "chacha", "pinky", "dadi", "ramesh")}


def to_studio(script):
    """चुनी script → 3D studio वाला episode (ऊपर खबर की screen, नीचे studio में किरदार). जिनकी 3D फ़ोटो नहीं, वो None."""
    ep = json.loads(json.dumps(script))
    swap = {"dadi": "pinky", "ramesh": "chacha"}              # जिनकी 3D फ़ोटो अभी नहीं, उनकी line नज़दीकी किरदार बोले
    for ln in ep.get("lines", []):
        if not (ROOT / TOON.get(ln["who"], "x") / "neutral_closed.png").exists():
            ln["who"] = swap.get(ln["who"], "bablu")
    who = {l["who"] for l in ep.get("lines", [])}
    have = {c for c in who if (ROOT / TOON.get(c, "x") / "neutral_closed.png").exists()}
    if who - have:
        print("  3D फ़ोटो नहीं:", who - have, "— पुराना renderer")
        return None
    ep["sprite"] = {c: TOON[c] for c in have}
    ep["hook"] = ep.get("hook") or ep.get("hook_text") or ""
    p = ep.get("poll")
    if isinstance(p, list) and len(p) >= 2:
        ep["poll"] = {"q": ep.get("ask") or "आप क्या कहते हो?", "a": str(p[0]), "b": str(p[1])}
    for ln in ep["lines"]:
        ln.setdefault("set", "studio" if ln["who"] == "bablu" else "village")
        if not (ROOT / f"assets/sets/{ln['set']}.png").exists():
            ln["set"] = "studio" if ln["who"] == "bablu" else "village"
    ep["production"] = True
    return ep


def do_bulletin(feed=None):
    """दूसरा format: "दिन भर की खबरें" — 4 खबरें, सिर्फ़ बबलू, हर खबर की असली फ़ोटो. बिना चुनाव के सीधे बनता है."""
    import gemini
    import news_writer
    import telegram
    import topics
    try:
        ep = news_writer.write_bulletin(topics.collect_news(feed), 4)
    except gemini.QuotaOver:
        telegram.send_text("⏳ आज 'दिन भर की खबरें' नहीं बनीं — Gemini का free कोटा ख़त्म है (दोपहर ~12:30 पर नया होता है).")
        return
    ep["sprite"] = {"bablu": TOON["bablu"]}
    ep["production"] = True
    name = f"episodes/bulletin_{ist().strftime('%Y%m%d_%H%M')}.json"
    json.dump(ep, open(ROOT / name, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    (ROOT / "studio_job.txt").write_text(name, encoding="utf-8")
    heads = "\n".join(f"{l['item']}. {l.get('headline', '')}" for l in ep["lines"] if l.get("item"))
    telegram.send_text("📰 आज की 'दिन भर की खबरें' बन रही हैं (25-30 मिनट):\n" + heads)
    print("  bulletin job:", name)


def do_render(script_path):
    import telegram
    script = json.load(open(script_path, encoding="utf-8"))
    if os.getenv("STUDIO", "1") == "1":                    # नया format: talk_episode workflow बनाएगा (~25 मिनट)
        ep = to_studio(script)
        if ep:
            name = f"episodes/daily_{ist().strftime('%Y%m%d_%H%M')}.json"
            json.dump(ep, open(ROOT / name, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
            (ROOT / "studio_job.txt").write_text(name, encoding="utf-8")
            log_done(script)
            telegram.send_text("🎬 3D studio वाला video बन रहा है (ऊपर खबर, नीचे बबलू) — 25-30 मिनट में यहीं आएगा.")
            print("  studio job:", name)
            return
    job = ROOT / "out" / ist().strftime("%Y%m%d_%H%M")
    job.mkdir(parents=True, exist_ok=True)
    shutil.copy(script_path, job / "script.json")
    try:
        import tts
        tts.speak_script(script, job / "audio")
        if os.getenv("PIXABAY_API_KEY") and os.getenv("REEL_STYLE", "real") == "real":
            import render_real as renderer                 # असली visuals वाला format
        else:
            import render_reel as renderer                 # पुराना कार्टून वाला
        renderer.AUDIO = job / "audio"
        renderer.main(str((job / "script.json").relative_to(ROOT)), str((job / "reel.mp4").relative_to(ROOT)))
    except Exception as e:                             # noqa: BLE001
        telegram.send_text(f"❌ video नहीं बना: {str(e)[:300]}\nवही नंबर दोबारा भेजो, फिर कोशिश करूँगा.")
        raise
    cap = script.get("caption_post", script.get("breaking", ""))
    (job / "caption.txt").write_text(cap, encoding="utf-8")
    log_done(script)
    if not script.get("preview_only"):
        telegram.send_video(job / "reel.mp4", cap)
    print(f"तैयार: {job / 'reel.mp4'}")


SPEAKER = {"बबलू": "bablu", "बबलु": "bablu", "चाचा": "chacha", "पिंकी": "pinky", "पिंकि": "pinky", "दादी": "dadi",
           "दादि": "dadi", "रमेश": "ramesh"}
FEEL = {"गुस्सा": "gussa", "गुस्से": "gussa", "हँसी": "hasi", "हंसी": "hasi", "ख़ुश": "hasi", "खुश": "hasi",
        "दुखी": "udaas", "उदास": "udaas", "हैरान": "hairan", "तंज़": "tanz", "तंज": "tanz", "गंभीर": "gambhir"}
SET_WORDS = [("thana", "ठगी|थाना|पुलिस|फ़्रॉड|फ्रॉड|साइबर|हैक|एपीके|APK|लिंक|ओटीपी|OTP"), ("road", "चालान|गड्ढ|सड़क|ट्रैफिक|पेट्रोल|हेलमेट"), ("mandi", "सब्ज़ी|सब्जी|टमाटर|प्याज़|प्याज|महँगाई|महंगाई|दाम"),
             ("office", "दफ़्तर|दफ्तर|फ़ॉर्म|फॉर्म|भर्ती|बाबू|फ़ाइल|फाइल"), ("school", "परीक्षा|पेपर|रिज़ल्ट|रिजल्ट|स्कूल"),
             ("bank", "बैंक|UPI|यूपीआई|लोन|ATM|एटीएम"),
             ("bijli", "बिजली|बिल|कटौती|ट्रांसफ़ॉर्मर"), ("station", "ट्रेन|रेल|स्टेशन|टिकट|किराया"),
             ("hospital", "अस्पताल|डॉक्टर|दवा|इलाज"), ("khet", "किसान|खाद|फ़सल|फसल|खेत"), ("gas", "गैस|सिलेंडर|LPG"),
             ("ration", "राशन"), ("kitchen", "रसोई|खाना"), ("room", "फ़ोन|फोन|मोबाइल|ऑनलाइन|इंस्टा|रील")]
TOPICS_HEAD = ("# यहाँ अपनी script लिखो — हर line ऐसे: \"बबलू: ...\"  (किरदार: बबलू, चाचा, पिंकी, दादी, रमेश)\n"
               "# जितने किरदार चाहिए उतने ही लिखो — कोई भी छोड़ सकते हो. भाव चाहिए तो: \"चाचा (गुस्सा): ...\"\n"
               "# (भाव: गंभीर, तंज़, गुस्सा, हैरान, दुखी, ख़ुश). कम से कम 2 lines. सबसे पहले इसी पर video बनेगा.\n"
               "# या बस एक लाइन का topic/viral बात लिखो — Gemini उस पर script बनाएगा.\n")


def _set_for(who, text, topic):
    for name, pat in SET_WORDS:
        if re.search(pat, text) or (who != "bablu" and re.search(pat, topic)):
            return "studio" if who == "bablu" and name not in ("road", "mandi") else name
    return "studio" if who == "bablu" else "village"


def user_script():
    """topics.txt में तुम्हारी script: कोई भी किरदार, कितनी भी बार, किसी भी क्रम में (बबलू ज़रूरी नहीं).
    "चाचा (गुस्सा): ..." से भाव; set (दफ़्तर/सड़क/मंडी…) बात के शब्दों से अपने-आप."""
    tf = ROOT / "topics.txt"
    if not tf.exists():
        return None
    lines = []
    for raw in tf.read_text(encoding="utf-8").splitlines():
        if raw.strip().startswith("#") or ":" not in raw:
            continue
        head, say = raw.split(":", 1)
        who = next((v for k, v in SPEAKER.items() if k in head), None)
        say = re.sub(r"[💥🔥]+", "", say).strip().strip('"“” ')   # Telegram वाली script चिपकाई हो तो निशान हटाओ
        if not (who and len(head) < 40 and say):
            continue
        expr = next((v for k, v in FEEL.items() if k in head), "gambhir")
        ln = {"who": who, "say": say, "caption": say, "expr": expr}
        if say.endswith(("!", "?")) or "।" in say[:-1]:
            ln["punch"] = True
        lines.append(ln)
    if len(lines) < 2:
        return None
    first = re.sub(r"^ब्रेकिंग न्यूज़[!।]?\s*", "", lines[0]["say"])
    head = re.split(r"[!?।]", first)[0].strip()
    words = head.split()
    topic = " ".join(l["say"] for l in lines)
    k = 0
    for ln in lines:
        import news_writer                               # set पहले line की अपनी बात से, फिर खबर (पहली line) से
        ln["set"] = news_writer.pick_set(ln["who"], ln["say"], head)
        ln["topic"] = head                              # तस्वीरें: इसी खबर के अख़बारों से
        if ln.get("punch") and k < 2:                    # सबसे तेज़ 2 lines पर ठप्पा (reaction वाला ठहराव नहीं — flow टूटता था)
            k += 1
        else:
            ln.pop("punch", None)
    fw = lines[0]["say"].split()                        # screen का hook = पहली बोली गई line (अलग-अलग बातें पढ़ना-सुनना नहीं)
    hook = lines[0]["say"] if len(fw) <= 12 else " ".join(fw[:10]) + "…"
    return {"format": "explain", "label": "BREAKING", "user_script": True, "category": "user",
            "topic": head, "breaking": " ".join(words[:10]), "hook_text": hook,
            "hook": hook, "ask": "आपके साथ भी ऐसा हुआ है? कमेंट करो",
            "source": "", "lines": lines,
            "caption_post": first[:180] + "\n\nआपके साथ भी ऐसा होता है? कमेंट में बताओ 👇\n\n#बकरान्यूज़ #desicomedy #funnyreels\n(AI से बने किरदार)"}


POLITICS = re.compile(r"नेता|नेताजी|चुनाव|मंत्री|मुख्यमंत्री|सांसद|विधायक|पार्टी|सरकार ने|योगी|मोदी|राहुल|भाजपा|कांग्रेस|वोट")


def script_warnings(ep):
    """तुम्हारी script पर वो बातें जिनसे हमारे page की reels पहले मरीं (असली आँकड़े) — video फिर भी बनेगा, बस सावधानी."""
    import topics
    w, lines = [], ep["lines"]
    first = len(lines[0]["say"].split())
    words = sum(len(l["say"].split()) for l in lines)
    blob = " ".join(l["say"] for l in lines)
    if first > 12:
        w.append(f"पहली line {first} शब्द की है — 10 शब्द तक का मज़ाक वाला hook हो तो 3 सेकंड में कम लोग भागते हैं")
    if words > 120:
        w.append(f"script {words} शब्द की है (~{words // 3} सेकंड) — हर line में मज़ा न हो तो बीच में लोग जाते हैं")
    if POLITICS.search(blob):
        w.append("राजनीति/नेता वाली बात है — Instagram ऐसी reels अनजान लोगों को कम दिखाता है (मुख्यमंत्री वाली reel = 10 views)")
    if topics.recently_used(ep.get("topic", "") + " " + blob[:200]):
        w.append("ये विषय पिछले 7 दिन में आ चुका है — दोबारा वाली reel पहले 148 views पर रुकी थी")
    if any(re.search(r"वीडियो.{0,25}(भेजो|शेयर|टैग)", l["say"]) for l in lines):
        w.append("'वीडियो भेजो' बोलने से share नहीं होता — किसी पहचाने जाने वाले इंसान पर सटीक चोट से होता है")
    import news_writer
    hard = news_writer.bookish(lines)
    if hard:
        w.append("किताबी शब्द: " + ", ".join(hard) + " — आम आदमी पहली बार सुनकर नहीं समझेगा (वितरक → एजेंसी वाले/डीलर, "
                 "उपभोक्ता → ग्राहक, द्वारा → ने). जो तुम्हें ख़ुद पहली बार में समझ न आए, वो देखने वाले को भी नहीं आएगा")
    return ("\n\n⚠️ ध्यान दो:\n• " + "\n• ".join(w)) if w else ""


INBOX = ROOT / "tg_inbox.json"                          # पढ़े गए पर अभी इस्तेमाल न हुए Telegram जवाब (नंबर वग़ैरह)


def replies():
    """Telegram के नए जवाब — पहले बचे हुए (inbox), फिर नए. (offset एक बार ही आगे बढ़े, कोई नंबर खोए नहीं)"""
    import telegram
    old = json.load(open(INBOX, encoding="utf-8")) if INBOX.exists() else []
    INBOX.unlink(missing_ok=True)
    return [tuple(x) for x in old] + list(telegram.read_replies(OFFSET))


def looks_like_script(text):
    rows = [r for r in text.splitlines() if ":" in r and len(r.split(":", 1)[0]) < 40
            and any(k in r.split(":", 1)[0] for k in SPEAKER)]
    return len(rows) >= 3


def grab_pasted_script():
    """Telegram पर चिपकाई script (जैसे Gemini app के Gem से) → topics.txt → उसी पर video. बाक़ी जवाब do_check के लिए."""
    rest, script = [], None
    for when, text in replies():
        if looks_like_script(text):
            script = text                                  # कई हों तो आख़िरी
        else:
            rest.append((when, text))
    if rest:
        json.dump(rest, open(INBOX, "w", encoding="utf-8"), ensure_ascii=False)
    if script:
        (ROOT / "topics.txt").write_text(TOPICS_HEAD + script.strip() + "\n", encoding="utf-8")
        print("  Telegram पर चिपकाई script मिली")


def as_rant(ep):
    """चिपकाई script "बकरा बहस" जैसी हो ("हमारी माँग" वाली line) तो उसी ढाँचे में: beat के cards, आवाज़, zoom, ठप्पे."""
    lines = ep["lines"]
    mi = next((i for i, l in enumerate(lines) if i and re.search(r"माँग|मांग", l["say"])), None)
    if mi is None or len(lines) < 6 or mi >= len(lines) - 2:
        return ep
    di = next((i for i in range(mi + 1, len(lines) - 1) if re.search(r"अगर|वरना|नहीं तो", lines[i]["say"])), mi + 1)
    for i, l in enumerate(lines):
        l["beat"] = ("hook" if i == 0 else "maang" if i == mi else "dhamki" if i == di else "twist" if i == di + 1
                     else "takiya" if i == len(lines) - 1 else "saboot")
    import rant_writer
    maang = re.split(r"माँग|मांग", lines[mi]["say"], maxsplit=1)[-1].strip(" :–-")
    try:
        return rant_writer.finish(dict(ep, maang=maang, twist="", samaj=""), strict=False)
    except Exception as e:                             # noqa: BLE001
        print("  rant ढाँचा नहीं लगा, सादा ढाँचा:", e)
        return ep


def take_user_script():
    """तुम्हारी script मिली तो उसी पर video (Gemini की ज़रूरत नहीं)."""
    tf0 = ROOT / "topics.txt"
    vishay = re.search(r"^\s*विषय\s*[:：]\s*(.+)$", tf0.read_text(encoding="utf-8"), re.M) if tf0.exists() else None
    ep = user_script()
    if not ep:
        return False
    if vishay:                                         # "विषय:" वाली line = असली खबर → अख़बार की फ़ोटो/YouTube clip इसी से खोजे जाते हैं
        v = vishay.group(1).strip()[:90]
        ep["topic"], ep["breaking"] = v, " ".join(v.split()[:10])
        for ln in ep["lines"]:
            ln["topic"] = v
    hk = re.search(r"^\s*(?:हुक|hook)\s*[:：]\s*(.+)$", tf0.read_text(encoding="utf-8"), re.M | re.I)
    if hk:                                             # screen पर पहले 3 सेकंड का छोटा झटका (≤6 शब्द), बोली गई line से अलग
        ep["hook_short"] = " ".join(hk.group(1).split()[:5])     # vidIQ: 4 शब्द — 1 सेकंड में पढ़ा जाए
    tg = re.search(r"^\s*(?:टैग|tag)\s*[:：]\s*(.+)$", tf0.read_text(encoding="utf-8"), re.M | re.I)
    if tg:                                             # आख़िर में screen पर: "टैग करो उसे जिसने…" (follow की जगह)
        ep["tag_ask"] = tg.group(1).strip()[:60]
    fmt = re.search(r"^\s*(?:फ़ॉर्मेट|फॉर्मेट|फार्मेट|format)\s*[:：]\s*(\S+)", tf0.read_text(encoding="utf-8"), re.M | re.I)
    if fmt:                                            # "फ़ॉर्मेट: 1/2/3" = नई presentation, "5" = बिना किरदार; 4 = बकरा बहस (माँग वाली line से)
        ep["style"] = {"1": "v2", "2": "v2", "3": "v2", "5": "nochar", "v2": "v2", "nochar": "nochar"}.get(fmt.group(1).strip().lower(), "")
        ep["format_no"] = fmt.group(1).strip()
    ep = as_rant(ep)
    import telegram
    tf = ROOT / "topics.txt"
    keep = ROOT / "meri_scripts.txt"                    # पुरानी scripts का रिकॉर्ड
    with open(keep, "a", encoding="utf-8") as f:
        f.write(f"\n===== {ist():%Y-%m-%d %H:%M} =====\n" + tf.read_text(encoding="utf-8"))
    tf.write_text(TOPICS_HEAD, encoding="utf-8")
    json.dump(ep, open(CHOICE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    cast = ", ".join(dict.fromkeys(NAME.get(l["who"], l["who"]) for l in ep["lines"]))
    telegram.send_text(f"✅ आपकी script मिल गई ({len(ep['lines'])} lines, किरदार: {cast}): {ep['topic']}\n🎬 उसी पर video बन रहा है, 25-30 मिनट…"
                       + script_warnings(ep))
    print("  तुम्हारी script मिली —", len(ep["lines"]), "lines → सीधे video")
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", nargs="?", default="auto", choices=["write", "check", "render", "auto", "bulletin"])
    ap.add_argument("--script")
    ap.add_argument("--feed")
    a = ap.parse_args()

    if a.script:
        return do_render(ROOT / a.script)
    mode = a.mode
    if mode in ("write", "check", "auto") and not CHOICE.exists():
        grab_pasted_script()                            # Telegram पर script चिपकाई हो तो वही topics.txt में
    if mode in ("write", "check", "auto") and not CHOICE.exists() and take_user_script():
        return                                          # तुम्हारी script पहले — बाक़ी काम अगली बार
    if mode == "auto":
        mode = "check" if PENDING.exists() else "write"
    if mode == "bulletin":
        return do_bulletin(a.feed)
    if mode == "write":
        do_write(a.feed)
    elif mode == "check":
        do_check()
    if mode == "render" or (mode == "check" and CHOICE.exists() and a.mode == "auto"):
        if CHOICE.exists():
            mine = json.load(open(CHOICE, encoding="utf-8")).get("user_script")
            do_render(CHOICE)
            CHOICE.unlink()
            if not mine:                                # तुम्हारी script से Gemini वाली scripts नहीं मिटतीं
                PENDING.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
