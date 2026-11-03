"""Join the cached Gemini narration to the verified TRAI visual scenes, without blur or caption collisions."""
import json
import math
import subprocess
import wave
from pathlib import Path
from PIL import Image, ImageDraw, ImageOps
import build_trai_visuals as visuals
import talk_test as tt


def frame(index, t, proof):
    im = visuals.scene(index, t)
    d = ImageDraw.Draw(im)
    d.rectangle((0, 1080, 720, 1280), fill='#f3f1e9')
    d.line((35, 1080, 685, 1080), fill='#a9c3c6', width=2)
    d.text((360, 1105), 'आधिकारिक आदेश का संबंधित हिस्सा', font=tt.font(22), fill='#17344a', anchor='mm')
    # An authentic document excerpt is supporting evidence, never a blurred full-screen filler.
    crop_h = min(proof.height, int(proof.width * 0.24))
    top = max(0, proof.height - crop_h) if index == 1 else 0
    excerpt = proof.crop((0, top, proof.width, top + crop_h))
    excerpt = ImageOps.contain(excerpt, (650, 105), Image.Resampling.LANCZOS)
    im.paste(excerpt, ((720 - excerpt.width) // 2, 1135 + (105 - excerpt.height) // 2))
    d.text((360, 1260), 'स्रोत: TRAI • 02 नवंबर 2026 • व्याख्यात्मक दृश्य', font=tt.font(21), fill='#52656f', anchor='mm')
    return im


def main(root='st_in', output='bakra_news_trai_final.mp4'):
    root = Path(root)
    episode = json.loads((root / 'episode.json').read_text(encoding='utf-8'))
    if episode.get('_voice') != 'gemini':
        raise RuntimeError('This final requires the cached Gemini voice')
    parts = Path('trai_clean_parts')
    parts.mkdir(exist_ok=True)
    checks, durations, previews = [], [], []
    for i, line in enumerate(episode['lines']):
        audio = root / 'audio' / f'{i:02d}.wav'
        with wave.open(str(audio)) as wav:
            seconds = wav.getnframes() / wav.getframerate()
        proof = Image.open(root / 'broll' / f'{i}_0own0.png').convert('RGB')
        output_part = parts / f'{i}.mp4'
        proc = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24',
            '-s', '720x1280', '-r', '15', '-i', '-', '-i', str(audio), '-t', str(seconds),
            '-vf', 'scale=1080:1920', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '21',
            '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '160k', '-movflags', '+faststart', str(output_part)], stdin=subprocess.PIPE)
        for k in range(math.ceil(seconds * 15)):
            proc.stdin.write(frame(i, (k / 15) * 10 / seconds, proof).tobytes())
        proc.stdin.close()
        if proc.wait():
            raise RuntimeError('Clean TRAI segment encoding failed')
        durations.append(seconds)
        previews.append(frame(i, 5, proof).resize((288, 512)))
        checks.append({'line': i, 'source_document': True, 'animated_explanation': True, 'voice': 'gemini'})
        print('Clean scene complete:', i, flush=True)
    listing = parts / 'list.txt'
    listing.write_text(''.join("file '" + p.resolve().as_posix() + "'\n" for p in sorted(parts.glob('[0-9].mp4'))))
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', str(listing),
                    '-c', 'copy', '-movflags', '+faststart', output], check=True)
    sheet = Image.new('RGB', (1440, 512), 'white')
    for i, preview in enumerate(previews):
        sheet.paste(preview, (i * 288, 0))
    sheet.save('trai_clean_preview.jpg', quality=90)
    Path('trai_clean_quality.json').write_text(json.dumps({'topic': episode['topic'], 'voice': 'gemini',
        'narration_seconds': round(sum(durations), 2), 'lines': checks, 'blur_background': False,
        'repeated_insurance_story': False, 'source': episode['sources']}, ensure_ascii=False, indent=2))
    return output


if __name__ == '__main__':
    import sys
    main(*(sys.argv[1:]))
