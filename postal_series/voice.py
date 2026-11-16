import pathlib,sys,wave,json,numpy as np
sys.path.insert(0,str(pathlib.Path.cwd()))
import main as M
M.TTS_WAITS=(20,40)
scripts={"intro_01":"हमने शुरू की है नई सीरीज़—डाक विभाग के डाउट्स। आज पहला डाउट: ट्रांसफर, एक साल या दो साल?","intro_02":"डाक विभाग के डाउट्स, भाग दो। आज: जीडीएस ट्रांसफर की पाँच जरूरी तारीखें।","outro_01":"ट्रांसफर, सेवा नियम और परीक्षा—रोज़ एक डाउट, शाम साढ़े छह बजे। कल: ट्रांसफर की पाँच जरूरी तारीखें। पोस्टल वाला को फॉलो करें।","outro_02":"इस सीरीज़ में ट्रांसफर, सेवा नियम और परीक्षा की जानकारी अब नियमित आएगी। रोज़ शाम साढ़े छह बजे, पोस्टल वाला को फॉलो करें।"}
p=pathlib.Path("demo_out/postal_series");p.mkdir(parents=True,exist_ok=True)
report={}
for name,text in scripts.items():
 a=M.gemini_tts_audio([text],voice="Charon")
 with wave.open(str(p/(name+".wav")),"wb") as w:
  w.setnchannels(1);w.setsampwidth(2);w.setframerate(M.SR);w.writeframes((np.clip(a,-1,1)*32767).astype(np.int16).tobytes())
 report[name]={"script":text,"duration_seconds":len(a)/M.SR}
 print(name,len(a)/M.SR,flush=True)
(p/"narration.json").write_text(json.dumps(report,ensure_ascii=False,indent=2))
