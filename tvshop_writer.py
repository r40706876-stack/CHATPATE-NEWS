"""📺 नकली ऐड (25 अक्टूबर 2026) — मालिक ने दो नए formats में से इसे चुना ("Format 1, format 2 से थोड़ा बेहतर है").

TV-shop (टेलीशॉपिंग) वाली जोशीली आवाज़ में आज की असली खबर से जुड़ा बेतुका "ऑफ़र" बेचो → अचानक धीमी आवाज़ में
असली खबर (जो ऑफ़र की पोल खोल दे) → चाचा की चोट → फिर जोश में वही ऑफ़र (loop). ~13-18 सेकंड, एक ही मुख्य आवाज़.
रोज़ 1 विकल्प सबसे ऊपर. TVSHOP=0 करने पर बंद.
"""
import json
import re

import gemini
import news_writer as nw

MAX_WORDS = 85

SAMPLE = """नमूना (स्तर और ढाँचा समझो — शब्द, ऑफ़र, दाम बिल्कुल मत दोहराओ):
खबर: SEBI ने एक शेयर-मार्केट "गुरु" पर निवेशकों को गुमराह करने पर कार्रवाई की.
  bablu (tvshop): "सिर्फ़ ₹999 में करोड़पति बनिए… गारंटी!"
  bablu (tvshop): "रोज़ बस एक घंटा, हमारा course, और करोड़ों आपके!"
  bablu (tvshop): "जैसे हमारे गुरुजी ने कमाए…"
  bablu (gambhir, news): "…और अब SEBI के सामने हिसाब दे रहे हैं।"
  chacha (tanz): "बेटा, असली कमाई शेयर में नहीं थी… course बेचने में थी।"
  bablu (tvshop, loop): "तो देर किस बात की? ₹999… गारंटी!"
  tag_who: "वो दोस्त जो YouTube देखकर रोज़ बोलता है 'कल से trading'"."""


def prompt_write(packs, n):
    return f"""तुम "बकरा न्यूज़" के सबसे तेज़ व्यंग्य writer हो. आज की असली खबरें (तथ्य सिर्फ़ इन्हीं से, कोई नया तथ्य/अंक नहीं):
{json.dumps(packs, ensure_ascii=False, indent=1)}

{nw.SATIRE}

काम: {n} अलग खबरों पर "📺 नकली ऐड" scripts. ऐसी खबर चुनो जिस पर कोई बेतुका "ऑफ़र/स्कीम/प्रोडक्ट" बेचा जा सके
(पैसा, नियम, सुविधा, दाम, नौकरी, सफ़र, फ़ोन, बैंक…). जिस खबर पर ऑफ़र न बने, उसे छोड़ दो.
ढाँचा (5-7 lines, कुल {MAX_WORDS} शब्द से कम, बोलने में 13-18 सेकंड):
 1. HOOK (bablu, expr "tvshop", ≤ 10 शब्द): TV-shop वाली जोशीली आवाज़ में खबर से जुड़ा बेतुका ऑफ़र + "गारंटी!/आज ही!/सिर्फ़…" जैसा
    TV-shop शब्द. ऑफ़र नकली है (यही मज़ाक है), पर सुनते ही खबर याद आए. सबसे चौंकाने वाला शब्द पहले 3 शब्दों में.
 2-3. PITCH (bablu, "tvshop", हर line ≤ 12 शब्द): ऑफ़र के "फ़ायदे" TV-shop के अंदाज़ में — हर line पिछली से ज़्यादा बेतुकी.
 4. DROP (bablu, expr "gambhir", "news": true, ≤ 14 शब्द): अचानक धीमी, गंभीर आवाज़ में असली खबर — वही सच जो ऑफ़र की पोल खोल दे.
    तथ्य हूबहू, बोलचाल में (जिसने खबर नहीं सुनी वो भी समझे: किसने, किसके साथ, क्या).
 5. chacha (expr "tanz", ≤ 14 शब्द): सबसे गहरी चोट — हमारे सिस्टम या किसी पहचाने इंसान पर (pun नहीं, उल्टा मोड़).
 6. LOOP (bablu, "tvshop", ≤ 10 शब्द): फिर उसी जोश में hook का वही शब्द/ऑफ़र दोहराओ — अब उल्टे मतलब के साथ.
"tag_who" = देखने वाला ये reel किसे भेजेगा ("वो दोस्त जो…") — ज़रूरी.

{SAMPLE}

मना (लिखा तो script रद्द): नेता/मंत्री/पार्टी/चुनाव; किसी असली इंसान का नाम लेकर उसकी नकल; असली कंपनी/ब्रांड के नाम से
नकली ऐड; मौत/हादसा/अपराध/हिंसा वाली खबर; "क्या… ?" वाला हाँ/ना सवाल; "नमस्कार"; किताबी शब्द; "शेयर/फ़ॉलो करो".
सिर्फ़ JSON list:
[{{"topic": "खबर 3-6 शब्द", "breaking": "≤ 10 शब्द", "source": "प्रकाशक", "hook_screen": "≤ 5 शब्द",
  "tag_who": "वो दोस्त जो…",
  "lines": [{{"who": "bablu", "say": "...", "caption": "...", "expr": "tvshop", "visuals": ["english search", "..."], "photo_hi": ["हिंदी खोज"]}},
            {{"who": "bablu", "say": "...", "caption": "...", "expr": "gambhir", "news": true, "visuals": ["..."], "photo_hi": ["..."]}},
            {{"who": "chacha", "say": "...", "caption": "...", "expr": "tanz", "punch": true, "stamp": "2-4 शब्द", "visuals": ["..."], "photo_hi": ["..."]}}],
  "caption_post": "hook + एक comment वाला सवाल + स्रोत: ... + 3-5 hashtags + (AI से बने किरदार)"}}]
"say" में अंक शब्दों में (₹999 = "नौ सौ निन्यानवे रुपये"), "caption" में अंकों में."""


def _words(t):
    return {w for w in re.findall(r"[ऀ-ॿ\w₹]+", t) if len(w) >= 3}


def finish(ep):
    lines = [l for l in ep.get("lines") or [] if l.get("who") in nw.writer.WHO and str(l.get("say", "")).strip()][:7]
    assert 5 <= len(lines) <= 7, f"lines: {len(lines)}"
    topic = str(ep.get("topic") or ep.get("breaking") or "")
    news_i = [i for i, l in enumerate(lines) if l.get("news")]
    assert news_i and 2 <= news_i[0] <= len(lines) - 2, "असली खबर वाली (news) line बीच में नहीं"
    for i, ln in enumerate(lines):
        ln["say"] = nw.plain(ln["say"])
        ln["caption"] = nw.plain(ln.get("caption") or "") or ln["say"]
        x = ln.get("expr")
        ln["expr"] = "hasi" if x == "tvshop" else (x if x in nw.EXPRS else "gambhir")   # tvshop = जोशीला (studio का hasi भाव)
        ln["tvshop"] = x == "tvshop"
        ln["set"] = nw.pick_set(ln["who"], ln["say"], topic, ln.get("set") if ln.get("set") in nw.SETS_OK else "")
        ln["visuals"] = [str(v) for v in (ln.get("visuals") or []) if str(v).strip()][:3]
        ln["topic"] = topic
    words = sum(nw.nwords(l["say"]) for l in lines)
    first, last = lines[0]["say"].strip(), lines[-1]["say"].strip()
    assert lines[0]["who"] == "bablu" and lines[-1]["who"] == "bablu", "hook और loop bablu के"
    assert any(l["who"] == "chacha" for l in lines), "chacha की चोट नहीं"
    assert nw.nwords(first) <= 14, f"hook लंबा ({nw.nwords(first)} शब्द)"
    assert words <= MAX_WORDS, f"लंबा: {words} शब्द ({MAX_WORDS} तक)"
    assert _words(first) & _words(last), "loop नहीं — आख़िरी line में hook का कोई शब्द नहीं"
    assert str(ep.get("tag_who", "")).strip(), "tag_who नहीं"
    assert not re.match(r"\s*(नमस्कार|आज की खबर)", first), "नमस्कार से शुरुआत"
    assert not nw.bookish(lines), "किताबी शब्द"
    assert not any(nw.SEND.search(l["say"]) or nw.FILLER.search(l["say"]) for l in lines), "ख़ाली/भेजो वाली line"
    for ln in lines:
        if not ln.get("punch"):
            ln.pop("stamp", None)
    ep["lines"] = lines
    ep["format"], ep["kind"], ep["label"] = "explain", "tvshop", "नकली ऐड"
    ep["hook"] = ep["hook_text"] = first
    hs = str(ep.get("hook_screen") or "").strip()
    if hs:
        ep["hook_short"] = " ".join(hs.split()[:5])
    ep["source"] = ep.get("source") or "Google News"
    ep["hasi"] = f"📺 {words} शब्द (~{round(words / 2.8)} सेकंड) | टैग: {ep.get('tag_who', '')}"
    return ep


def write_from(c, packs, picks, n=1):
    """पक्के तथ्यों (news_writer.gather) से n "नकली ऐड" scripts (1 Gemini call)."""
    raw = gemini.json_from(gemini.ask(prompt_write(packs, n + 1), json_mode=True, temperature=0.9))
    eps = []
    for ep in raw if isinstance(raw, list) else []:
        if not isinstance(ep, dict):
            continue
        try:
            eps.append(finish(json.loads(json.dumps(ep))))
        except Exception as e:                              # noqa: BLE001
            print("  नकली ऐड नहीं बना:", ep.get("topic"), "—", e)
    for ep in eps:
        w = set(str(ep.get("topic", "")).split())
        best = max(picks, key=lambda p: len(w & set(str(p.get("topic", "")).split()))) if picks else {}
        ep["trend"] = best.get("trend")
        ep["category"] = best.get("cat") or "other"
    return eps[:n]
