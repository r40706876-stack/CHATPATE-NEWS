"""Animated explanation using only the current line's text and credited sources."""
import re
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw
import talk_test as tt

W, H, FPS = 720, 1280, 15


def wrap(draw, text, font, width):
    rows, row = [], ''
    for word in str(text).split():
        candidate = (row + ' ' + word).strip()
        if row and draw.textbbox((0, 0), candidate, font=font)[2] > width:
            rows.append(row)
            row = word
        else:
            row = candidate
    return rows + ([row] if row else [])


def frame(line, sources, t):
    im = Image.new('RGB', (W, H), '#f5f4ec')
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((30, 35, 690, 115), 18, fill='#124f70')
    d.text((360, 75), 'बकरा न्यूज़ | खबर समझिए', font=tt.font(30), fill='white', anchor='mm')
    # Phone / document are explanatory diagrams, never presented as incident footage.
    phone = bool(re.search('मोबाइल|फोन|लिंक|UPI|यूपीआई|डिजिटल|मैसेज', line['say'], re.I))
    box = (225, 155, 495, 470) if phone else (125, 170, 595, 435)
    d.rounded_rectangle(box, 24, fill='white', outline='#124f70', width=7)
    x0, y0, x1, y1 = box
    for i in range(4):
        y = y0 + 55 + i * 48
        d.rounded_rectangle((x0 + 30, y, x1 - 30, y + 18), 6,
                            fill='#f27a35' if int(t * 1.3) % 4 == i else '#d7f0ef')
    text = line.get('say', '')
    clauses = [x.strip() for x in re.split(r'।|(?<!\d),(?!\d)|[!?]', text) if x.strip()]
    clauses = clauses or [text]
    index = min(len(clauses) - 1, int(t / 10 * len(clauses)))
    font = tt.font(38)
    rows = wrap(d, clauses[index], font, 610)
    while len(rows) > 9:
        font = tt.font(max(20, font.size - 2))
        rows = wrap(d, clauses[index], font, 610)
        if font.size == 20:
            break
    for i, row in enumerate(rows):
        d.text((360, 535 + i * (font.size + 15)), row, font=font, fill='#153d55', anchor='mt')
    d.text((360, 1100), 'तथ्य का संकेत-चित्र • घटना की तस्वीर नहीं', font=tt.font(23), fill='#52636c', anchor='mm')
    credit = 'स्रोत: ' + ', '.join(dict.fromkeys(s.get('name', '') for s in sources))
    for i, row in enumerate(wrap(d, credit, tt.font(23), 620)[:3]):
        d.text((360, 1150 + i * 30), row, font=tt.font(23), fill='#52636c', anchor='mm')
    return im


def render(line, sources, out):
    out = Path(out)
    proc = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24',
        '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-an', '-c:v', 'libx264', '-preset', 'veryfast',
        '-crf', '22', '-pix_fmt', 'yuv420p', str(out)], stdin=subprocess.PIPE)
    for k in range(10 * FPS):
        proc.stdin.write(frame(line, sources, k / FPS).tobytes())
    proc.stdin.close()
    if proc.wait():
        raise RuntimeError('News explanation encoding failed')
    out.with_suffix('.txt').write_text('तथ्य आधारित ग्राफिक • स्रोत: ' + ', '.join(s.get('name', '') for s in sources), encoding='utf-8')
    return out
