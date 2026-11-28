"""Render the Postal Edge syllabus hook or body using the approved puppets."""
import argparse
from functools import lru_cache
import json
import math
import re
from pathlib import Path
import subprocess

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps
from postal_edge_lip_shapes import measure_mouth
from postal_edge_puppet import puppet

W, H, FPS, RATE = 720, 1280, 24, 48000
CREAM, RED, INK, NAVY, GOLD = "#fff8eb", "#a22432", "#281e27", "#1e324d", "#ffdb55"
BOARDS = [
    ("पढ़ाई कितनी हुई?", ()),
    ("तैयारी की दो गलतियाँ", ("नोट्स ढूँढते रहना", "बिना पैटर्न देखे पढ़ना")),
    ("Postal Edge", ("एक जगह से शुरुआत करें",)),
    ("फ्री में शुरुआत करें", ("डेमो क्लास", "स्टडी नोट्स", "मॉक टेस्ट")),
    ("MTS  •  Paper I  •  100 अंक", ("PO Guide I  ·  46 अंक", "Postal Manual V  ·  14 अंक", "GK  ·  20   |   गणित  ·  20")),
    ("Postman  •  150 अंक", ("Paper I  ·  100 अंक", "Paper II  ·  50 अंक")),
    ("Postman  •  Paper II", ("PO Guide I  ·  10 अंक", "Manual VI, Part III  ·  20 अंक", "Manual VII  ·  20 अंक")),
    ("Qualifying Papers", ("दोनों  ·  स्थानीय भाषा", "Postman  ·  टाइपिंग (DEST) भी")),
    ("Free Demo Class", ("चित्रों से समझें  •  फिर फैसला करें", "postaledge.in")),
    ("अगले पार्ट में", ("GDS से MTS बनने का सही रास्ता", "postaledge.in")),
]
MIN_DURATIONS = (3, 4.3, 3.4, 3.4, 5.0, 2.5, 5.0, 4.0, 4.8, 3.4)


@lru_cache
def font(size, hindi=False):
    family = "NotoSansDevanagari" if hindi else "NotoSans"
    return ImageFont.truetype(f"/usr/share/fonts/truetype/noto/{family}-Bold.ttf", size)


def runs(content, size):
    for group in re.findall(r"[\u0900-\u097f]+|[^\u0900-\u097f]+", content):
        yield group, font(size, "\u0900" <= group[0] <= "\u097f")


def text_width(draw, content, size):
    return sum(draw.textlength(group, font=face) for group, face in runs(content, size))


def label(draw, x, y, content, size, color):
    while text_width(draw, content, size) > 590:
        size -= 1
    pieces = list(runs(content, size))
    bounds = [draw.textbbox((0, 0), group, font=face, anchor="ls") for group, face in pieces]
    baseline = y - (min(bounds_row[1] for bounds_row in bounds)
                    + max(bounds_row[3] for bounds_row in bounds))/2
    left = x - text_width(draw, content, size)/2
    for group, face in pieces:
        draw.text((left, baseline), group, font=face, fill=color, anchor="ls")
        left += draw.textlength(group, font=face)


def box(draw, bounds, fill, radius=16, outline=None):
    draw.rounded_rectangle(bounds, radius, fill=fill, outline=outline, width=2)


def ease(progress):
    value = min(1, max(0, progress))
    return value * value * (3 - 2*value)


def caption(draw, text, speaker):
    words = text.split()
    lines = [""]
    for word in words:
        candidate = (lines[-1] + " " + word).strip()
        if lines[-1] and text_width(draw, candidate, 32) > 575:
            lines.append(word)
        else:
            lines[-1] = candidate
    box(draw, (52, 971, 668, 1084), CREAM, 18, "#ead4bb")
    box(draw, (282, 948, 438, 983), RED if speaker == "bhaiya" else NAVY, 14)
    label(draw, 360, 966, "डाकिया भाई" if speaker == "bhaiya" else "गोलू", 20, CREAM)
    for index, line in enumerate(lines):
        y = 1032 + (index - (len(lines)-1)/2)*40
        if index == len(lines) - 1:
            width = min(574, text_width(draw, line, 32) + 18)
            box(draw, (360-width/2, y-18, 360+width/2, y+18), "#ffe38b", 7)
        label(draw, 360, y, line, 32, INK)


def scene(background, index, t, speaker, line, mouth):
    zoom = int(7 * ease(t/3))
    im = background.crop((zoom, zoom, W-zoom, H-zoom)).resize((W,H)).convert("RGBA")
    im = Image.blend(im, Image.new("RGBA", im.size, "#e6bea0"), .20)
    draw = ImageDraw.Draw(im)
    box(draw, (42, 96, 678, 146), CREAM, 14)
    label(draw, 148, 121, "POSTAL EDGE", 25, RED)
    label(draw, 563, 121, "postaledge.in", 22, NAVY)
    box(draw, (148, 160, 572, 207), NAVY, 17)
    label(draw, 360, 184, "GDS → MTS / Postman 2027", 26, "#fff1c2")
    title, details = BOARDS[index]
    if index == 0:
        box(draw, (73, 252, 647, 493), CREAM, 25, "#edc8a9")
        label(draw, 360, 304, "समय निकाला…", 40, RED)
        if t >= .62:
            p = ease((t-.62)/.35)
            for x, icon in [(249, "घड़ी"), (471, "किताब")]:
                box(draw, (x-100, 361 + 16*(1-p), x+100, 420 + 16*(1-p)), "#f5e1c4", 16)
                label(draw, x, 392 + 16*(1-p), icon if t < 1.5 else ("नोट्स" if x < 300 else "सवाल"), 26, NAVY)
            if t >= 2.0:
                box(draw, (123, 430, 597, 482), GOLD, 14)
                label(draw, 360, 457, title, 35, INK)
    else:
        box(draw, (64, 239, 656, 517), CREAM, 22, "#edc8a9")
        box(draw, (83, 255, 637, 322), RED, 17)
        label(draw, 360, 289, title, 33, CREAM)
        for row, detail in enumerate(details):
            if t < row*.28:
                continue
            y = 355 + row*53
            box(draw, (92, y-20, 628, y+22), "#fff0cf" if row%2 == 0 else "#f5e0d5", 9)
            label(draw, 360, y, detail, 29, INK)
        if index in (4, 5, 6, 7):
            label(draw, 360, 495, "2026 के विभागीय पैटर्न पर आधारित", 20, RED)
    for golu in (True, False):
        active = (speaker == "golu") == golu
        actor = puppet(golu, t, 0, .62 if golu else -.54, mouth if active else None,
                       "surprise" if index == 0 and golu else "happy",
                       (.66, ("raise" if golu else "pointup") if active else "chin"),
                       .59 if golu else -.53, 0, .15 * math.sin(t*3))
        size = 292 if active else 271
        actor = actor.resize((size, int(size*520/340)), Image.Resampling.LANCZOS)
        im.alpha_composite(actor, (82 if golu else 351, 509 if active else 531))
    caption(ImageDraw.Draw(im), line, speaker)
    return im.convert("RGB")


def read_audio(path, duration, mute):
    sample_count = round(duration * RATE)
    if mute:
        return np.zeros(sample_count, dtype=np.float32)
    command = ["ffmpeg", "-v", "error", "-i", str(path), "-ac", "1", "-ar", str(RATE),
               "-af", "loudnorm=I=-17:TP=-2:LRA=7", "-f", "f32le", "-"]
    spoken = np.frombuffer(subprocess.check_output(command), dtype="<f4")
    if duration == 3 and len(spoken) > 2.82*RATE:
        tempo = len(spoken)/(2.82*RATE)
        command = ["ffmpeg", "-v", "error", "-f", "f32le", "-ac", "1", "-ar", str(RATE),
                   "-i", "-", "-af", f"atempo={tempo}", "-f", "f32le", "-"]
        spoken = np.frombuffer(subprocess.check_output(command, input=spoken.tobytes()), dtype="<f4")
    return np.r_[np.zeros(1920, dtype="float32"), spoken]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--office", type=Path, required=True)
    parser.add_argument("--lines", type=Path, required=True)
    parser.add_argument("--audio", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--part", choices=["hook", "body"], required=True)
    parser.add_argument("--mute", action="store_true")
    args = parser.parse_args()
    rows = json.loads(args.lines.read_text())
    rows = [row for row in rows if (row[0] == 0) == (args.part == "hook")]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    raw = args.output.with_suffix(".f32")
    segments = []
    for index, role, text, *_ in rows:
        audio = read_audio(args.audio / f"line{index}.wav", MIN_DURATIONS[index], args.mute)
        n = 3 * FPS if index == 0 else math.ceil(max(MIN_DURATIONS[index], len(audio)/RATE+.16)*FPS)
        samples = n * RATE // FPS
        if index == 0 and len(audio) > samples and not args.mute:
            raise ValueError("Hook voice exceeds 3 seconds after fitting")
        audio = np.pad(audio, (0, max(0, samples-len(audio))))[:samples].astype("<f4")
        segments.append((index, role, text, n, audio))
    np.concatenate([part[-1] for part in segments]).tofile(raw)
    backgrounds = [
        ImageOps.fit(Image.open(args.office/f"office{i}.jpg").convert("RGB"), (W,H))
        for i in (0, 1, 2)
    ]
    command = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pixel_format", "rgb24",
               "-video_size", f"{W}x{H}", "-framerate", str(FPS), "-i", "-",
               "-f", "f32le", "-ar", str(RATE), "-ac", "1", "-i", str(raw),
               "-c:v", "libx264", "-preset", "veryfast", "-crf", "19", "-pix_fmt", "yuv420p",
               "-threads", "3", "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart",
               str(args.output)]
    render = subprocess.Popen(command, stdin=subprocess.PIPE)
    try:
        for index, role, subtitle, count, audio in segments:
            mouths = measure_mouth(audio[::3], FPS, count/FPS)
            backdrop = backgrounds[1 if index < 4 else 2 if index < 8 else 0]
            for frame in range(count):
                output = scene(backdrop, index, frame/FPS, role, subtitle, mouths[frame])
                render.stdin.write(output.tobytes())
    finally:
        render.stdin.close()
    if render.wait():
        raise RuntimeError("FFmpeg failed")
    raw.unlink()


if __name__ == "__main__":
    main()
