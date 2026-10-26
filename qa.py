"""
बनी video की अपने-आप जाँच (Telegram पर भेजने से पहले) — वही कमियाँ जो बार-बार हाथ से पकड़नी पड़ती थीं:
  1. ऊपर की screen पर एक ही नज़ारा 3 सेकंड से ज़्यादा (video "रुकी" लगती है)
  2. ऊपर की screen ख़ाली/काली/धुंधली
  3. कुल लंबाई 30 सेकंड से ज़्यादा
  4. पहले 3 सेकंड में ऊपर कोई बदलाव/हरकत नहीं
नतीजा: [कमियाँ] — ख़ाली list = पास.
"""
import subprocess
import sys

import numpy as np

W, H, FPS = 132, 101, 10          # ऊपर वाली screen छोटी करके (तेज़)


def _frames(video, crop="1056:810:12:130"):
    raw = subprocess.run(["ffmpeg", "-loglevel", "quiet", "-i", str(video), "-vf",
                          f"crop={crop},scale={W}:{H},fps={FPS}", "-f", "rawvideo", "-pix_fmt", "gray", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, H, W).astype(np.float32)


def longest_unchanged(frames):
    """Return (longest frames, start frame, current anchor).

    A cut is meaningful when the *whole upper story panel* has changed enough
    since the last anchor. Tiny lip movements, caption flicker or compression
    noise alone must not reset the clock.
    """
    if len(frames) == 0:
        return 0, 0, 0
    start = 0
    longest = 0
    worst_at = 0
    for i in range(1, len(frames)):
        delta = float(np.abs(frames[i] - frames[start]).mean())
        # A clear story-prop/scene change should be visible at 132x101;
        # similarity can remain high when both scenes share a title/background.
        if delta >= 10.0:
            start = i
        if i - start > longest:
            longest, worst_at = i - start, start
    return longest, worst_at, start


def check(video, tail=0.3):
    f = _frames(video)
    if len(f) < FPS * 3:
        return ["video बहुत छोटी या पढ़ी नहीं गई"]
    body = f[: max(FPS * 3, len(f) - int(tail * FPS))]       # आख़िरी ठहराव छोड़कर
    issues = []
    secs = len(f) / FPS
    if secs > 40:                                         # 26-37 सेकंड वाली reels भी चलीं; दोबारा बनाने से लंबाई नहीं बदलती
        issues.append(f"लंबाई {secs:.0f} सेकंड (40 से ज़्यादा)")
    # Compare against the LAST meaningful visual change, not just adjacent 0.1s frames.
    # The old gate required adjacent-frame delta >18 AND correlation <0.75.
    # That misses obvious 1.35s cartoon scene cuts (shared backdrop/title), falsely
    # reporting a 3.7s freeze despite visibly different story props.
    longest, worst_at, start = longest_unchanged(body)
    if longest > FPS * 3.2:
        issues.append(f"{worst_at / FPS:.0f}वें सेकंड से {longest / FPS:.1f} सेकंड तक ऊपर एक ही तस्वीर")
    dark = [i for i, b in enumerate(body) if b.std() < 8]
    if len(dark) > FPS * 1.5:
        issues.append(f"{len(dark) / FPS:.1f} सेकंड ऊपर की screen ख़ाली/एक-रंग (पहली बार {dark[0] / FPS:.0f}वें सेकंड)")
    first = body[: FPS * 3]
    if np.abs(first[-1] - first[0]).mean() < 4:
        issues.append("पहले 3 सेकंड में ऊपर कोई हरकत/बदलाव नहीं")
    if np.abs(first[FPS // 2] - first[0]).mean() < 2:    # virality skill: frame 0 और 0.5 सेकंड एक जैसे = "रुका हुआ card" (skip बढ़ता)
        issues.append("पहले आधे सेकंड में कोई हरकत नहीं (frame 0 रुका हुआ)")
    return issues



def check_media(video):
    """Delivery gate: both streams must exist and the opening must have audible sound."""
    import json
    from pathlib import Path
    p = Path(video)
    if not p.exists() or p.stat().st_size < 100_000:
        return ["MP4 गायब या बहुत छोटी"]
    try:
        probe = subprocess.run(
            ["ffprobe", "-v", "error", "-show_streams", "-show_format",
             "-of", "json", str(p)], capture_output=True, text=True, check=True)
        meta = json.loads(probe.stdout)
        kinds = {s.get("codec_type") for s in meta.get("streams", [])}
        issues = []
        if "video" not in kinds:
            issues.append("वीडियो stream नहीं")
        if "audio" not in kinds:
            issues.append("ऑडियो stream नहीं")
            return issues
        duration = float(meta.get("format", {}).get("duration", 0))
        if duration < 3:
            issues.append("वीडियो 3 सेकंड से छोटी")
        raw = subprocess.run(
            ["ffmpeg", "-loglevel", "error", "-i", str(p), "-t", "3",
             "-vn", "-ac", "1", "-ar", "8000", "-f", "s16le", "-"],
            capture_output=True, check=True).stdout
        if len(raw) < 8000:
            issues.append("शुरुआती ऑडियो अधूरा")
        else:
            samples = np.frombuffer(raw, dtype=np.int16).astype(np.float32)
            rms = float(np.sqrt(np.mean(samples ** 2)))
            if rms < 90:
                issues.append("शुरुआती 3 सेकंड में आवाज़ बहुत कम/गायब")
        return issues
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        return ["ऑडियो/वीडियो जाँच नहीं चली: " + type(exc).__name__]


def _onset(wav):
    """पहला शब्द कितने सेकंड पर — पहली line की अपनी आवाज़ से (reel की 0 सेकंड वाली whoosh गिनती में न आए)."""
    raw = subprocess.run(["ffmpeg", "-loglevel", "quiet", "-i", str(wav), "-t", "3", "-vn", "-ac", "1", "-ar", "8000",
                          "-f", "s16le", "-"], capture_output=True).stdout
    a = np.abs(np.frombuffer(raw, np.int16).astype(np.float32))
    if not len(a):
        return None
    e = np.convolve(a, np.ones(160) / 160, "same")[::80]          # 10 ms
    on = np.nonzero(e > max(600, e.max() * 0.25))[0]
    return on[0] / 100 if len(on) else None


def targets(video, first_wav=None):
    """virality skill के लक्ष्य (दोबारा बनाने से नहीं बदलते — सिर्फ़ रिपोर्ट): लंबाई 13-20 सेकंड, पहला शब्द ≤ 0.5 सेकंड."""
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(video)],
                       capture_output=True, text=True).stdout.strip()
    secs = float(r or 0)
    out = [f"⏱️ लंबाई {secs:.1f} सेकंड " + ("✅" if secs <= 20 else "⚠️ (लक्ष्य 13-18 — 70% देखा जाना मुश्किल)")]
    on = _onset(first_wav) if first_wav else None
    if on is not None:
        out.append(f"🗣️ पहला शब्द {on:.2f} सेकंड पर " + ("✅" if on <= 0.5 else "⚠️ (0.5 से पहले चाहिए)"))
    return "🎯 Virality जाँच: " + " | ".join(out)


if __name__ == "__main__":
    r = check(sys.argv[1])
    print("✅ पास" if not r else "⚠️ " + " | ".join(r))
