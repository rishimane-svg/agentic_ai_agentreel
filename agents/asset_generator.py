"""ScamShield third-cut designed visuals (Pillow, no image API).

Run: python -m agents.asset_generator
Reads storyboard.json and generates 7 distinct 1080x1920 illustrated mockups.
No faces, official logos, external fonts, network or third-party photos needed.
"""
import csv
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'assets/images'
W, H = 1080, 1920
BG=(11,22,41); SURFACE=(21,42,65); PANEL=(28,55,78)
TEAL=(54,226,195); WHITE=(246,250,253); MUTED=(174,202,216)
RED=(250,106,107); AMBER=(255,202,91)


def font(n, bold=False):
    paths = ([
        '/System/Library/Fonts/Supplemental/Arial Bold.ttf',
        '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
    ] if bold else [
        '/System/Library/Fonts/Supplemental/Arial.ttf',
        '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
    ])
    for p in paths:
        if Path(p).exists():
            return ImageFont.truetype(p, n)
    return ImageFont.load_default()


def centered(d, text, y, size=46, color=WHITE, bold=True):
    d.text((W//2,y), text, anchor='mm', font=font(size,bold), fill=color)


def rounded(d, box, fill=SURFACE, outline=None, radius=35, width=3):
    d.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def pill(d, text, box, fill=PANEL, ink=WHITE, size=32):
    rounded(d, box, fill=fill, radius=23)
    d.text(((box[0]+box[2])/2, (box[1]+box[3])/2), text, anchor='mm', font=font(size,True), fill=ink)


def text_width(d, value, f):
    bb=d.textbbox((0,0),value,font=f)
    return bb[2]-bb[0]


def fit_text(d, value, max_width, start=60, minimum=25, bold=True):
    """Choose the largest usable font that fits the allotted panel width."""
    for size in range(start, minimum-1, -1):
        candidate=font(size,bold)
        if text_width(d,value,candidate)<=max_width:
            return candidate
    raise ValueError('Text cannot fit safe frame: '+value)


def safe_text(d, xy, value, width, size, fill, anchor=None, minimum=25):
    f=fit_text(d,value,width,size,minimum,True)
    d.text(xy,value,font=f,fill=fill,anchor=anchor)

def base(i, heading):
    im=Image.new('RGB',(W,H),BG)
    d=ImageDraw.Draw(im)
    d.ellipse((-330,-420,560,470),fill=(15,46,64))
    d.ellipse((670,1340,1480,2150),fill=(15,47,62))
    rounded(d,(64,262,1016,334),fill=SURFACE,radius=23)
    safe_text(d,(92,297),'SCAMSHIELD  /  STUDENT CYBER SAFETY',880,34,TEAL,anchor='lm')
    safe_text(d,(78,389),heading,924,65,WHITE)
    d.line((80,470,1000,470),fill=TEAL,width=6)
    # Avoid the bottom 350px platform overlay safe zone (y >= 1570).
    return im,d


def phone(d, x1=180,y1=475,x2=900,y2=1485):
    rounded(d,(x1,y1,x2,y2),fill=(4,12,28),outline=(92,144,167),radius=72,width=8)
    rounded(d,(x1+35,y1+55,x2-35,y2-40),fill=(242,248,250),radius=32)
    rounded(d,((x1+x2)//2-110,y1+15,(x1+x2)//2+110,y1+42),fill=(76,111,131),radius=15)
    return (x1+60,y1+100,x2-60,y2-80)


def scene1(d):
    rounded(d,(110,510,970,820),fill=SURFACE,radius=42)
    d.text((155,570),'NEW INTERNSHIP OFFER',font=font(48,True),fill=TEAL)
    d.text((155,675),'Selected instantly? Pay first?',font=font(39),fill=WHITE)
    rounded(d,(110,885,970,1240),fill=(64,41,59),radius=42)
    d.text((155,955),'"POLICE" VIDEO CALL',font=font(48,True),fill=AMBER)
    d.text((155,1065),'Threats and urgent demands?',font=font(38),fill=WHITE)
    pill(d,'KNOW THE WARNING SIGNS',(120,1260,960,1360),fill=(28,70,72),ink=TEAL,size=37)


def scene2(d):
    x1,y1,x2,y2=phone(d,140,470,940,1310)
    d.text((x1+44,y1+20),'Recruitment Chat',font=font(45,True),fill=(20,51,72))
    rounded(d,(x1+30,y1+100,x2-30,y1+395),fill=(226,235,244),radius=26)
    d.text((x1+55,y1+145),'Earn Rs 50,000/month!',font=font(42,True),fill=(15,45,72))
    d.text((x1+55,y1+217),'Pay Rs 5,000 fee first.',font=font(36),fill=(158,50,56))
    d.text((x1+55,y1+282),'Offer expires today!',font=font(32),fill=(158,50,56))
    pill(d,'FICTIONAL EXAMPLE',(x1+46,y1+440,x2-46,y1+518),fill=(255,231,190),ink=(111,67,14),size=29)
    pill(d,'UPFRONT FEE',(82,1320,384,1390),fill=(107,47,58),size=28)
    pill(d,'EASY MONEY',(405,1320,690,1390),fill=(107,47,58),size=28)
    pill(d,'URGENCY',(710,1320,1003,1390),fill=(107,47,58),size=28)


def scene3(d):
    rounded(d,(140,490,940,1335),fill=(8,18,36),outline=(81,110,134),radius=56,width=6)
    d.text((W//2,555),'VIDEO CALL',anchor='mm',font=font(43,True),fill=WHITE)
    d.ellipse((385,670,695,980),fill=(49,75,100))
    d.ellipse((477,725,603,850),fill=(151,178,193))
    d.rounded_rectangle((420,840,660,965),radius=70,fill=(151,178,193))
    centered(d,'Caller claims: POLICE',1080,44,AMBER)
    rounded(d,(200,1160,880,1315),fill=(88,36,49),radius=30)
    centered(d,'"Digital arrest"',1215,44)
    centered(d,'Send details now!',1280,37)
    pill(d,'FAKE AUTHORITY  •  FEAR  •  PRESSURE',(155,1340,925,1398),fill=(71,42,56),ink=WHITE,size=32)


def scene4(d):
    rounded(d,(70,510,525,1380),fill=(58,43,63),radius=35)
    rounded(d,(555,510,1010,1380),fill=(23,76,76),radius=35)
    safe_text(d,(297,586),'SUSPICIOUS',390,35,AMBER,anchor='mm')
    safe_text(d,(782,586),'VERIFY',390,39,TEAL,anchor='mm')
    for y,t in [(755,'Share OTP?'),(875,'Send password?'),(995,'Pay immediately?')]:
        d.text((100,y),t,font=font(34,True),fill=WHITE)
        d.text((493,y),'X',font=font(36,True),fill=RED,anchor='ra')
    for y,t in [(755,'Official site'),(875,'Known number'),(995,'Check identity')]:
        d.text((590,y),t,font=font(32,True),fill=WHITE)
        d.text((970,y),'OK',font=font(30,True),fill=TEAL,anchor='ra')
    pill(d,'NEVER SHARE CREDENTIALS',(130,1280,950,1355),fill=(26,67,73),ink=TEAL,size=35)


def scene5(d):
    rounded(d,(100,540,980,985),fill=SURFACE,radius=46)
    centered(d,'REPORT CYBERCRIME',620,45,TEAL)
    centered(d,'cybercrime.gov.in',780,61,WHITE)
    rounded(d,(100,1030,980,1385),fill=(33,75,78),radius=46)
    centered(d,'FINANCIAL CYBER FRAUD',1105,37,TEAL)
    centered(d,'1930',1215,124,WHITE)
    centered(d,'For financial cyber fraud',1334,31,WHITE)


def scene6(d):
    d.ellipse((245,545,835,1135),fill=(27,88,91))
    d.ellipse((300,600,780,1080),outline=TEAL,width=13)
    centered(d,'OK',845,150,WHITE)
    centered(d,'TAKE A MOMENT',1270,59,WHITE)
    centered(d,'VERIFY BEFORE YOU TRUST',1330,48,TEAL)


def scene7(d):
    centered(d,'SCAMSHIELD',620,78,WHITE)
    centered(d,'STAY SAFE ONLINE',695,43,TEAL)
    d.line((170,715,910,715),fill=TEAL,width=5)
    centered(d,'cybercrime.gov.in',905,57,TEAL)
    centered(d,'1930',1065,104,WHITE)
    centered(d,'For financial cyber fraud',1150,38,MUTED)
    rounded(d,(95,1370,985,1540),fill=SURFACE,radius=30)
    centered(d,'Created with AI agents —',1424,34,WHITE)
    centered(d,'LY Agentic AI Lab',1488,34,MUTED)

DRAW={1:scene1,2:scene2,3:scene3,4:scene4,5:scene5,6:scene6,7:scene7}
HEADINGS=['TWO SCAMS TO SPOT','FAKE INTERNSHIP TRAP','DIGITAL ARREST TRAP','PAUSE AND VERIFY','REPORT THROUGH OFFICIAL CHANNELS','THINK BEFORE YOU TRUST','STAY SAFE ONLINE']


def main():
    path=ROOT/'outputs/storyboard.json'
    data=json.loads(path.read_text(encoding='utf-8'))
    scenes=data.get('scenes',[])
    if len(scenes)!=7 or [s.get('scene_id') for s in scenes]!=list(range(1,8)):
        raise ValueError('Expected storyboard scenes 1..7')
    if scenes[0]['start_s']!=0 or scenes[-1]['end_s']!=59:
        raise ValueError('Storyboard must span 0–59 seconds')
    OUT.mkdir(parents=True,exist_ok=True)
    manifest=ROOT/'assets/manifest.csv'
    with manifest.open('w',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=['asset','source','license','method'])
        writer.writeheader()
        for scene in scenes:
            i=scene['scene_id']
            image,d=base(i,HEADINGS[i-1])
            DRAW[i](d)
            file=OUT/f'scene_{i:02d}.png'
            image.save(file,optimize=True)
            writer.writerow({'asset':str(file.relative_to(ROOT)), 'source':'local storyboard.json','license':'Original Pillow graphics, system font usage subject to OS font terms','method':'rule_based_visual_mockup'})
            print('Created:',file.relative_to(ROOT))
    print('Created 7 images at 1080x1920')
    print('Mode: rule_based_visual_mockups (NOT AI-generated images)')
    print('Manifest:',manifest.relative_to(ROOT))

if __name__=='__main__':
    main()
