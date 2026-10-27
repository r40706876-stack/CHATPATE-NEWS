"""Download openly licensed illustrative news visuals; never label them as actual event footage."""
import json, pathlib, urllib.parse, urllib.request, re, html
ROOT=pathlib.Path("assets/licensed"); ROOT.mkdir(parents=True,exist_ok=True)
FILES={"arrival":"File:TV_set_(46_inch)_in_self-customized_box_for_sending_via_parcel_service_N.1.jpg","freight":"File:Refrigerator_Delivery_(b%26w)_(11327379273).jpg"}
out={}
for scene,title in FILES.items():
    url="https://commons.wikimedia.org/w/api.php?"+urllib.parse.urlencode({"action":"query","format":"json","prop":"imageinfo","iiprop":"url|extmetadata","titles":title})
    try:
        req=urllib.request.Request(url,headers={"User-Agent":"BakraNewsVisuals/1.0 (educational attribution)"})
        with urllib.request.urlopen(req,timeout=25) as r: data=json.load(r)
        info=next(iter(data["query"]["pages"].values()))["imageinfo"][0]
        meta=info.get("extmetadata",{})
        license_name=html.unescape(re.sub("<[^>]+>","",meta.get("LicenseShortName",{}).get("value","")))
        if not any(x in license_name.lower() for x in ("cc by","cc0","public domain")): raise ValueError("license not approved: "+license_name)
        author=html.unescape(re.sub("<[^>]+>","",meta.get("Artist",{}).get("value","unknown")))[:80]
        image_url=info["url"]
        ext=pathlib.Path(urllib.parse.urlparse(image_url).path).suffix.lower()
        if ext not in (".jpg",".jpeg",".png",".webp"): raise ValueError("not an image")
        name=scene+ext
        req=urllib.request.Request(image_url,headers={"User-Agent":"BakraNewsVisuals/1.0"})
        with urllib.request.urlopen(req,timeout=45) as r: payload=r.read(12_000_001)
        if len(payload)>12_000_000: raise ValueError("image too large")
        (ROOT/name).write_bytes(payload)
        out[scene]={"path":name,"author":author or "Wikimedia Commons contributor","source":"Wikimedia Commons — illustrative, NOT actual event","license":license_name}
        print(scene,"downloaded",len(payload),license_name)
    except Exception as e: print(scene,"SKIPPED",str(e))
(ROOT/"manifest.json").write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding="utf-8")
if not out: raise SystemExit("No verified openly licensed imagery downloaded")
