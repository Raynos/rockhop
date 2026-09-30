"""Pixel-only evidence layout and silent CPU video encoding for rejected trial."""
import hashlib,json,subprocess
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
REPO=Path('/Users/raynos/projects/games/rockhop')
BASE='one-rider-v2/glove-cleanup/ring-loft-trial1'
OUT=REPO/'docs/evidence/hero-remaster'/BASE
RUN=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1')/BASE
inspection=json.loads((OUT/'inspection.json').read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
for row in inspection['views']+inspection['motion']:assert sha(Path(row['file']))==row['sha256']
font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',20)
board=Image.new('RGB',(6*320,2*365),(24,27,31));draw=ImageDraw.Draw(board)
for r,mode in enumerate(['gray','pbr']):
    for s,side in enumerate([1,-1]):
        for v,view in enumerate(['front','profile','back']):
            col=s*3+v;im=Image.open(RUN/f'glove-{side}-{view}-{mode}.png').convert('RGB');im.thumbnail((320,320),Image.Resampling.LANCZOS)
            board.paste(im,(col*320,r*365+45));draw.text((col*320+4,r*365+8),f'{side:+d} {view} / {mode}',font=font,fill='white')
board.save(OUT/'rejected-glove-gray-pbr.jpg',quality=95,subsampling=0)
combined=RUN/'motion-combined';combined.mkdir(exist_ok=True)
for frame in range(36):
    canvas=Image.new('RGB',(960,520),(24,27,31));d=ImageDraw.Draw(canvas)
    for col,side in enumerate([1,-1]):
        im=Image.open(RUN/f'motion-{side}-{frame:04d}.png').convert('RGB');im.thumbnail((480,480),Image.Resampling.LANCZOS)
        canvas.paste(im,(col*480,40));d.text((col*480+8,8),f'Temporary seam rig {side:+d} / {frame/12:.2f}s',font=font,fill='white')
    canvas.save(combined/f'{frame:04d}.png')
video=OUT/'temporary-seam-motion.mp4'
if video.exists():raise RuntimeError('Frozen video exists')
command=['/opt/homebrew/bin/ffmpeg','-hide_banner','-loglevel','error','-framerate','12','-i',str(combined/'%04d.png'),'-c:v','libx264','-crf','20','-pix_fmt','yuv420p','-threads','4','-movflags','+faststart',str(video)]
subprocess.run(command,check=True,timeout=60)
probe=subprocess.run(['/opt/homebrew/bin/ffprobe','-v','error','-show_entries','stream=codec_name,codec_type,width,height,nb_frames,r_frame_rate,duration','-of','json',str(video)],check=True,capture_output=True,text=True)
streams=json.loads(probe.stdout)['streams'];assert len(streams)==1 and streams[0]['codec_type']=='video' and int(streams[0]['nb_frames'])==36
(OUT/'verification.json').write_text(json.dumps({'status':'FAILED appearance; parent rejected slab palm and unnatural knuckle transition','verifiedStaticFrames':12,'verifiedMotionFrames':72,'video':{'file':str(video),'sha256':sha(video),'streams':streams,'command':command},'boardSHA256':sha(OUT/'rejected-glove-gray-pbr.jpg'),'sourcePreservationVerified':inspection['sourcePreservationVerifiedAfterFinal'],'rigScope':'temporary local seam test only; not final19bone/gameplay'},indent=2)+'\n')
print('REJECTED_TRIAL_EVIDENCE_VERIFIED',flush=True)
