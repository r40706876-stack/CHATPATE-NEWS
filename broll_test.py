import io, sys, traceback, contextlib, visuals
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    try:
        items = [("विभाग के अनुसार गाँव में चौबीस घंटे बिजली दी जा रही है। हफ़्ते भर में मिलाकर।", "power cut candle night"),
                 ("मैंने तो सोलर लगवा लिया। अब सूरज से उम्मीद है।", "solar panel village roof"),
                 ("परीक्षा समय पर हुई। पेपर उससे भी पहले।", "students exam hall")]
        for t, q in items:
            cs = visuals.candidates(q)
            print("CANDS", q, [(c["tags"], c["match"]) for c in cs])
        print("PICK", visuals.pick_checked(items))
    except Exception:
        print(traceback.format_exc())
open("viral_test.txt", "w").write(buf.getvalue()); print(buf.getvalue())
