"""Cold open: reel का पहला second ही joke दिखाए (29 Oct, असली data: 57% लोग 1-3 सेकंड में जा रहे थे — तब तक joke आया ही नहीं).
सबसे ज़्यादा देखे गए references (Prakash Bharati, mock documentary, Satish Ray…) का साझा तरीका: पहला दृश्य ख़ुद मज़ाक है —
टूटी छत, कमर तक पानी, चार जैकेट पहना आदमी. हमारे पास हर खबर का असली ऐसा दृश्य नहीं होता, इसलिए रोज़ की चीज़ों के
ढाँचे — जिन्हें हर भारतीय एक नज़र में पहचानता है — writer उनमें joke भरता है:

  phone     — फ़ोन की notification       {"app": "…", "title": "…", "body": "…", "btn": ["…", "…"]}
  whatsapp  — परिवार ग्रुप का forward    {"group": "…", "sender": "…", "msg": "…", "tag": "Forwarded many times"}
  bill      — बिल/रसीद                  {"shop": "…", "rows": [["चीज़", "₹"]…], "total": "…", "note": "…"}
  notice    — सरकारी नोटिस/बोर्ड         {"office": "…", "title": "…", "body": "…", "sign": "…"}
  price     — दुकान का दाम-बोर्ड          {"item": "…", "old": "…", "new": "…", "note": "…"}

render(kind, data, out) → 1056x810 PNG (ऊपर की news screen के नाप का) + zoom() → पहले second के लिए क़रीब का हिस्सा.
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).parent))
import render_reel as rr  # noqa: E402

W, H = 1056, 810


def _wrap(text, f, width):
    words, rows, cur = str(text).split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if f.getlength(t) <= width:
            cur = t
        else:
            rows.append(cur)
            cur = w
    return rows + ([cur] if cur else [])


def _fit(d, text, x, y, width, size, fill, max_rows=3, anchor="la", step=1.18):
    """text को width में, size घटाकर, ज़्यादा से ज़्यादा max_rows में. लौटाता है नीचे का y."""
    while True:
        f = rr.font(size)
        rows = _wrap(text, f, width)
        if len(rows) <= max_rows or size <= 22:
            break
        size -= 4
    for r in rows[:max_rows]:
        d.text((x, y), r, font=f, fill=fill, anchor=anchor)
        y += int(size * step)
    return y


def _bg(c1=(18, 22, 40), c2=(28, 34, 60)):
    im = Image.new("RGB", (W, H), c1)
    d = ImageDraw.Draw(im)
    for k in range(0, W + 300, 40):
        d.line((k, 0, k - 300, H), fill=c2, width=3)
    return im, d


def phone(data):
    im, d = _bg()
    px0, py0, px1, py1 = 298, 24, 758, 806
    d.rounded_rectangle((px0 - 14, py0 - 14, px1 + 14, py1 + 20), 60, fill=(10, 10, 14))
    scr = Image.new("RGB", (px1 - px0, py1 - py0))
    sd = ImageDraw.Draw(scr)
    for y in range(scr.height):
        c = int(40 + 60 * y / scr.height)
        sd.line((0, y, scr.width, y), fill=(c // 2, c // 2 + 10, c + 40))
    sd.text((scr.width / 2, 70), data.get("time", "10:43"), font=rr.font(64), fill="white", anchor="mm")
    if data.get("status"):
        sd.text((scr.width / 2, 125), data["status"], font=rr.font(30), fill=(255, 130, 130), anchor="mm")
    nx0, ny0, nx1 = 20, 180, scr.width - 20
    card = Image.new("RGB", (nx1 - nx0, 600), (245, 245, 250))
    cd = ImageDraw.Draw(card)
    cd.ellipse((20, 22, 76, 78), fill=(90, 80, 230))
    cd.text((48, 50), str(data.get("icon", "●"))[:2], font=rr.font(26), fill="white", anchor="mm")
    cd.text((92, 50), str(data.get("app", ""))[:22], font=rr.font(28), fill=(60, 60, 70), anchor="lm")
    y = _fit(cd, data.get("title", ""), 26, 100, card.width - 52, 46, (20, 20, 20), 2)
    y = _fit(cd, data.get("body", ""), 26, y + 8, card.width - 52, 52, (200, 20, 40), 3)
    btn = data.get("btn") or []
    if btn:
        y += 16
        cd.rounded_rectangle((26, y, 200, y + 56), 22, fill=(200, 20, 40))
        cd.text((113, y + 28), str(btn[0])[:10], font=rr.font(30), fill="white", anchor="mm")
        if len(btn) > 1:
            cd.rounded_rectangle((card.width - 200, y, card.width - 26, y + 56), 22, outline=(120, 120, 130), width=3)
            cd.text((card.width - 113, y + 28), str(btn[1])[:10], font=rr.font(30), fill=(80, 80, 90), anchor="mm")
        y += 56
    card = card.crop((0, 0, card.width, y + 24))
    m = Image.new("L", card.size, 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, card.width - 1, card.height - 1), 28, fill=255)
    scr.paste(card, (nx0, ny0), m)
    if data.get("footer"):
        sd.text((scr.width / 2, ny0 + card.height + 90), data["footer"], font=rr.font(42), fill=(255, 214, 0), anchor="mm")
    im.paste(scr, (px0, py0))
    return im, (px0, ny0 + py0 - 14, px1, ny0 + py0 + card.height + 14)


def whatsapp(data):
    im = Image.new("RGB", (W, H), (236, 229, 221))
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, W, 110), fill=(7, 94, 84))
    d.ellipse((30, 22, 96, 88), fill=(200, 200, 200))
    d.text((120, 40), str(data.get("group", "परिवार")).replace("❤️", "")[:26], font=rr.font(40), fill="white", anchor="lm")
    d.text((120, 82), "पापा, मम्मी, चाचा, +34", font=rr.font(26), fill=(220, 240, 235), anchor="lm")
    bx0, by0, bx1 = 60, 170, W - 160
    tmp = Image.new("RGB", (bx1 - bx0, 700), "white")
    td = ImageDraw.Draw(tmp)
    td.text((24, 24), str(data.get("sender", "चाचा"))[:20], font=rr.font(30), fill=(200, 60, 40), anchor="la")
    td.text((24, 70), "» " + str(data.get("tag", "Forwarded many times")), font=rr.font(24), fill=(130, 130, 130), anchor="la")
    y = _fit(td, data.get("msg", ""), 24, 115, tmp.width - 48, 50, (20, 20, 20), 5)
    td.text((tmp.width - 20, y + 20), "10:43", font=rr.font(22), fill=(80, 150, 230), anchor="ra")
    tmp = tmp.crop((0, 0, tmp.width, y + 60))
    m = Image.new("L", tmp.size, 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, tmp.width - 1, tmp.height - 1), 22, fill=255)
    im.paste(tmp, (bx0, by0), m)
    return im, (bx0 - 10, by0 - 10, bx1 + 10, by0 + tmp.height + 10)


def bill(data):
    im, d = _bg((30, 24, 20), (40, 32, 26))
    x0, y0, x1 = 178, 20, 878
    paper = Image.new("RGB", (x1 - x0, 790), (250, 248, 240))
    pd = ImageDraw.Draw(paper)
    pd.text((paper.width / 2, 50), str(data.get("shop", "बिल"))[:24], font=rr.font(46), fill=(20, 20, 20), anchor="mm")
    pd.line((30, 90, paper.width - 30, 90), fill=(120, 120, 120), width=2)
    y = 120
    for name, amt in (data.get("rows") or [])[:6]:
        pd.text((30, y), str(name)[:22], font=rr.font(44), fill=(30, 30, 30), anchor="la")
        pd.text((paper.width - 30, y), str(amt)[:12], font=rr.font(44), fill=(30, 30, 30), anchor="ra")
        y += 70
    pd.line((30, y + 6, paper.width - 30, y + 6), fill=(120, 120, 120), width=2)
    pd.text((30, y + 30), "कुल", font=rr.font(54), fill=(20, 20, 20), anchor="la")
    pd.text((paper.width - 30, y + 30), str(data.get("total", ""))[:12], font=rr.font(54), fill=(200, 20, 40), anchor="ra")
    y += 110
    if data.get("note"):
        y = _fit(pd, data["note"], 30, y, paper.width - 60, 44, (200, 20, 40), 3)
    paper = paper.crop((0, 0, paper.width, min(790, y + 30)))
    im.paste(paper, (x0, y0))
    return im, (x0, y0, x1, y0 + paper.height)


def notice(data):
    im, d = _bg((60, 50, 40), (70, 58, 46))
    x0, y0, x1, y1 = 120, 40, 936, 770
    d.rectangle((x0 - 16, y0 - 16, x1 + 16, y1 + 16), fill=(110, 70, 30))
    d.rectangle((x0, y0, x1, y1), fill=(246, 238, 210))
    d.text(((x0 + x1) / 2, y0 + 60), str(data.get("office", "कार्यालय"))[:30], font=rr.font(40), fill=(30, 30, 30), anchor="mm")
    d.text(((x0 + x1) / 2, y0 + 130), str(data.get("title", "सूचना"))[:20], font=rr.font(58), fill=(180, 20, 30), anchor="mm")
    y = _fit(d, data.get("body", ""), x0 + 50, y0 + 200, x1 - x0 - 100, 46, (20, 20, 20), 6)
    if data.get("sign"):
        d.text((x1 - 50, min(y1 - 50, y + 40)), str(data["sign"])[:30], font=rr.font(32), fill=(60, 60, 60), anchor="ra")
    return im, (x0, y0 + 100, x1, min(y1, y + 80))


def price(data):
    im, d = _bg((20, 40, 30), (28, 52, 40))
    x0, y0, x1, y1 = 140, 80, 916, 740
    d.rounded_rectangle((x0, y0, x1, y1), 30, fill=(255, 214, 0))
    d.text(((x0 + x1) / 2, y0 + 80), str(data.get("item", ""))[:24], font=rr.font(56), fill=(20, 20, 20), anchor="mm")
    old = str(data.get("old", ""))
    if old:
        f = rr.font(72)
        d.text(((x0 + x1) / 2, y0 + 210), old, font=f, fill=(90, 90, 90), anchor="mm")
        tw = f.getlength(old)
        d.line(((x0 + x1) / 2 - tw / 2 - 10, y0 + 210, (x0 + x1) / 2 + tw / 2 + 10, y0 + 210), fill=(200, 20, 40), width=10)
    d.text(((x0 + x1) / 2, y0 + 360), str(data.get("new", ""))[:14], font=rr.font(130), fill=(200, 20, 40), anchor="mm")
    if data.get("note"):
        _fit(d, data["note"], (x0 + x1) / 2, y0 + 480, x1 - x0 - 80, 42, (20, 20, 20), 3, anchor="ma")
    return im, (x0, y0, x1, y1)


KINDS = {"phone": phone, "whatsapp": whatsapp, "bill": bill, "notice": notice, "price": price}


def render(kind, data, out, zoom_out=None):
    """out = पूरा दृश्य; zoom_out = joke वाला हिस्सा क़रीब से (पहले second के लिए)."""
    im, box = KINDS[kind](data or {})
    im.save(out)
    if zoom_out:
        x0, y0, x1, y1 = box
        crop = im.crop((max(0, x0), max(0, y0), min(W, x1), min(H, y1)))
        s = min(W / crop.width, H / crop.height) * 0.96           # पूरा joke दिखे (किनारे न कटें), जितना बड़ा हो सके
        z = crop.resize((int(crop.width * s), int(crop.height * s)), Image.LANCZOS)
        from PIL import ImageFilter
        base = im.resize((W, H)).filter(ImageFilter.GaussianBlur(18))
        base = Image.blend(base, Image.new("RGB", (W, H)), 0.45)
        base.paste(z, ((W - z.width) // 2, (H - z.height) // 2))
        base.save(zoom_out)
    return out


def for_episode(ep, out_dir):
    """ep["cold_open"] = {"kind", "data", "lines": [line indexes]} → उन lines पर visual_files (पहले zoom, फिर पूरा)."""
    co = ep.get("cold_open") or {}
    if co.get("kind") not in KINDS or not ep.get("lines"):
        return []
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    full, zoom = out_dir / "cold_full.png", out_dir / "cold_zoom.png"
    render(co["kind"], co.get("data") or {}, full, zoom)
    idx = [i for i in (co.get("lines") or [0, 1]) if 0 <= i < len(ep["lines"])] or [0]
    ep["lines"][idx[0]]["visual_files"] = [str(zoom)]
    for i in idx[1:]:
        ep["lines"][i]["visual_files"] = [str(full)]
    return [zoom, full]


if __name__ == "__main__":
    demo = {
        "phone": {"app": "फ़ोन का AI सहायक", "icon": "AI", "status": "बैटरी 14%", "title": "बैटरी बचानी है?",
                  "body": "AI बंद कर दें.", "btn": ["बंद करें", "बाद में"], "footer": "₹11,999 का फ़ोन"},
        "whatsapp": {"group": "परिवार", "sender": "चाचा", "msg": "नासा ने कन्फ़र्म किया: इस दिवाली पटाखे सिर्फ़ WhatsApp पर फूटेंगे. आगे भेजो."},
        "bill": {"shop": "रेलवे टिकट काउंटर", "rows": [["टिकट", "₹180"], ["यात्रा बीमा", "₹0.45"], ["खुल्ला", "टॉफी ×1"]],
                 "total": "₹180.45", "note": "बचे 55 पैसे: टॉफी में लौटाए गए"},
        "notice": {"office": "नगर निगम कार्यालय", "title": "सूचना", "body": "सड़क की मरम्मत पूरी हो चुकी है. गड्ढे फ़िलहाल अपनी जगह पर रहेंगे.",
                   "sign": "आज्ञा से — अधिशासी अभियंता"},
        "price": {"item": "अरहर दाल (1 किलो)", "old": "₹125", "new": "₹145", "note": "आयात 67% बढ़ा. कटोरी वही."},
    }
    out = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
    for k, v in demo.items():
        render(k, v, out / f"co_{k}.png", out / f"co_{k}_zoom.png")
    print("ok")
