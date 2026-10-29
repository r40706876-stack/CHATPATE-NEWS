"""बकरा mascot (29 Oct, मालिक: "Ramesh की जगह mascot") — अपना बनाया vector किरदार, assets/toon/bakra/ में
बाकी किरदारों जैसी फ़ाइलें: {भाव}_{closed,half,open}.png (768x1376, सलेटी पृष्ठभूमि) + blink.png + reaction poses (पारदर्शी पृष्ठभूमि — rembg की ज़रूरत नहीं).
Gemini image का free quota नहीं है, इसलिए SVG से; Chromium (playwright) से PNG.

    python bakra_sprite.py            → assets/toon/bakra/*.png
    python bakra_sprite.py preview    → सिर्फ़ एक contact sheet (scratch)
"""
import sys
from pathlib import Path

W, H = 768, 1376
FUR, FUR_D, FUR_L = "#efe3cc", "#cdb894", "#fbf5ea"
PATCH = "#8a5a36"
HORN, HORN_D = "#d9c29a", "#9c8458"

# भाव: (ऊपरी पलक कितनी ढकी 0-1, भौंह झुकाव°, भौंह ऊँचाई, पुतली dy, मुँह मुड़ाव, एक भौंह ऊपर?)
EXPRS = {
    "neutral": dict(lid=0.42, tilt=0, lift=0, smile=0.0, smug=False),     # deadpan: आधी झुकी पलकें
    "happy": dict(lid=0.25, tilt=-6, lift=6, smile=0.9, smug=False),
    "angry": dict(lid=0.38, tilt=20, lift=-10, smile=-0.6, smug=False),
    "sad": dict(lid=0.5, tilt=-20, lift=4, smile=-0.8, smug=False),
    "shock": dict(lid=0.0, tilt=-4, lift=26, smile=-0.2, smug=False),
    "smug": dict(lid=0.5, tilt=0, lift=0, smile=0.6, smug=True),
}
POSES = {"laugh": ("happy", "open", 0.0), "eyeroll": ("neutral", "closed", "roll"), "facepalm": ("sad", "closed", 0.95),
         "thinking": ("smug", "closed", 0.3)}


def eye(cx, cy, e, side, closed=False, look=0.0):
    rx, ry = 46, 52
    out = [f'<ellipse cx="{cx}" cy="{cy}" rx="{rx + 6}" ry="{ry + 6}" fill="{FUR_D}" opacity=".5"/>',
           f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" fill="#fffdf6" stroke="#3b2a1c" stroke-width="3"/>']
    if not closed:
        iy = cy + 6 + (-30 if look == "roll" else 0)
        out += [f'<circle cx="{cx + 4 * side * 0}" cy="{iy}" r="29" fill="url(#iris)"/>',
                f'<rect x="{cx - 17}" y="{iy - 6}" width="34" height="12" rx="6" fill="#120c07"/>',   # बकरे की आड़ी पुतली
                f'<circle cx="{cx + 9}" cy="{iy - 11}" r="6" fill="#fff"/>']
    lid = 1.0 if closed else e["lid"]
    if lid > 0:
        top = cy - ry - 4
        bot = top + (2 * ry + 8) * lid
        out.append(f'<clipPath id="c{side}{int(lid*100)}"><ellipse cx="{cx}" cy="{cy}" rx="{rx + 1}" ry="{ry + 1}"/></clipPath>'
                   f'<rect x="{cx - rx - 2}" y="{top}" width="{2 * rx + 4}" height="{bot - top}" fill="url(#lid)" '
                   f'clip-path="url(#c{side}{int(lid*100)})"/>'
                   f'<path d="M{cx - rx + 2},{bot} Q{cx},{bot + 5} {cx + rx - 2},{bot}" stroke="#3b2a1c" stroke-width="4" fill="none" '
                   f'clip-path="url(#c{side}{int(lid*100)})"/>')
    # भौंह (फ़र का गुच्छा)
    tilt = e["tilt"] * (-side)
    lift = e["lift"] + (22 if e["smug"] and side == 1 else 0)
    by = cy - ry - 22 - lift
    out.append(f'<g transform="rotate({tilt} {cx} {by})"><path d="M{cx - 38},{by + 6} Q{cx},{by - 14} {cx + 38},{by + 6} '
               f'Q{cx},{by - 2} {cx - 38},{by + 6}Z" fill="{PATCH}" stroke="#4a2e18" stroke-width="3"/></g>')
    return "".join(out)


def mouth(state, e):
    cx, cy = 384, 548
    s = e["smile"]
    if state == "closed":
        return (f'<path d="M{cx - 44},{cy - 4 * s} Q{cx},{cy + 22 * s} {cx + 44},{cy - 4 * s}" stroke="#3b2a1c" '
                f'stroke-width="6" fill="none" stroke-linecap="round"/>')
    h = 22 if state == "half" else 46
    w = 40 if state == "half" else 50
    return (f'<path d="M{cx - w},{cy - 6 * s} Q{cx},{cy - 8 + 10 * s} {cx + w},{cy - 6 * s} Q{cx + w * .8},{cy + h} {cx},{cy + h + 6} '
            f'Q{cx - w * .8},{cy + h} {cx - w},{cy - 6 * s}Z" fill="#4a1e1e" stroke="#3b2a1c" stroke-width="5"/>'
            f'<ellipse cx="{cx}" cy="{cy + h - 2}" rx="{w * .55}" ry="{h * .35}" fill="#d9767a"/>'
            f'<rect x="{cx - w * .55}" y="{cy - 6 + 4 * s}" width="{w * 1.1}" height="{8 if state == "half" else 11}" rx="3" fill="#fffaf0"/>')


def svg(expr="neutral", state="closed", blink=False, pose=None):
    e = dict(EXPRS[expr])
    look = 0.0
    if pose == "roll":
        look = "roll"
    eyes = eye(330, 392, e, -1, blink, look) + eye(438, 392, e, 1, blink, look)
    hand = ""
    if pose == "facepalm":
        hand = (f'<path d="M200,800 Q150,640 300,500" stroke="#e6dac2" stroke-width="74" fill="none" stroke-linecap="round"/>'
                f'<ellipse cx="320" cy="470" rx="62" ry="50" fill="#3a2a1c" transform="rotate(-30 320 470)"/>')
    if pose == "thinking":
        hand = (f'<path d="M578,800 Q620,760 470,700" stroke="#e6dac2" stroke-width="70" fill="none" stroke-linecap="round"/>'
                f'<ellipse cx="450" cy="700" rx="46" ry="38" fill="#3a2a1c"/>')
    check = "".join(f'<rect x="{x}" y="0" width="14" height="80" fill="#fff" opacity=".55"/>' for x in range(0, 80, 28))
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
<defs>
 <radialGradient id="bg" cx=".5" cy=".35" r=".8"><stop offset="0" stop-color="#d6d6d6"/><stop offset="1" stop-color="#a9a9a9"/></radialGradient>
 <radialGradient id="fur" cx=".42" cy=".32" r=".75"><stop offset="0" stop-color="{FUR_L}"/><stop offset=".65" stop-color="{FUR}"/><stop offset="1" stop-color="{FUR_D}"/></radialGradient>
 <radialGradient id="muz" cx=".45" cy=".3" r=".8"><stop offset="0" stop-color="#fbeedd"/><stop offset="1" stop-color="#dcc39f"/></radialGradient>
 <linearGradient id="lid" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{FUR_D}"/><stop offset="1" stop-color="{FUR}"/></linearGradient>
 <radialGradient id="iris" cx=".4" cy=".35" r=".7"><stop offset="0" stop-color="#e8b23a"/><stop offset="1" stop-color="#9a6410"/></radialGradient>
 <linearGradient id="horn" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#f4e6c4"/><stop offset="1" stop-color="{HORN_D}"/></linearGradient>
 <linearGradient id="jacket" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#3f5a43"/><stop offset=".5" stop-color="#58785b"/><stop offset="1" stop-color="#34493a"/></linearGradient>
 <linearGradient id="kurta" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#d9d4c8"/><stop offset=".5" stop-color="#f6f2e8"/><stop offset="1" stop-color="#cfc9bb"/></linearGradient>
 <pattern id="gam" width="80" height="80" patternUnits="userSpaceOnUse"><rect width="80" height="80" fill="#c0392b"/>{check}
  <rect y="20" width="80" height="12" fill="#fff" opacity=".45"/><rect y="56" width="80" height="12" fill="#fff" opacity=".45"/></pattern>
 <filter id="sh" x="-20%" y="-20%" width="140%" height="140%"><feDropShadow dx="0" dy="10" stdDeviation="12" flood-opacity=".25"/></filter>
</defs>
<g filter="url(#sh)">
 <!-- शरीर: कुर्ता + हरी बंडी -->
 <path d="M150,1376 L170,860 Q190,760 300,730 L468,730 Q578,760 598,860 L618,1376Z" fill="url(#kurta)"/>
 <path d="M175,1376 L190,880 Q205,780 300,748 L352,748 L352,1376Z" fill="url(#jacket)"/>
 <path d="M593,1376 L578,880 Q563,780 468,748 L416,748 L416,1376Z" fill="url(#jacket)"/>
 <circle cx="384" cy="900" r="7" fill="#c9a24a"/><circle cx="384" cy="980" r="7" fill="#c9a24a"/><circle cx="384" cy="1060" r="7" fill="#c9a24a"/>
 <path d="M300,1000 L340,1000" stroke="#2c3f30" stroke-width="5"/>
 <!-- बाँहें + खुर -->
 {'' if pose == 'facepalm' else '<path d="M190,800 Q120,950 150,1180" stroke="#e6dac2" stroke-width="72" fill="none" stroke-linecap="round"/><ellipse cx="152" cy="1200" rx="40" ry="34" fill="#3a2a1c"/>'}
 {'' if pose == 'thinking' else '<path d="M578,800 Q648,950 618,1180" stroke="#e6dac2" stroke-width="72" fill="none" stroke-linecap="round"/><ellipse cx="616" cy="1200" rx="40" ry="34" fill="#3a2a1c"/>'}
 <!-- गर्दन + गमछा -->
 <rect x="322" y="640" width="124" height="110" rx="40" fill="{FUR}"/>
 <path d="M262,720 Q384,800 506,720 L520,770 Q384,860 248,770Z" fill="url(#gam)" stroke="#8e2a20" stroke-width="3"/>
 <path d="M440,780 L470,940 L420,950 L405,800Z" fill="url(#gam)" stroke="#8e2a20" stroke-width="3"/>
 <g transform="translate(384 470) scale(1.22) translate(-384 -400)">
 <!-- सींग -->
 <path d="M318,250 Q250,120 150,150 Q230,150 268,250Z" fill="url(#horn)" stroke="{HORN_D}" stroke-width="4"/>
 <path d="M450,250 Q518,120 618,150 Q538,150 500,250Z" fill="url(#horn)" stroke="{HORN_D}" stroke-width="4"/>
 <path d="M280,200 L300,215 M250,170 L262,190 M488,200 L468,215 M518,170 L506,190" stroke="{HORN_D}" stroke-width="4"/>
 <!-- कान -->
 <g transform="rotate(18 230 360)"><ellipse cx="190" cy="360" rx="78" ry="30" fill="{FUR_D}"/><ellipse cx="196" cy="362" rx="56" ry="16" fill="#e2a49a"/></g>
 <g transform="rotate(-18 538 360)"><ellipse cx="578" cy="360" rx="78" ry="30" fill="{FUR_D}"/><ellipse cx="572" cy="362" rx="56" ry="16" fill="#e2a49a"/></g>
 <!-- सिर -->
 <ellipse cx="384" cy="380" rx="140" ry="150" fill="url(#fur)"/>
 <path d="M300,250 Q384,200 470,250 Q440,232 384,236 Q328,232 300,250Z" fill="{FUR_L}"/>
 <path d="M345,232 Q370,200 384,236 Q400,198 425,232" fill="{FUR}" stroke="{FUR_D}" stroke-width="3"/>
 <ellipse cx="438" cy="392" rx="66" ry="70" fill="{PATCH}" opacity=".85"/>
 <!-- थूथन -->
 <ellipse cx="384" cy="520" rx="104" ry="92" fill="url(#muz)"/>
 <!-- दाढ़ी -->
 <path d="M350,598 Q384,640 418,598 Q412,690 384,720 Q356,690 350,598Z" fill="{FUR_D}" stroke="#b39b72" stroke-width="3"/>
 {eyes}
 <path d="M352,474 Q384,456 416,474 Q412,500 384,506 Q356,500 352,474Z" fill="#8c5a4e"/>
 <ellipse cx="368" cy="484" rx="8" ry="5" fill="#3b221c"/><ellipse cx="400" cy="484" rx="8" ry="5" fill="#3b221c"/>
 <path d="M384,506 L384,526" stroke="#3b2a1c" stroke-width="4"/>
 {mouth(state, e)}
 </g>
</g>
{hand}
</svg>'''


def render(jobs, out_dir):
    from playwright.sync_api import sync_playwright
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": W, "height": H})
        for name, s in jobs:
            pg.set_content(f'<html><body style="margin:0;background:transparent">{s}</body></html>')
            pg.screenshot(path=str(out_dir / name), clip={"x": 0, "y": 0, "width": W, "height": H}, omit_background=True)
        b.close()


def jobs():
    out = []
    for ex in EXPRS:
        for st in ("closed", "half", "open"):
            out.append((f"{ex}_{st}.png", svg(ex, st)))
    out.append(("blink.png", svg("neutral", "closed", blink=True)))
    for pose, (ex, st, x) in POSES.items():
        out.append((f"{pose}.png", svg(ex, st, blink=(pose == "laugh"), pose=x if isinstance(x, str) else pose)))
    return out


if __name__ == "__main__":
    ROOT = Path(__file__).parent
    if sys.argv[1:] == ["preview"]:
        d = Path(sys.argv[2] if len(sys.argv) > 2 else "/tmp/bakra_prev")
        render(jobs(), d)
    else:
        render(jobs(), ROOT / "assets/toon/bakra")
