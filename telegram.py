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
