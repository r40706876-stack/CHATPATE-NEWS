import json, traceback, viral_check as vc, gemini
eps = json.load(open("episodes/samples_dark.json", encoding="utf-8"))
out = []
try:
    raw = gemini.ask(vc.prompt_connect(eps), json_mode=True, temperature=0.2)
    out.append("RAW: " + raw[:3000])
except Exception:
    out.append("ERR: " + traceback.format_exc()[-1500:])
open("viral_test.txt", "w", encoding="utf-8").write("\n".join(out)); print("\n".join(out))
