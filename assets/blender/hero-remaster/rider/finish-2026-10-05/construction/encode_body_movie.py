"""Encode a silent played sequence with declared native command cadence."""
from pathlib import Path
import argparse,hashlib,json,subprocess
ap=argparse.ArgumentParser(description=__doc__)
for k in ['frames','metadata','movie','receipt']:ap.add_argument('--'+k,required=True)
a=ap.parse_args();frames,metadata,movie,receipt=[Path(getattr(a,k)).resolve()for k in ['frames','metadata','movie','receipt']]
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
r=json.loads(metadata.read_text());assert len(list(frames.glob('*.png')))==r['frames']
assert not movie.exists(),'Preserve completed review movie bytes'
movie.parent.mkdir(parents=True,exist_ok=True)
command=['/opt/homebrew/bin/ffmpeg','-v','error','-framerate',str(r['fps']),'-i',str(frames/'%04d.png'),'-an','-c:v','libx264','-preset','fast','-crf','17','-pix_fmt','yuv420p','-movflags','+faststart',str(movie)]
subprocess.run(command,check=True)
probe=json.loads(subprocess.check_output(['/opt/homebrew/bin/ffprobe','-v','error','-show_streams','-show_format','-of','json',str(movie)]))
assert len(probe['streams'])==1 and probe['streams'][0]['codec_type']=='video'
assert int(probe['streams'][0]['nb_frames'])==r['frames']
receipt.write_text(json.dumps({'status':'UNACCEPTED played silent native movie ready for parent','movie':str(movie),'movieSHA256':sha(movie),'bytes':movie.stat().st_size,'inputMetadataSHA256':sha(metadata),'encoderRecipeSHA256':sha(__file__),'fps':r['fps'],'frames':r['frames'],'durationS':float(probe['format']['duration']),'audioStreams':0,'sourcePins':r['inputs'],'mode':r['mode'],'yawNativeDegrees':r['yawNativeDegrees'],'limits':r['limits']},indent=2)+'\n')
print(movie,sha(movie),flush=True)
