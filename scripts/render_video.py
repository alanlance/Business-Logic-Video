#!/usr/bin/env python3
"""Offline-friendly, evidence-checked Chinese animated explainer video renderer.
Speech via macOS 'say' only. Generates mp4, SRT, manifest. No network calls.
"""
import argparse
import json
import math
import shutil
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def cmd(*args):
    return subprocess.run(list(map(str,args)), check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)


def duration(media):
    return float(cmd('ffprobe','-v','error','-show_entries','format=duration','-of','default=noprint_wrappers=1:nokey=1',media).stdout.strip())


def font(size):
    candidates = [
        '/System/Library/Fonts/PingFang.ttc',
        '/System/Library/Fonts/STHeiti Medium.ttc',
        '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
        '/usr/share/fonts/truetype/wqy/wqy-microhei.ttc',
    ]
    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path,size)
    raise RuntimeError('找不到中文字型。請安裝 Noto Sans CJK 或使用 macOS PingFang。')


def wrap(text, ft, max_px, draw):
    lines, cur = [], ''
    for c in text:
        if cur and draw.textlength(cur + c, font=ft) > max_px:
            lines.append(cur)
            cur = c
        else:
            cur += c
    if cur: lines.append(cur)
    return lines


def paint(scene, board, w, h, p, t):
    im = Image.new('RGB',(w,h),(12,20,37))
    d = ImageDraw.Draw(im)
    a = w/1280
    f = lambda n: font(max(12,int(n*a)))
    # slow animated background ribbons
    for i in range(11):
        x = int((i*180 + 24*math.sin(t*0.65+i)) * a)
        y = int((i*93 + 32*math.cos(t*.35+i)) * a)
        d.ellipse((x,y,x+int(150*a),y+int(150*a)),outline=(20,35,62),width=max(1,int(2*a)))
    d.rounded_rectangle((52*a,48*a,1228*a,155*a),radius=22*a,fill=(28,42,66))
    d.text((80*a,60*a),board.get('title','業務邏輯懶人包'),font=f(30),fill=(246,249,255))
    d.text((80*a,113*a),board.get('subtitle',''),font=f(17),fill=(156,197,239))
    d.text((64*a,180*a),scene['title'],font=f(44),fill=(255,255,255))
    steps=scene['steps']
    n=len(steps)
    x0=72*a
    spacing= (1110*a)/n
    focus=scene.get('focus',0)
    # animate one emphasized node; other nodes shown with low contrast
    for j, name in enumerate(steps):
        x=x0 + j*spacing
        selected = (j == focus)
        pulse=0.5+0.5*math.sin(t*3.2)
        fill=(29,117+int(20*pulse),171+int(22*pulse)) if selected else (31,46,72)
        d.rounded_rectangle((x,310*a,x+spacing-17*a,426*a),radius=17*a,fill=fill,outline=(68,182,231) if selected else (61,77,105),width=max(1,int(2*a)))
        d.text((x+16*a,332*a),f'{j+1:02d}',font=f(21),fill=(178,226,255) if selected else (132,144,164))
        lines=wrap(name,f(21),spacing-38*a,d)
        for k,line in enumerate(lines[:2]):
            d.text((x+16*a,(369+24*k)*a),line,font=f(21),fill=(255,255,255) if selected else (198,207,225))
        if j<n-1:
            d.line((x+spacing-16*a,368*a,x+spacing-4*a,368*a),fill=(98,181,219),width=max(1,int(3*a)))
    # accessible visible excerpt and dynamic progress
    d.rounded_rectangle((62*a,475*a,1218*a,635*a),radius=20*a,fill=(22,33,52))
    narr=scene['narration']
    for k,line in enumerate(wrap(narr,f(23),1090*a,d)[:3]):
        d.text((90*a,(492+39*k)*a),line,font=f(23),fill=(232,239,247))
    label='示意流程｜非實際系統' if board.get('example') else ('已核對原始碼' if scene.get('status')=='CONFIRMED' else '待確認')
    d.text((70*a,666*a),label,font=f(16),fill=(144,165,191))
    d.rectangle((70*a,701*a,1210*a,708*a),fill=(44,60,81))
    d.rectangle((70*a,701*a,(70+1140*p)*a,708*a),fill=(72,190,231))
    return im


def srt_stamp(seconds):
    msec=round(seconds*1000)
    hr, msec=divmod(msec,3600000)
    mi,msec=divmod(msec,60000)
    se,ms=divmod(msec,1000)
    return f'{hr:02}:{mi:02}:{se:02},{ms:03}'


def validate(data):
    if not isinstance(data,dict) or not isinstance(data.get('scenes'),list) or not 2<=len(data['scenes'])<=12:
        raise ValueError('scenes 必須有 2–12 個場景')
    demo=data.get('example',False)
    for i,sc in enumerate(data['scenes']):
        for key in ('title','narration','steps','evidence_ids','status'):
            if key not in sc: raise ValueError(f'場景 {i+1} 缺少 {key}')
        if not 2 <= len(sc['steps']) <= 5: raise ValueError('每個場景需 2–5 個步驟')
        if not 0 <= sc.get('focus',0) < len(sc['steps']): raise ValueError('focus 不合法')
        if not demo and sc['status']=='CONFIRMED' and not sc['evidence_ids']:
            raise ValueError(f'場景 {i+1} 未附 evidence_ids')
        if not demo and sc['status'] not in ('CONFIRMED','UNKNOWN'):
            raise ValueError(f'場景 {i+1} 的 status 不合法')


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('storyboard')
    ap.add_argument('--out',required=True)
    ap.add_argument('--tts',choices=['macos','none'],default='macos')
    ap.add_argument('--voice',default=None)
    ap.add_argument('--resolution',choices=['1280x720','1920x1080'],default='1280x720')
    ap.add_argument('--target-seconds',type=float,default=180)
    ap.add_argument('--fps',type=int,default=24)
    args=ap.parse_args()
    for executable in ('ffmpeg','ffprobe'):
        if not shutil.which(executable): ap.error(f'需要安裝 {executable}')
    if args.tts=='macos' and (sys.platform!='darwin' or not shutil.which('say')):
        ap.error('macos TTS 需要 macOS 與 say 指令；或使用 --tts none 產生無旁白影片')
    data=json.loads(Path(args.storyboard).read_text(encoding='utf-8'))
    validate(data)
    out=Path(args.out).resolve()
    out.mkdir(parents=True,exist_ok=True)
    work=out/'assets'
    work.mkdir(exist_ok=True)
    w,h=map(int,args.resolution.split('x'))
    lens=[]
    audio=[]
    if args.tts=='macos':
        for i,sc in enumerate(data['scenes']):
            path=work/f'voice_{i:02d}.aiff'
            args_say=['say']
            if args.voice: args_say+=['-v',args.voice]
            args_say+=['-o',str(path),sc['narration']]
            try: cmd(*args_say)
            except subprocess.CalledProcessError as e:
                raise RuntimeError('無法產生 macOS 旁白。使用 say -v ? 檢查可用聲音。'+e.stderr[-300:])
            audio.append(path)
            lens.append(duration(path)+0.6)
    else:
        # default 6s per scene minimum; length estimate based on Chinese narration
        lens=[max(6.0,len(sc['narration'])/4.3) for sc in data['scenes']]
    # Match user pacing only by extending pauses: never speed up voices to arbitrary rate.
    extra=max(0.0,args.target_seconds-sum(lens))/len(lens)
    lens=[n+extra for n in lens]
    clips=[]
    t0=0
    captions=[]
    for i,(sc,sec) in enumerate(zip(data['scenes'],lens)):
        captions.append(f'{i+1}\n{srt_stamp(t0)} --> {srt_stamp(t0+sec)}\n{sc["narration"]}\n')
        t0+=sec
        # Produce real per-frame motion, not a static slideshow
        clip=work/f'clip_{i:02d}.mp4'
        pipe=subprocess.Popen(['ffmpeg','-y','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s',f'{w}x{h}','-r',str(args.fps),'-i','-', '-c:v','libx264','-preset','veryfast','-pix_fmt','yuv420p','-crf','23','-an',str(clip)],stdin=subprocess.PIPE,stderr=subprocess.PIPE)
        total=round(sec*args.fps)
        for frame in range(total):
            t=frame/args.fps
            p=(sum(lens[:i])+t)/sum(lens)
            pipe.stdin.write(paint(sc,data,w,h,p,t).tobytes())
        pipe.stdin.close()
        err=pipe.stderr.read().decode('utf-8',errors='replace')
        if pipe.wait()!=0: raise RuntimeError('FFmpeg 動畫渲染失敗: '+err[-1000:])
        clips.append(clip)
    srt=out/'captions.srt'
    srt.write_text('\n'.join(captions),encoding='utf-8')
    concat=work/'clips.txt'
    concat.write_text(''.join("file '"+str(c).replace("'","'\\''")+"'\n" for c in clips))
    silent=work/'silent.mp4'
    cmd('ffmpeg','-y','-loglevel','error','-f','concat','-safe','0','-i',concat,'-c','copy',silent)
    narration=work/'narration.m4a'
    if audio:
        # Audio separated by exactly the same per-scene duration incl. padding
        af=[]
        for i,(raw,sec) in enumerate(zip(audio,lens)):
            seg=work/f'audio_{i:02d}.m4a'
            cmd('ffmpeg','-y','-loglevel','error','-i',raw,'-af','apad','-t',str(sec),'-c:a','aac',seg)
            af.append(seg)
        alist=work/'audio.txt'
        alist.write_text(''.join("file '"+str(p)+"'\n" for p in af))
        cmd('ffmpeg','-y','-loglevel','error','-f','concat','-safe','0','-i',alist,'-c','copy',narration)
    # Burn subtitles when supported; otherwise keep sidecar SRT
    has_subtitle='subtitles' in cmd('ffmpeg','-hide_banner','-filters').stdout
    output=out/'overview.mp4'
    video_input=['-i',str(silent)]
    ff=['ffmpeg','-y','-loglevel','error',*video_input]
    if audio: ff+=['-i',str(narration)]
    if has_subtitle:
        # ffmpeg subtitles filename path escaping; safer to run in output directory with relative name
        vf='subtitles=captions.srt'
        ff+=['-vf',vf,'-c:v','libx264','-preset','fast','-crf','24']
    else:
        ff+=['-c:v','copy']
    if audio: ff+=['-c:a','aac','-shortest']
    ff+=[str(output)]
    subprocess.run(ff,check=True,cwd=out)
    stream=json.loads(cmd('ffprobe','-v','error','-show_streams','-of','json',output).stdout)['streams']
    manifest={'source_storyboard':str(Path(args.storyboard).resolve()),'demo':data.get('example',False),'revision':data.get('revision'),'duration_seconds':duration(output),'audio_present':any(s['codec_type']=='audio' for s in stream),'subtitles_burned':has_subtitle,'sidecar_srt':str(srt),'resolution':args.resolution,'tts':args.tts,'scene_count':len(data['scenes']),'note':'Scene facts must be checked against evidence by the agent before rendering.'}
    (out/'render_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(manifest,ensure_ascii=False,indent=2))

if __name__=='__main__':
    try: main()
    except Exception as e:
        print('ERROR:',e,file=sys.stderr)
        sys.exit(1)
