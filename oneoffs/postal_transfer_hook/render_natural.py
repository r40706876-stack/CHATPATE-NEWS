import importlib.util
import math
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps

CORE = Path.cwd()
sys.path.insert(0, str(CORE))
from postal_edge_lip_shapes import measure_mouth
from postal_edge_puppet import puppet

W, H, FPS, RATE, SECONDS = 720, 1280, 30, 48000, 4
GREEN, INK, CREAM, RED = "#14624F", "#153D32", "#F7F5EA", "#A7332D"
DIALOGUE = "भैया, ट्रांसफर के बाद मेरी पुरानी सर्विस गिनेगी?"
SHORT_DIALOGUE = "भैया, ट्रांसफर के बाद पुराने साल गिनेंगे?"
OUT = CORE / "hook-output"
OUT.mkdir(exist_ok=True)
DEV = "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Bold.ttf"
LAT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def text(im, x, y, value, size, color, hindi=False):
    draw = ImageDraw.Draw(im)
    face = ImageFont.truetype(DEV if hindi else LAT, size)
    a, b, c, d = draw.textbbox((0, 0), value, font=face)
    draw.text((x - (a+c)/2, y - (b+d)/2), value, font=face, fill=color)


def rect(im, xy, fill, radius=12, outline=None, width=1):
    ImageDraw.Draw(im).rounded_rectangle(tuple(round(x) for x in xy), radius, fill, outline, width)


def ease(x):
    x = min(1, max(0, x))
    return x*x*(3-2*x)


def generate_sound(voice_script):
    spec = importlib.util.spec_from_file_location("approved_voice", voice_script)
    voice = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(voice)
    voice.OUT = OUT
    name, _ = voice.VOICES["golu"]
    voice.VOICES["golu"] = (name, "You are Golu, a young Hindi speaker talking to your elder brother across a counter. Use normal conversational Hindi pace, light concern and a small lift on the final question. Say only the line. Use no dramatic pauses.")
    for line in (DIALOGUE, SHORT_DIALOGUE):
        voice.DIALOGUE = [("golu", line)]
        voice.voice_parts("golu")
        raw = ["ffmpeg","-v","error","-i",str(OUT/"voice0.wav"),
               "-af","silenceremove=start_periods=1:start_duration=0.024:start_threshold=-44dB:stop_periods=1:stop_duration=0.24:stop_threshold=-48dB,loudnorm=I=-16:TP=-3:LRA=6",
               "-ac","1","-ar",str(RATE),"-f","f32le","-"]
        speech = np.frombuffer(subprocess.check_output(raw), dtype="<f4")
        if len(speech) <= 3.90*RATE:
            break
    assert 1.7*RATE < len(speech) <= 3.90*RATE, len(speech)
    print(f"Natural voice at original speed: {len(speech)/RATE:.2f}s | {line}", flush=True)
    dry = np.zeros(SECONDS*RATE, dtype="float32")
    cue = int(.025*RATE)
    dry[cue:cue+len(speech)] = speech
    audio = dry.copy()
    rng = np.random.default_rng(29)
    for moment, length, gain in ((.16,.14,.055),(.43,.20,.047),(2.28,.17,.034),(3.56,.12,.032)):
        ticks = np.arange(int(length*RATE))/RATE
        noise = rng.uniform(-1,1,len(ticks))
        texture = .65*(noise-np.r_[0, noise[:-1]]) + .25*np.sin(2*np.pi*155*ticks)
        effect = gain*texture*np.sin(np.pi*np.minimum(1, ticks/length))**2
        start = int(moment*RATE)
        audio[start:start+len(ticks)] += effect
    (OUT/"audio.f32").write_bytes(np.clip(audio,-.97,.97).astype("<f4").tobytes())
    return measure_mouth(dry[::3], FPS, SECONDS)


def backdrop(path):
    photo = ImageOps.fit(Image.open(path).convert("RGB"), (W,H), centering=(.50,.46)).convert("RGBA")
    glaze = Image.new("RGBA", (W,H))
    d = ImageDraw.Draw(glaze)
    for y in range(H):
        a = int(64 + 107*ease((y-397)/760))
        d.line((0,y,W,y), fill=(249,244,223,a))
    return Image.alpha_composite(photo, glaze)


def counter():
    face = Image.new("RGBA", (W, 400))
    d = ImageDraw.Draw(face)
    d.rectangle((0,45,W,400), fill="#17634F")
    for y in range(72,400):
        m=(y-72)/328
        d.line((0,y,W,y), fill=(int(36-20*m),int(111-33*m),int(89-26*m)))
    for x in (20,246,473):
        d.rounded_rectangle((x,94,x+204,260),radius=5,outline="#38816D",width=2)
        d.rounded_rectangle((x+10,104,x+194,250),radius=4,outline="#1E5749",width=2)
    d.polygon([(90,0),(630,0),(W,37),(0,37)],fill="#956044")
    for x in range(17,704,16):
        y = 4 + x * 11 % 31
        d.line((x,y,min(719,x+25+x%70),y),fill=("#A87251" if x%3 else "#86553F"),width=1)
    d.rectangle((0,35,W,48),fill="#6F4432")
    d.line((0,36,W,36), fill="#B3845C",width=2)
    return face


def document(t):
    pic = Image.new("RGBA",(306,170))
    d = ImageDraw.Draw(pic)
    p = ease((t-.16)/.55)
    d.rounded_rectangle((13,79,292,160),8,fill="#59442B")
    d.rounded_rectangle((10,76,288,156),8,fill="#C3975B",outline="#6C4E2B",width=2)
    y = round(78-69*p)
    d.rounded_rectangle((48,y,251,141),6,fill=CREAM,outline="#D5C7AA",width=2)
    if p > .38:
        text(pic,150,y+17,"POSTMAN DRAFT",15,INK)
        d.line((71,y+34,226,y+34),fill="#B2C8AF",width=2)
        for y2 in (y+45,y+54,y+63):
            if y2 < 120:
                d.line((75,y2,172,y2),fill="#CCC5AF",width=2)
    d.polygon([(11,86),(291,86),(271,149),(27,149)],fill="#AB733D",outline="#765336")
    d.polygon([(11,84),(292,84),(273,138),(29,138)],fill="#D6AB70",outline="#A47A49")
    d.rounded_rectangle((105,101,201,126),5,fill=CREAM)
    text(pic,153,113,"POSTMAN DRAFT",11,INK)
    return pic


def state_cards(scene,t):
    if t < 2.15:
        return
    rise = ease((t-2.15)/.34)
    split = ease((t-3.48)/.33)
    y = round(978 - 187*(1-rise))
    if split <= .03:
        width = 478*rise
        if width < 5:
            return
        rect(scene,(360-width/2+3,y-32+7,360+width/2+3,y+32+7),"#155341",11)
        rect(scene,(360-width/2,y-32,360+width/2,y+32),CREAM,11,"#ADC5AB",2)
        if rise > .71:
            text(scene,360,y,"पुरानी सर्विस गिनेगी?",35,INK,True)
        return

    d = ImageDraw.Draw(scene)
    d.line((314,y,406,y), fill="#A6CCAE", width=3)
    d.polygon([(372,y),(361,y-6),(361,y+6)],fill=CREAM)
    for side, state, years, hindi in ((-1,"MP", "2 साल",False),(1,"हरियाणा","1 साल",True)):
        x = 360+side*(31+115*split)
        angle = side*(8*(1-split))
        tile = Image.new("RGBA",(267,78))
        rect(tile,(2,2,264,75),CREAM,11,"#ABCAB1",2)
        rect(tile,(10,14,17,63),GREEN,3)
        text(tile,83,38,state,28 if hindi else 26,INK,hindi)
        text(tile,202,38,years,29,INK,True)
        tile = tile.rotate(angle,Image.Resampling.BICUBIC,expand=True)
        scene.alpha_composite(tile,(round(x-tile.width/2),round(y-tile.height/2)))


def shot(base, desk, t, mouth):
    im = base.copy()
    p = ease(t/2.35)
    if p:
        z = .037*p
        im = im.crop((round(W*z),round(H*z),W-round(W*z),H-round(H*z))).resize((W,H),Image.Resampling.BICUBIC)
    rect(im,(45,84,675,132),CREAM,10)
    text(im,145,108,"POSTAL EDGE",18,INK)
    text(im,564,108,"postaledge.in",17,INK)
    rect(im,(411,166,658,217),RED,7)
    text(im,534,192,"डाक काउंटर",25,CREAM,True)

    rect(im,(250,226,470,254),GREEN,6)
    text(im,360,240,"नया पोस्टमैन ड्राफ्ट",18,CREAM,True)
    past = ease((t-2.25)/.23)
    if past < .97:
        rect(im,(38,259,682,423),CREAM,20,"#DADECB",2)
        rect(im,(65,288,75,392),GREEN,4)
        text(im,365,314,"ट्रांसफर लेकर",48,INK,True)
        text(im,365,379,"फँस गए?",69,INK,True)
    else:
        rect(im,(186,299,534,373),CREAM,13,"#DADECB",2)
        text(im,360,336,"ट्रांसफर के बाद?",32,INK,True)

    for is_golu in (False,True):
        face = .25+ease((t-.65)/.7)*.59 if is_golu else -.13-.54*ease((t-.8)/.95)
        scale = 1+.125*p if is_golu else 1+.035*p
        x = (45 - 16*p) if is_golu else (359 + 10*p)
        y = (510-22*p+7*math.sin(t*2.7)) if is_golu else (497-9*p)
        action = ("right" if t<.78 else "open") if is_golu else "chin"
        strength = .30+.50*ease((t-.14)/.45) if is_golu else .39
        actor = puppet(is_golu,t,0,face,mouth if is_golu else None,
                      "surprise" if is_golu else "think",(strength,action),
                      face,0,0)
        actor = actor.resize((round(298*scale),round(456*scale)),Image.Resampling.LANCZOS)
        im.alpha_composite(actor,(round(x),round(y)))
    im.alpha_composite(desk,(0,857))
    f = document(t)
    arrival = ease(t/.31)
    drop = math.sin(math.pi*arrival)
    f = f.rotate(15-19*arrival,resample=Image.Resampling.BICUBIC,expand=True)
    x = round(182-259*(1-arrival)); y = round(742-29*drop)
    im.alpha_composite(f,(x,y))
    impact = ease((t-.14)/.14)*(1-ease((t-.28)/.18))
    if impact > .04:
        d = ImageDraw.Draw(im)
        for side in (-1,1):
            origin = 360+side*171
            for index in range(2):
                yy=829+18*index
                d.line((origin,yy,origin+side*round(28*impact),yy-4+9*index), fill="#F4DEB0",width=3)
    state_cards(im,t)
    return im.convert("RGB")


def main():
    asset, voice_script = map(Path,sys.argv[1:3])
    lips = generate_sound(voice_script)
    background, desk = backdrop(asset),counter()
    final = OUT/"Postal_Edge_Transfer_Hook_4s.mp4"
    command = ["ffmpeg","-v","error","-y","-f","rawvideo","-pix_fmt","rgb24",
               "-s",f"{W}x{H}","-framerate",str(FPS),"-i","-",
               "-f","f32le","-ar",str(RATE),"-ac","1","-i",str(OUT/"audio.f32"),
               "-c:v","libx264","-preset","fast","-crf","17","-pix_fmt","yuv420p",
               "-c:a","aac","-b:a","144k","-movflags","+faststart","-t","4",str(final)]
    with subprocess.Popen(command,stdin=subprocess.PIPE) as encoder:
        for i in range(SECONDS*FPS):
            frame = shot(background,desk,i/FPS,lips[i])
            if i in (0,12,36,78,119):
                frame.resize((360,640),Image.Resampling.LANCZOS).save(OUT/f"qc-{i:03d}.jpg",quality=92)
            encoder.stdin.write(frame.tobytes())
        encoder.stdin.close()
        if encoder.wait():
            raise RuntimeError("MP4 encoding failed")
    subprocess.run(["ffmpeg","-v","error","-xerror","-i",str(final),"-f","null","-"],check=True)
    subprocess.run(["ffprobe","-v","error","-show_entries","format=duration:stream=codec_name,width,height,nb_frames","-of","json",str(final)],check=True)


if __name__ == "__main__":
    main()
