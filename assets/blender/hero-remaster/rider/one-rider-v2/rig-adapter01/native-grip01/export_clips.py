"""CPU2 silent video encoding of literal ordered native deformation frames."""
import subprocess,json,hashlib,datetime
from pathlib import Path
ROOT=Path('/Users/raynos/projects/games/rockhop');RUN=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/rig-adapter01/native-grip01');OUT=ROOT/'docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/native-grip01'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
deadline=datetime.datetime.fromisoformat(json.loads((OUT/'setup.json').read_text())['hardDeadlineUTC']);clips=[]
for name in ['front','palm','profile']:
 remaining=(deadline-datetime.datetime.now(datetime.timezone.utc)).total_seconds()
 if remaining<=1:raise RuntimeError('SharedCPUbatchdeadline')
 target=OUT/f'actual-{name}-open-wrap-open.mp4';command=['/opt/homebrew/bin/ffmpeg','-v','error','-nostdin','-framerate','16','-i',str(RUN/name/'%03d.png'),'-an','-c:v','libx264','-threads','2','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',str(target)];subprocess.run(command,check=True,timeout=remaining)
 clips.append({'view':name,'file':str(target),'sha256':sha(target),'frames':33,'fps':16,'durationSeconds':33/16,'audio':False,'threads':2,'sourceFrameFolder':str(RUN/name)})
(OUT/'clips.json').write_text(json.dumps({'status':'Actual silent open-wrap-open CPU frame encodings; noacceptedgrip','clips':clips,'recipeSHA256':sha(Path(__file__))},indent=2)+'\n')
print('ACTUAL_THREE_CAMERA_CLIPS_FROZEN')
