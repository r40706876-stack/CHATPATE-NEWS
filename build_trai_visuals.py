"""Visuals for the verified TRAI 2 November notification, without text-model calls."""
import math
import subprocess
import urllib.request
from pathlib import Path
import fitz
from PIL import Image, ImageDraw
import talk_test as tt

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'assets/news/trai_20261102'
URL = 'https://www.trai.gov.in/sites/default/files/2026-11/Regulation_02112026.pdf'
W, H, FPS = 720, 1280, 15


def text(d, xy, value, size=42, color='#17344a'):
    d.text(xy, value, font=tt.font(size), fill=color, anchor='mm')


def scene(index, t):
    im = Image.new('RGB', (W, H), '#f3f1e9')
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((25, 30, 695, 110), 20, fill='#0a3e59')
    text(d, (360, 70), 'बकरा न्यूज़ | ग्राहक के काम की खबर', 29, 'white')
    orange, teal, ink = '#e76632', '#117e89', '#17344a'
    if index == 0:
        text(d, (360, 190), 'शिकायत बन्द… बात खत्म?', 47)
        d.rounded_rectangle((195, 295, 525, 850), 32, fill=ink)
        d.rounded_rectangle((210, 320, 510, 805), 20, fill='white')
        text(d, (360, 405), 'शिकायत', 44)
        d.line((260, 470, 460, 470), fill='#c1d8dc', width=8)
        text(d, (360, 540), 'बन्द', 65, orange)
        d.rounded_rectangle((235, 655, 485, 760), 18, fill=teal if t > 2 else '#c1d8dc')
        text(d, (360, 707), 'अपील का रास्ता', 32, 'white')
        if t > 2:
            d.ellipse((475, 665 + int(8 * math.sin(t * 3)), 495, 685 + int(8 * math.sin(t * 3))), fill=orange)
        text(d, (360, 955), 'नया आदेश: 2 नवंबर 2026', 35)
    elif index == 1:
        text(d, (360, 190), 'सहायता 24 घंटे', 56)
        box = (120, 300, 600, 780)
        d.ellipse(box, fill='white', outline=ink, width=9)
        d.arc(box, -90, 150, fill=orange, width=30)
        d.arc(box, 150, 270, fill=teal, width=30)
        angle = t / 10 * math.tau - math.pi / 2
        d.line((360, 540, 360 + int(170 * math.cos(angle)), 540 + int(170 * math.sin(angle))), fill=ink, width=9)
        d.ellipse((347, 527, 373, 553), fill=ink)
        text(d, (360, 850), 'मानव प्रतिनिधि: कम-से-कम 16 घंटे', 35, orange)
        text(d, (360, 925), 'बाकी समय स्वचालित सहायता हो सकती है', 30, teal)
        text(d, (360, 1000), '24 घंटे = हर समय इंसान नहीं', 35)
    elif index == 2:
        text(d, (360, 190), 'कम्पनी की ऐप से भी', 48)
        d.rounded_rectangle((160, 280, 560, 940), 35, fill=ink)
        d.rounded_rectangle((180, 310, 540, 900), 22, fill='white')
        labels = ['शिकायत', 'अपील', 'सेवा अनुरोध']
        active = min(2, int(t / 3))
        for j, label in enumerate(labels):
            y = 395 + j * 135
            d.rounded_rectangle((205, y - 45, 515, y + 45), 16, fill=teal if active == j else '#dce9e8')
            text(d, (360, y), label, 36, 'white' if active == j else ink)
        text(d, (360, 835), 'AI से बात? इसकी सूचना जरूरी', 24, orange)
        text(d, (360, 1010), 'प्रक्रिया का संकेत-चित्र • वास्तविक ऐप नहीं', 26)
    elif index == 3:
        text(d, (360, 190), 'सामान्य अपील अवधि', 49)
        d.rounded_rectangle((85, 330, 635, 805), 22, fill='white', outline=teal, width=5)
        d.rounded_rectangle((85, 330, 635, 425), 20, fill=teal)
        text(d, (360, 378), '30 दिन से', 40, 'white')
        text(d, (360, 585), '15', 150, orange)
        text(d, (360, 730), 'दिन', 52)
        if t > 3:
            d.line((245, 378, 475, 378), fill=orange, width=5)
        text(d, (360, 900), 'देरी की पर्याप्त वजह: सीमित छूट का प्रावधान', 29)
        text(d, (360, 975), 'इसे अपील टालने की वजह न बनाएं', 31, orange)
    else:
        text(d, (360, 185), 'अभी से सब लागू नहीं', 49, orange)
        text(d, (360, 270), 'राजपत्र में प्रकाशन के बाद', 38)
        d.line((150, 390, 150, 870), fill=teal, width=14)
        labels = [('30 दिन', 'सामान्य प्रावधान'), ('60 दिन', 'निर्दिष्ट अपवाद'), ('90 दिन', 'निर्दिष्ट अपवाद')]
        for j, (num, label) in enumerate(labels):
            y = 420 + 210 * j
            active = min(2, int(t / 3)) == j
            d.ellipse((125, y - 25, 175, y + 25), fill=orange if active else teal)
            text(d, (405, y - 10), num, 61, orange if active else ink)
            text(d, (405, y + 65), label, 32)
        text(d, (360, 1030), 'शिकायत नंबर और जवाब सुरक्षित रखें', 33)
    text(d, (360, 1150), 'स्रोत: TRAI • 2 नवंबर 2026 का आधिकारिक आदेश', 23)
    text(d, (360, 1200), 'नियम का व्याख्यात्मक ग्राफिक', 23, '#52656f')
    return im


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    pdf = OUT / 'official_order.pdf'
    if not pdf.exists():
        with urllib.request.urlopen(URL, timeout=90) as response:
            pdf.write_bytes(response.read())
    doc = fitz.open(pdf)
    for i, page_no in enumerate((0, 2, 3, 7, 0)):
        page = doc[page_no]
        # Distinct original document extracts accompany each exact spoken rule.
        if i in (0, 4):
            clip = fitz.Rect(35, 25 if i == 0 else 190, page.rect.width - 30, 235 if i == 0 else 430)
        else:
            clip = fitz.Rect(35, 100, page.rect.width - 30, 640)
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), clip=clip)
        pix.save(str(OUT / f'{i}_source_photo.png'))
        (OUT / f'{i}_source_photo.txt').write_text('स्रोत: TRAI • आधिकारिक आदेश, 02 नवंबर 2026', encoding='utf-8')
        target = OUT / f'{i}_explanation.mp4'
        proc = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24',
            '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-an', '-c:v', 'libx264', '-preset', 'veryfast',
            '-crf', '21', '-pix_fmt', 'yuv420p', str(target)], stdin=subprocess.PIPE)
        for k in range(FPS * 10):
            proc.stdin.write(scene(i, k / FPS).tobytes())
        proc.stdin.close()
        if proc.wait():
            raise RuntimeError('TRAI explanation encoding failed')
        target.with_suffix('.txt').write_text('तथ्य आधारित ग्राफिक • स्रोत: TRAI, 02 नवंबर 2026', encoding='utf-8')
        print('Prepared TRAI scene', i, flush=True)


if __name__ == '__main__':
    main()
