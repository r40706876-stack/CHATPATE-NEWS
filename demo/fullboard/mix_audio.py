"""Demo ki awaaz: render meta.json ke SFX pal -> chhote sound + halki dhun -> wav.
python mix_audio.py meta.json out.wav"""
import json
import sys
import wave

import numpy as np

SR = 44100
rng = np.random.default_rng(7)


def band(x, lo, hi):
    f = np.fft.rfft(x)
    fr = np.fft.rfftfreq(len(x), 1 / SR)
    f[(fr < lo) | (fr > hi)] = 0
    return np.fft.irfft(f, len(x))


def env(n, a=0.01, r=0.1):
    e = np.ones(n)
    na, nr = max(1, int(a * SR)), max(1, int(r * SR))
    e[:na] = np.linspace(0, 1, na)
    e[-nr:] *= np.linspace(1, 0, nr)
    return e


def norm(x, g):
    m = np.max(np.abs(x)) or 1
    return x / m * g


def pencil(d):
    n = int(d * SR)
    x = band(rng.standard_normal(n), 1800, 7000)
    t = np.arange(n) / SR
    am = 0.55 + 0.45 * np.abs(np.sin(2 * np.pi * 7.5 * t + rng.random() * 3)) * (0.7 + 0.3 * rng.random(n))
    return norm(x * am * env(n, .03, .06), .10)


def swish():
    n = int(.22 * SR)
    x = band(rng.standard_normal(n), 2500, 9000)
    return norm(x * np.hanning(n) ** 0.7, .16)


def thud(g=.55):
    n = int(.45 * SR)
    t = np.arange(n) / SR
    s = np.sin(2 * np.pi * (75 - 30 * t) * t) * np.exp(-t * 9)
    c = band(rng.standard_normal(n), 100, 900) * np.exp(-t * 40) * .5
    return norm(s + c, g)


def stamp():
    n = int(.5 * SR)
    t = np.arange(n) / SR
    k = np.sin(2 * np.pi * 170 * t) * np.exp(-t * 28)
    slap = band(rng.standard_normal(n), 800, 4500) * np.exp(-t * 55)
    th = np.pad(thud(.5), (0, n))[:n]
    return norm(th + .5 * k + .6 * slap, .6)


def whoosh():
    n = int(.5 * SR)
    x = rng.standard_normal(n)
    out = np.zeros(n)
    for i, (lo, hi) in enumerate([(300, 1200), (600, 2500), (1200, 4500)]):
        seg = band(x, lo, hi) * np.sin(np.linspace(0, np.pi, n)) ** (2 + i)
        out += seg
    return norm(out, .20)


def tone(freqs, d, dec, g):
    n = int(d * SR)
    t = np.arange(n) / SR
    s = sum(np.sin(2 * np.pi * f * t) * (0.6 ** i) for i, f in enumerate(freqs))
    return norm(s * np.exp(-t * dec) * env(n, .004, .05), g)


def ding():
    return tone([1318.5, 1975.5, 2637], .9, 4.5, .22)


def chime():
    out = np.zeros(int(1.2 * SR))
    for i, f in enumerate([880, 1108.7, 1318.5]):
        s = tone([f, f * 2], .9, 4, .13)
        o = int(i * .09 * SR)
        out[o:o + len(s)] += s
    return out


def pop():
    n = int(.09 * SR)
    t = np.arange(n) / SR
    return norm(np.sin(2 * np.pi * (520 + 2600 * t) * t) * np.exp(-t * 45), .17)


def tape():
    n = int(.32 * SR)
    x = band(rng.standard_normal(n), 300, 3500)
    t = np.arange(n) / SR
    return norm(x * (0.5 + 0.5 * np.sign(np.sin(2 * np.pi * 38 * t))) * np.exp(-t * 6), .2) + np.pad(thud(.3), (0, n))[:n]


def power():
    n = int(.6 * SR)
    t = np.arange(n) / SR
    return norm(np.sin(2 * np.pi * (180 * t + 500 * t * t)) * np.sin(np.pi * t / .6) ** 2, .08)


def bed(total):
    """halki dhun: 4 chord, dheemi, pichhe."""
    n = int(total * SR)
    t = np.arange(n) / SR
    chords = [[261.6, 329.6, 392.0, 493.9], [220.0, 261.6, 329.6, 392.0], [174.6, 220.0, 261.6, 329.6], [196.0, 246.9, 293.7, 392.0]]
    out = np.zeros(n)
    L = 4.0
    for ci in range(int(total / L) + 1):
        a = int(ci * L * SR)
        if a >= n:
            break
        m = min(n - a, int((L + 1.5) * SR))
        tt = np.arange(m) / SR
        e = np.minimum(1, tt / 1.2) * np.minimum(1, np.maximum(0, (L + 1.5 - tt) / 1.5))
        s = sum(np.sin(2 * np.pi * f * tt) + .25 * np.sin(2 * np.pi * f * 2 * tt + 1) for f in chords[ci % 4])
        out[a:a + m] += s * e
    pulse = 0.85 + 0.15 * np.sin(2 * np.pi * 2.0 * t)
    out = band(out * pulse, 80, 2500)
    return norm(out, .045)


MAKE = {"pencil": None, "swish": swish, "thud": thud, "stamp": stamp, "whoosh": whoosh, "ding": ding,
        "chime": chime, "pop": pop, "tape": tape, "power": power}


def main():
    meta = json.load(open(sys.argv[1]))
    total = meta["total"] + .5
    n = int(total * SR)
    mix = bed(total)[:n]
    mix = np.pad(mix, (0, n - len(mix)))
    for ev in meta["sfx"]:
        s = pencil(ev.get("d", .5)) if ev["k"] == "pencil" else MAKE[ev["k"]]()
        a = int(ev["t"] * SR)
        if a >= n:
            continue
        s = s[:n - a]
        mix[a:a + len(s)] += s
    mix = np.tanh(mix * 1.4) / 1.4
    st = np.stack([mix, mix * .97], 1)
    data = (np.clip(st, -1, 1) * 32000).astype(np.int16)
    with wave.open(sys.argv[2], "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(data.tobytes())
    print("AUDIO", sys.argv[2], round(total, 1))


if __name__ == "__main__":
    main()
