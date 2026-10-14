import json, viral_check as vc
eps = json.load(open("episodes/samples_dark.json", encoding="utf-8"))
vc.connect(eps)
out = [f"CONNECT {e.get('connect',{}).get('score','?')}/10 {e.get('connect',{}).get('parts','')} {e['topic']}\n  ✅ {e.get('connect',{}).get('why','')}\n  ⚠️ {e.get('connect',{}).get('weak','')}\n  🔧 {e.get('connect',{}).get('fix','')}" for e in eps]
open("viral_test.txt", "w", encoding="utf-8").write("\n".join(out)); print("\n".join(out))
