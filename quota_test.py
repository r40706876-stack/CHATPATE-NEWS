import traceback, gemini
try:
    out = "OK: " + gemini.ask("सिर्फ़ 'हाँ' लिखो", temperature=0)[:50]
except Exception:
    out = "ERR: " + traceback.format_exc()[-800:]
open("viral_test.txt", "w").write(out); print(out)
