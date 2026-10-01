"""Encode unchanged actual frame samples, retain all source pixels and receipts."""
from pathlib import Path
import hashlib
import json
import shutil
import subprocess
from PIL import Image, ImageDraw

repo=Path('/Users/raynos/projects/games/rockhop')
base=repo/'docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/body-bind11/sitting-multiangle01'
private=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/rig-adapter01/body-bind11/sitting-multiangle01/decoded-evidence')
manifest=json.loads((base/'fixture02/render-manifest.json').read_text())
assert manifest['sourceUnchanged'] and manifest['samplesPerAngle']==24
rows=[]
for name in ['front','side','rear-three-quarter']:
    folder=base/'fixture02'/name;movie=folder/'played.mp4';assert not movie.exists()
    subprocess.run(['ffmpeg','-v','error','-framerate','12','-i',str(folder/'frames/%04d.png'),
        '-c:v','libx264','-crf','18','-pix_fmt','yuv420p','-an',str(movie)],check=True)
    slow=folder/'half-speed.mp4'
    subprocess.run(['ffmpeg','-v','error','-i',str(movie),'-vf','setpts=2*PTS','-r','24',
        '-c:v','libx264','-crf','18','-pix_fmt','yuv420p','-an',str(slow)],check=True)
    decode=private/'fixture02'/name/'decoded';decode.mkdir(parents=True,exist_ok=True)
    subprocess.run(['ffmpeg','-v','error','-i',str(movie),str(decode/'%04d.png')],check=True)
    frames=sorted(decode.glob('*.png'));assert len(frames)==24
    board=Image.new('RGB',(1536,2688),(24,24,24));draw=ImageDraw.Draw(board)
    for i,p in enumerate(frames):
        im=Image.open(p).convert('RGB');im.thumbnail((384,420));x=(i%4)*384;y=(i//4)*448
        board.paste(im,(x,y));draw.text((x+8,y+425),f'{name} sample{i}',fill='white')
    board.save(folder/'decoded-all24.jpg',quality=94)
    probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(movie)],text=True))
    assert len(probe['streams'])==1 and probe['streams'][0]['codec_type']=='video'
    rows.append({'angle':name,'samples':24,'normalSeconds':float(probe['format']['duration']),
        'movieSHA256':hashlib.sha256(movie.read_bytes()).hexdigest(),'halfSpeedSHA256':hashlib.sha256(slow.read_bytes()).hexdigest(),
        'halfSpeedMeaning':'Same samples, presentation time doubled; duplication to24fps, no generated intermediate poses.'})
# Freeze exact source frames for both the initial mislocated fixture and the
# corrected fixture. Do not keep raw PNG families in the repository.
archives=[]
for prefix in ['', 'fixture02']:
    for name in ['front','side','rear-three-quarter']:
        folder=base/prefix/name;frames=sorted((folder/'frames').glob('*.png'));assert len(frames)==24
        archive=private/(prefix or 'initial-fixture')/name/'source';archive.mkdir(parents=True,exist_ok=True)
        hashes=[]
        for p in frames:
            dest=archive/p.name
            if dest.exists():assert dest.read_bytes()==p.read_bytes()
            else:shutil.copy2(p,dest)
            hashes.append({'name':p.name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
        receipt={'privateSourceFrames':str(archive),'frames':hashes,'sourcePixelsExact':True}
        (folder/'frames-archive.json').write_text(json.dumps(receipt,indent=2)+'\n');archives.append(receipt)
        for p in frames:p.unlink()
        (folder/'frames').rmdir()
(base/'fixture02/movies.json').write_text(json.dumps({'currentSourceSHA256':manifest['sourceSHA256'],
    'clips':rows,'limits':'Current source unmodified; authored diagnostic sitting motion with Blender LBS. Deformation and contact quality not accepted.'},indent=2)+'\n')
print('Encoded and decoded three current sitting angles; exact source frames archived')
