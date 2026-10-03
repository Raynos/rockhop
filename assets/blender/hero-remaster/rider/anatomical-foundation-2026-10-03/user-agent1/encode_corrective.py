"""Encode/verify exact paired native corrective review movies without audio."""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path

ap = argparse.ArgumentParser(description=__doc__)
ap.add_argument('--review', required=True)
a = ap.parse_args(); directory = Path(a.review).resolve()
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
receipt = directory / 'movies.json'
if receipt.exists():
    raise RuntimeError('Frozen movie receipt exists')
render_path = directory / 'native-review.json'; render = json.loads(render_path.read_text())
movies = []
for view in render['views']:
    file = directory / ('native-' + view['name'] + '-before-after.mp4')
    if not file.exists():
        subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-n', '-framerate', '12', '-i',
            str(Path(view['folders']['before']) / '%04d.png'), '-framerate', '12', '-i',
            str(Path(view['folders']['after']) / '%04d.png'), '-filter_complex', '[0:v][1:v]hstack=inputs=2[v]',
            '-map', '[v]', '-c:v', 'libx264', '-crf', '20', '-pix_fmt', 'yuv420p', '-an', str(file)], check=True)
    probe = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries',
        'stream=codec_type,codec_name,width,height,r_frame_rate,nb_frames,duration', '-show_entries',
        'format=duration,size', '-of', 'json', str(file)], text=True))
    streams = probe['streams']; assert len(streams) == 1
    s = streams[0]; assert s['codec_type'] == 'video' and s['width'] == 1024 and s['height'] == 768
    assert s['r_frame_rate'] == '12/1' and int(s['nb_frames']) == render['framesPerFilm']
    assert abs(float(s['duration']) - render['framesPerFilm'] / 12) < 1e-6
    frames = {}
    for state, folder in view['folders'].items():
        files = sorted(Path(folder).glob('*.png')); assert len(files) == render['framesPerFilm']
        frames[state] = {p.name: sha(p) for p in files}
    movies.append({'view': view['name'], 'path': str(file), 'sha256': sha(file), 'bytes': file.stat().st_size,
        'ffprobe': probe, 'sourceFrameSHA256': frames, 'panels': 'BeforeLEFT/afterRIGHT'})
report = {'status': 'UNACCEPTED played native local corrective movies; root judges', 'nativeReviewSHA256': sha(render_path),
    'masterSHA256': render['masterSHA256'], 'poseDriverSHA256': render['poseDriverSHA256'],
    'expandedDriverSHA256': render['expandedDriverSHA256'], 'encoderSHA256': sha(__file__), 'movies': movies,
    'limits': render['limits']}
receipt.write_text(json.dumps(report, indent=2) + '\n')
print('CORRECTIVE_MOVIES', sha(receipt), [(m['view'], m['sha256']) for m in movies], flush=True)
