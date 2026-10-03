"""Encode/decode every continuous collision-off/on comparison frame."""
import hashlib
import json
import subprocess
import sys
from pathlib import Path
folder = Path(sys.argv[1]).resolve(); review_file = folder / 'review.json'; review = json.loads(review_file.read_text())
file = folder / 'matched-skin-collision-off-on-v1.mp4'; sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
if (folder / 'movie.json').exists():
    raise RuntimeError('Frozen sleeve movie receipt exists')
subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-n', '-framerate', '12', '-i', str(folder / '%04d.png'),
    '-c:v', 'libx264', '-crf', '18', '-pix_fmt', 'yuv420p', '-an', '-video_track_timescale', '12000', str(file)], check=True)
probe = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries',
    'stream=codec_type,codec_name,width,height,r_frame_rate,nb_frames,duration', '-show_entries', 'format=duration,size', '-of', 'json', str(file)], text=True))
assert len(probe['streams']) == 1; stream = probe['streams'][0]; count = len(review['frames'])
assert stream['codec_type'] == 'video' and [stream['width'], stream['height']] == review['resolution'] and stream['r_frame_rate'] == '12/1'
assert int(stream['nb_frames']) == count and abs(float(stream['duration']) - count/12) < .001
subprocess.run(['ffmpeg', '-v', 'error', '-i', str(file), '-f', 'null', '-'], check=True)
pts = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-select_streams', 'v', '-show_entries',
    'frame=best_effort_timestamp_time', '-of', 'json', str(file)], text=True))
assert len(pts['frames']) == count
for i, f in enumerate(pts['frames']):
    assert abs(float(f['best_effort_timestamp_time']) - i/12) < 1e-6
report = {'status': 'UNACCEPTED continuous native actual-response comparison, root judges folds', 'path': str(file), 'sha256': sha(file), 'bytes': file.stat().st_size,
    'reviewSHA256': sha(review_file), 'encoderSHA256': sha(__file__), 'pins': review['pins'], 'ffprobe': probe,
    'completeDecode': True, 'presentationTimestampsVerified': True, 'minimumNormalizedBorder': review['minimumNormalizedBorder'], 'limits': review['limits']}
(folder / 'movie.json').write_text(json.dumps(report, indent=2)+'\n'); print(json.dumps(report))
