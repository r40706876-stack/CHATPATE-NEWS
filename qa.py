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


def check(video, tail=0.3):
    f = _frames(video)
    if len(f) < FPS * 3:
        return ["video बहुत छोटी या पढ़ी नहीं गई"]
    body = f[: max(FPS * 3, len(f) - int(tail * FPS))]       # आख़िरी ठहराव छोड़कर
    issues = []
    secs = len(f) / FPS
    if secs > 40:                                         # 26-37 सेकंड वाली reels भी चलीं; दोबारा बनाने से लंबाई नहीं बदलती
        issues.append(f"लंबाई {secs:.0f} सेकंड (40 से ज़्यादा)")
    # "वही तस्वीर" = zoom/pan होने पर भी बहुत छोटे (16x12) रूप में scene की शुरुआत जैसी दिखे; cut = पिछले frame से बड़ा फ़र्क
    tiny = [b[::8, ::8].ravel() for b in body]
    cut = np.abs(np.diff(body, axis=0)).mean(axis=(1, 2)) > 18
    longest, start, worst_at = 0, 0, 0
    for i in range(1, len(body)):
        same = tiny[i].std() > 2 and tiny[start].std() > 2 and np.corrcoef(tiny[i], tiny[start])[0, 1] > 0.75
        if cut[i - 1] and not same:
            start = i
        if i - start > longest:
            longest, worst_at = i - start, start
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
