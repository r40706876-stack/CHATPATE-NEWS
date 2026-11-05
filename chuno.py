"""
"क्लिप + आप चुनो" format (5 Nov 2026, मालिक ने option 3 चुना).
आँकड़े: 13-20 Oct (जब मालिक Telegram पर ख़ुद script चुनते थे) = 4 reels 1,000+ views; पूरी तरह automatic होने के बाद एक भी नहीं.
बड़े channels (Neeraj Badhwar, Raju Roy, India Daily) में आधा मज़ा असली video ख़ुद देता है.

हर slot (7, 10, 13, 16, 19 IST):
  1. ask: आज की वायरल खबर जिसका असली YouTube clip मिले → Gemini से hook + 2-3 तथ्य lines + 10 पंच → Telegram पर.
  2. मालिक 2-3 नंबर भेजते हैं (जैसे "4 7 2"; आख़िरी नंबर = आख़िरी पंच; 0 = दूसरी खबर).
  3. tick जवाब पढ़कर script जोड़ता है (बिना Gemini) → studio_job.txt → video.
Gemini: हर slot 2 calls.
"""
import json
import re
import time
from pathlib import Path

import gemini

ROOT = Path(__file__).parent
PENDING = ROOT / "chuno_pending.json"
OFFSET = ROOT / "tg_offset.txt"
NAME = {"bablu": "बबलू", "chacha": "चाचा", "pinky": "पिंकी"}

PICK = """नीचे आज की वायरल/आदत वाली खबरें हैं. ऐसी 3 खबरें चुनो (सबसे अच्छी पहले) जिनका असली video YouTube पर ज़रूर होगा और
video में ही कुछ अजीब/मज़ेदार/चौंकाने वाला होता दिखे (कोई कुछ करता दिखे — सिर्फ़ घोषणा/बयान/दाम नहीं).
उस घटना में हमारी रोज़ की ज़िंदगी/सिस्टम/आदत पर मज़ाक की जगह हो. मौत/चोट/अपराध-पीड़ित, नेता/पार्टी, धर्म/जाति, सरकारी नियम नहीं.
recent वाली खबरें दोबारा नहीं.
सिर्फ JSON list: [{"index": 0, "topic": "एक वाक्य", "category": "...", "clip_query": "YouTube खोज, हिंदी, 3-6 शब्द, घटना के मुख्य शब्द"}]"""

PUNCH = """तुम बकरा न्यूज़ के लेखक हो. reporter बबलू गंभीर, deadpan anchor है जो वायरल घटना को "राष्ट्रीय उपलब्धि/बड़ी ब्रेकिंग" की तरह
बताता है — चेहरा गंभीर, बात बेतुकी. screen पर ऊपर असली video चलेगा, इसलिए lines छोटी रखो.

{winners}

खबर: {topic}
headline/स्रोत: {headlines}
मिला video: {clip}

लिखो:
- "hook": पहली line, उल्टा headline (≤10 शब्द) — घटना को उपलब्धि/गंभीर ब्रेकिंग की तरह. हाँ/ना सवाल नहीं.
- "facts": 2-3 सीधी lines (हर एक ≤14 शब्द) जो घटना पूरी समझा दें — सिर्फ़ headline/video title में लिखी बातें, कोई नया अंक/नाम/जगह नहीं.
- "punches": ठीक 10 पंच (हर एक ≤16 शब्द). हर पंच अलग निशाने पर: हमारा सिस्टम (सड़क, नाले, दफ़्तर, ट्रेन, कंपनी के वादे),
  हमारी आदत (views की भूख, दिखावा, return), पहचाने लोग (मम्मी, चाचा, बॉस, रिश्तेदार, EMI वाला दोस्त, पड़ोसन).
  घटना वाले इंसान का मज़ाक नहीं. "सरकारी बयान + उसी शब्द पर twist" ढाँचा अच्छा चलता है. सुनते ही समझ आए.
  घिसे joke मना: सोन पापड़ी, शर्मा जी का बेटा, "पापा की परी", "दोस्तों", "आपको बता दें", "ये वीडियो भेजो".
  "who": ज़्यादातर bablu; 2-3 पंच chacha (पुरानी सोच) या pinky (18 साल, नई पीढ़ी) के.
- "breaking": screen headline ≤8 शब्द; "ask": comment के लिए छोटा सवाल; "caption_post": Instagram caption + 4-5 hashtag.

सिर्फ JSON: {{"hook": "...", "facts": ["..."], "punches": [{{"who": "bablu", "say": "..."}}], "breaking": "...", "ask": "...",
"caption_post": "..."}}"""


def _clip_for(query):
    """इसी घटना का YouTube video (title में खोज के 2+ शब्द, भारत का) — download नहीं, सिर्फ़ खोज."""
    import clips
    import visuals
    want = visuals._stems(query)
    need = 2 if len(want) >= 3 else 1
    for url, title, ch, dur in clips.search(query, n=10):
        if len(want & visuals._stems(title)) >= need and clips.indian(title, ch) and (not dur or 8 <= dur <= 1200):
            return {"url": url, "title": title, "channel": ch}
    return None


def ask(exclude=()):
    import topics
    import viral_writer
    c = topics.collect_news()
    cands = viral_writer.candidates(c)
    recent = [t for _, _, t in topics.history(7)] + list(exclude)
    picks = gemini.ask_json(PICK + "\n\nrecent: " + json.dumps(recent[-30:], ensure_ascii=False)
                            + "\n\nखबरें:\n" + json.dumps(cands, ensure_ascii=False), json_mode=True, temperature=0.3)
    if isinstance(picks, dict):
        picks = [picks]
    chosen = None
    for p in picks[:3]:
        clip = _clip_for(p.get("clip_query") or p.get("topic", ""))
        print("  🎯", p.get("topic"), "→ clip:", (clip or {}).get("title", "नहीं मिला"))
        if clip:
            i = p.get("index")
            p["headlines"] = ([cands[i]["title"]] + [str(x) for x in cands[i]["more"] if x]) if isinstance(i, int) and 0 <= i < len(cands) else []
            chosen = (p, clip)
            break
    if not chosen:
        import telegram
        telegram.send_text("🔍 इस बार किसी वायरल खबर का असली video नहीं मिला, इसलिए पंच नहीं भेजे। अगली बारी में फिर कोशिश होगी।")
        return None
    p, clip = chosen
    out = gemini.ask_json(PUNCH.format(winners=viral_writer.WINNERS, topic=p["topic"],
                                       headlines=json.dumps(p["headlines"], ensure_ascii=False),
                                       clip=f'{clip["title"]} ({clip["channel"]})'), json_mode=True, temperature=0.9)
    punches = [x for x in out.get("punches", []) if isinstance(x, dict) and str(x.get("say", "")).strip()][:10]
    for x in punches:
        x["who"] = x.get("who") if x.get("who") in NAME else "bablu"
    facts = [str(f) for f in out.get("facts", []) if str(f).strip()][:3]
    if len(punches) < 4 or not facts or not out.get("hook"):
        raise ValueError("पंच/तथ्य अधूरे मिले")
    state = {"sent_at": int(time.time()), "topic": p["topic"], "category": p.get("category", "वायरल"), "clip": clip,
             "hook": out["hook"], "facts": facts, "punches": punches, "breaking": out.get("breaking", ""),
             "ask": out.get("ask", ""), "caption_post": out.get("caption_post", ""), "headlines": p["headlines"]}
    PENDING.write_text(json.dumps(state, ensure_ascii=False, indent=1), encoding="utf-8")
    msg = [f"🎬 खबर: {p['topic']}", f"📹 असली video: {clip['title']} — {clip['channel']}", "",
           f"🎤 बबलू (शुरुआत): {out['hook']}"] + [f"   • {f}" for f in facts] + ["", "😂 पंच चुनो:"]
    msg += [f"{k}. [{NAME[x['who']]}] {x['say']}" for k, x in enumerate(punches, 1)]
    msg += ["", "👉 2-3 नंबर भेजो, जैसे: 4 7 2  (आख़िरी नंबर = video का आख़िरी पंच)", "0 = दूसरी खबर"]
    import telegram
    telegram.send_text("\n".join(msg))
    with open(ROOT / "shown.txt", "a", encoding="utf-8") as f:
        f.write(f"{time.strftime('%Y-%m-%d')}|{state['category']}|{p['topic'].replace('|', ' ')}\n")
    print("  पंच Telegram पर भेजे —", p["topic"])
    return state


def parse(text, n):
    """'4 7 2' / '4,7,2' → [4, 7, 2]; '0' → [0]; बाकी → None."""
    nums = [int(x) for x in re.findall(r"\d+", str(text))]
    if nums == [0]:
        return [0]
    nums = list(dict.fromkeys(x for x in nums if 1 <= x <= n))
    return nums[:4] if nums else None


def build(state, picks):
    """hook → तथ्य और चुने पंच बारी-बारी → आख़िरी चुना पंच सबसे आख़िर में. (Gemini नहीं)"""
    chosen = [state["punches"][k - 1] for k in picks]
    body, mid = [], chosen[:-1]
    for i, fact in enumerate(state["facts"]):
        body.append({"who": "bablu", "say": fact, "expr": "gambhir"})
        if i < len(mid):
            body.append(dict(mid[i], expr="tanz", punch=True))
    body += [dict(x, expr="tanz", punch=True) for x in mid[len(state["facts"]):]]
    lines = [{"who": "bablu", "say": state["hook"], "expr": "gambhir"}] + body + [dict(chosen[-1], expr="tanz", punch=True)]
    for k, ln in enumerate(lines):
        ln["caption"] = ln["say"]
        ln["set"] = "studio" if ln["who"] == "bablu" else "village"
        ln["photo_hi"] = [state["topic"]] if k <= 2 else []
        ln["visuals"] = []
    return {"topic": state["topic"], "breaking": state.get("breaking") or state["topic"], "category": state["category"],
            "hook": state["hook"], "hook_text": state["hook"], "hook_short": " ".join(str(state.get("breaking") or state["hook"]).split()[:5]),
            "ask": state.get("ask", ""), "lines": lines, "clip_urls": [state["clip"]["url"]], "clip_first": True,
            "caption_post": (state.get("caption_post") or state["topic"]) + f"\nवीडियो: {state['clip']['channel']}",
            "format": "chuno", "writer": "chuno", "label": "अधपकी खबर", "layout": "anchor", "editorial_mode": "viral_mazaak",
            "style": "flow", "lips": "sadtalker", "renderer": "studio", "no_memes": True, "picked": picks}


def tick():
    """हर ~20 मिनट: पहले मालिक का जवाब, फिर slot की बारी हो तो नए पंच."""
    import results
    import scheduled_production as sp
    import telegram
    msgs = []
    for when, text in telegram.read_replies(OFFSET):
        ans = results.record(text)                       # "डेटा skip 57 watch 6.2" वाले जवाब पहले की तरह
        if ans:
            telegram.send_text(ans)
        else:
            msgs.append((when, text))
    state = json.loads(PENDING.read_text(encoding="utf-8")) if PENDING.exists() else None
    if state:
        got = None
        for when, text in msgs:
            if when + 60 >= state["sent_at"]:
                p = parse(text, len(state["punches"]))
                if p is None:
                    telegram.send_text(f"समझ नहीं आया 🙂 पंच के 2-3 नंबर भेजो (1-{len(state['punches'])}), या 0 = दूसरी खबर")
                else:
                    got = p
        if got == [0]:
            PENDING.unlink()
            telegram.send_text("ठीक है, दूसरी खबर ढूँढ रहा हूँ… 🔎")
            return ask(exclude=[state["topic"]])
        if got:
            import run_daily
            ep = run_daily.to_studio(build(state, got))
            slot = sp.slot_for()
            if slot:
                ep["_production_slot"] = slot
            name = f"episodes/chuno_{run_daily.ist().strftime('%Y%m%d_%H%M')}.json"
            (ROOT / name).write_text(json.dumps(ep, ensure_ascii=False, indent=1), encoding="utf-8")
            (ROOT / "studio_job.txt").write_text(name, encoding="utf-8")
            PENDING.unlink()
            telegram.send_text(f"✅ पंच {', '.join(map(str, got))} से video बन रहा है (~40 मिनट): {state['topic']}")
            print("  चुने पंच:", got, "→", name)
            return
    slot = sp.slot_for()
    st = sp.load(slot) if slot else {}
    if not slot or st.get("status") in ("asked", "noclip", "dispatched", "delivered") or st.get("tries", 0) >= 2:
        print("  अभी कुछ नहीं:", slot, st.get("status"))
        return
    try:
        sp.save(slot, {"status": "asked" if ask() else "noclip"})
    except Exception as e:                               # noqa: BLE001 — quota/busy: इस slot में ज़्यादा से ज़्यादा 2 कोशिश
        sp.save(slot, {"status": "failed", "tries": st.get("tries", 0) + 1, "last_error": repr(e)[:300]})
        raise


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "ask":
        ask()
    else:
        tick()
