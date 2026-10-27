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

REQUIRED={"sweets","arrival","freight","bill","house"}


def main():
    ep=json.loads(Path("episodes/waiting_ticket_comedy.json").read_text(encoding="utf-8"))
    lines=ep["lines"]
    scenes=tuple(x.get("scene") for x in lines)
    if not 5 <= len(scenes) <= 9 or not REQUIRED.issubset(set(scenes)) or scenes[0] != "sweets" or scenes[-1] != "house":
        raise SystemExit(f"Story-stage preflight: missing or incoherent narrative progression {scenes}")
    if any(story_stage.scene_for(line) != scene for line, scene in zip(lines, scenes)):
        raise SystemExit("Story-stage preflight: unknown scene silently replaced by fallback")
    if not ep.get("no_clips") or ep.get("visual_policy")!="character_only":
        raise SystemExit("Story-stage preflight: external clips/images must remain disabled")
    if any(x.get("shot")!="story" for x in lines):
        raise SystemExit("Story-stage preflight: each line must use full-frame story shot")
    # The old preflight used one base for every scene and could report PASS
    # while the actual episode repeated the same village background throughout.
    backgrounds={scene:story_stage._house_base(scene) for scene in REQUIRED}
    signatures={scene:np.asarray(img.resize((36,64)),dtype=np.float32)
                for scene,img in backgrounds.items()}
    distinct=[]
    for scene,sig in signatures.items():
        if all(float(np.abs(sig-other).mean()) >= 5.0 for other in distinct):
            distinct.append(sig)
    if len(distinct)<4:
        raise SystemExit(f"Story-stage preflight: only {len(distinct)} visually distinct backgrounds; need at least 4")
    tiles=[]
    report=[]
    for i,scene in enumerate(scenes):
        samples=[]
        for t in (0,35):
            im=backgrounds[scene].copy()
            story_stage._scene_action(im,scene,t,60,line=lines[i])
            samples.append(im)
        a=np.asarray(samples[0].resize((180,320)),dtype=np.float32)
        b=np.asarray(samples[1].resize((180,320)),dtype=np.float32)
        diff=float(np.abs(a-b).mean())
        if diff<0.015:
            raise SystemExit(f"Story-stage preflight: no meaningful motion for {scene} ({diff:.3f})")
        report.append({"scene":scene,"sample_frame_difference":round(diff,2),"speaker":lines[i]["who"]})
        tiles.extend(im.resize((270,480)) for im in samples)
    sheet=Image.new("RGB",(540,480*len(lines)),"white")
    for i,im in enumerate(tiles):
        sheet.paste(im,((i%2)*270,(i//2)*480))
    sheet.save("preflight_storyboard.jpg",quality=85)
    Path("storyboard_report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print(f"PASS: {len(lines)} full-frame story beats have per-line animated props",report)
    print("EDITORIAL HOLD: this is structural/visual motion QA, not human viewing QA")


if __name__=="__main__":
    main()
