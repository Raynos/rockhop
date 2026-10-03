"""Verify the complete silent moving contact-label receipt."""
import hashlib
import json
import subprocess
import sys
from pathlib import Path
folder = Path(sys.argv[1]).resolve(); report_file = folder / 'review.json'; review = json.loads(report_file.read_text())
file = folder / 'labeled-contact-patches-v1.mp4'; sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
if (folder / 'movie.json').exists():
    raise RuntimeError('Frozen contact film receipt exists')
if not file.exists():
    subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-n', '-framerate', '6', '-i', str(folder / '%04d.png'),
        '-c:v', 'libx264', '-crf', '18', '-pix_fmt', 'yuv420p', '-an', '-video_track_timescale', '12000', str(file)], check=True)
probe = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries',
    'stream=codec_type,codec_name,width,height,r_frame_rate,nb_frames,duration', '-show_entries', 'format=duration,size', '-of', 'json', str(file)], text=True))
assert len(probe['streams']) == 1
s = probe['streams'][0]; count = len(review['frames'])
assert s['codec_type'] == 'video' and [s['width'], s['height']] == [512, 768] and s['r_frame_rate'] == '6/1'
assert int(s['nb_frames']) == count and abs(float(s['duration']) - count / 6) < .001
subprocess.run(['ffmpeg', '-v', 'error', '-i', str(file), '-f', 'null', '-'], check=True)
pts = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-select_streams', 'v', '-show_entries',
    'frame=best_effort_timestamp_time', '-of', 'json', str(file)], text=True))
assert len(pts['frames']) == count
for i, frame in enumerate(pts['frames']):
    assert abs(float(frame['best_effort_timestamp_time']) - i / 6) < 1e-6
receipt = {'status': 'UNACCEPTED played contact-label proposals; root judges', 'path': str(file), 'sha256': sha(file), 'bytes': file.stat().st_size,
    'reviewSHA256': sha(report_file), 'encoderSHA256': sha(__file__), 'candidateGLBSHA256': review['candidateGLBSHA256'], 'pins': review['pins'],
    'ffprobe': probe, 'completeDecode': True, 'presentationTimestampsVerified': True, 'minimumWholeRiderNormalizedBorder': review['minimumWholeRiderNormalizedBorder'],
    'limits': review['limits'] + ['Actual05 GLTFLoader patch positions overlay native05 master. Native full weights and exported normalized four-weight skinning may differ; this film labels patches and does not measure their fit.']}
(folder / 'movie.json').write_text(json.dumps(receipt, indent=2) + '\n'); print(json.dumps(receipt))
