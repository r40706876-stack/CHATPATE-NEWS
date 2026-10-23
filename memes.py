"""
Memes: पंच वाली line के ठीक बाद 2-2.5 सेकंड का मशहूर Hindi meme (पूरी screen, अपनी आवाज़ के साथ).
  • लाइब्रेरी पहले से बनी रहती है (memes/*.mp4, repo में) — हर बार YouTube खोजने से ग़लत/watermark वाली clip आती थी
  • build(): YouTube से हर meme का "meme template" video ढूँढकर शुरू के ~2.4 सेकंड काटता है (probe workflow से एक बार)
  • pick(): line के भाव (expr) से meme; एक reel में ज़्यादा से ज़्यादा 2, हर बार अलग
  • splice(): बनी हुई reel में उन lines के बाद meme जोड़ता है
"""
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent
DIR = ROOT / "memes"
W, H, FPS = 1080, 1920, 25

# id, YouTube खोज, भाव (line के expr से मेल), start (सेकंड), secs
LIB = [
    ("na_ho_payega", "beta tumse na ho payega meme template", "tanz", 0, 2.6),
    ("kya_kar_raha_hai", "bhai kya kar raha hai tu meme template", "hairan", 0, 2.2),
    ("ye_kya_ho_raha", "ye kya ho raha hai meme template", "hairan", 0, 2.2),
    ("rasode_mein", "rasode mein kaun tha meme template", "hairan", 0, 2.6),
    ("kehna_kya_chahte", "kehna kya chahte ho meme template", "hairan", 0, 2.2),
    ("utha_le_re_baba", "utha le re baba meme template", "udaas", 0, 2.6),
    ("paisa_hi_paisa", "paisa hi paisa hoga meme template", "hasi", 0, 2.6),
    ("ye_baburao_style", "ye baburao ka style hai meme template", "tanz", 0, 2.4),
    ("jor_jor_se", "jor jor se bolke sabko scheme bata meme template", "gussa", 0, 2.6),
    ("mogambo_khush", "mogambo khush hua meme template", "hasi", 0, 2.2),
    ("picture_baaki", "picture abhi baaki hai mere dost meme template", "end", 0, 2.6),
    ("bahut_hard", "bahut hard bahut hard meme template", "hasi", 0, 2.2),
    ("aaj_khush_honge", "aaj khush to bahut hoge tum meme template", "tanz", 0, 2.6),
    ("ye_dukh_kahe", "ye dukh kahe khatam nahi hota meme template", "udaas", 0, 2.6),
    ("bas_kar_pagle", "bas kar pagle rulayega kya meme template", "udaas", 0, 2.4),
    ("mujhe_pata_tha", "mujhe to pehle se pata tha meme template", "tanz", 0, 2.4),
    ("ruko_zara", "ruko zara sabar karo meme template", "hairan", 0, 2.4),
    ("tension_lene_ka", "tension lene ka nahi sirf dene ka meme template", "tanz", 0, 2.6),
    ("ab_tera_kya_hoga", "ab tera kya hoga kaliya meme template", "gussa", 0, 2.4),
    ("bilkul_ricks_nahi", "bilkul ricks nahi lene ka meme template", "tanz", 0, 2.4),
    ("ek_baar_commitment", "ek baar jo maine commitment kar di meme template", "end", 0, 2.6),
    ("main_kya_karu", "main kya karu job chhod du meme template", "udaas", 0, 2.6),
    ("haan_main_pagal", "haan main pagal hoon meme template", "hasi", 0, 2.4),
    ("achha_theek_hai", "acha theek hai meme template hindi", "tanz", 0, 2.0),
]
# मज़ेदार आवाज़ें (सिर्फ़ आवाज़): id, खोज, start, secs — पंच के आख़िरी शब्द पर, tag वाली line के बाद हँसी
SFX = [
    ("sfx_vine_boom", "vine boom sound effect", 0, 1.2),
    ("sfx_crowd_laugh", "crowd laughing sound effect short", 0, 2.2),
    ("sfx_record_scratch", "record scratch sound effect", 0, 1.0),
    ("sfx_bruh", "bruh sound effect", 0, 1.0),
    ("sfx_sad_violin", "sad violin meme sound effect", 0, 2.4),
    ("sfx_dun_dun", "dun dun dunnn sound effect", 0, 2.0),
]
MOOD_OF = {"hairan": "hairan", "gussa": "gussa", "tanz": "tanz", "hasi": "hasi", "udaas": "udaas", "gambhir": "tanz"}


def _ok(mid):
    p = DIR / f"{mid}.mp4"
    return p if p.exists() and p.stat().st_size > 30000 else None


def _probe_len(p):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)],
                       capture_output=True, text=True)
    try:
        return float(r.stdout.strip())
    except ValueError:
        return 0.0


def _one(item, status):
    import clips
    mid, q, mood, start, secs = item
    hits = clips.search(q, n=4)
    hits = [h for h in hits if 3 <= (h[3] or 30) <= 120] or hits
    for url, title, ch, dur in hits[:2]:
        raw = DIR / f"{mid}.src.mp4"
        cmd = clips._ytdlp() + ["-q", "--no-warnings", "--no-playlist", "-f", "b[height<=720]/bv*[height<=720]+ba/b",
                                "--download-sections", f"*{start:.1f}-{start + secs + 0.4:.1f}", "--force-keyframes-at-cuts",
                                "-o", str(raw)] + clips._cookies("YT_COOKIES") + [url]
        try:
            subprocess.run(cmd, capture_output=True, timeout=75)
        except subprocess.TimeoutExpired:
            print(f"  ⏱ {mid}: download अटका", flush=True)
        got = next((p for p in DIR.glob(f"{mid}.src*") if p.suffix in (".mp4", ".webm", ".mkv")), None)
        if not got:
            continue
        out = DIR / f"{mid}.mp4"
        vf = (f"[0:v]split[a][b];[a]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},boxblur=30:5,"
              f"eq=brightness=-0.15[bg];[b]scale={W}:-2[fg];[bg][fg]overlay=0:(H-h)/2,fps={FPS},setsar=1,format=yuv420p[v]")
        r = subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(got), "-f", "lavfi", "-i",
                            "anullsrc=r=44100:cl=stereo", "-filter_complex", vf, "-map", "[v]", "-map", "0:a?",
                            "-map", "1:a", "-t", f"{secs}", "-c:v", "libx264", "-preset", "veryfast", "-crf", "22",
                            "-c:a", "aac", "-ar", "44100", "-ac", "2", "-shortest", str(out)], capture_output=True, text=True)
        for p in DIR.glob(f"{mid}.src*"):
            p.unlink(missing_ok=True)
        if r.returncode == 0 and _ok(mid):
            status[mid] = {"title": title, "channel": ch, "url": url, "secs": round(_probe_len(out), 2)}
            print(f"  ✅ {mid}: {title[:60]} — {ch}", flush=True)
            return
        print(f"  ⚠️ {mid}: ffmpeg {r.stderr[-160:]}", flush=True)
    print(f"  ❌ {mid}: नहीं मिला ({len(hits)} नतीजे)", flush=True)


def _sfx_ok(sid):
    p = DIR / f"{sid}.m4a"
    return p if p.exists() and p.stat().st_size > 3000 else None


def _one_sfx(item, status):
    import clips
    sid, q, start, secs = item
    for url, title, ch, dur in clips.search(q, n=3)[:2]:
        raw = DIR / f"{sid}.src"
        cmd = clips._ytdlp() + ["-q", "--no-warnings", "--no-playlist", "-f", "ba/b", "--download-sections",
                                f"*{start:.1f}-{start + secs + 0.3:.1f}", "-o", str(raw) + ".%(ext)s"] + \
            clips._cookies("YT_COOKIES") + [url]
        try:
            subprocess.run(cmd, capture_output=True, timeout=60)
        except subprocess.TimeoutExpired:
            pass
        got = next(iter(DIR.glob(f"{sid}.src.*")), None)
        if not got:
            continue
        out = DIR / f"{sid}.m4a"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(got), "-t", f"{secs}", "-vn", "-af",
                        "loudnorm=I=-16:TP=-1.5,afade=t=out:st=%.2f:d=0.25" % max(0.1, secs - 0.25),
                        "-ar", "44100", "-ac", "2", "-c:a", "aac", str(out)], capture_output=True)
        for q_ in DIR.glob(f"{sid}.src.*"):
            q_.unlink(missing_ok=True)
        if _sfx_ok(sid):
            status[sid] = {"title": title, "channel": ch, "url": url}
            print(f"  🔊 {sid}: {title[:60]}", flush=True)
            return
    print(f"  ❌ {sid}: नहीं मिला", flush=True)


def build(only=None):
    """लाइब्रेरी बनाओ (6 एक साथ): हर meme का template video खोजो, शुरू का हिस्सा काटो, 1080x1920 (पीछे धुंधला)."""
    from concurrent.futures import ThreadPoolExecutor
    DIR.mkdir(exist_ok=True)
    status = json.loads((DIR / "status.json").read_text(encoding="utf-8")) if (DIR / "status.json").exists() else {}
    todo = [m for m in LIB if (only and m[0] in only) or (not only and not _ok(m[0]))]
    sfx = [x for x in SFX if (only and x[0] in only) or (not only and not _sfx_ok(x[0]))]
    with ThreadPoolExecutor(6) as ex:
        list(ex.map(lambda x: _one_sfx(x, status), sfx))
        list(ex.map(lambda m: _one(m, status), todo))
    (DIR / "status.json").write_text(json.dumps(status, ensure_ascii=False, indent=1), encoding="utf-8")
    sheet()


def sheet():
    """सारे memes की एक तस्वीर (हर एक का 1 सेकंड वाला frame + नाम) — जाँच के लिए."""
    from PIL import Image, ImageDraw
    tiles = []
    for mid, *_ in LIB:
        p = _ok(mid)
        if not p:
            continue
        jpg = DIR / f"_{mid}.jpg"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", "1.0", "-i", str(p), "-frames:v", "1",
                        "-vf", "scale=216:384", str(jpg)])
        if jpg.exists():
            im = Image.open(jpg).convert("RGB")
            ImageDraw.Draw(im).rectangle((0, 0, 216, 22), fill=(0, 0, 0))
            ImageDraw.Draw(im).text((4, 4), mid, fill=(255, 255, 0))
            tiles.append(im)
            jpg.unlink()
    if tiles:
        cols = 6
        rows = (len(tiles) + cols - 1) // cols
        S = Image.new("RGB", (216 * cols, 384 * rows))
        for i, t in enumerate(tiles):
            S.paste(t, ((i % cols) * 216, (i // cols) * 384))
        S.save(DIR / "_sheet.jpg", quality=80)


def pick(ep, lens):
    """[(बाद_में_सेकंड, meme_path, id)] — पंच वाली lines (पहली line नहीं, hook न टूटे) और आख़िरी line, ज़्यादा से ज़्यादा 2."""
    if not DIR.exists() or ep.get("no_memes"):
        return []
    lines = [s for s in ep["_segs_ln"]]
    ends, t = [], 0.0
    for L in lens:
        t += L
        ends.append(t)
    want = [i for i, ln in enumerate(lines) if i > 0 and ln.get("punch") and ln.get("say")]
    last = max((i for i, ln in enumerate(lines) if ln.get("say")), default=-1)
    if last > 0 and last not in want:
        want.append(last)
    want = sorted(set(want))[-2:]
    seed = int(hashlib.md5(str(ep.get("topic", "")).encode()).hexdigest(), 16)
    used, out = set(), []
    for k, i in enumerate(want):
        mood = "end" if i == last and k == len(want) - 1 and seed % 3 == 0 else MOOD_OF.get(lines[i].get("expr", ""), "hasi")
        cands = [m for m in LIB if m[2] == mood and _ok(m[0]) and m[0] not in used] or \
                [m for m in LIB if _ok(m[0]) and m[0] not in used]
        if not cands:
            break
        m = cands[(seed + k * 7) % len(cands)]
        used.add(m[0])
        out.append((ends[i], _ok(m[0]), m[0]))
    return out


def splice(video, picks, out):
    """video में picks के समय पर memes डालो (बाक़ी video और आवाज़ वैसी ही)."""
    if not picks:
        return None
    total = _probe_len(video)
    cuts = [0.0] + [min(t, total) for t, _, _ in picks] + [total]
    ins, parts, fc = ["-i", str(video)], [], []
    for j, (_, p, _) in enumerate(picks, 1):
        ins += ["-i", str(p)]
    norm = f"fps={FPS},scale={W}:{H},setsar=1,format=yuv420p"
    anorm = "aformat=sample_rates=44100:channel_layouts=stereo"
    for k in range(len(cuts) - 1):
        a, b = cuts[k], cuts[k + 1]
        fc.append(f"[0:v]trim={a:.3f}:{b:.3f},setpts=PTS-STARTPTS,{norm}[v{k}];"
                  f"[0:a]atrim={a:.3f}:{b:.3f},asetpts=PTS-STARTPTS,{anorm}[a{k}]")
        parts.append(f"[v{k}][a{k}]")
        if k < len(picks):
            fc.append(f"[{k + 1}:v]setpts=PTS-STARTPTS,{norm}[mv{k}];[{k + 1}:a]asetpts=PTS-STARTPTS,{anorm},volume=1.3[ma{k}]")
            parts.append(f"[mv{k}][ma{k}]")
    fc.append("".join(parts) + f"concat=n={len(parts)}:v=1:a=1[v][a]")
    r = subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *ins, "-filter_complex", ";".join(fc), "-map", "[v]", "-map", "[a]",
                        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-c:a", "aac", "-b:a", "160k",
                        "-movflags", "+faststart", str(out)], capture_output=True, text=True)
    if r.returncode or not Path(out).exists():
        print("  meme जोड़ना नहीं हुआ:", r.stderr[-200:])
        return None
    return out


def overlay_sfx(video, hits, out):
    """[(सेकंड, sfx_id)] — reel की आवाज़ के ऊपर मज़ेदार आवाज़ें."""
    hits = [(t, _sfx_ok(sid)) for t, sid in hits if _sfx_ok(sid)]
    if not hits:
        return None
    ins, fc, labels = ["-i", str(video)], [], ["[0:a]"]
    for j, (t, p) in enumerate(hits, 1):
        ins += ["-i", str(p)]
        ms = int(max(0, t) * 1000)
        fc.append(f"[{j}:a]adelay={ms}|{ms},volume=0.9[s{j}]")
        labels.append(f"[s{j}]")
    fc.append("".join(labels) + f"amix=inputs={len(labels)}:duration=first:normalize=0[a]")
    r = subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *ins, "-filter_complex", ";".join(fc), "-map", "0:v",
                        "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", str(out)], capture_output=True, text=True)
    return out if r.returncode == 0 and Path(out).exists() else None


def sfx_hits(ep, lens, meme_after):
    """कहाँ कौन-सी आवाज़: hook के बाद vine boom; tag वाली line के बाद हँसी; बाकी पंच (जहाँ meme नहीं) पर boom/bruh."""
    ends, t = [], 0.0
    for L in lens:
        t += L
        ends.append(t)
    hits = []
    for i, ln in enumerate(ep["_segs_ln"]):
        if not ln.get("say") or any(abs(ends[i] - m) < 0.05 for m in meme_after):
            continue
        if i == 0:
            hits.append((ends[i] - 0.15, "sfx_vine_boom"))
        elif re.match(r"\s*हर .{2,30} में एक", ln.get("say", "")):
            hits.append((ends[i] - 0.1, "sfx_crowd_laugh"))
        elif ln.get("punch"):
            hits.append((ends[i] - 0.15, "sfx_bruh" if ln.get("expr") == "tanz" else "sfx_vine_boom"))
    return hits


def add(ep, segs, video):
    """talk_episode से: बनी reel में memes डालो. लौटाता है [id] (Telegram रिपोर्ट के लिए)."""
    import reel_v3 as rv
    try:
        lens = [rv._read(s["wav"]).shape[0] / rv.SR for s in segs]
        ep["_segs_ln"] = [s["ln"] for s in segs]
        picks = pick(ep, lens)
        hits = sfx_hits(ep, lens, [t for t, _, _ in picks])
        ep.pop("_segs_ln", None)
        tmp0 = Path(video).with_name("with_sfx.mp4")
        if hits and overlay_sfx(video, hits, tmp0):        # पहले आवाज़ें (reel के अपने समय पर), फिर memes बीच में
            tmp0.replace(video)
            print("  🔊 आवाज़ें:", [h for _, h in hits])
        tmp = Path(video).with_name("with_memes.mp4")
        if picks and splice(video, picks, tmp):
            tmp.replace(video)
            print("  😂 memes:", [m for _, _, m in picks])
            return [m for _, _, m in picks]
    except Exception as e:                                # noqa: BLE001  meme न जुड़े तो भी reel जाए
        print("  meme नहीं जुड़ा:", repr(e)[:150])
    return []


if __name__ == "__main__":
    build(only=set(sys.argv[1:]) or None)
