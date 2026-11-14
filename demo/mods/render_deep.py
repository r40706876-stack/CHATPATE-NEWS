"""
DEEP CLASS renderer: HTML scene (window.seek(t)) -> frames -> MP4 (1080x1920, 30fps).
  python deep/render_deep.py scene.html out.mp4 [cues.json] [--peek 1.0,5.5,9]
cues.json (optional) = {"line_id": {"t": start_sec, "d": dur_sec}} -> window.CUES (asli awaaz ke samay).
--peek: sirf un samay ke PNG (dekhne ke liye), video nahi.
"""
import json
import os
import shutil
import subprocess
import sys

from playwright.sync_api import sync_playwright


def open_page(p, html, cues):
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 540, "height": 960}, device_scale_factor=2)
    if cues:
        pg.add_init_script(f"window.CUES = {json.dumps(cues)};")
    pg.goto("file://" + os.path.abspath(html))
    try:
        pg.wait_for_load_state("networkidle", timeout=15000)
    except Exception:
        pass
    pg.evaluate("document.fonts.ready.then(()=>1)")
    pg.evaluate("window.READY ? window.READY() : 1")          # 3D clips ke saare frame pehle se taiyaar
    pg.wait_for_timeout(500)
    return b, pg


SYNC = "Promise.all([...document.querySelectorAll('#cutImg,#estImg')].map(i => i.src ? i.decode().catch(() => 0) : 0))"


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    html, out = args[0], args[1]
    cues = json.load(open(args[2], encoding="utf-8")) if len(args) > 2 and os.path.exists(args[2]) else None
    peek = None
    if "--peek" in sys.argv:
        peek = [float(x) for x in sys.argv[sys.argv.index("--peek") + 1].split(",")]
    fps = int(os.environ.get("FPS", "30"))
    with sync_playwright() as p:
        b, pg = open_page(p, html, cues)
        total = pg.evaluate("window.TOTAL")
        if peek:
            os.makedirs(out, exist_ok=True)
            for t in peek:
                pg.evaluate(f"window.seek({t})")
                pg.evaluate(SYNC)
                pg.screenshot(path=os.path.join(out, f"peek_{t:05.2f}.png"))
            json.dump({"total": total, "sfx": pg.evaluate("window.SFX ? window.SFX() : []")},
                      open(os.path.join(out, "meta.json"), "w"))
            b.close()
            print("PEEK", out, total)
            return
        fdir = out + ".frames"
        shutil.rmtree(fdir, True)
        os.makedirs(fdir)
        n = int(total * fps)
        for i in range(n):
            pg.evaluate(f"window.seek({i / fps})")
            pg.evaluate(SYNC)
            pg.screenshot(path=os.path.join(fdir, f"f{i:05d}.jpg"), type="jpeg", quality=93)
        sfx = pg.evaluate("window.SFX ? window.SFX() : []")
        b.close()
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(fps), "-i", os.path.join(fdir, "f%05d.jpg"),
                    "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-pix_fmt", "yuv420p", out], check=True)
    shutil.rmtree(fdir)
    json.dump({"total": total, "sfx": sfx}, open(out + ".meta.json", "w"))
    print("DEEP_RENDER_DONE", out, round(total, 1), "sec", n, "frames")


if __name__ == "__main__":
    main()
