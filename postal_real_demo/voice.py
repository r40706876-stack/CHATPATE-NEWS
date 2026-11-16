import pathlib,sys,wave,numpy as np
sys.path.insert(0,str(pathlib.Path.cwd()))
import main as M
M.TTS_WAITS=(20,40)
text="ये हमारी वेबसाइट का असली सवाल है। ए चुना, गलत हुआ। सही जवाब सी क्यों है, बाकी विकल्प क्यों गलत—सब समझिए। फ्री मॉक कॉम्पिटिशन के लिए पोस्टल वाला से जुड़िए।"
a=M.gemini_tts_audio([text],voice="Charon")
p=pathlib.Path("demo_out/real_demo");p.mkdir(parents=True,exist_ok=True)
with wave.open(str(p/"narration.wav"),"wb") as w:
 w.setnchannels(1);w.setsampwidth(2);w.setframerate(M.SR);w.writeframes((np.clip(a,-1,1)*32767).astype(np.int16).tobytes())
(p/"script.txt").write_text(text)
print("VOICE_SECONDS",len(a)/M.SR)
