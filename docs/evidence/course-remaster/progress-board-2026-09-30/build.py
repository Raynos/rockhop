"""Compose unchanged frames from archived played videos; no generated artwork."""
from pathlib import Path
import hashlib
import io
import json
import subprocess
from PIL import Image, ImageDraw, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
BASE = 'docs/evidence/course-remaster/baseline-clips/'
COURSE = 'docs/evidence/course-remaster/'
# Course, baseline video, latest accepted art video, clock, clip clock offset, change.
ROWS = [
 ('C1 Low Tide', 'c1-low-tide/clip.mp4', 'c1/brake-sightline/after/rookie-full/clip.mp4', 8.0, 0, 'Quay, workboats, sheds; full Coast remaster still open'),
 ('C2 Crane Hop', 'c2-crane-hop/clip.mp4', 'c2/pier-art/after/full-final/clip.mp4', 8.0, 0, 'Pier 2 supporting trestle and grounded landing fascia'),
 ('C3 Hull Breach', 'c3-hull-breach/clip.mp4', 'c3/breach-art/after/rookie-full/clip.mp4', 21.5, 0, 'Tapered wreck, layered steel and torn bulkhead'),
 ('A1 Sawdust', 'a1-sawdust/clip.mp4', 'a1/mill-complex/after/full/clip.mp4', 17.5, 0, 'Working mill landmark, stock and conveyor'),
 ('A2 Log Jam', 'a2-log-jam/clip.mp4', 'a2/jam-after.mp4', 25.25, 22.05, 'Log pivot, axle, cut ends and supported pile'),
 ('A3 Timberline', 'a3-timberline/clip.mp4', 'a3/loader-cab/after/full/clip.mp4', 21.0, 0, 'Framed loader cab, hydraulic boom and grapple'),
 ('D1 Dust Devil', 'd1-dust-devil/clip.mp4', 'd1/contact-road/after/rookie/clip.mp4', 8.6, 0, 'Four actual terrace tops and short entry faces'),
 ('D2 Conveyor', 'd2-conveyor/clip.mp4', 'd2/cart-run/after/full/clip.mp4', 29.0, 0, 'Dusted metal wagon tops, low rims and machinery'),
 ('D3 Rope Walk', 'd3-rope-walk/pro.mp4', None, 30.0, 0, 'No new graphics pass since this baseline; scene unchanged'),
 ('S1 Lift Line', 's1-lift-line/pro.mp4', 's1/route-read/after/pro/clip.mp4', 20.0, 0, 'Supported bridge, grounded lift frames and cable'),
 ('S2 Cornice', 's2-cornice/pro.mp4', 's2/cornice-landmark/after/full-pro/clip.mp4', 12.2, 0, 'True cornice undercut and layered far landing'),
 ('S3 Whiteout', 's3-whiteout/pro.mp4', 's3/after-pro.mp4', 11.0, 0, 'Cue timing only; no substantive environment remaster'),
]
FONT = '/System/Library/Fonts/Supplemental/Arial.ttf'
BOLD = '/System/Library/Fonts/Supplemental/Arial Bold.ttf'
def font(size, bold=False):
    return ImageFont.truetype(BOLD if bold else FONT, size)
def sample(relative, seconds):
    source = ROOT / relative
    probe = json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=avg_frame_rate,width,height','-of','json',str(source)]))['streams'][0]
    a,b = map(int,probe['avg_frame_rate'].split('/')); fps=a/b
    frame = round(seconds * fps)
    data = subprocess.check_output(['ffmpeg','-v','error','-i',str(source),'-vf',f'select=eq(n\\,{frame})','-frames:v','1','-f','image2pipe','-vcodec','png','-threads','1','-'])
    if not data:
        raise RuntimeError(f'No frame {frame} in {source}')
    shot = Image.open(io.BytesIO(data)).convert('RGB')
    return shot, {'video':relative, 'videoSha256':hashlib.sha256(source.read_bytes()).hexdigest(), 'frame':frame,'fps':fps,'videoTimeSeconds':frame/fps,'width':probe['width'],'height':probe['height']}

manifest = {'baselineCommit':'609293eaac58913420a1e06ca8fc530bfc907cc1','kind':'unchanged frames from actual played recordings','signedOffCourses':0,'rows':[], 'limits':[
 'Before is the saved 2026-09-29 start-of-remaster art baseline, after the first mechanical retarget; not the original accelerator-only demo.',
 'After is the latest accepted graphics capture for the pictured location, not a new capture of the current audio/hero/Pro candidates or deployed URL.',
 'The initial baseline uses high renderer quality; most later accepted captures use low. Camera, video cadence and viewport height also vary, so this is an art progress board, not a pixel-identical A/B.',
 'D3 repeats its baseline because no later course graphics change landed. S3 changed teaching cues, not environment art.',
 'New Blender tug and Alpine kit are unaccepted and excluded. No whole-course or physical-phone quality pass is implied.'
]}
for group, biome in enumerate(['Coast','Alpine','Quarry','Snowline']):
    board=Image.new('RGB',(1784,1648),'#0b2228');d=ImageDraw.Draw(board)
    d.text((24,20),f'ROCKHOP / {biome.upper()} / GRAPHICS PROGRESS',font=font(34,True),fill='#fff0cf')
    d.text((24,65),'Actual played frames / 0 of 12 complete remasters / 30 September 2026',font=font(23),fill='#b4cece')
    d.text((24,105),'BEFORE: start-of-remaster capture',font=font(26,True),fill='#b4cece')
    d.text((910,105),'AFTER: latest accepted art capture',font=font(26,True),fill='#ffcc72')
    for ri,row in enumerate(ROWS[group*3:group*3+3]):
        title,before,after,clock,offset,change=row
        before_image,bmeta=sample(BASE+before,clock)
        if after:
            after_image,ameta=sample(COURSE+after,clock-offset)
        else:
            after_image=before_image.copy();ameta=dict(bmeta,unchangedBaseline=True)
        y=148+ri*464
        d.text((24,y),f'{title} / recorded clock ~{clock:.2f}s',font=font(24,True),fill='#fff0cf')
        for x,shot in [(24,before_image),(910,after_image)]:
            fitted=ImageOps.contain(shot,(850,394),Image.Resampling.LANCZOS)
            board.paste(fitted,(x,y+34+(394-fitted.height)//2))
        d.text((24,y+431),change,font=font(22),fill='#b4cece')
        manifest['rows'].append({'course':title,'change':change,'recordingClockSeconds':clock,'afterVideoClockOffsetSeconds':offset,'before':bmeta,'after':ameta})
    d.text((24,1554),'Partial improvements only. High baseline vs mostly low later tier; camera/cadence vary.',font=font(22),fill='#ffcc72')
    d.text((24,1587),'D3: unchanged baseline. S3: cue-only change. New candidate assets are excluded.',font=font(22),fill='#b4cece')
    board.save(OUT/f'{group+1}-{biome.lower()}.jpg',quality=93,subsampling=0)
(OUT/'frames.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('Wrote four twelve-course boards and exact video/frame provenance.')
