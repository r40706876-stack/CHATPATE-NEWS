"""c7_full.html + engine.js + scene.js -> ek HTML (deep_demo.py ke liye)."""
import os
import sys
d = os.path.dirname(os.path.abspath(__file__))
s = open(os.path.join(d, "c7_full.html"), encoding="utf-8").read()
s = s.replace("/*ENGINE*/", open(os.path.join(d, "engine.js"), encoding="utf-8").read())
s = s.replace("/*SCENE*/", open(os.path.join(d, "scene.js"), encoding="utf-8").read())
open(sys.argv[1], "w", encoding="utf-8").write(s)
print("built", sys.argv[1])
