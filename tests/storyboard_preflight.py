"""Fast storyboard/scene QA before costly TTS and full MP4 encoding."""
import json
import sys
from pathlib import Path

# GitHub executes this file as a script, so the repository root is not on sys.path.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
from PIL import Image, ImageDraw
import reel_studio as studio

EP = Path("episodes/waiting_ticket_comedy.json")
EXPECTED = ["sweets", "showroom", "laddoo_hdmi", "bill", "delivery"]
VALID = set(EXPECTED) | {"shop"}


def main():
    ep = json.loads(EP.read_text(encoding="utf-8"))
    lines = ep["lines"]
    if len(lines) != len(EXPECTED):
        raise SystemExit("Story preflight: expected five illustrated dialogue beats")
    scenes = [line.get("scene") for line in lines]
    if scenes != EXPECTED:
        raise SystemExit(f"Story preflight: dialogue/scene mismatch: {scenes} != {EXPECTED}")
    if not ep.get("no_clips") or ep.get("visual_policy") != "character_only":
        raise SystemExit("Story preflight: unrelated external clips/images are not disabled")
    if any(x not in VALID for x in scenes):
        raise SystemExit("Story preflight: unknown scene name")
    # Render two representative frames per beat; verify actual visual changes.
    size = (1056, 810)
    contact = Image.new("RGB", (size[0] * 2, size[1] * len(scenes)), (255, 255, 255))
    differences = []
    for i, scene in enumerate(scenes):
        gen = studio._story_scene({"scene": scene}, size)
        before = next(gen)
        after = None
        for _ in range(int(studio.FPS * 1.7)):
            after = next(gen)
        a = np.asarray(before.resize((176, 135)), dtype=np.float32)
        b = np.asarray(after.resize((176, 135)), dtype=np.float32)
        difference = float(np.abs(a - b).mean())
        differences.append(round(difference, 1))
        if difference < 9:
            raise SystemExit(f"Story preflight: scene {i+1} ({scene}) is effectively static ({difference:.1f})")
        contact.paste(before, (0, i * size[1]))
        contact.paste(after, (size[0], i * size[1]))
        gen.close()
    contact.resize((792, 1520)).save("preflight_storyboard.jpg", quality=84)
    print("PASS: dialogue matches all five cartoon scenes")
    print("PASS: every scene has an actual visual change", differences)
    print("PASS: storyboard generated before audio/full video render")


if __name__ == "__main__":
    main()
