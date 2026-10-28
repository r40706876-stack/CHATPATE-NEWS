# Bakra News experimental scene engines
These are isolated optional render prototypes, NOT yet wired to the daily publishing pipeline.
- Godot 4: `godot --headless --path production/godot --write-movie ../../godot_scene.avi --fixed-fps 30 --quit-after 90` (requires project file)
- Blender: `blender -b -t 2 --python production/blender_shot.py`
- Remotion: `cd production/remotion && npm install && npm run render`
Start with a separate manual CI smoke test. Review frames and timings before allowing any of these to replace existing visuals.
