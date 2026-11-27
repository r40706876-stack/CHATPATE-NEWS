"""Gemini ki aukaat test (2026-11-27): Demo 1 ke 3 drishya Gemini se code (HTML+SVG+JS) me banwao,
Playwright se frame lo, contact sheet + chhota mp4 -> out/. Koi Claude nahi."""
import json, os, re, subprocess, sys, time, requests
OUT = "out"; os.makedirs(OUT, exist_ok=True)
KEYS = [k.strip() for k in [os.getenv("GEMINI_API_KEY", ""), *os.getenv("GEMINI_TTS_KEYS", "").split(",")] if k.strip()]
API = "https://generativelanguage.googleapis.com/v1beta"
log = open(f"{OUT}/log.txt", "w")
def P(*a):
    s = " ".join(str(x) for x in a); print(s); log.write(s + "\n"); log.flush()

def models():
    for k in KEYS:
        r = requests.get(f"{API}/models?pageSize=200&key={k}", timeout=60)
        if r.ok:
            return [m["name"].split("/")[-1] for m in r.json().get("models", []) if "generateContent" in m.get("supportedGenerationMethods", [])]
    return []
ms = models(); P("models:", ms)
def rank(n):
    v = re.findall(r"gemini-(\d+)(?:\.(\d+))?", n); v = (int(v[0][0]), int(v[0][1] or 0)) if v else (0, 0)
    bad = any(x in n for x in ["tts", "image", "audio", "live", "embedding", "lite", "thinking-exp", "native", "robotics", "computer"])
    return (not bad, "pro" in n, v, "preview" not in n)
cands = sorted([m for m in ms if m.startswith("gemini")], key=rank, reverse=True)
MODEL = os.getenv("MODEL") or (cands[0] if cands else "gemini-flash-latest")
P("MODEL:", MODEL, "| next:", cands[1:4])

RULES = """You are a senior motion designer who writes animated explainer scenes as code for an Indian exam-prep YouTube course (Hindi, premium look).
Write ONE self-contained scene for a 960x540 canvas. Output ONLY a JSON object (no markdown) with two string fields:
  "html": markup (inline SVG and divs, absolutely positioned, inline styles only, no external images/fonts/URLs) that goes inside <div id="sc" style="position:absolute;left:0;top:0;width:960px;height:540px">
  "js":   JavaScript source that defines   function draw(t) { ... }   where t is seconds since scene start.
Rules:
- draw(t) must be DETERMINISTIC: every element's look depends only on t (no setTimeout, no requestAnimationFrame, no Math.random, no CSS transitions/animations). It is called for arbitrary t in any order.
- Elements appear exactly at their beat times (given below) with smooth easing (pop/rise/draw-on of lines over ~0.5s) and stay unless told.
- Keep a calm safe area: nothing important below y=440 (subtitles live there) and nothing above y=90 (brand bar). Leave the right 300px (x>660) mostly empty (two cartoon teachers stand there).
- Style: dark navy background is already behind you (do NOT paint a full background). Use flat vector illustration style, rounded shapes, soft shadows, colors: gold #ffc83d, red #e8433f, sky #4ea8ff, mint #22c993, cream #fffdf5, text white or navy #13245c. Font-family 'Baloo 2', 'Hind', sans-serif. Hindi text must be exactly as given (Devanagari).
- Make it look premium and alive: subtle idle motion (gentle float, glow pulse) after things arrive; clear visual hierarchy; big readable labels (>=14px).
"""
SCENES = {
 "s1_dukaan_kahani": """Scene: a simple story that explains the post office hierarchy. Beats (seconds):
0.0 'सबसे पहले, एक सीधी सी कहानी' (title-less, maybe a soft spotlight)
1.9 a BIG SHOP in a city appears top-center (illustrate a shop with awning), label 'शहर की बड़ी दुकान'
4.6 next to it a thick account DIARY/ledger appears, label 'सारा हिसाब'
6.9 business grew: two roads draw down-left and down-right to TWO smaller TOWN shops, label each 'कस्बे की दुकान'
10.6 from each town shop, two roads draw down to tiny ONE-ROOM VILLAGE shops (4 total), label 'गाँव'
14.6 money: small coins travel from village and town shops back along the roads up into the city DIARY (loop a few coins until 19.0), diary glows
19.4 badges pop on the shops: big shop gets red 'HO' tag, town shops blue 'SO', village shops green 'BO' (badges arrive at 19.9, 21.6, 23.9)
29.3 a caption card pops: 'यही एक तस्वीर = पूरा क्लॉज़ 2'
Scene lasts 33 s.""",
 "s2_ped": """Scene: three classes of post offices, remembered as a TREE. Beats:
0.6 heading pill: 'डाकघर = 3 श्रेणियाँ' with small '(श्रेणी = क़िस्म / वर्ग)'
5.4 definition card 1 (right of the tree): red square 'HO' + 'हेड पोस्ट ऑफ़िस' + small 'हेड = सिर · सबसे ऊपर' + 'हिंदी: प्रधान डाकघर'
10.4 card 2: blue 'SO' 'सब पोस्ट ऑफ़िस' small 'सब = उप · नीचे वाला' 'हिंदी: उप डाकघर'
14.8 card 3: green 'BO' 'ब्रांच पोस्ट ऑफ़िस' small 'ब्रांच = शाखा · डाली' 'हिंदी: शाखा डाकघर'
21.0 a tree grows on the left: trunk first (label 'तना = HO' at 21.4), thick branches at 23.0 (label 'डालियाँ = SO'), leaves pop at 25.0 (label 'पत्तियाँ = BO')
27.0 'ऊपर HO → नीचे SO → सबसे नीचे BO': the three cards get highlighted one by one (27.2, 28.4, 29.6) with a glowing outline
Scene lasts 31 s. Cards must not overlap the tree.""",
 "s3_do_raste": """Scene: why a Branch Office (BO) can send its accounts to two places. Beats:
0.3 title: 'BO का लेखा कार्यालय?' 
3.0 top-right area (but keep x<640): an HO building (red tag 'HO'); left side an SO building (blue tag 'SO')
10.8 bottom-left: village A house with green tag 'BO' + label 'गाँव A का BO'; a road draws from it up to the SO (11.5) with label 'SO से जुड़ा → हिसाब SO में'
15.0 bottom-middle: village B house 'BO' + label 'गाँव B का BO'; a road draws directly up to the HO (15.7) with label 'सीधे HO से जुड़ा → हिसाब HO में'
16.5 small coins move along both roads continuously
19.8 a result card pops at bottom-center: 'BO का लेखा कार्यालय = HO या SO, जिससे जुड़ा हो'
Scene lasts 27 s.""",
}

def ask(prompt, tries=3):
    body = {"contents": [{"role": "user", "parts": [{"text": RULES + "\n\n" + prompt}]}],
            "generationConfig": {"temperature": 0.6, "responseMimeType": "application/json", "maxOutputTokens": 32000}}
    last = None
    for a in range(tries):
        for k in KEYS:
            try:
                r = requests.post(f"{API}/models/{MODEL}:generateContent?key={k}", json=body, timeout=600)
                if not r.ok:
                    last = f"{r.status_code} {r.text[:300]}"; continue
                txt = "".join(p.get("text", "") for p in r.json()["candidates"][0]["content"]["parts"])
                txt = re.sub(r"^```(json)?|```$", "", txt.strip()).strip()
                return json.loads(txt), r.json().get("usageMetadata")
            except Exception as e:
                last = repr(e)[:300]
        time.sleep(20)
    raise RuntimeError(last)

PAGE = """<!doctype html><html><head><meta charset="utf-8"><style>*{margin:0;padding:0;box-sizing:border-box}body{width:960px;height:540px;overflow:hidden;background:radial-gradient(120% 80% at 50% 0%,#1d2a6e 0%,#0d1440 55%,#070b24 100%);font-family:'Baloo 2','Hind',sans-serif;color:#fff}</style></head>
<body><div id="sc" style="position:absolute;left:0;top:0;width:960px;height:540px">%HTML%</div>
<div style="position:absolute;left:0;right:0;top:0;height:64px;background:rgba(7,11,36,.9);border-bottom:2px solid #ffc83d;font:800 18px/64px 'Baloo 2';padding-left:16px">PostalEdge · Gemini TEST</div>
<div style="position:absolute;left:24px;right:24px;top:446px;height:50px;text-align:center;font:800 22px/50px 'Baloo 2';color:#fff;opacity:.5">[ कैप्शन यहाँ ]</div>
<div style="position:absolute;left:690px;top:150px;width:240px;height:300px;border:2px dashed rgba(255,255,255,.25);border-radius:20px;font:600 14px 'Hind';color:rgba(255,255,255,.4);text-align:center;padding-top:130px">गोलू + भैया</div>
<script>%JS%
window.__err=null;</script></body></html>"""

from playwright.sync_api import sync_playwright
res = {}
with sync_playwright() as p:
    br = p.chromium.launch()
    for name, sp in SCENES.items():
        P("\n==", name)
        t0 = time.time()
        try:
            out, use = ask(sp)
        except Exception as e:
            P("FAIL ask:", e); res[name] = "ask-fail"; continue
        P("secs:", round(time.time() - t0), "usage:", use)
        html = PAGE.replace("%HTML%", out.get("html", "")).replace("%JS%", out.get("js", ""))
        open(f"{OUT}/{name}.html", "w").write(html)
        pg = br.new_page(viewport={"width": 960, "height": 540})
        errs = []; pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.goto("file://" + os.path.abspath(f"{OUT}/{name}.html")); pg.wait_for_timeout(500)
        dur = {"s1_dukaan_kahani": 33, "s2_ped": 31, "s3_do_raste": 27}[name]
        fd = f"{OUT}/{name}_f"; os.makedirs(fd, exist_ok=True)
        ok = True
        for i in range(int(dur * 15)):
            try:
                pg.evaluate(f"draw({i / 15})")
            except Exception as e:
                errs.append(str(e)[:200]); ok = False; break
            pg.screenshot(path=f"{fd}/f{i:04d}.jpg", type="jpeg", quality=80)
        P("errors:", errs[:3])
        if ok:
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", "15", "-i", f"{fd}/f%04d.jpg", "-vf", "scale=960:540", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "26", f"{OUT}/{name}.mp4"])
            picks = [int(x * 15) for x in [2.5, 8, 12, 17, 22, 26, dur - 1.5]]
            picks = [min(x, int(dur * 15) - 1) for x in picks]
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error"] + sum([["-i", f"{fd}/f{x:04d}.jpg"] for x in picks[:6]], []) +
                           ["-filter_complex", "[0][1][2]hstack=3[a];[3][4][5]hstack=3[b];[a][b]vstack", f"{OUT}/{name}_sheet.jpg"])
        subprocess.run(["rm", "-rf", fd]); pg.close()
        res[name] = "ok" if ok and not errs else "errors"
    br.close()
P("\nRESULT", json.dumps(res), "MODEL", MODEL)
