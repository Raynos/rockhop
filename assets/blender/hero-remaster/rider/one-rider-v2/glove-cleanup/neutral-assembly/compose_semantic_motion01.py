"""Pixel-only layout and silent encoding of one diagnostic correction."""
import hashlib,json,subprocess
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
ROOT=Path('/Users/raynos/projects/games/rockhop');BASE='one-rider-v2/glove-cleanup/neutral-assembly'
OUT=ROOT/'docs/evidence/hero-remaster'/BASE/'motion-correction01'
RUN=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1')/BASE/'motion-correction01'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
d=json.loads((OUT/'report.json').read_text())
for row in d['motion']+d['closeups']:assert sha(Path(row['file']))==row['sha256']
font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',18)
combined=RUN/'motion-combined';combined.mkdir(exist_ok=True)
for frame in range(36):
    canvas=Image.new('RGB',(960,520),(24,27,31));draw=ImageDraw.Draw(canvas)
    for c,side in enumerate([1,-1]):
        image=Image.open(RUN/f'motion-{side}-{frame:04d}.png').convert('RGB');image.thumbnail((480,480),Image.Resampling.LANCZOS);canvas.paste(image,(c*480,40));draw.text((c*480+8,8),f'Semantic correction {side:+d} / {frame/12:.2f}s / pending review',font=font,fill='white')
    canvas.save(combined/f'{frame:04d}.png')
film=Image.new('RGB',(1920,1152),(24,27,31))
for frame in range(36):
    image=Image.open(combined/f'{frame:04d}.png');image.thumbnail((320,180),Image.Resampling.LANCZOS);film.paste(image,((frame%6)*320,(frame//6)*192))
film.save(OUT/'all36-moving-filmstrip.jpg',quality=95,subsampling=0)
close=Image.new('RGB',(1920,750),(24,27,31));draw=ImageDraw.Draw(close)
for r,side in enumerate([1,-1]):
    for c,frame in enumerate([4,9,10,13,26,31]):
        image=Image.open(RUN/f'wrist-{side}-{frame:04d}.png').convert('RGB');image.thumbnail((320,320),Image.Resampling.LANCZOS);close.paste(image,(c*320,45+r*365));draw.text((c*320+4,8+r*365),f'{side:+d} frame {frame} / wrist extrema',font=font,fill='white')
close.save(OUT/'wrist-extrema-board.jpg',quality=95,subsampling=0)
compare=Image.new('RGB',(960,1040),(24,27,31));draw=ImageDraw.Draw(compare)
for r,base in enumerate([RUN.parent,RUN]):
    for c,side in enumerate([1,-1]):
        image=Image.open(base/f'motion-{side}-0010.png').convert('RGB');image.thumbnail((480,480),Image.Resampling.LANCZOS);compare.paste(image,(c*480,40+r*520));draw.text((c*480+4,8+r*520),('FAILED initial' if r==0 else 'CORRECTED pending')+f' / {side:+d} / frame10',font=font,fill='white')
compare.save(OUT/'frame10-failed-vs-correction.jpg',quality=95,subsampling=0)
video=OUT/'semantic-seam-motion.mp4'
if video.exists():raise RuntimeError('Frozen corrected video exists')
command=['/opt/homebrew/bin/ffmpeg','-hide_banner','-loglevel','error','-framerate','12','-i',str(combined/'%04d.png'),'-c:v','libx264','-crf','20','-pix_fmt','yuv420p','-threads','4','-movflags','+faststart',str(video)]
subprocess.run(command,check=True,timeout=60)
streams=json.loads(subprocess.run(['/opt/homebrew/bin/ffprobe','-v','error','-show_entries','stream=codec_name,codec_type,width,height,nb_frames,r_frame_rate,duration','-of','json',str(video)],check=True,capture_output=True,text=True).stdout)['streams']
assert len(streams)==1 and streams[0]['codec_type']=='video' and int(streams[0]['nb_frames'])==36
(OUT/'media-verification.json').write_text(json.dumps({'status':'Media bytes and framecount verified only; parent moving appearance judgment pending','verifiedMotionFrames':72,'verifiedCloseupFrames':12,'video':{'file':str(video),'sha256':sha(video),'streams':streams,'command':command},'boards':{p.name:sha(p) for p in OUT.glob('*.jpg')},'noBake':True},indent=2)+'\n')
print('SEMANTIC_CORRECTION_MEDIA_VERIFIED')
