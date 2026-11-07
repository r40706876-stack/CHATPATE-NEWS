"""बना हुआ reel Telegram पर भेजो (फ़ोन पर मिलेगा → trending audio लगाकर post करो).
ज़रूरी: TELEGRAM_BOT_TOKEN (@BotFather से), TELEGRAM_CHAT_ID (अपना chat id)."""
import json
import os
import uuid
import urllib.request
from pathlib import Path


def send_video(path, caption=""):
    tok, chat = os.getenv("TELEGRAM_BOT_TOKEN"), os.getenv("TELEGRAM_CHAT_ID")
    if not (tok and chat):
        print("  Telegram secrets नहीं — भेजना छोड़ा")
        return False
    b = uuid.uuid4().hex
    parts = []
    for k, v in (("chat_id", chat), ("caption", caption[:1000]), ("supports_streaming", "true")):
        parts.append(f'--{b}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode())
    parts.append(f'--{b}\r\nContent-Disposition: form-data; name="video"; filename="{Path(path).name}"\r\n'
                 f"Content-Type: video/mp4\r\n\r\n".encode() + Path(path).read_bytes() + b"\r\n")
    parts.append(f"--{b}--\r\n".encode())
    req = urllib.request.Request(f"https://api.telegram.org/bot{tok}/sendVideo", b"".join(parts),
                                 {"Content-Type": f"multipart/form-data; boundary={b}"})
    with urllib.request.urlopen(req, timeout=300) as r:
        ok = json.load(r).get("ok")
    print("  Telegram पर भेजा:", ok)
    return ok


def _api(method, params=None):
    tok = os.getenv("TELEGRAM_BOT_TOKEN")
    data = json.dumps(params or {}).encode()
    req = urllib.request.Request(f"https://api.telegram.org/bot{tok}/{method}", data,
                                 {"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def download(file_id, out):
    """Telegram पर भेजी file (bot के लिए 20 MB तक) → out."""
    tok = os.getenv("TELEGRAM_BOT_TOKEN")
    path = _api("getFile", {"file_id": file_id})["result"]["file_path"]
    with urllib.request.urlopen(f"https://api.telegram.org/file/bot{tok}/{path}", timeout=300) as r:
        Path(out).write_bytes(r.read())
    return Path(out)


def send_text(text):
    if not (os.getenv("TELEGRAM_BOT_TOKEN") and os.getenv("TELEGRAM_CHAT_ID")):
        print(text)
        return False
    for k in range(0, len(text), 3900):                  # Telegram की सीमा 4096
        _api("sendMessage", {"chat_id": os.getenv("TELEGRAM_CHAT_ID"), "text": text[k:k + 3900]})
    return True


def read_replies(offset_file):
    """नए जवाब [(unix समय, text)] — सिर्फ़ अपने chat से. offset फ़ाइल में याद रहता है."""
    if not os.getenv("TELEGRAM_BOT_TOKEN"):
        return []
    off = int(Path(offset_file).read_text().strip() or 0) if Path(offset_file).exists() else 0
    res = _api("getUpdates", {"offset": off, "timeout": 0}).get("result", [])
    out = []
    for u in res:
        off = max(off, u["update_id"] + 1)
        m = u.get("message") or {}
        if str(m.get("chat", {}).get("id")) != str(os.getenv("TELEGRAM_CHAT_ID")):
            continue
        if m.get("text"):
            out.append((m.get("date", 0), m["text"].strip()))
            continue
        # 7 Nov: मालिक ख़ुद video file भेजे (या document में video) → "__video__:<file_id>|<size>|<caption>"
        v = m.get("video") or m.get("animation") or (m.get("document") if str((m.get("document") or {}).get("mime_type", "")).startswith("video") else None)
        if v:
            out.append((m.get("date", 0), f"__video__:{v['file_id']}|{v.get('file_size', 0)}|{(m.get('caption') or '').strip()}"))
        elif m.get("caption"):
            out.append((m.get("date", 0), m["caption"].strip()))
    Path(offset_file).write_text(str(off))
    return out
