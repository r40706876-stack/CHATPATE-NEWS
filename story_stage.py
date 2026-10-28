"""Single-stage visual comedy for character-only episodes.

Unlike the old split-screen template, the speaker, the house and the objects
share one continuous 9:16 scene. All props are local vector drawings; no
unverified external images or generated 'news footage' are represented as real.
"""
import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter
import talk_test as tt

SIZE = (1080, 1920)
INK = (42, 57, 76)
RED = (206, 63, 64)
YELLOW = (255, 214, 79)


def scene_for(line):
    scene = str(line.get("scene") or "")
    return scene if scene in ("sweets", "arrival", "freight", "bill", "house") else "sweets"


def _box(d, x, y, w=230, h=160, label="COD"):
    x, y = int(x), int(y)
    d.rounded_rectangle((x, y, x+w, y+h), 16, fill=(205, 145, 84), outline=(102, 68, 47), width=7)
    d.rectangle((x+w//2-18, y, x+w//2+18, y+h), fill=(246, 211, 145))
    if label:
        d.rounded_rectangle((x+20, y+42, x+w-20, y+104), 10, fill=(255, 249, 227))
        d.text((x+w//2, y+73), label, font=tt.font(43), fill=RED, anchor="mm")


def _tv(d, x, y, w=400, h=300):
    x, y = int(x), int(y)
    d.rounded_rectangle((x, y, x+w, y+h), 22, fill=INK, outline=(25, 35, 48), width=10)
    d.rounded_rectangle((x+24, y+24, x+w-24, y+h-40), 12, fill=(100, 185, 211))
    d.polygon([(x+24,y+h-40),(x+w//2,y+50),(x+w-24,y+h-40)], fill=(246, 204, 110))
    d.line((x+w//2,y+h,x+w//2,y+h+35),fill=INK,width=15)
    d.line((x+w//2-90,y+h+35,x+w//2+90,y+h+35),fill=INK,width=15)


def _worker(d, x, y, arm=0):
    x, y = int(x), int(y)
    d.ellipse((x+60,y,x+190,y+130),fill=(234,177,129),outline=INK,width=5)
    d.rounded_rectangle((x+30,y+115,x+220,y+410),38,fill=(70,133,195),outline=INK,width=5)
    d.line((x+60,y+190,x-40,y+260+arm),fill=(70,133,195),width=32)
    d.line((x+195,y+185,x+295,y+225-arm),fill=(70,133,195),width=32)
    d.line((x+90,y+405,x+70,y+540),fill=INK,width=36)
    d.line((x+170,y+405,x+190,y+540),fill=INK,width=36)


SCENE_SETS = {
    "sweets": "mandi",      # Chacha's promised sweets: start at the market
    "arrival": "road",      # Courier arrives outside the house
    "freight": "road",      # Oversized COD goods block the street
    "bill": "aangan",       # The invoice is opened in the courtyard
    "house": "room",        # Family reactions and Dadi's final payoff indoors
}


def _house_base(scene="house"):
    # Distinct existing 3D sets give each narrative location a visible identity.
    # Previously every line reused the same village photo regardless of scene.
    try:
        from reel_studio import set_img
        return ImageEnhance.Brightness(set_img(SCENE_SETS.get(scene, "village"), *SIZE).filter(ImageFilter.GaussianBlur(1.2))).enhance(0.88)
    except (OSError, KeyError, ValueError):
        pass
    im=Image.new("RGB",SIZE,(232,245,252))
    d=ImageDraw.Draw(im)
    d.rectangle((0,1320,1080,1920),fill=(193,212,207))
    d.rectangle((0,1380,1080,1470),fill=(172,192,185))
    d.rounded_rectangle((75,400,1005,1400),30,fill=(246,218,183),outline=(154,112,84),width=10)
    d.polygon([(35,435),(540,215),(1045,435)],fill=(173,77,72))
    d.rounded_rectangle((120,740,370,1320),16,fill=(120,79,58),outline=(76,53,44),width=8)
    d.ellipse((320,1030,342,1052),fill=YELLOW)
    d.rounded_rectangle((745,690,940,955),14,fill=(166,205,218),outline=(88,112,130),width=10)
    d.line((840,690,840,955),fill=(88,112,130),width=7)
    return im


def _character(im, sprite, x, y, height, flip=False, tilt=0):
    if sprite is None:
        return
    w=int(sprite.width*height/max(1,sprite.height))
    sp=sprite.resize((w,height),Image.Resampling.LANCZOS)
    if flip:
        sp=sp.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    if tilt:
        old_w, old_h = sp.size
        sp = sp.rotate(tilt, resample=Image.Resampling.BICUBIC, expand=True)
        x -= (sp.width - old_w) // 2
        y -= (sp.height - old_h) // 2
    im.paste(sp,(int(x),int(y)),sp)


def _scene_action(im, scene, t, n, line=None):
    d=ImageDraw.Draw(im)
    q=min(1.0,t/max(1,n-1))
    wobble=int(12*math.sin(t/5))
    if scene=="sweets":
        d.rounded_rectangle((80,560,470,830),20,fill=(255,237,176),outline=(171,112,58),width=10)
        for j in range(3):
            d.ellipse((125+j*100,625,210+j*100,710),fill=(235,159,57),outline=(163,96,37),width=5)
        # Start with the absurdly expensive TV already in frame, not an empty hook.
        # It rolls toward Bablu during the first 0.6s as the COD price lands.
        _tv(d, int(640-170*min(1,t/15)), 550+wobble, 505,365)
        d.rounded_rectangle((565,925,1000,1045),20,fill=RED)
        d.text((782,982),"₹1,69,000",font=tt.font(77),fill="white",anchor="mm")
    elif scene=="arrival":
        for j in range(3):
            _box(d, int(1100-350*min(1,(t-j*7)/17))-j*175, 910-j*120+wobble, 240,160)
        _tv(d,485,570+wobble,360,265)
        # The TV displays the laddoo Chacha asked for: a visual gag, not a title card.
        d.ellipse((610,630,740,760),fill=(242,162,52),outline=(166,96,38),width=9)
        for dx,dy in ((-27,-15),(12,-23),(-8,23),(30,15)):
            d.ellipse((675+dx-8,690+dy-8,675+dx+8,690+dy+8),fill=(255,218,125))
        if any(k in str((line or {}).get("say", "")) for k in ("वसूली", "बैंक मैनेजर")):
            # Pinky's actual joke: an agent is about to climb out of the TV.
            # A speech bubble makes the threat legible even without narration.
            d.rounded_rectangle((500,490,840,570),18,fill=(255,247,215),outline=RED,width=8)
            d.text((670,530),"किश्त अभी दो!",font=tt.font(48),fill=RED,anchor="mm")
        elif "पैसे" in str((line or {}).get("say", "")):
            d.rounded_rectangle((535,620,815,800),18,fill=(253,247,221),outline=RED,width=10)
            d.text((675,665),"PAY NOW",font=tt.font(49),fill=RED,anchor="mm")
            d.text((675,737),"₹1,69,000",font=tt.font(45),fill=INK,anchor="mm")
    elif scene=="freight":
        if "फ्रिज" in str((line or {}).get("say", "")):
            # A SECOND appliance rolls in, escalating the COD nightmare.
            x=int(1050-480*q)
            d.rounded_rectangle((x,505,x+325,1095),24,fill=(226,238,241),outline=INK,width=17)
            d.line((x+12,805,x+313,805),fill=INK,width=9)
            d.rounded_rectangle((x+30,645,x+58,780),9,fill=(106,121,138))
            d.rounded_rectangle((x+30,865,x+58,1020),9,fill=(106,121,138))
            d.rounded_rectangle((x+60,570,x+275,630),10,fill=(255,250,231),outline=RED,width=5)
            d.text((x+168,600),"COD फ्रिज",font=tt.font(41),fill=RED,anchor="mm")
            for wheel in (x+60,x+265):
                d.ellipse((wheel-24,1090,wheel+24,1138),fill=INK)
        else:
            d.rounded_rectangle((415,710,925,1120),42,fill=(34,52,73),outline=YELLOW,width=13)
            d.rounded_rectangle((450,745,890,1070),26,fill=(243,249,252))
            d.text((670,835),"COD",font=tt.font(105),fill=INK,anchor="mm")
            d.text((670,955),"पैसे दो!",font=tt.font(74),fill=RED,anchor="mm")
            d.rounded_rectangle((555,480,930,670),25,fill=(44,60,83))
            d.text((742,570),"बिल बाकी!",font=tt.font(90),fill=YELLOW,anchor="mm")
            d.ellipse((740,1090,930,1280),fill=(247,193,99),outline=INK,width=7)
            d.text((835,1185),"?",font=tt.font(140),fill=INK,anchor="mm")
    elif scene=="bill":
        _tv(d,500,590+wobble,365,265)
        # The courier is an existing 3D-style Ramesh sprite, composited below.
        d.rounded_rectangle((470,930,1030,1290),20,fill="white",outline=RED,width=14)
        d.text((750,1010),"COD बिल",font=tt.font(71),fill=INK,anchor="mm")
        d.text((750,1130),"₹1,69,000",font=tt.font(76),fill=RED,anchor="mm")
        d.rounded_rectangle((540,1210,965,1270),12,fill=YELLOW)
        d.text((752,1240),"इतना बड़ा बिल!",font=tt.font(44),fill=INK,anchor="mm")
        if "बैंक ऐप" in str((line or {}).get("say", "")):
            # Bank-app rejection is a literal acted-out visual gag.
            # Move the phone into frame and shake it when the bank blocks Chacha.
            phone_x = int(1080 - 545 * min(1, q * 2.0))
            if q > 0.55:
                phone_x += int(13 * math.sin(t * 1.8))
            d.rounded_rectangle((phone_x,425,phone_x+325,900),35,fill=INK,outline=YELLOW,width=13)
            d.rounded_rectangle((phone_x+24,470,phone_x+301,850),16,fill=(244,250,251))
            d.text((phone_x+162,545),"बैंक ऐप",font=tt.font(53),fill=INK,anchor="mm")
            d.rounded_rectangle((phone_x+45,625,phone_x+280,765),18,fill=RED)
            d.text((phone_x+162,675),"अगला जन्म",font=tt.font(43),fill="white",anchor="mm")
            d.text((phone_x+162,731),"गिरवी!",font=tt.font(57),fill="white",anchor="mm")
    elif scene=="house":
        # Visual punchlines are acted out as objects; no giant explanation cards.
        say=str((line or {}).get("say",""))
        if "दरवाज़ा" in say:
            # Chacha tries to send the door back with the television.
            x=int(600+220*q)
            d.rounded_rectangle((x,540,x+190,980),16,fill=(139,86,53),outline=(70,45,33),width=13)
            d.ellipse((x+155,755,x+177,777),fill=YELLOW)
            d.line((x-80,750,x-10,750),fill=RED,width=22)
            d.polygon([(x+5,750),(x-40,718),(x-40,782)],fill=RED)
        elif "रिटर्न" in say:
            # Editorially motivated physical gag: Chacha offers to return himself.
            # Move the self-return carton in during his line so the visual sets up
            # Dadi offering Chacha as the exchange in the next beat.
            bx = int(1030 - 350 * q)
            _box(d, bx, 660, 310, 325, "")
            d.rounded_rectangle((bx+20, 770, bx+290, 900), 12,
                                fill=(255, 250, 233), outline=RED, width=8)
            d.text((bx+155, 811), "SELF RETURN", font=tt.font(39),
                   fill=RED, anchor="mm")
            d.text((bx+155, 864), "चाचा", font=tt.font(53),
                   fill=INK, anchor="mm")
        elif "रिमोट" in say:
            # Pinky shakes an oversized remote and finds no matching Chacha controls.
            rx=int(580+65*math.sin(q*math.pi*2))
            d.rounded_rectangle((rx,585,rx+180,1000),36,fill=INK,outline=YELLOW,width=10)
            for j in range(4):
                d.ellipse((rx+40+(j%2)*80,670+(j//2)*105,rx+85+(j%2)*80,715+(j//2)*105),fill=(229,234,239))
            d.line((rx-25,565,rx+210,1020),fill=RED,width=23)
            d.ellipse((rx+180,515,rx+295,630),outline=RED,width=14)
        elif "वापसी" in say:
            # The delivery box is sealed NO RETURN while Chacha keeps talking.
            _box(d,575,710,360,330,"COD")
            # The no-return seal visibly SLIDES onto the parcel; the previous
            # fixed stamp produced identical frames at t=0 and t=35 and
            # correctly failed the full-frame storyboard motion preflight.
            seal_x=int(1080-475*min(1.0,t/35.0))
            d.rounded_rectangle((seal_x,890,seal_x+300,1005),16,fill=(255,249,232),outline=RED,width=9)
            d.text((seal_x+150,945),"वापसी बंद!",font=tt.font(43),fill=RED,anchor="mm")
            for j in range(3):
                d.arc((460-j*28,650-j*30,580+j*28,910+j*30),-80,80,fill=RED,width=9)
        elif "मुफ्त सलाह" in say:
            # The final roast is physical: Dadi slaps a FREE ADVICE label on
            # Chacha's exchange carton, and the courier runs out of frame.
            _box(d, 535, 645, 405, 420, "")
            label_x = int(1150 - 540 * min(1, q * 2.0))
            d.rounded_rectangle((label_x, 740, label_x+300, 925), 17,
                                fill=(255, 247, 215), outline=RED, width=12)
            d.text((label_x+150, 802), "मुफ्त सलाह", font=tt.font(59),
                   fill=RED, anchor="mm")
            d.text((label_x+150, 873), "COD चाचा", font=tt.font(46),
                   fill=INK, anchor="mm")
            for j in range(3):
                d.arc((780-j*35, 490-j*32, 910+j*35, 700+j*32),
                      -85, 75, fill=RED, width=11)
        else:
            # Dadi offers Chacha in exchange for the television.
            _tv(d,510,540,300,220)
            d.line((790,875,530,875),fill=YELLOW,width=23)
            d.polygon([(505,875),(560,835),(560,915)],fill=YELLOW)
            _box(d,int(665+90*q),1000,250,180,"COD")

    # Story-first action overlays. Do not cycle giant text cards every 1.3s:
    # those used to cover the actual gag and made the scene look like a slideshow.
    phase=t/max(1,n-1)
    if scene=="sweets":
        # The COD carton slides across the sweets: the promised gift is replaced.
        if phase>0.34:
            x=int(50+min(1,(phase-.34)/.35)*190)
            _box(d,x,545,290,240,"COD")
    elif scene=="arrival":
        # Delivery stack keeps growing instead of alternating unrelated cards.
        if phase>.38:
            _box(d,int(930-400*min(1,(phase-.38)/.4)),735,200,145,"COD")
    elif scene=="freight":
        # The courier presents the COD invoice; never depict an unrelated UPI error.
        if phase>.20:
            x=int(970-130*min(1,(phase-.20)/.65))
            d.rounded_rectangle((x,1030,x+150,1250),12,fill=(255,250,232),outline=RED,width=9)
            d.text((x+75,1100),"COD",font=tt.font(46),fill=RED,anchor="mm")
            d.text((x+75,1180),"₹",font=tt.font(63),fill=INK,anchor="mm")
    elif scene=="bill":
        # An exchange arrow connects the expensive TV to the person being offered.
        x=int(450-65*math.sin(phase*math.pi))
        d.line([(x,820),(x-170,820)],fill=YELLOW,width=24)
        d.polygon([(x-195,820),(x-145,786),(x-145,854)],fill=YELLOW)
    elif scene=="house":
        # A red return stamp lands on the COD parcel as Dadi finishes the punch.
        if phase>.48 and "एक्सचेंज" in str((line or {}).get("say","")):
            scale=min(1,(phase-.48)/.26)
            cx,cy=765,1090
            r=int(125*scale)
            if r>5:
                d.ellipse((cx-r,cy-r,cx+r,cy+r),outline=RED,width=18)
                d.line((cx-r//2,cy-r//2,cx+r//2,cy+r//2),fill=RED,width=15)


def frames(line, episode, talk, n, cut, seed=0):
    """Yield full-screen scene with two cutout characters, voice-driven mouth and actual prop actions."""
    import sprite_talk
    from reel_studio import EXPR, pose_file
    scene=scene_for(line)
    base=_house_base(scene)
    who=line.get("who","bablu")
    supporter="chacha" if who!="chacha" else "pinky"
    if who=="chacha":
        supporter="pinky"
    folder=Path(episode["sprite"][who])
    expr=EXPR.get(talk.get("expr",""),talk.get("expr","")) or "neutral"
    talking=sprite_talk.frames(folder,expr,talk["wav"],n,cut,seed)
    supporting=None
    if supporter in episode.get("sprite",{}):
        reaction = "hairan" if who in ("bablu", "chacha") else "hasi"
        supporting=cut(pose_file(episode["sprite"][supporter],reaction))
    courier=None
    if "ramesh" in episode.get("sprite",{}):
        courier=cut(pose_file(episode["sprite"]["ramesh"],"neutral"))
    # Original Blender 3D COD reconstruction, not documentary news footage.
    # Only the delivery-arrival gag uses this insert; the bank-manager and
    # refrigerator beats keep their distinct, dialogue-specific animations.
    cod_path=Path("blender_output/bakra_cod_3d.mp4")
    cod_insert=(scene=="arrival" and "लड्डू" in str(line.get("say","")))
    cod_frames=None
    if cod_insert:
        if not cod_path.is_file():
            raise RuntimeError("Original Blender COD proof missing: cannot render integrated 3D arrival")
        from reel_studio import _vid_frames
        cod_frames=_vid_frames(cod_path, 1080, 1920)
    # Load and verify each licensed illustration ONCE, not once per video frame.
    # A failed/missing Commons download must never be misrepresented as footage.
    licensed_entry, licensed_insert = None, None
    try:
        import json
        manifest_path = Path("assets/licensed/manifest.json")
        if manifest_path.is_file():
            entries = json.loads(manifest_path.read_text(encoding="utf-8"))
            # Lead with the verified parcel photograph during the first hook,
            # rather than spending the highest-drop-off seconds on a generic TV icon.
            # This is illustrative Commons photography, NEVER the Madurai event.
            # Reuse the arrival asset so its creator/license attribution is preserved.
            entry = entries.get("arrival" if scene == "sweets" else scene, {})
            if all(entry.get(k) for k in ("path", "author", "source", "license")):
                media = Path("assets/licensed") / Path(entry["path"]).name
                if media.is_file() and media.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp"):
                    # Keep the entire documentary illustration visible, but make
                    # it large enough to read on a 9:16 phone. Blurred edge-fill
                    # preserves the original photo without cropping its subject.
                    from PIL import ImageOps
                    with Image.open(media) as picture:
                        original = picture.convert("RGB")
                    photo_size = (850, 530)
                    background = ImageOps.fit(original, photo_size,
                                              method=Image.Resampling.LANCZOS).filter(
                                                  ImageFilter.GaussianBlur(22))
                    foreground = ImageOps.contain(original, photo_size,
                                                  method=Image.Resampling.LANCZOS)
                    background.paste(foreground,
                                     ((photo_size[0] - foreground.width) // 2,
                                      (photo_size[1] - foreground.height) // 2))
                    licensed_insert = background
                    licensed_entry = entry
    except (OSError, ValueError, TypeError, KeyError):
        licensed_entry, licensed_insert = None, None
    for t,sp in enumerate(talking):
        im=base.copy()
        _scene_action(im,scene,t,n,line=line)
        # The COD Blender proof is a schematic, not convincing event footage.
        # Limit it to a fast 0.6s establishing cutaway; a long full-screen
        # low-detail 3D scene was hiding the actual licensed photo and acting.
        # Afterwards, use the village stage and attributed documentary illustration.
        cod_reveal_frames = min(15, max(1, n // 4))
        if cod_frames is not None and t < cod_reveal_frames:
            frame=next(cod_frames, None)
            if frame is None:
                raise RuntimeError("Blender COD proof video contains no decodable frames")
            im = frame.crop((0, 130, 1080, 1790)).resize(SIZE, Image.Resampling.BICUBIC)
            d = ImageDraw.Draw(im)
            d.rounded_rectangle((28, 225, 370, 292), 12, fill=INK)
            d.text((199, 258), "3D रीक्रिएशन", font=tt.font(37),
                   fill="white", anchor="mm")
        # Clearly labelled *illustrative* Commons photo, not claimed event footage.
        # On the Blender delivery reveal, let the original 3D fill the screen first.
        # News illustration is supporting evidence, not a 4-second static wallpaper.
        # Show it briefly with readable attribution, then reveal the moving
        # actors and gag props for the majority of the spoken line.
        # On the COD 3D reveal, do not cover the opening full-screen Blender shot.
        illustration_start = cod_reveal_frames if cod_insert else 0
        illustration_end = min(n, illustration_start + 42)  # 1.68s at 25 fps
        if licensed_insert is not None and illustration_start <= t < illustration_end:
            pan = int(35 * math.sin(t / max(1, n - 1) * math.pi))
            x, y = 105 + pan, 245
            d = ImageDraw.Draw(im)
            d.rounded_rectangle((x-12, y-12, x+licensed_insert.width+12, y+licensed_insert.height+12),
                                16, fill=(255,255,255), outline=INK, width=8)
            im.paste(licensed_insert, (x,y))
            credit_y = y + licensed_insert.height + 13
            d.rounded_rectangle((x-8, credit_y-5, min(1060, x+licensed_insert.width+16), credit_y+115),
                                8, fill=(255,250,233), outline=INK, width=3)
            d.text((x+5,credit_y+4), "चित्र: " + str(licensed_entry["author"])[:29],
                   font=tt.font(31), fill=INK)
            d.text((x+5,credit_y+42), "Wikimedia Commons | " + str(licensed_entry["license"])[:20],
                   font=tt.font(29), fill=INK)
            d.text((x+5,credit_y+80), "उदाहरण चित्र — असली घटना नहीं",
                   font=tt.font(28), fill=RED)
        if scene=="arrival" and any(k in str(line.get("say","")) for k in ("वसूली", "बैंक मैनेजर")):
            # Existing courier character literally emerges from the television.
            # Start small and move upward instead of showing another static icon.
            progress=min(1.0,t/max(1,n-1))
            if courier is not None:
                _character(im,courier,550-int(45*progress),720-int(310*progress),int(110+370*progress))
            else:
                _worker(ImageDraw.Draw(im),520,650-int(230*progress),int(25*math.sin(progress*6)))
        # Choreograph bodies around the actual joke, not just floating prop icons.
        # Use eased entrances and clear recoil / exchange movements.
        progress = min(1.0, t / max(1, n - 1))
        ease = progress * progress * (3 - 2 * progress)
        say = str(line.get("say", ""))
        courier_x = 70 + int(9 * math.sin(t / 7))
        if scene in ("freight", "bill", "house"):
            if "मुफ्त सलाह" in say:
                courier_x = int(70 - 480 * ease)  # courier visibly flees the unsolicited advice
            elif "पैसे" in say or "बिल" in say:
                courier_x = int(-300 + 370 * ease)
            _character(im, courier, courier_x, 810, 575)
        supporter_x = 5 + int(9 * math.sin(t / 8))
        speaker_x = 600 + int(8 * math.sin(t / 6))
        speaker_y = 990 + int(7 * math.sin(t / 9))
        if scene == "sweets":
            speaker_x = int(575 - 40 * ease)  # Reporter visible from frame one; no empty hook shot
        if "लड्डू" in say or "ससुराल" in say:
            speaker_x += int(110 * ease)  # Chacha backs away from the huge delivery
        if "दरवाज़ा" in say:
            speaker_x -= int(95 * ease)  # Pull attention toward the door gag
        if "रिटर्न" in say:
            speaker_x += int(90 * ease)  # Chacha shuffles into his return carton
            speaker_y += int(45 * ease)
        if "एक्सचेंज" in say:
            supporter_x += int(165 * ease)  # Dadi physically pushes Chacha toward carton
        if "मुफ्त सलाह" in say:
            supporter_x += int(70 * ease)
            speaker_y -= int(30 * math.sin(progress * math.pi * 3) ** 2)
        # Dialogue-timed acting: Chacha recoils, Pinky leans into the remote
        # gag, and Dadi punctuates the final roti-powered exchange.
        acting = 8 if any(k in say for k in ("लड्डू", "दरवाज़ा", "रिटर्न", "रिमोट", "मुफ्त सलाह")) else 4
        speaker_tilt = acting * math.sin(progress * math.pi * 1.3)
        supporter_tilt = -3 * math.sin(progress * math.pi * 1.6)
        _character(im, supporting, supporter_x, 1120 + int(5 * math.sin(t / 10)),
                   610, flip=True, tilt=supporter_tilt)
        _character(im, sp, speaker_x, speaker_y, 760, tilt=speaker_tilt)
        d=ImageDraw.Draw(im)
        if scene=="house" and who=="dadi" and ("एक्सचेंज" in str(line.get("say","")) or "वापसी" in str(line.get("say","")) or "मुफ्त सलाह" in str(line.get("say",""))) and t>=int(n*.40):
            # Physical payoff: Dadi has packed Chacha, not merely flashed a RETURN icon.
            # Leave his face visible; the carton covers his torso and stays attached to him.
            d.rounded_rectangle((12,1390,430,1730),20,fill=(201,146,92),outline=(108,69,44),width=14)
            d.rectangle((200,1390,242,1730),fill=(246,212,150))
            d.rounded_rectangle((45,1490,398,1635),14,fill=(255,250,233),outline=RED,width=8)
            label=("मुफ्त सलाह!" if "मुफ्त सलाह" in str(line.get("say",""))
                   else ("वापसी बंद!" if "वापसी" in str(line.get("say","")) else "एक्सचेंज!"))
            d.text((221,1535),label,font=tt.font(50),fill=RED,anchor="mm")
            d.text((221,1594),"चाचा पैक!",font=tt.font(42),fill=INK,anchor="mm")
        # Alternate full-scene camera framing during long dialogue. This is a
        # real visual cut across props and characters, not a subtitle flicker.
        # Keep the original wide composition for the first beat and payoff.
        if (t // 18) % 2 == 1 and t < n - 6:
            w, h = im.size
            margin_x, margin_y = int(w * .105), int(h * .105)
            im = im.crop((margin_x, margin_y, w - margin_x, h - margin_y)).resize((w, h), Image.Resampling.BICUBIC)
        yield im
