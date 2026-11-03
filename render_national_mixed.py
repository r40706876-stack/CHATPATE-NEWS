"""Prominent source pictures + supporting cards + factual animation, with cached Gemini narration."""
import argparse
import functools
import hashlib
import json
import math
import subprocess
import urllib.request
import wave
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from PIL import Image, ImageDraw, ImageOps
import talk_test as tt

W, H, FPS = 720, 1280, 20
FONT = functools.lru_cache(maxsize=30)(tt.font)
WORK = Path('national_mixed_work')
ASSETS = {
    'poster': ('https://pbs.twimg.com/media/HV20sk-bIAA4RPZ?format=jpg&name=large', 'PIB द्वारा साझा CyberCrimesHyd जागरूकता पोस्टर'),
    'phone': ('https://images.unsplash.com/photo-1719204718581-5c95889c8ec9?auto=format&fit=crop&fm=jpg&q=85&w=1280', 'प्रतीकात्मक फोटो: Amanz / Unsplash'),
    'money': ('https://images.unsplash.com/photo-1565374392032-8007fb37c26e?auto=format&fit=crop&fm=jpg&q=85&w=1280', 'प्रतीकात्मक फोटो: rupixen / Unsplash'),
}


def label(draw, xy, value, size=36, color='white', anchor='mm'):
    draw.text(xy, value, font=FONT(size), fill=color, anchor=anchor)


def wrap(draw, value, size, width):
    rows, row = [], ''
    for word in value.split():
        test = (row + ' ' + word).strip()
        if row and draw.textbbox((0, 0), test, font=FONT(size))[2] > width:
            rows.append(row)
            row = word
        else:
            row = test
    return rows + ([row] if row else [])


def card(im, box, lines, color='#d84135', size=38):
    d = ImageDraw.Draw(im)
    d.rounded_rectangle(box, 20, fill=color)
    x0, y0, x1, y1 = box
    rows = wrap(d, lines, size, x1 - x0 - 38)
    top = (y0 + y1) / 2 - (len(rows) - 1) * (size + 12) / 2
    for i, row in enumerate(rows):
        label(d, ((x0 + x1) / 2, top + i * (size + 12)), row, size)


def photo(im, image, box, crop=None, zoom=1):
    if crop:
        image = image.crop(crop)
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    fit = ImageOps.fit(image, (int(w * zoom), int(h * zoom)), Image.Resampling.LANCZOS)
    left, top = (fit.width - w) // 2, (fit.height - h) // 2
    im.paste(fit.crop((left, top, left + w, top + h)), (x0, y0))


def frame(index, t, photos):
    im = Image.new('RGB', (W, H), '#08283e')
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((22, 25, 698, 100), 18, fill='#f8c844')
    label(d, (360, 63), 'बकरा न्यूज़ | आपकी जेब और सुरक्षा', 30, '#09283d')
    credits = ''
    z = 1 + 0.025 * min(1, t / 7)
    if index == 0:
        label(d, (360, 138), 'सरकार से ₹8,000 का बोनस?', 42)
        photo(im, photos['poster'], (20, 190, 700, 1040), zoom=z)
        card(im, (30, 1060, 690, 1178), 'दावा फर्जी है • लिंक न खोलें', size=37)
        credits = ASSETS['poster'][1]
    elif index == 1:
        label(d, (360, 147), 'सरकारी नाम, नकली वेबसाइट', 42)
        photo(im, photos['phone'], (20, 215, 700, 720), crop=(230, 90, 1120, 720), zoom=z)
        label(d, (360, 750), 'प्रतीकात्मक तस्वीर • यह फर्जी मैसेज का स्क्रीनशॉट नहीं', 21)
        labels = ['मैसेज', 'नकली लिंक', 'निजी जानकारी']
        active = min(2, int(t / 2))
        for j, word in enumerate(labels):
            y = 825 + j * 110
            card(im, (75, y - 34, 645, y + 40), word, '#d84135' if j == active else '#145a72', 33)
            if j < 2:
                d.polygon([(350, y + 55), (370, y + 55), (360, y + 75)], fill='#f8c844')
        credits = ASSETS['phone'][1]
    elif index == 2:
        label(d, (360, 145), 'बोनस लेने के नाम पर सावधान', 40)
        photo(im, photos['money'], (20, 220, 700, 875), crop=(530, 295, 800, 555), zoom=z)
        label(d, (360, 905), 'भारतीय रुपयों की प्रतीकात्मक तस्वीर', 24)
        warnings = ['OTP / UPI PIN न दें', 'बैंक की जानकारी न दें', 'अग्रिम फीस न भेजें']
        card(im, (30, 958, 690, 1135), warnings[min(2, int(t / 2))], size=42)
        credits = ASSETS['money'][1]
    elif index == 3:
        label(d, (360, 145), 'रकम चली गई? तुरंत कदम उठाएं', 40)
        banner = ImageOps.contain(photos['poster'].crop((0, 1250, 1122, 1402)), (680, 350), Image.Resampling.LANCZOS)
        im.paste(banner, ((720 - banner.width) // 2, 320))
        label(d, (360, 640), 'पहले बैंक को सूचित करें', 39, '#f8c844')
        d.rounded_rectangle((110, 700, 610, 1000), 25, fill='#f4f1e7')
        label(d, (360, 775), 'आर्थिक साइबर धोखाधड़ी', 31, '#0b3d54')
        label(d, (360, 888), '1930', 110, '#d84135')
        # The moving call indicator illustrates reporting, not an actual completed call.
        cx = 235 + int(250 * min(1, t / 4))
        d.ellipse((cx - 10, 1025, cx + 10, 1045), fill='#f8c844')
        card(im, (30, 1080, 690, 1160), 'cybercrime.gov.in', '#145a72', 36)
        credits = 'स्रोत: गृह मंत्रालय / I4C • पोस्टर: CyberCrimesHyd'
    else:
        label(d, (360, 145), 'फॉरवर्ड करने से पहले रुकिए', 42)
        photo(im, photos['poster'], (20, 195, 700, 1045), zoom=z)
        card(im, (30, 1055, 690, 1115), 'पहले आधिकारिक स्रोत से पुष्टि करें', '#145a72', 31)
        card(im, (30, 1125, 690, 1185), 'ठग को बोनस नहीं देना है!', size=34)
        credits = ASSETS['poster'][1]
    d = ImageDraw.Draw(im)
    label(d, (360, 1215), credits, 20)
    label(d, (360, 1255), 'राष्ट्रीय चेतावनी • PIB Fact Check • 02 नवंबर 2026', 21, '#f8c844')
    return im


def download_assets():
    (WORK / 'assets').mkdir(parents=True, exist_ok=True)
    def get(item):
        key, (url, _) = item
        path = WORK / 'assets' / (key + '.jpg')
        if not path.exists():
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0', 'Referer': 'https://platform.twitter.com/'})
            with urllib.request.urlopen(req, timeout=60) as response:
                path.write_bytes(response.read())
        with Image.open(path) as check:
            check.verify()
        return path
    with ThreadPoolExecutor(3) as executor:
        list(executor.map(get, ASSETS.items()))


def prepare(script):
    import tts
    WORK.mkdir(exist_ok=True)
    episode = json.loads(Path(script).read_text(encoding='utf-8'))
    cached = WORK / 'episode.json'
    if cached.exists():
        episode = json.loads(cached.read_text(encoding='utf-8'))
    else:
        episode['_voice'] = tts.speak_script(episode, WORK / 'audio')
        if episode['_voice'] != 'gemini':
            raise RuntimeError('Gemini narration is required')
        cached.write_text(json.dumps(episode, ensure_ascii=False, indent=2), encoding='utf-8')
    download_assets()
    print('Prepared fresh national news with Gemini voice and three distinct source images', flush=True)


def render():
    episode = json.loads((WORK / 'episode.json').read_text(encoding='utf-8'))
    if episode.get('_voice') != 'gemini':
        raise RuntimeError('Cached Gemini narration missing')
    photos = {key: Image.open(WORK / 'assets' / (key + '.jpg')).convert('RGB') for key in ASSETS}
    if len({hashlib.sha256((WORK / 'assets' / (key + '.jpg')).read_bytes()).hexdigest() for key in photos}) != 3:
        raise RuntimeError('The prepared pictures are duplicated')
    parts = WORK / 'parts'
    parts.mkdir(exist_ok=True)
    checks, previews = [], []
    for index, line in enumerate(episode['lines']):
        audio = WORK / 'audio' / f'{index:02d}.wav'
        with wave.open(str(audio)) as wav:
            seconds = wav.getnframes() / wav.getframerate()
        target = parts / f'{index}.mp4'
        proc = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24',
            '-s', '720x1280', '-r', str(FPS), '-i', '-', '-i', str(audio), '-t', str(seconds),
            '-vf', 'scale=1080:1920', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '21',
            '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '160k', str(target)], stdin=subprocess.PIPE)
        for k in range(math.ceil(seconds * FPS)):
            proc.stdin.write(frame(index, k / FPS * 7 / seconds, photos).tobytes())
        proc.stdin.close()
        if proc.wait():
            raise RuntimeError('Mixed photo sequence encoding failed')
        previews.append(frame(index, 3.5, photos).resize((288, 512)))
        checks.append({'line': index, 'seconds': seconds, 'prominent_source_image': True,
                       'factual_animation': True, 'voice': 'gemini'})
        print('Rendered mixed source-photo scene', index, flush=True)
    listing = parts / 'list.txt'
    listing.write_text(''.join("file '" + p.resolve().as_posix() + "'\n" for p in sorted(parts.glob('[0-9].mp4'))))
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', str(listing),
        '-c', 'copy', '-movflags', '+faststart', 'bakra_news_bonus_scam.mp4'], check=True)
    preview = Image.new('RGB', (1440, 512), 'white')
    for index, image in enumerate(previews):
        preview.paste(image, (index * 288, 0))
    preview.save('national_mixed_preview.jpg', quality=92)
    Path('national_mixed_quality.json').write_text(json.dumps({'topic': episode['topic'], 'voice': 'gemini',
        'format': 'prominent photos + supporting cards + animation', 'source_image_count': 3,
        'scenes': checks, 'selection_priority': episode['selection_priority']}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=['prepare', 'render'])
    parser.add_argument('script', nargs='?')
    args = parser.parse_args()
    prepare(args.script) if args.mode == 'prepare' else render()
