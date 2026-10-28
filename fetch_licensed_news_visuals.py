"""Download openly licensed illustrative news visuals; never label them as actual event footage."""
import json, pathlib, urllib.parse, urllib.request, urllib.error, re, html, io, time
from PIL import Image
ROOT=pathlib.Path("assets/licensed"); ROOT.mkdir(parents=True,exist_ok=True)
FILES={"arrival":"File:TV_set_(46_inch)_in_self-customized_box_for_sending_via_parcel_service_N.1.jpg","freight":"File:Refrigerator_Delivery_(b&w)_(11327379273).jpg"}
def _read_with_retry(url, timeout, alternate=None):
    """Retry transient Wikimedia/CDN outages; never bypass license metadata."""
    failures = []
    for candidate in (url, alternate):
        if not candidate:
            continue
        for attempt in range(3):
            try:
                req = urllib.request.Request(
                    candidate,
                    headers={"User-Agent": "BakraNewsVisuals/1.0 (https://github.com/r40706876-stack/CHATPATE-NEWS)"})
                with urllib.request.urlopen(req, timeout=timeout) as response:
                    return response.read(12_000_001)
            except urllib.error.HTTPError as exc:
                failures.append(f"HTTP {exc.code} at {urllib.parse.urlparse(candidate).netloc}")
                if exc.code not in (429, 500, 502, 503, 504):
                    break  # e.g. a 404 is not a temporary outage
            except (urllib.error.URLError, TimeoutError, OSError) as exc:
                failures.append(f"{type(exc).__name__} at {urllib.parse.urlparse(candidate).netloc}")
            if attempt < 2:
                time.sleep((2, 5)[attempt])
    raise RuntimeError("Wikimedia fetch failed after retry/fallback: " + "; ".join(failures))


out={}
for scene,title in FILES.items():
    url="https://commons.wikimedia.org/w/api.php?"+urllib.parse.urlencode({"action":"query","format":"json","prop":"imageinfo","iiprop":"url|extmetadata","titles":title})
    try:
        alternate=url.replace("https://commons.wikimedia.org/w/api.php", "https://en.wikipedia.org/w/api.php")
        data=json.loads(_read_with_retry(url, 25, alternate))
        info=next(iter(data["query"]["pages"].values()))["imageinfo"][0]
        meta=info.get("extmetadata",{})
        license_name=html.unescape(re.sub("<[^>]+>","",meta.get("LicenseShortName",{}).get("value","")))
        if not any(x in license_name.lower() for x in ("cc by","cc0","public domain")): raise ValueError("license not approved: "+license_name)
        author=html.unescape(re.sub("<[^>]+>","",meta.get("Artist",{}).get("value","unknown")))[:80]
        image_url=info["url"]
        ext=pathlib.Path(urllib.parse.urlparse(image_url).path).suffix.lower()
        if ext not in (".jpg",".jpeg",".png",".webp"): raise ValueError("not an image")
        name=scene+ext
        # Same Commons file through an alternative URL if the upload CDN is temporarily unavailable.
        alternate_image="https://commons.wikimedia.org/wiki/Special:Redirect/file/"+urllib.parse.quote(title.removeprefix("File:"), safe="")
        payload=_read_with_retry(image_url, 45, alternate_image)
        if len(payload)>12_000_000: raise ValueError("image too large")
        with Image.open(io.BytesIO(payload)) as picture:
            picture.verify()
        (ROOT/name).write_bytes(payload)
        out[scene]={"path":name,"author":author or "Wikimedia Commons contributor",
                    "source":"Wikimedia Commons (illustrative)",
                    "source_url":info.get("descriptionurl",""),
                    "license":license_name,
                    "license_url":meta.get("LicenseUrl",{}).get("value",""),
                    "modified":"cropped/animated in Bakra News; not actual COD event footage"}
        print(scene,"downloaded",len(payload),license_name)
    except Exception as e: print(scene,"SKIPPED",str(e))
(ROOT/"manifest.json").write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding="utf-8")
(ROOT/"CREDITS.txt").write_text("\n".join(
    f"{scene}: {entry['author']} | {entry['license']} | {entry['source_url']} | "
    f"{entry['license_url']} | {entry['modified']}"
    for scene,entry in out.items())+"\n",encoding="utf-8")
if not out: raise SystemExit("No verified openly licensed imagery downloaded")
