"""Compose verified neutral-hand boards and encode silent seam motion; CPU only."""
import hashlib,json,subprocess
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
ROOT=Path('/Users/raynos/projects/games/rockhop')
BASE='one-rider-v2/glove-cleanup/neutral-assembly'
OUT=ROOT/'docs/evidence/hero-remaster'/BASE
RUN=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1')/BASE
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
inspection=json.loads((OUT/'inspection.json').read_text())
for row in inspection['views']+inspection['motion']:assert sha(Path(row['file']))==row['sha256']
font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',23)
small=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',19)
boards=[]
for scope,title in [('fullhand','NEUTRAL HANDS / source geometry preserved / parent review pending'),('wristjoin','SEWN WRISTS / actual shared-index loops / parent review pending')]:
    board=Image.new('RGB',(1440,1080),(24,27,31));draw=ImageDraw.Draw(board);draw.text((14,12),title,font=font,fill='white')
    for r,side in enumerate([1,-1]):
        for c,view in enumerate(['front','profile','back']):
            row=next(v for v in inspection['views'] if v['scope']==scope and v['side']==side and v['view']==view)
            im=Image.open(row['file']).convert('RGB');im.thumbnail((480,480),Image.Resampling.LANCZOS);board.paste(im,(c*480,72+r*500))
            draw.text((c*480+12,46+r*500),f'{side:+d} / {view}',font=small,fill='white')
    draw.text((14,1053),'No curl / no grip solve / no bake / no final19-bone character rig',font=small,fill='white')
    path=OUT/f'{scope}-gray-board.jpg';board.save(path,quality=95,subsampling=0);boards.append({'file':str(path),'sha256':sha(path)})
board=Image.new('RGB',(1440,770),(24,27,31));draw=ImageDraw.Draw(board)
draw.text((14,12),'BODY / hands replaced / original H21-4 head & hair REJECTED, new head pending',font=small,fill='white')
for c,view in enumerate(['front','profile','back']):
    row=next(v for v in inspection['views'] if v['scope']=='body' and v['view']==view)
    im=Image.open(row['file']).convert('RGB');im.thumbnail((480,640),Image.Resampling.LANCZOS);board.paste(im,(c*480,90));draw.text((c*480+12,58),view,font=font,fill='white')
path=OUT/'full-body-gray-board.jpg';board.save(path,quality=95,subsampling=0);boards.append({'file':str(path),'sha256':sha(path)})
combined=RUN/'motion-combined';combined.mkdir(exist_ok=True)
for frame in range(36):
    canvas=Image.new('RGB',(960,520),(24,27,31));d=ImageDraw.Draw(canvas)
    for col,side in enumerate([1,-1]):
        im=Image.open(RUN/f'motion-{side}-{frame:04d}.png').convert('RGB');im.thumbnail((480,480),Image.Resampling.LANCZOS);canvas.paste(im,(col*480,40));d.text((col*480+8,8),f'Neutral seam diagnostic {side:+d} / {frame/12:.2f}s',font=small,fill='white')
    canvas.save(combined/f'{frame:04d}.png')
video=OUT/'temporary-seam-motion.mp4'
if video.exists():raise RuntimeError('Frozen video exists')
command=['/opt/homebrew/bin/ffmpeg','-hide_banner','-loglevel','error','-framerate','12','-i',str(combined/'%04d.png'),'-c:v','libx264','-crf','20','-pix_fmt','yuv420p','-threads','4','-movflags','+faststart',str(video)]
subprocess.run(command,check=True,timeout=60)
streams=json.loads(subprocess.run(['/opt/homebrew/bin/ffprobe','-v','error','-show_entries','stream=codec_name,codec_type,width,height,nb_frames,r_frame_rate,duration','-of','json',str(video)],check=True,capture_output=True,text=True).stdout)['streams']
assert len(streams)==1 and streams[0]['codec_type']=='video' and int(streams[0]['nb_frames'])==36
(OUT/'verification.json').write_text(json.dumps({'status':'Neutral assembly evidence only; parent judgment pending; no bake','verifiedStaticFrames':15,'verifiedMotionFrames':72,'boards':boards,'video':{'file':str(video),'sha256':sha(video),'streams':streams,'command':command},'sourcePreservationVerified':inspection['sourcePreservationVerifiedAfterFinal'],'rigScope':'temporary local seam test; native anatomy weights remain in clean master; no final19bone/gameplay'},indent=2)+'\n')
print('NEUTRAL_ASSEMBLY_VISUAL_EVIDENCE_VERIFIED')
