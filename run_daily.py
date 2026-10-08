"""
एक command = एक पूरा Bakra News reel.

    python run_daily.py                        # topics → Gemini script → आवाज़ → video → Telegram
    python run_daily.py --script examples_sale.json   # बना-बनाया script (Gemini के बिना)
    python run_daily.py --feed sample_trends.xml       # offline feed से topics

नतीजा: out/<तारीख-समय>/reel.mp4 + caption.txt (+ script.json)
"""
import argparse
import datetime as dt
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).parent


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--script")
    ap.add_argument("--feed")
    a = ap.parse_args()

    stamp = dt.datetime.utcnow() + dt.timedelta(hours=5, minutes=30)
    job = ROOT / "out" / stamp.strftime("%Y%m%d_%H%M")
    job.mkdir(parents=True, exist_ok=True)

    if a.script:
        script_path = ROOT / a.script
    else:
        import topics
        import writer
        c = topics.collect(a.feed)
        # सुबह: खबर + Insta trend | शाम: पूरा viral/Insta वाला (बारी-बारी, ताकि हर बार एक जैसा न हो)
        c["mode"] = "viral" if dt.datetime.utcnow().hour >= 9 else "news"
        if not c["news"]:
            c["mode"] = "viral"
        if not (c["viral"] or c["insta"]):
            c["mode"] = "news"
        print("  mode:", c["mode"])
        script_path = writer.write(c)
        if script_path is None:
            return
    script = json.load(open(script_path, encoding="utf-8"))
    shutil.copy(script_path, job / "script.json")

    import tts
    tts.speak_script(script, job / "audio")
    import render_reel
    render_reel.AUDIO = job / "audio"
    rel = (job / "script.json").relative_to(ROOT)
    render_reel.main(str(rel), str((job / "reel.mp4").relative_to(ROOT)))

    cap = script.get("caption_post", script.get("breaking", ""))
    (job / "caption.txt").write_text(cap, encoding="utf-8")
    with open(ROOT / "done.txt", "a", encoding="utf-8") as f:
        today = (dt.datetime.utcnow() + dt.timedelta(hours=5, minutes=30)).date().isoformat()
        topic = str(script.get("topic") or script.get("breaking") or "").replace("|", " ").strip()
        f.write(f"{today}|{script.get('category', 'other')}|{topic} {script.get('news_used', '')}".strip() + "\n")
        for k in ("insta_used", "trend"):
            if script.get(k):
                f.write(str(script[k]).strip() + "\n")
        blob = json.dumps(script, ensure_ascii=False)
        tf = ROOT / "topics.txt"                    # topics.txt की इस्तेमाल हुई line भी done
        if tf.exists():
            for line in tf.read_text(encoding="utf-8").splitlines():
                if line.strip() and not line.startswith("#") and line.strip() in blob:
                    f.write(line.strip() + "\n")
    import telegram
    telegram.send_video(job / "reel.mp4", cap)
    print(f"तैयार: {job / 'reel.mp4'}")


if __name__ == "__main__":
    main()
