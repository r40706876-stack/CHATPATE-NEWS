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
DIALOGUE = "भैया, ट्रांसफर लेकर फँस गया! नए पोस्टमैन ड्राफ्ट में पुरानी सर्विस बेकार हो गई क्या?"
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
    voice.DIALOGUE = [("golu", DIALOGUE)]
    name, _ = voice.VOICES["golu"]
    voice.VOICES["golu"] = (name, "Young Hindi character Golu, immediately speaking with worried urgency. Deliver the complete single line in one brisk natural breath, target 3.7 seconds. Clear consonants, tiny pause after 'गया', no added words.")
    voice.voice_parts("golu")
    raw = ["ffmpeg", "-v", "error", "-y", "-i", str(OUT/"voice0.wav"),
           "-af", "silenceremove=start_periods=1:start_duration=0.024:start_threshold=-44dB:stop_periods=1:stop_duration=0.28:stop_threshold=-48dB,loudnorm=I=-16:TP=-3:LRA=6",
           "-ac", "1", "-ar", str(RATE), "-f", "f32le", "-"]
    speech = np.frombuffer(subprocess.check_output(raw), dtype="<f4")
    tempo = max(1, len(speech)/(3.85*RATE))
    if tempo > 1:
        speech = np.frombuffer(subprocess.check_output(
            ["ffmpeg","-v","error","-f","f32le","-ar",str(RATE),"-ac","1","-i","-",
             "-af",f"atempo={math.sqrt(tempo):.5f},atempo={math.sqrt(tempo):.5f}",
             "-f","f32le","-"], input=speech.tobytes()), dtype="<f4")
    assert 2.4*RATE < len(speech) < 3.95*RATE, len(speech)
    print(f"Final speech {len(speech)/RATE:.2f}s, tempo {tempo:.2f}", flush=True)
    dry = np.zeros(SECONDS*RATE, dtype="float32")
    cue = int(.025*RATE)
    dry[cue:cue+len(speech)] = speech
    audio = dry.copy()
    rng = np.random.default_rng(29)
    for moment, length, gain in ((.035,.18,.06),(2.62,.15,.035),(3.73,.12,.03)):
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
    p = ease((t-.06)/.62)
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
    if t < 2.55:
        return
    p = ease((t-2.55)/.26)
    split = ease((t-3.65)/.30)
    y = 978 + 24*(1-p)
    if split > .06:
        rect(scene,(79,y-38,343,y+38),CREAM,12)
        rect(scene,(377,y-38,641,y+38),CREAM,12)
        text(scene,145,y,"MP",26,INK)
        text(scene,239,y,"2 साल",29,INK,True)
        text(scene,482,y,"हरियाणा",27,INK,True)
        text(scene,571,y,"1 साल",27,INK,True)
        d = ImageDraw.Draw(scene)
        d.line((348,y,371,y),fill=CREAM,width=3)
        d.polygon([(371,y),(364,y-5),(364,y+5)],fill=CREAM)
    else:
        rect(scene,(119,y-38,601,y+38),CREAM,12,"#ADC5AB",2)
        text(scene,360,y+1,"पुरानी सर्विस गिनेगी?",36,INK,True)


def shot(base, desk, t, mouth):
    im = base.copy()
    p = ease(t/2.35)
    if p:
        z = .025*p
        im = im.crop((round(W*z),round(H*z),W-round(W*z),H-round(H*z))).resize((W,H),Image.Resampling.BICUBIC)
    rect(im,(45,84,675,132),CREAM,10)
    text(im,145,108,"POSTAL EDGE",18,INK)
    text(im,564,108,"postaledge.in",17,INK)
    rect(im,(411,166,658,217),RED,7)
    text(im,534,192,"डाक काउंटर",25,CREAM,True)

    past = ease((t-2.56)/.24)
    if past < .97:
        rect(im,(38,259,682,423),CREAM,20,"#DADECB",2)
        rect(im,(65,288,75,392),GREEN,4)
        text(im,365,314,"ट्रांसफर लेकर",48,INK,True)
        text(im,365,379,"फँस गए?",69,INK,True)
    else:
        rect(im,(186,299,534,373),CREAM,13,"#DADECB",2)
        text(im,360,336,"नया पोस्टमैन ड्राफ्ट",29,INK,True)

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
    f = f.rotate(6-10*ease(t/.65),resample=Image.Resampling.BICUBIC,expand=True)
    im.alpha_composite(f,(180,742))
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
            if i in (0,34,85,119):
                frame.resize((360,640),Image.Resampling.LANCZOS).save(OUT/f"qc-{i:03d}.jpg",quality=92)
            encoder.stdin.write(frame.tobytes())
        encoder.stdin.close()
        if encoder.wait():
            raise RuntimeError("MP4 encoding failed")
    subprocess.run(["ffmpeg","-v","error","-xerror","-i",str(final),"-f","null","-"],check=True)
    subprocess.run(["ffprobe","-v","error","-show_entries","format=duration:stream=codec_name,width,height,nb_frames","-of","json",str(final)],check=True)


if __name__ == "__main__":
    main()
