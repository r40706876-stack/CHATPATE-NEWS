import pathlib,sys,wave,numpy as np
sys.path.insert(0,str(pathlib.Path.cwd()))
import main as M
M.TTS_WAITS=(20,40)
s="ये ज़रूरी नियम है, इसलिए वीडियो पहले ही सेव कर लो।"
a=M.gemini_tts_audio([s],voice="Charon")
p=pathlib.Path("save_prompt");p.mkdir(exist_ok=True)
with wave.open(str(p/"save_prompt.wav"),"wb") as w:
 w.setnchannels(1);w.setsampwidth(2);w.setframerate(M.SR);w.writeframes((np.clip(a,-1,1)*32767).astype(np.int16).tobytes())
(p/"script.txt").write_text(s)
print("SAVE_PROMPT_SECONDS",len(a)/M.SR)
