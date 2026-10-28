"""YouTube के सबसे ज़्यादा देखे गए Hindi व्यंग्य/देसी comedy Shorts की असली script (Hindi auto-subtitles) → yt_examples.json.
इनसे Gemini को नमूने मिलते हैं (नियम कम, असली viral उदाहरण ज़्यादा). मुफ़्त: yt-dlp, कोई API credit नहीं.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

import clips

ROOT = Path(__file__).parent
# आम खोज (28 Oct) बेकार निकली — फ़िल्मी scene, trailer, गाने. अब सिर्फ़ जाने-माने deadpan व्यंग्य वाले channel (मालिक की पसंद:
# Anurag Tiwari का "प्रकाश भारती"), और channel का नाम मिलना ज़रूरी.
QUERIES = [("Prakash Bharati Anurag Tiwari", "anurag tiwari"), ("प्रकाश भारती विशेष रिपोर्ट", "anurag tiwari"),
           ("Anurag Tiwari shorts", "anurag tiwari"), ("Prakash Bharati news", "anurag tiwari"),
           ("Prakash Bharati prasaran", "anurag tiwari")]
POLITICS = re.compile(r"मोदी|राहुल|बीजेपी|भाजपा|कांग्रेस|चुनाव|modi|rahul|bjp|congress|election", re.I)


def search(q, n=25):
    cmd = clips._ytdlp() + ["-J", "--no-warnings", "--skip-download", f"ytsearch{n}:{q}"] + clips._cookies("YT_COOKIES")
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=240)
        return (json.loads(r.stdout or "{}") or {}).get("entries") or []
    except Exception as e:                                # noqa: BLE001
        print("  खोज नहीं चली:", q, repr(e)[:100])
        return []


def subs(url, vid):
    out = ROOT / "yt_subs"
    out.mkdir(exist_ok=True)
    cmd = clips._ytdlp() + ["--skip-download", "--write-auto-subs", "--write-subs", "--sub-langs", "hi.*,hi",
                            "--sub-format", "vtt", "-o", str(out / "%(id)s"), url] + clips._cookies("YT_COOKIES")
    subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    f = next(out.glob(f"{vid}*.vtt"), None)
    if not f:
        return ""
    lines, seen = [], set()
    for ln in f.read_text(encoding="utf-8", errors="ignore").splitlines():
        ln = re.sub(r"<[^>]+>", "", ln).strip()
        if not ln or "-->" in ln or ln.startswith(("WEBVTT", "Kind:", "Language:")) or ln in seen:
            continue
        seen.add(ln)
        lines.append(ln)
    return " ".join(lines)


def main():
    got = {}
    for q, must in QUERIES:
        for e in search(q):
            if must not in (str(e.get("channel") or "") + " " + str(e.get("uploader") or "")).lower():
                continue
            vid, dur, views = e.get("id"), e.get("duration") or 0, e.get("view_count") or 0
            title = e.get("title") or ""
            if not vid or vid in got or not (8 <= dur <= 240) or views < 2000 or POLITICS.search(title):
                continue
            got[vid] = {"id": vid, "title": title, "channel": e.get("channel") or "", "views": views, "secs": dur,
                        "url": f"https://www.youtube.com/shorts/{vid}", "query": q}
        print(f"  {q}: अब तक {len(got)}")
    top = sorted(got.values(), key=lambda x: -x["views"])[:40]
    for v in top:
        v["text"] = subs(v["url"], v["id"])
        print(f"  {v['views']:>10,} | {len(v['text']):>4} अक्षर | {v['title'][:60]}")
    top = [v for v in top if len(v["text"]) >= 40]
    json.dump(top, open(ROOT / "yt_examples.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("subtitle वाले:", len(top))


if __name__ == "__main__":
    sys.exit(main())
