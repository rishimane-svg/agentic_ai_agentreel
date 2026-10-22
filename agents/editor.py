"""ScamShield final-polish editor (adaptive pacing, short captions, 9:16 safe zones).

Run: python -m agents.editor
Optional: python -m agents.editor --keep-timeline  # fixed 59-second timeline

This deterministic compositor doesn't claim LLM autonomy. Captions are estimated from
TTS duration using words; no forced alignment is claimed. Outputs remain review drafts.
"""
import argparse
import json
import math
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[1]
OUTPUTS=ROOT/'outputs'; IMAGES=ROOT/'assets/images'; AUDIO=ROOT/'assets/audio'
FPS=25; W,H=1080,1920
# Mandatory platform-safe zones: top 250px, bottom 350px. Captions: 1405-1555.
CAPTION_TOP=1408; CAPTION_BOTTOM=1555


def run(cmd):
    r=subprocess.run([str(a) for a in cmd],capture_output=True,text=True)
    if r.returncode:
        raise RuntimeError(f'Command failed: {" ".join(map(str,cmd))}\n{r.stderr[-3200:]}')
    return r.stdout.strip()


def duration(path):
    return float(run(['ffprobe','-v','error','-show_entries','format=duration','-of','default=noprint_wrappers=1:nokey=1',path]))


def audio_path(i):
    for ext in ['mp3','wav','m4a']:
        matches=sorted(AUDIO.glob(f'scene_{i:02d}.{ext}'))
        if matches:return matches[0]
    raise FileNotFoundError('Missing audio for scene '+str(i))


def font(n):
    for p in ['/System/Library/Fonts/Supplemental/Arial Bold.ttf','/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf']:
        try:return ImageFont.truetype(p,n)
        except OSError:pass
    return ImageFont.load_default()


def width(d,t,f):
    b=d.textbbox((0,0),t,font=f);return b[2]-b[0]


def wrap(d,txt,f,limit):
    lines=[];cur=''
    for word in txt.split():
        trial=(cur+' '+word).strip()
        if width(d,trial,f)<=limit:cur=trial
        else:
            if cur:lines.append(cur)
            if width(d,word,f)>limit:raise ValueError('Single caption word exceeds width: '+word)
            cur=word
    if cur:lines.append(cur)
    return lines


def caption_frame(source,destination,phrase):
    with Image.open(source) as im:
        im=im.convert('RGB')
        if im.size!=(W,H):raise ValueError('Expected exactly 1080x1920: '+str(source))
        if phrase:
            layer=Image.new('RGBA',(W,H),(0,0,0,0));d=ImageDraw.Draw(layer)
            n=54
            while n>=46:
                f=font(n); lines=wrap(d,phrase,f,900)
                if len(lines)<=2:break
                n-=2
            if len(lines)>2:raise ValueError('Caption too long: '+phrase)
            d.rounded_rectangle((57,CAPTION_TOP,1023,CAPTION_BOTTOM),radius=26,fill=(5,17,33,242))
            h=65; y=CAPTION_TOP+(CAPTION_BOTTOM-CAPTION_TOP-len(lines)*h)/2
            for line in lines:
                d.text((W//2,y),line,font=f,fill='white',anchor='ma');y+=h
            im=Image.alpha_composite(im.convert('RGBA'),layer).convert('RGB')
        im.save(destination,quality=94)


def caption_phrases(text,max_words=7):
    # Prefer splitting at punctuation; then cap each phrase to keep max two lines.
    words=text.strip().split();return [' '.join(words[i:i+max_words]) for i in range(0,len(words),max_words)]


def srt_stamp(t):
    ms=round(t*1000);h,r=divmod(ms,3600000);m,r=divmod(r,60000);s,msec=divmod(r,1000)
    return f'{h:02}:{m:02}:{s:02},{msec:03}'


def frame_count(t):return max(1,int(round(t*FPS)))


def main(keep_timeline=False):
    if not shutil.which('ffmpeg') or not shutil.which('ffprobe'):raise RuntimeError('Install FFmpeg + ffprobe')
    script=json.loads((OUTPUTS/'script.json').read_text(encoding='utf-8'))
    scenes=script['scenes']
    if len(scenes)!=7 or [s.get('scene_id') for s in scenes]!=list(range(1,8)):
        raise ValueError('Expected approved seven-scene script')
    if any(abs(float(a['end_s'])-float(b['start_s']))>0.01 for a,b in zip(scenes,scenes[1:])):
        raise ValueError('Non-contiguous source timeline')
    starts=[];total=0.;segments=[];subtitles=[];pacing=[]
    OUTPUTS.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='scamshield_final_') as tmp:
        tmp=Path(tmp)
        for s in scenes:
            i=int(s['scene_id']); txt=s.get('voiceover','').strip()
            image=IMAGES/f'scene_{i:02d}.png'
            if not image.exists():raise FileNotFoundError(str(image))
            old_slot=float(s['end_s'])-float(s['start_s'])
            if txt:
                audio=audio_path(i); aud_len=duration(audio)
                # Avoid static tail pauses; allow 0.28s after the entire audio file,
                # never truncate narration. Original clips may themselves contain silence.
                slot=max(3.2 if i==1 else 0,aud_len+0.28)
                if keep_timeline:
                    if aud_len>old_slot+0.02:raise ValueError(f'Scene {i} audio exceeds fixed timeline')
                    slot=old_slot
            else:
                aud_len=0.;audio=None;slot=old_slot
            if i==7:slot=4.
            count=frame_count(slot);slot=count/FPS
            starts.append(total)
            phrase_list=caption_phrases(txt)
            # Split audio's entire measurable duration across sequential caption phrases,
            # using number of characters for rough proportional timing. Not word alignment.
            if phrase_list:
                weights=[max(1,len(p)) for p in phrase_list];den=sum(weights)
                boundaries=[0.];position=0.
                for weight in weights[:-1]:
                    position+=weight/den*min(aud_len,slot);boundaries.append(position)
                boundaries.append(min(aud_len,slot))
            else:boundaries=[0.,slot]
            per_scene_parts=[]
            for k,phrase in enumerate(phrase_list or ['']):
                img_path=tmp/f'caption_{i:02d}_{k:02d}.jpg'
                caption_frame(image,img_path,phrase)
                # Each slice gets gentle motion via FFmpeg zoompan (the visual starts
                # freshly each phrase rather than being static for the entire scene).
                start=boundaries[k] if phrase_list else 0.
                stop=boundaries[k+1] if phrase_list else slot
                if k==len(phrase_list)-1:stop=slot
                part_frames=max(1,frame_count(stop-start))
                part=tmp/f'part_{i:02d}_{k:02d}.mp4'
                # zoom=1.015, tiny movement; safe to avoid text cropping. Main image
                # remains within a 1.5% inset (approx 8px on each side).
                zoom="zoompan=z='min(zoom+0.00003,1.015)':x='(iw-iw/zoom)/2':y='(ih-ih/zoom)/2':d=1:s=1080x1920:fps=25"
                run(['ffmpeg','-hide_banner','-loglevel','error','-y','-loop','1','-framerate',FPS,'-i',img_path,
                     '-vf',zoom+',format=yuv420p','-frames:v',part_frames,'-an','-c:v','libx264',
                     '-preset','veryfast','-crf','23',part])
                per_scene_parts.append(part)
                if phrase:
                    subtitles.append((total+start,total+min(stop,slot),phrase))
            joined=tmp/f'scene_visual_{i:02d}.mp4'
            concat=tmp/f'scene_list_{i:02d}.txt'
            concat.write_text(''.join("file '{}'\n".format(p.as_posix()) for p in per_scene_parts))
            run(['ffmpeg','-hide_banner','-loglevel','error','-y','-f','concat','-safe','0','-i',concat,'-c','copy',joined])
            seg=tmp/f'scene_{i:02d}.mp4'
            if audio:
                # trim any extra empty tail from prior segmentation, but keep entire audio.
                run(['ffmpeg','-hide_banner','-loglevel','error','-y','-i',joined,'-i',audio,
                     '-filter_complex','[1:a]aresample=48000,aformat=channel_layouts=stereo,apad[a]',
                     '-map','0:v','-map','[a]','-t',slot,'-c:v','copy','-c:a','aac','-ar','48000',
                     '-b:a','160k',seg])
            else:
                run(['ffmpeg','-hide_banner','-loglevel','error','-y','-i',joined,'-f','lavfi',
                     '-i','anullsrc=r=48000:cl=stereo','-t',slot,'-map','0:v','-map','1:a',
                     '-c:v','copy','-c:a','aac','-b:a','160k',seg])
            segments.append(seg)
            pacing.append({'scene':i,'original_slot_s':old_slot,'audio_s':round(aud_len,3),'final_slot_s':slot,
                           'estimated_captions':len(phrase_list)})
            total+=slot
            print(f'Scene {i:02}: original={old_slot:.2f}s, audio={aud_len:.2f}s, final={slot:.2f}s')
        if not 30<=total<=60:
            raise ValueError(f'Final timeline {total:.2f}s outside mandatory 30-60s range; shorten narration first')
        concat=tmp/'video_list.txt';concat.write_text(''.join("file '{}'\n".format(p.as_posix()) for p in segments))
        final=OUTPUTS/'scamshield_final_polish.mp4'
        run(['ffmpeg','-hide_banner','-loglevel','error','-y','-f','concat','-safe','0','-i',concat,
             '-c','copy','-movflags','+faststart',final])
    srt=OUTPUTS/'scamshield_final_polish.srt'
    srt.write_text('\n\n'.join(f'{i}\n{srt_stamp(a)} --> {srt_stamp(b)}\n{text}'
              for i,(a,b,text) in enumerate(subtitles,1))+'\n',encoding='utf-8')
    (OUTPUTS/'pacing_report.json').write_text(json.dumps({'target_duration_s':round(total,3),
       'actual_duration_s':round(duration(final),3),'method':'adaptive-to-TTS-file-duration; estimated caption timings, no forced alignment',
       'scenes':pacing},indent=2),encoding='utf-8')
    print('Export:',final,'total',round(duration(final),2),'s; SRT:',srt)
    print('Must visually review: captions, safe-zones, source accuracy, end-card official logo, loudness')


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--keep-timeline',action='store_true')
    args=parser.parse_args();main(args.keep_timeline)
