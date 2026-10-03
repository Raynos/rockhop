"""Encode and fully decode pinned silent textured native motion films."""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path
ap = argparse.ArgumentParser(description=__doc__); ap.add_argument('--review', required=True)
a = ap.parse_args(); directory = Path(a.review).resolve(); sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
receipt = directory / 'movies.json'
if receipt.exists():
    raise RuntimeError('Frozen movie receipt exists')
render_path = directory / 'native-review.json'; render = json.loads(render_path.read_text()); movies = []
for view in render['views']:
    file = directory / ('native-textured-' + view['name'] + '-v2.mp4')
    if not file.exists():
        subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-n', '-framerate', '12', '-i',
        str(Path(view['folder']) / '%04d.png'), '-c:v', 'libx264', '-crf', '18', '-pix_fmt', 'yuv420p', '-an', '-video_track_timescale', '12000', str(file)], check=True)
    probe = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries',
        'stream=codec_type,codec_name,width,height,r_frame_rate,nb_frames,duration', '-show_entries', 'format=duration,size', '-of', 'json', str(file)], text=True))
    assert len(probe['streams']) == 1; s = probe['streams'][0]
    assert s['codec_type'] == 'video' and [s['width'], s['height']] == [512, 768] and s['r_frame_rate'] == '12/1'
    assert int(s['nb_frames']) == render['framesPerFilm'] and abs(float(s['duration']) - render['framesPerFilm'] / 12) < .001
    subprocess.run(['ffmpeg', '-v', 'error', '-i', str(file), '-f', 'null', '-'], check=True)
    pts = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-select_streams', 'v', '-show_entries', 'frame=best_effort_timestamp_time', '-of', 'json', str(file)], text=True))
    assert len(pts['frames']) == render['framesPerFilm']
    for i, frame in enumerate(pts['frames']):
        assert abs(float(frame['best_effort_timestamp_time']) - i / 12) < 1e-6
    movies.append({'view': view['name'], 'path': str(file), 'sha256': sha(file), 'bytes': file.stat().st_size,
        'ffprobe': probe, 'expectedDisplayDurationS': render['framesPerFilm'] / 12,
        'streamDurationDifferenceS': float(s['duration']) - render['framesPerFilm'] / 12, 'completeDecode': True, 'presentationTimestampsVerified': True,
        'minimumWholeRiderNormalizedBorder': view['minimumNormalizedBorder']})
report = {'status': 'UNACCEPTED played recognizable textured native appearance01; root judges',
    'nativeReviewSHA256': sha(render_path), 'pins': render['pins'], 'encoderSHA256': sha(__file__), 'movies': movies, 'limits': render['limits']}
receipt.write_text(json.dumps(report, indent=2) + '\n'); print('APPEARANCE_MOVIES', sha(receipt), [(m['view'], m['sha256']) for m in movies], flush=True)
