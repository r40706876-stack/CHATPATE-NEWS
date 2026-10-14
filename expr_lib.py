"""
भाव वाली library (free, अपने-आप): Pixabay पर असली इंसान के भाव वाला video (AI देखकर चुनता है)
→ LivePortrait उस भाव को हमारे किरदार की फ़ोटो पर लगाता है → assets/expr/<who>_<expr>.mp4
    python expr_lib.py drivers ramesh hasi,udaas     → drv/<who>_<expr>.mp4 (system python, Gemini + Pixabay)
    python expr_lib.py sheet                          → preview_expr.jpg
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent
FEMALE = {"dadi", "pinky"}
AGE = {"chacha": "old ", "dadi": "old ", "pinky": "young ", "bablu": "young ", "ramesh": ""}
EXPR = {   # भाव: (Pixabay खोज, AI को क्या देखना है)
    "hasi": ("{g} laughing close up face", "ज़ोर से, असली हँसी"),
    "udaas": ("sad {g} face close up", "दुखी/उदास चेहरा"),
    "hairan": ("surprised {g} face shocked", "हैरान, चौंका हुआ चेहरा"),
    "gussa": ("frustrated annoyed {g} face", "झुँझलाया/परेशान चेहरा"),
    "tanz": ("{g} smirk smile close up", "तिरछी/तंज़ वाली मुस्कान"),
    "haan": ("{g} nodding head yes", "हाँ में सिर हिलाना"),
}


def drivers(who, exprs):
    import shutil
    import visuals
    g = AGE.get(who, "") + ("woman" if who in FEMALE else "man")
    items = [(f"एक इंसान का चेहरा, सामने से, साफ़ और पास से (close-up), अकेला, भाव: {EXPR[e][1]}. "
              "कोई text/logo नहीं, चेहरा ढका नहीं.", EXPR[e][0].format(g=g)) for e in exprs]
    Path("drv").mkdir(exist_ok=True)
    for e, path in zip(exprs, visuals.pick_checked(items)):
        if path and str(path).endswith(".mp4"):
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(path), "-t", "4", "-an",
                            "-vf", "fps=25,scale=-2:720", f"drv/{who}_{e}.mp4"], check=True)
            print("driver:", who, e)
        else:
            print("driver नहीं मिला:", who, e)


# LivePortrait के साथ आने वाले भाव (Pixabay/Gemini की ज़रूरत नहीं): भाव → driver
BUILTIN = {"hasi": "d12.mp4", "tanz": "d0.mp4", "gussa": "d18.mp4", "sharm": "d14.mp4",
           "hairan": "d19.jpg", "udaas": "d8.jpg", "cheekh": "d9.jpg"}


def peak(video):
    """पहले frame से सबसे ज़्यादा अलग frame = भाव का चरम."""
    import numpy as np
    from PIL import Image
    tmp = video.with_suffix("")
    tmp.mkdir(exist_ok=True)
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(video), "-vf", "fps=5", str(tmp / "%03d.png")])
    fr = sorted(tmp.glob("*.png"))
    if not fr:
        return
    a0 = np.asarray(Image.open(fr[0]).convert("L"), np.float32)
    best = max(fr, key=lambda f: np.abs(np.asarray(Image.open(f).convert("L"), np.float32) - a0).mean())
    Image.open(best).convert("RGB").save(video.with_suffix(".jpg"), quality=92)
    for f in fr:
        f.unlink()
    tmp.rmdir()


def sheet():
    from PIL import Image
    tiles = []
    for p in sorted((ROOT / "assets/expr").glob("*.jpg")):
        im = Image.open(p)
        im.thumbnail((400, 300))
        tiles.append(im)
    if not tiles:
        return
    w = max(t.width for t in tiles)
    im = Image.new("RGB", (w * 7, 300 * ((len(tiles) + 6) // 7)), "black")
    for i, t in enumerate(tiles):
        im.paste(t, ((i % 7) * w, (i // 7) * 300))
    im.save(ROOT / "preview_expr.jpg")
    for p in ROOT.glob("_t_*.jpg"):
        p.unlink()


if __name__ == "__main__":
    if sys.argv[1] == "drivers":
        drivers(sys.argv[2], sys.argv[3].split(","))
    elif sys.argv[1] == "still":                  # clip में सबसे तेज़ भाव वाला frame → .jpg
        peak(Path(sys.argv[2]))
    elif sys.argv[1] == "source":
        import talk_episode
        talk_episode.source_img(sys.argv[2], ROOT / f"drv/{sys.argv[2]}_src.png")
    else:
        sheet()
