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
import re
import shutil
import time
from pathlib import Path

ROOT = Path(__file__).parent
PENDING, CHOICE, OFFSET = ROOT / "pending.json", ROOT / "choice.json", ROOT / "tg_offset.txt"
NAME = {"bablu": "🐐 बबलू", "chacha": "🐃 चाचा", "pinky": "🐱 पिंकी", "dadi": "👵 दादी"}
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
        out.append(f"📰 {ep.get('topic') or ep.get('breaking', '')}")
        if ep.get("insta_used"):
            out.append(f"📱 Insta trend: {ep['insta_used']}")
        if ep.get("hook_text"):
            out.append(f"🪝 Hook: {ep['hook_text']}")
        for ln in ep.get("lines", []):
            mark = " 💥" if ln.get("punch") else ""
            out.append(f"{NAME.get(ln.get('who'), ln.get('who'))}: {ln.get('say', '')}{mark}")
        poll = ep.get("poll") or []
        if len(poll) >= 2:
            out.append(f"🗳 Poll: 1) {poll[0]}  2) {poll[1]}")
    out.append("\n👉 जो पसंद हो उसका नंबर भेजो: 1, 2 या 3"
               "\n👉 कोई पसंद नहीं? 0 भेजो — 3 नई scripts आएँगी"
               "\n(जवाब के 15-20 मिनट में video आ जाएगा)")
    return "\n".join(out)


def do_write(feed=None):
    import telegram
    import writer
    eps = writer.write_options(candidates(feed), 3)
    json.dump({"sent_at": int(time.time()), "eps": eps}, open(PENDING, "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)
    CHOICE.unlink(missing_ok=True)
    telegram.send_text(preview(eps))
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
    for when, text in telegram.read_replies(OFFSET):
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
    json.dump(ep, open(CHOICE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    telegram.send_text(f"✅ विकल्प {k} चुना: {ep.get('topic') or ep.get('breaking', '')}\n🎬 video बन रहा है, 10-15 मिनट…")
    print("  चुना:", k)


def log_done(script):
    with open(ROOT / "done.txt", "a", encoding="utf-8") as f:
        topic = str(script.get("topic") or script.get("breaking") or "").replace("|", " ").strip()
        f.write(f"{ist().date().isoformat()}|{script.get('category', 'other')}|{topic} {script.get('news_used', '')}".strip() + "\n")
        for k in ("insta_used", "trend"):
            if script.get(k):
                f.write(str(script[k]).strip() + "\n")
        blob = json.dumps(script, ensure_ascii=False)
        tf = ROOT / "topics.txt"                       # topics.txt की इस्तेमाल हुई line भी done
        if tf.exists():
            for line in tf.read_text(encoding="utf-8").splitlines():
                if line.strip() and not line.startswith("#") and line.strip() in blob:
                    f.write(line.strip() + "\n")


def do_render(script_path):
    import telegram
    job = ROOT / "out" / ist().strftime("%Y%m%d_%H%M")
    job.mkdir(parents=True, exist_ok=True)
    script = json.load(open(script_path, encoding="utf-8"))
    shutil.copy(script_path, job / "script.json")
    try:
        import tts
        tts.speak_script(script, job / "audio")
        import render_reel
        render_reel.AUDIO = job / "audio"
        render_reel.main(str((job / "script.json").relative_to(ROOT)), str((job / "reel.mp4").relative_to(ROOT)))
    except Exception as e:                             # noqa: BLE001
        telegram.send_text(f"❌ video नहीं बना: {str(e)[:300]}\nवही नंबर दोबारा भेजो, फिर कोशिश करूँगा.")
        raise
    cap = script.get("caption_post", script.get("breaking", ""))
    (job / "caption.txt").write_text(cap, encoding="utf-8")
    log_done(script)
    telegram.send_video(job / "reel.mp4", cap)
    print(f"तैयार: {job / 'reel.mp4'}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", nargs="?", default="auto", choices=["write", "check", "render", "auto"])
    ap.add_argument("--script")
    ap.add_argument("--feed")
    a = ap.parse_args()

    if a.script:
        return do_render(ROOT / a.script)
    mode = a.mode
    if mode == "auto":
        mode = "check" if PENDING.exists() else "write"
    if mode == "write":
        do_write(a.feed)
    elif mode == "check":
        do_check()
    if mode == "render" or (mode == "check" and CHOICE.exists() and a.mode == "auto"):
        if CHOICE.exists():
            do_render(CHOICE)
            CHOICE.unlink()
            PENDING.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
