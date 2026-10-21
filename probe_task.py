import clips
from pathlib import Path
got = clips.for_topic("पैरामोटर से उड़कर ऑफिस जाने वाला शख्स", ["paramotor flies to work"], want=1)
print("RESULT:", [(str(p), Path(p).stat().st_size, c) for p, c in got])
