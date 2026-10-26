"""Optional independent Gemini comedy critique; never claims Instagram retention.

Run before expensive audio/render. If Gemini is quota-limited, report unreviewed
rather than inventing a passing score. A genuinely low score blocks the render.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent
OUT = ROOT / "comedy_review.json"
MIN_EDITORIAL_SCORE = 7.5


def review(path):
    ep = json.loads(Path(path).read_text(encoding="utf-8"))
    lines = [{"who": ln.get("who"), "say": ln.get("say")} for ln in ep.get("lines", [])]
    prompt = (
        "तुम स्वतंत्र, बहुत सख़्त हिंदी कॉमेडी संपादक हो। 'बकरा न्यूज़' की इस स्क्रिप्ट को "
        "वास्तविक देसी हास्य, पहले 2 सेकंड का hook, किरदारों की टक्कर, अप्रत्याशित punch "
        "और किसी दोस्त को भेजने की वजह पर परखो। तथ्य और काल्पनिक मज़ाक में अंतर रखो। "
        "हर पहलू को 0-10 दो, अतिशयोक्ति से बचो; 7 औसत है, 9 असाधारण। "
        "Instagram skip/retention का कोई अनुमान मत लगाओ। केवल JSON लौटाओ: "
        '{"hook":number,"character_clash":number,"surprise":number,'
        '"shareability":number,"weakest_line":number,"specific_fix":"Hindi suggestion"}'
        "\nNEWS TOPIC: " + str(ep.get("topic", "")) +
        "\nLINES: " + json.dumps(lines, ensure_ascii=False)
    )
    report = {"status": "unavailable", "episode": str(path), "editorial_only": True}
    try:
        import gemini
        data = gemini.json_from(gemini.ask(prompt, json_mode=True, temperature=0.2, patient=False))
        dims = ("hook", "character_clash", "surprise", "shareability")
        ratings = {k: float(data[k]) for k in dims}
        if any(not (0 <= value <= 10) for value in ratings.values()):
            raise ValueError("invalid rubric scores")
        # Shareability and surprise matter more than merely announcing the news.
        score = round(0.25 * ratings["hook"] + 0.25 * ratings["character_clash"] +
                      0.25 * ratings["surprise"] + 0.25 * ratings["shareability"], 2)
        report.update(status="reviewed", rubric=ratings, score=score,
                      weakest_line=data.get("weakest_line"),
                      specific_fix=str(data.get("specific_fix") or "")[:700])
    except Exception as exc:
        report["error"] = (type(exc).__name__ + ": " + str(exc))[:250]
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Independent comedy editorial review:", json.dumps(report, ensure_ascii=False))
    if report["status"] == "reviewed" and report["score"] < MIN_EDITORIAL_SCORE:
        raise SystemExit("Comedy editorial gate failed; improve the script before delivery")


if __name__ == "__main__":
    review(sys.argv[1] if len(sys.argv) > 1 else ROOT / "episodes/waiting_ticket_comedy.json")
