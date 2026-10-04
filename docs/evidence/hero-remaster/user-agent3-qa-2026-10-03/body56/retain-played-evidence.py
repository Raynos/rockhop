"""Copy only hash-pinned frames from continuous playback into stable evidence."""
import hashlib,json,shutil
from pathlib import Path
out=Path(__file__).resolve().parent;report=json.loads((out/'playback.json').read_text());dest=out/'played';dest.mkdir(exist_ok=True)
for frame in [*report['playedFrames'],*report['movingPlayedFrames']]:
 source=out/'tmp/played'/frame['file'];assert hashlib.sha256(source.read_bytes()).hexdigest()==frame['sha256'];shutil.copy2(source,dest/frame['file']);assert hashlib.sha256((dest/frame['file']).read_bytes()).hexdigest()==frame['sha256']
print('Preserved',len(report['playedFrames'])+len(report['movingPlayedFrames']),'byte-identical played frames')
