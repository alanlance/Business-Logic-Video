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
        '/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc',
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
    """Warm flat 2D explainer: distinct original design, not a copied channel layout."""
    cream=(255,248,229); evergreen=(22,54,43); green=(156,205,149)
    yellow=(255,217,109); orange=(255,173,125); blue=(145,195,230)
    im=Image.new('RGB',(w,h), evergreen)
    d=ImageDraw.Draw(im)
    a=w/1280
    f=lambda n:font(max(12,round(n*a)))
    # subtle dot-pattern frame
    for x in range(0,w,round(26*a)):
        for y in range(0,h,round(26*a)):
            d.ellipse((x,y,x+max(1,round(2*a)),y+max(1,round(2*a))),fill=(34,73,60))
    d.rounded_rectangle((18*a,16*a,1262*a,610*a),radius=22*a,fill=cream,outline=(10,38,31),width=max(2,round(4*a)))
    d.rounded_rectangle((54*a,45*a,195*a,91*a),radius=12*a,fill=green,outline=evergreen,width=max(2,round(3*a)))
    chapter=scene.get('chapter',f'章節 {int(1+p*7):02d}')
    d.text((70*a,52*a),chapter,font=f(22),fill=evergreen)
    d.text((215*a,45*a),scene['title'],font=f(35),fill=evergreen)
    # progressive diagram (reveal cards in order and animate connector arrows)
    steps=scene['steps']; n=len(steps); gap=19*a
    x0=66*a; usable=1148*a
    boxw=(usable-(n-1)*gap)/n
    y0=210*a; y1=396*a
    active=scene.get('focus',0)
    pal=[green,orange,blue,yellow,green]
    beat=int(t/1.15) % n
    for j,name in enumerate(steps):
        x=x0+j*(boxw+gap)
        if j>0:
            start=x-gap+3*a
            end=x-3*a
            d.line((start,303*a,end,303*a),fill=evergreen,width=max(2,round(4*a)))
            d.polygon([(end,303*a),(end-10*a,296*a),(end-10*a,310*a)],fill=evergreen)
        # each card enters with a brief vertical easing, then pulses active step
        appear=max(0.0,min(1.0,(t-0.16*j)/0.34))
        if appear<=0: continue
        dy=(1-appear)*24*a
        accent=evergreen if j==beat else (49,85,68)
        d.rounded_rectangle((x+4*a,y0+8*a+dy,x+boxw+4*a,y1+9*a+dy),radius=18*a,fill=(28,65,49))
        d.rounded_rectangle((x,y0+dy,x+boxw,y1+dy),radius=18*a,fill=pal[j%len(pal)],outline=accent,width=max(2,round((5 if j==beat else 3)*a)))
        d.text((x+19*a,y0+23*a+dy),f'{j+1:02d}',font=f(22),fill=evergreen)
        ft=f(26 if n<=4 else 23)
        lines=wrap(name,ft,boxw-35*a,d)
        for k,line in enumerate(lines[:3]):
            d.text((x+18*a,y0+(88+31*k)*a+dy),line,font=ft,fill=evergreen)
        if j==beat:
            d.rounded_rectangle((x+14*a,y1-22*a+dy,x+boxw-14*a,y1-13*a+dy),radius=4*a,fill=evergreen)
    # short visible takeaway, not the long narration (subtitle is later burned in at bottom)
    d.rounded_rectangle((67*a,459*a,1208*a,534*a),radius=16*a,fill=(255,255,248),outline=evergreen,width=max(2,round(2*a)))
    snippet=scene.get('takeaway','新人工程師重點：看入口、追流程、查規則、驗證修改')
    for k,line in enumerate(wrap(snippet,f(22),1085*a,d)[:2]):
        d.text((89*a,(476+27*k)*a),line,font=f(22),fill=evergreen)
    demo='虛構示範・非真實專案' if board.get('example') else ('原始碼已核對' if scene.get('status')=='CONFIRMED' else '待確認問題')
    d.text((75*a,572*a),demo,font=f(18),fill=(66,102,76))
    # subtitle reserved near bottom and scene timeline
    d.rectangle((50*a,696*a,1230*a,703*a),fill=(91,117,104))
    d.rectangle((50*a,696*a,(50+1180*p)*a,703*a),fill=yellow)
    return im

def srt_stamp(seconds):
    msec=round(seconds*1000)
    hr, msec=divmod(msec,3600000)
    mi,msec=divmod(msec,60000)
    se,ms=divmod(msec,1000)
    return f'{hr:02}:{mi:02}:{se:02},{ms:03}'


def split_caption(text, max_chars=21):
    """Short readable subtitle chunks (approximate timing, not phoneme alignment)."""
    import re
    pieces = [v.strip() for v in re.split(r'(?<=[。！？；，])', text) if v.strip()]
    chunks = []
    for part in pieces:
        while len(part) > max_chars:
            chunks.append(part[:max_chars])
            part=part[max_chars:]
        if part: chunks.append(part)
    return chunks or [text]


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
        parts=split_caption(sc['narration'])
        weights=[max(1,len(part)) for part in parts]
        unit=sec/sum(weights)
        cursor=t0
        for part,weight in zip(parts,weights):
            end=cursor+unit*weight
            captions.append(f'{len(captions)+1}\n{srt_stamp(cursor)} --> {srt_stamp(end)}\n{part}\n')
            cursor=end
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
