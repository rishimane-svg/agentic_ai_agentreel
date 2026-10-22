"""ScamShield Critic: evidence-based video QA with explicit human checkpoints.
Run: python -m agents.critic --video outputs/scamshield_with_college_logo.mp4
Uses Python stdlib and installed ffmpeg/ffprobe. Does not edit video or source files.
"""
import argparse
import csv
import json
import re
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def command(args):
    return subprocess.run(args, capture_output=True, text=True, check=False)

def inspect_media(path):
    p = command(['ffprobe','-v','error','-show_format','-show_streams','-of','json',str(path)])
    if p.returncode: raise RuntimeError('ffprobe: '+p.stderr.strip())
    return json.loads(p.stdout)

def tc_to_seconds(s):
    h,m,rest=s.replace('.',',').split(':'); sec,ms=rest.split(',')
    return int(h)*3600+int(m)*60+int(sec)+int(ms)/1000

def parse_srt(path):
    text=path.read_text(encoding='utf-8-sig')
    chunks=re.split(r'\n\s*\n',text.strip()); result=[]
    for chunk in chunks:
        lines=[x.strip() for x in chunk.splitlines() if x.strip()]
        i=next((i for i,x in enumerate(lines) if '-->' in x),None)
        if i is None: continue
        left,right=[v.strip() for v in lines[i].split('-->',1)]
        result.append((tc_to_seconds(left),tc_to_seconds(right), ' '.join(lines[i+1:])))
    return result

def analyse_audio(video):
    p=command(['ffmpeg','-hide_banner','-nostats','-i',str(video),'-vn','-af','ebur128=peak=true','-f','null','-'])
    data=p.stderr
    # Last summary reflects integrated measurement over the full reel
    summaries=list(re.finditer(r'Summary:\s*Integrated loudness:\s*I:\s*(-?[\d.]+)\s*LUFS.*?True peak:\s*Peak:\s*(-?[\d.]+)\s*dBFS',data,re.S))
    if summaries:
        m=summaries[-1]; return {'integrated_lufs':float(m.group(1)),'true_peak_dbfs':float(m.group(2))}
    return None

def evaluate(video,srt=None,require_logo=True):
    checks=[]
    def add(id,status,detail,kind='machine',severity='major'):
        checks.append({'id':id,'status':status,'detail':detail,'method':kind,'severity':severity})
    if not video.is_file():
        add('video_exists','FAIL',f'Cannot find {video}');return checks
    data=inspect_media(video); fmt=data['format']; streams=data.get('streams',[])
    v=next((s for s in streams if s.get('codec_type')=='video'),{})
    a=next((s for s in streams if s.get('codec_type')=='audio'),{})
    dur=float(fmt.get('duration',0)); fps_text=v.get('avg_frame_rate','0/1')
    try: n,d=map(int,fps_text.split('/'));fps=n/d if d else 0
    except (ValueError,ZeroDivisionError): fps=0
    def rule(id,passed,detail,severity='major'):add(id,'PASS' if passed else 'FAIL',detail,severity=severity)
    rule('duration_30_60',30<=dur<=60,f'{dur:.3f} seconds')
    rule('resolution_9_16',v.get('width')==1080 and v.get('height')==1920,f"{v.get('width')}x{v.get('height')}")
    rule('constant_framerate_25_or_30',abs(fps-25)<0.01 or abs(fps-30)<0.01,f'{fps:.3f} fps; check CFR with ffprobe when needed')
    rule('h264_high',v.get('codec_name')=='h264' and str(v.get('profile','')).lower()=='high',f"codec={v.get('codec_name')} profile={v.get('profile')}")
    rule('pixel_format',v.get('pix_fmt')=='yuv420p',f"pixel_format={v.get('pix_fmt')}")
    rule('aac_stereo_48khz',a.get('codec_name')=='aac' and a.get('channels')==2 and str(a.get('sample_rate'))=='48000',f"{a.get('codec_name')}, {a.get('channels')}ch, {a.get('sample_rate')}Hz")
    rule('file_under_100mb',video.stat().st_size<=100_000_000,f'{video.stat().st_size/1e6:.2f} MB')
    if srt and srt.is_file():
        cues=parse_srt(srt)
        rule('srt_nonempty',bool(cues),f'{len(cues)} caption cues')
        invalid=[i+1 for i,(x,y,t) in enumerate(cues) if x<0 or y<=x or y>dur+0.25 or not t]
        rule('srt_cue_bounds',not invalid,f'invalid cues: {invalid[:12]}')
        overlaps=[i+1 for i in range(1,len(cues)) if cues[i][0] < cues[i-1][1]-0.03]
        rule('srt_cue_overlap',not overlaps,f'overlapping cue indices: {overlaps[:12]}')
        add('subtitle_appearance_and_alignment','REVIEW','SRT timestamps cannot prove speech-level synchronization, minimum visual font size, or burned-in captions','human')
    else: add('srt_file','FAIL','Matching .srt file is missing; supply --srt path')
    script=ROOT/'outputs/script.json'; facts=ROOT/'outputs/facts.json'; manifest=ROOT/'assets/manifest.csv'
    if script.exists():
        try:
            obj=json.loads(script.read_text(encoding='utf-8'));scenes=obj.get('scenes',[])
            full=' '.join(str(sc.get('voiceover','')) for sc in scenes).lower()
            rule('script_has_scenes',bool(scenes),f'{len(scenes)} scenes')
            rule('reporting_portal_in_script','cybercrime.gov.in' in full,'Script text match only—not an independent official-source check')
            rule('1930_in_script',bool(re.search(r'(?<!\d)1930(?!\d)',full)),'Script text match only; 1930 refers to cyber financial fraud helpline')
        except (ValueError,TypeError) as e: add('script_parse','FAIL',str(e))
    else: add('script_available','REVIEW','script.json absent from this evaluation environment; needed to trace claims','human')
    if facts.exists():
        try:
            f=json.loads(facts.read_text(encoding='utf-8'))
            add('fact_sources','REVIEW','facts.json present; compare each factual claim and helpline to original official documents; matching local notes is not independent verification','human')
        except ValueError: add('facts_valid_json','FAIL','facts.json is not valid JSON')
    else:add('fact_sources','REVIEW','facts.json not found; full claim provenance cannot be reviewed','human')
    add('official_1930_and_portal','REVIEW','Official government sources confirm cybercrime.gov.in and 1930 (financial cyber fraud). A human must check they are rendered correctly in the video.','human')
    if manifest.exists():
        try:
            with manifest.open(encoding='utf-8-sig',newline='') as fh:
                rows=list(csv.DictReader(fh))
            add('asset_manifest','REVIEW',f'{len(rows)} manifest rows; manually inspect asset origin, licenses and official logo authorization','human')
        except Exception as e:add('asset_manifest','FAIL',str(e))
    else:add('asset_manifest','REVIEW','assets/manifest.csv missing; cannot audit asset attribution','human')
    for cid,detail in [
        ('logo', 'College logo must be supplied by the institution, present and undistorted on the end card'),
        ('disclosure','End card must show exactly: Created with AI agents — LY Agentic AI Lab'),
        ('safe_zones','All important text should avoid top 250px and bottom 350px, per assignment'),
        ('no_real_likeness','No synthetic real student, faculty, or public-figure face/voice'),
        ('mobile_readability','Check captions, contrast, clipped text, warning labels and contact detail on a phone'),
        ('human_safety_approval','Category A safety brief requires mandatory human review before final export')]:
        add(cid,'REVIEW',detail,'human')
    if shutil.which('ffmpeg'):
        audio=analyse_audio(video)
        if audio:
            lufs=audio['integrated_lufs'];peak=audio['true_peak_dbfs']
            rule('integrated_loudness',-16<=lufs<=-12,f'{lufs:.1f} LUFS (assignment target about -14 LUFS)',severity='minor')
            rule('no_audio_clipping',peak<0,f'true peak {peak:.1f} dBFS',severity='major')
        else:add('audio_loudness','REVIEW','FFmpeg could not extract EBU R128 loudness; inspect audio manually','human')
    return checks

def main():
    parser=argparse.ArgumentParser(description='ScamShield read-only Critic / QA')
    parser.add_argument('--video',default='outputs/scamshield_with_college_logo.mp4')
    parser.add_argument('--srt',default=None)
    parser.add_argument('--report',default='outputs/qa_report.json')
    args=parser.parse_args()
    def locate(x):
        p=Path(x);return p if p.is_absolute() else ROOT/p
    video=locate(args.video)
    srt=locate(args.srt) if args.srt else video.with_suffix('.srt')
    # Logo-overlay export has same timeline as final_polish; use its SRT as explicit fallback.
    if not srt.exists() and video.name=='scamshield_with_college_logo.mp4':
        fallback=ROOT/'outputs/scamshield_final_polish.srt'
        if fallback.exists():srt=fallback
    try: checks=evaluate(video,srt)
    except Exception as e:checks=[{'id':'critic_execution','status':'FAIL','detail':str(e),'method':'machine','severity':'major'}]
    counts={s:sum(c['status']==s for c in checks) for s in ('PASS','FAIL','REVIEW')}
    outcome='FAIL' if counts['FAIL'] else 'HUMAN_REVIEW_REQUIRED' if counts['REVIEW'] else 'PASS'
    report={'generated_utc':datetime.now(timezone.utc).isoformat(),'video':str(video),'subtitle_file':str(srt),'overall_status':outcome,'counts':counts,
            'checks':checks,'note':'Automated tests do not verify visual claims or constitute mandatory Category A human approval. Critic is assessment only; no automatic repair loop implemented.'}
    output=locate(args.report);output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
    for c in checks:print(c['status'].ljust(6),c['id'],'—',c['detail'])
    print('SUMMARY',outcome,counts,'\nReport:',output)
    return 2 if counts['FAIL'] else 0
if __name__=='__main__':raise SystemExit(main())
