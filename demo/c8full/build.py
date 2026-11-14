"""Clause 8 page: head + body + tail + lines + engine + scene -> ek HTML."""
import os
import sys
d = os.path.dirname(os.path.abspath(__file__))
r = lambda f: open(os.path.join(d, f), encoding="utf-8").read()
head = r("head.html").replace("Clause 7 • रविवार और छुट्टी", "Clause 8 • डाकघर की छुट्टियाँ")
s = head + r("body.html") + r("tail.html") + "<script>" + r("engine.js") + "</script>\n" + r("lines.html") + "<script>" + r("scene.js") + "</script>\n</body></html>\n"
open(sys.argv[1], "w", encoding="utf-8").write(s)
print("built", sys.argv[1])
