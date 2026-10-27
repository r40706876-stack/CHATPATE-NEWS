"""Fast, honest story-stage preflight before expensive TTS/MP4 encoding.

Tests actual full-frame story backgrounds/props, not the unused split-screen
preview. Passing this check does NOT prove comedy quality or viewer retention.
"""
import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))

import numpy as np
from PIL import Image
import story_stage

EXPECTED=("sweets","arrival","otp","bill","house")


def main():
    ep=json.loads(Path("episodes/waiting_ticket_comedy.json").read_text(encoding="utf-8"))
    lines=ep["lines"]
    scenes=tuple(x.get("scene") for x in lines)
    if scenes != EXPECTED:
        raise SystemExit(f"Story-stage preflight: incorrect narrative scenes {scenes}")
    if not ep.get("no_clips") or ep.get("visual_policy")!="character_only":
        raise SystemExit("Story-stage preflight: external clips/images must remain disabled")
    if any(x.get("shot")!="story" for x in lines):
        raise SystemExit("Story-stage preflight: each line must use full-frame story shot")
    base=story_stage._house_base()
    tiles=[]
    report=[]
    for i,scene in enumerate(scenes):
        samples=[]
        for t in (0,35):
            im=base.copy()
            story_stage._scene_action(im,scene,t,60)
            samples.append(im)
        a=np.asarray(samples[0].resize((180,320)),dtype=np.float32)
        b=np.asarray(samples[1].resize((180,320)),dtype=np.float32)
        diff=float(np.abs(a-b).mean())
        if diff<0.015:
            raise SystemExit(f"Story-stage preflight: no meaningful motion for {scene} ({diff:.3f})")
        report.append({"scene":scene,"sample_frame_difference":round(diff,2),"speaker":lines[i]["who"]})
        tiles.extend(im.resize((270,480)) for im in samples)
    sheet=Image.new("RGB",(540,2400),"white")
    for i,im in enumerate(tiles):
        sheet.paste(im,((i%2)*270,(i//2)*480))
    sheet.save("preflight_storyboard.jpg",quality=85)
    Path("storyboard_report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print("PASS: five full-frame story beats are distinct and animate",report)
    print("EDITORIAL HOLD: this is structural/visual motion QA, not human viewing QA")


if __name__=="__main__":
    main()
