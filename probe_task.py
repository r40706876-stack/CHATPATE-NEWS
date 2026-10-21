import subprocess, sys
from pathlib import Path
subprocess.run([sys.executable, "-m", "pip", "install", "-q", "--break-system-packages", "-U", "yt-dlp"])
import clips
got = clips.for_topic("पैरामोटर से उड़कर ऑफिस जाने वाला शख्स", ["paramotor flies to work"], want=1)
print("RESULT:", got)
for p, c in got:
    print("size", Path(p).stat().st_size)
