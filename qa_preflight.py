"""Read-only machine-checkable preflight, not a semantic/factual Critic Agent.
Run from project root: python qa_preflight.py
"""
import json
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parent
VIDEO=ROOT/'outputs/scamshield_final_polish.mp4'
SCRIPT=ROOT/'outputs/script.json'
SRT=ROOT/'outputs/scamshield_final_polish.srt'


def probe(path):
    p=subprocess.run(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(path)],capture_output=True,text=True)
    if p.returncode:raise RuntimeError(p.stderr)
    return json.loads(p.stdout)


def main():
    checks=[]
    def check(label,passed,detail):checks.append({'check':label,'pass':bool(passed),'detail':detail})
    if not VIDEO.exists():
        print('Missing video; run python -m agents.editor');return
    data=probe(VIDEO);fmt=data['format'];streams=data['streams']
    v=next((s for s in streams if s.get('codec_type')=='video'),{})
    a=next((s for s in streams if s.get('codec_type')=='audio'),{})
    t=float(fmt['duration']);check('duration_30_to_60',30<=t<=60,f'{t:.2f}s')
    check('vertical_full_hd',v.get('width')==1080 and v.get('height')==1920,str((v.get('width'),v.get('height'))))
    check('h264_yuv420p',v.get('codec_name')=='h264' and v.get('pix_fmt')=='yuv420p',str((v.get('codec_name'),v.get('pix_fmt'))))
    check('aac_audio',a.get('codec_name')=='aac',str(a.get('codec_name')))
    check('48khz_stereo',a.get('sample_rate')=='48000' and a.get('channels')==2,str((a.get('sample_rate'),a.get('channels'))))
    rate=v.get('avg_frame_rate','0/1');numer,denom=map(int,rate.split('/'));fps=numer/denom if denom else 0
    check('25_or_30_fps',abs(fps-25)<0.01 or abs(fps-30)<0.01,str(fps))
    check('size_under_100mb',VIDEO.stat().st_size<=100_000_000,f'{VIDEO.stat().st_size/1e6:.1f} MB')
    check('caption_file_present',SRT.exists(),str(SRT))
    if SCRIPT.exists():
        sc=json.loads(SCRIPT.read_text(encoding='utf-8')).get('scenes',[])
        full=' '.join(x.get('voiceover','') for x in sc).lower()
        check('script_reports_cybercrime_portal','cybercrime.gov.in' in full,'Text match only; source verification separate')
        check('script_mentions_1930','1930' in full,'Text match only; source verification separate')
        check('seven_scenes',len(sc)==7,str(len(sc)))
    report={'video':str(VIDEO.relative_to(ROOT)),'checks':checks,
       'manual_review_required':['safe-zone rendered visuals on mobile','caption synchronization (timing estimated, not forced-aligned)',
       'official logo supplied and displayed unchanged','end-card AI disclosure readable',
       'all scene claims trace to official source documents','sound loudness near -14 LUFS and no clipping',
       'mandatory Category A human approval before submission'],
       'scope_note':'Automated engineering checks only, NOT a full factual critic or human sign-off'}
    out=ROOT/'outputs/qa_preflight.json';out.write_text(json.dumps(report,indent=2),encoding='utf-8')
    for c in checks:print(('PASS' if c['pass'] else 'FAIL'),c['check'],c['detail'])
    print('Preflight:',out,'; manual checks still required')
    if not all(c['pass'] for c in checks):raise SystemExit(1)

if __name__=='__main__':main()
