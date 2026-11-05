"""Idempotent scheduled production. No secrets are written to repository state."""
import datetime as dt
import json
import os
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
IST = dt.timezone(dt.timedelta(hours=5, minutes=30))
HOURS = (7, 10, 13, 16, 19)


def slot_for(now=None):
    now = (now or dt.datetime.now(dt.timezone.utc)).astimezone(IST)
    if not 7 <= now.hour < 20:
        return None
    hour = max(h for h in HOURS if h <= now.hour)
    return f"{now:%Y-%m-%d}_{hour:02d}"


def state_path(slot, root=ROOT):
    return root / "production_slots" / f"{slot}.json"


def load(slot, root=ROOT):
    p = state_path(slot, root)
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def save(slot, data, root=ROOT):
    p = state_path(slot, root)
    p.parent.mkdir(exist_ok=True)
    data = dict(data, slot=slot, updated_at=int(time.time()))
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(p)


def prepare(now=None, root=ROOT):
    slot = slot_for(now)
    if slot is None:
        print("Outside production window 07:00–20:00 IST")
        return None
    state = load(slot, root)
    job = root / "studio_job.txt"
    job.unlink(missing_ok=True)
    if state.get("status") == "delivered":
        print("Already delivered:", slot)
        return None
    if state.get("status") == "dispatched" and time.time() - state.get("updated_at", 0) < 2 * 3600:
        print("Already rendering:", slot)
        return None
    script = state.get("script")
    if not script or not (root / script).is_file():
        import run_daily
        os.environ["NEWS_CACHE_KEY"] = slot
        run_daily.do_direct()
        if not job.is_file():
            raise RuntimeError("Fresh news script unavailable; no old demo fallback")
        script = job.read_text(encoding="utf-8").strip()
        if not (root / script).is_file():
            raise RuntimeError("Generated episode file missing")
    # Existing prepared script is reused after a failure; never call the writer again.
    ep_path = root / script
    ep = json.loads(ep_path.read_text(encoding="utf-8"))
    if ep.get("editorial_mode", "news_first") == "news_first":
        from news_first import require_national
        require_national(ep)  # Cached local/legacy scripts cannot bypass the current audience policy.
    ep["_production_slot"] = slot
    ep_path.write_text(json.dumps(ep, ensure_ascii=False, indent=2), encoding="utf-8")
    save(slot, dict(state, status="prepared", script=script), root)
    job.write_text(script, encoding="utf-8")
    print("Prepared slot:", slot, script)
    return slot


def dispatched(slot, root=ROOT):
    save(slot, dict(load(slot, root), status="dispatched"), root)


def delivered(ep, seconds, root=ROOT):
    slot = ep.get("_production_slot")
    if not slot:
        return
    save(slot, dict(load(slot, root), status="delivered",
                   telegram_delivered_at=int(time.time()), seconds=round(seconds, 2),
                   topic=ep.get("topic") or ep.get("title", "")), root)


def failure_message(run_url):
    path = ROOT / "production_error.json"
    err = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    if err.get("script_cached"):
        progress = "तैयार स्क्रिप्ट सुरक्षित है।"
    elif err.get("checkpoint_cached"):
        progress = "तैयारी का अधूरा checkpoint सुरक्षित है; पूरी स्क्रिप्ट अभी नहीं बनी।"
    else:
        progress = "इस प्रयास में पूरी स्क्रिप्ट नहीं बन पाई।"
    cause = "Gemini अनुरोध सीमा" if err.get("error_type") == "QuotaOver" else (err.get("reason") or "तैयारी/dispatch में त्रुटि")
    return f"⚠️ Bakra News: वीडियो नहीं बना। कारण: {cause}। {progress} Run: {run_url}"


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "dispatched":
        dispatched(sys.argv[2])
    else:
        try:
            prepare()
        except Exception as exc:
            slot = slot_for()
            state = load(slot) if slot else {}
            script = state.get("script")
            cached = bool(script and (ROOT / script).is_file())
            error = {"slot": slot, "error_type": type(exc).__name__, "reason": str(exc)[:600],
                     "script_cached": cached,
                     "checkpoint_cached": bool(slot and (ROOT / "news_cache" / f"{slot}.json").is_file())}
            (ROOT / "production_error.json").write_text(json.dumps(error, ensure_ascii=False), encoding="utf-8")
            if slot:
                save(slot, dict(state, status="preparation_failed", last_error=error))
            raise
