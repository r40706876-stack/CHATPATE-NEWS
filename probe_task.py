import subprocess, shutil
import clips
print("deno:", shutil.which("deno"))
got = clips.for_topic("पैरामोटर से उड़कर ऑफिस जाने वाला शख्स", ["paramotor flies to work"], want=1)
print("RESULT:", got)
