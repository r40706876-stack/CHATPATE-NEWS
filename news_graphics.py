"""Exact news facts as animated graphics; no external image model required."""
import json
import math
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw
import talk_test as tt

W, H, FPS = 1080, 1920, 15


def frame(data, t):
    im = Image.new('RGB', (W, H), '#f5f4ec')
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((45, 70, 1035, 175), 24, fill='#124f70')
    d.text((540, 122), 'बकरा न्यूज़ | यात्री जानकारी', font=tt.font(46), fill='white', anchor='mm')
    d.text((540, 290), data['title'], font=tt.font(64), fill='#153d55', anchor='mm')
    rows=data.get('rows', [])
    if data.get('kind') == 'route':
        x=150
        top, step=440, 115
        d.line((x,top,x,top+step*(len(rows)-1)),fill='#149ba7',width=14)
        progress=(t/7)%1
        for i, row in enumerate(rows):
            y=top+i*step
            d.ellipse((x-16,y-16,x+16,y+16),fill='#124f70')
            d.text((220,y),row,font=tt.font(48),fill='#153d55',anchor='lm')
        y=top+progress*step*(len(rows)-1)
        d.rounded_rectangle((x-34,y-35,x+34,y+35),12,fill='#f27a35')
        d.text((540,1550),'मार्ग का संकेत-चित्र • भौगोलिक नक्शा नहीं',font=tt.font(32),fill='#52636c',anchor='mm')
    else:
        for i,row in enumerate(rows):
            y=480+i*225
            active=(int(t/1.8)%max(1,len(rows)))==i
            d.rounded_rectangle((75,y-70,1005,y+100),24,fill='#d7f0ef' if active else 'white',outline='#149ba7',width=3)
            d.text((540,y+10),row,font=tt.font(57),fill='#153d55',anchor='mm')
    if data.get('note'):
        d.text((540,1630),data['note'],font=tt.font(36),fill='#52636c',anchor='mm')
    d.text((540,1740),'स्रोत: रेल मंत्रालय / PIB • 01 नवंबर 2026',font=tt.font(32),fill='#52636c',anchor='mm')
    return im


def render(data, out):
    out=Path(out)
    wr=subprocess.Popen(['ffmpeg','-y','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}',
                         '-r',str(FPS),'-i','-','-an','-c:v','libx264','-preset','veryfast','-crf','21',
                         '-pix_fmt','yuv420p',str(out)],stdin=subprocess.PIPE)
    for k in range(FPS*20):
        wr.stdin.write(frame(data,k/FPS).tobytes())
    wr.stdin.close()
    if wr.wait():
        raise RuntimeError('News graphic encoding failed')
    out.with_suffix('.txt').write_text('तथ्य-आधारित ग्राफिक • स्रोत: PIB / रेल मंत्रालय',encoding='utf-8')
    return out
