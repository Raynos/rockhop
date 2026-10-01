"""Trim actual moving contact films at matched maximum-lean/landing events."""
from pathlib import Path
import json,subprocess,hashlib,sys
repo=Path('/Users/raynos/projects/games/rockhop');out=Path(sys.argv[1]) if len(sys.argv)>1 else repo/'docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/played-surfaces11';audit=json.loads((out/'surface-audit.json').read_text());events=[('maximum-forward',audit['maxLean']['positiveSamples'][0]),('maximum-backward',audit['maxLean']['negativeSamples'][0]),('landing-recovery',max(audit['twoWheelAirborneLandingsAndRecovery'],key=lambda x:x['sampledAirborneSeconds'])['landingSample'])];rows=[]
for focus in ['hands','feet']:
 for label,i in events:
  start=max(0,i/12-.8);dest=out/focus/(label+'.mp4');command=['ffmpeg','-v','error','-y','-ss',str(start),'-i',str(out/focus/'played.mp4'),'-t','2.4','-an','-c:v','libx264','-crf','18','-pix_fmt','yuv420p',str(dest)];subprocess.run(command,check=True)
  rows.append({'focus':focus,'event':label,'sample':i,'tick':(i+1)*10,'physicsTimeSeconds':(i+1)/12,'movieTrimStartSeconds':start,'movieDurationSeconds':2.4,'file':str(dest.relative_to(out)),'sha256':hashlib.sha256(dest.read_bytes()).hexdigest()})
(out/'events.json').write_text(json.dumps({'clips':rows,'limits':'Actual alternating camera films trimmed and reencoded, no pose/frame fabrication. Hands show even samples, feet odd samples, each six fps. Movie zero is first captured sample (hands physics .083333s, feet .166667s).'},indent=2)+'\n')
print('ACTUAL_EVENT_CLIPS_FROZEN')
