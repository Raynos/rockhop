"""Preserve rendered pixels, label unaccepted derivative and encode no audio."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

from PIL import Image, ImageDraw, ImageFont


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


parser = argparse.ArgumentParser()
parser.add_argument('--orbit', required=True)
parser.add_argument('--movie', required=True)
args = parser.parse_args()
root, movie = Path(args.orbit), Path(args.movie)
report = json.loads((root / 'orbit.json').read_text())
assert sorted(row['frame'] for row in report['rows']) == list(range(48))
assert not movie.exists()
labels = root / 'labeled'
assert not labels.exists()
labels.mkdir()
font = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf', 16)
for row in report['rows']:
    path = Path(row['path'])
    assert sha(path) == row['SHA256']
    original = Image.open(path).convert('RGB')
    assert original.size == (512, 512)
    frame = Image.new('RGB', (512, 576), (20, 25, 33))
    frame.paste(original, (0, 32))
    draw = ImageDraw.Draw(frame)
    draw.text((12, 8), 'Hunyuan30step: finite-cell DERIVATIVE, unaccepted', font=font, fill='white')
    draw.text((12, 552), 'No cleanup, learned texture, fit or rig; root review', font=font, fill='white')
    assert frame.crop((0, 32, 512, 544)).tobytes() == original.tobytes()
    frame.save(labels / path.name)
movie.parent.mkdir(parents=True, exist_ok=True)
subprocess.run(['ffmpeg', '-n', '-loglevel', 'error', '-framerate', '8', '-i', str(labels / '%03d.png'),
                '-an', '-c:v', 'libx264', '-crf', '20', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', str(movie)], check=True)
probe = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries',
       'stream=codec_type,width,height,avg_frame_rate,nb_frames:format=duration,size', '-of', 'json', str(movie)], text=True))
assert len(probe['streams']) == 1 and probe['streams'][0]['codec_type'] == 'video'
assert probe['streams'][0]['nb_frames'] == '48' and probe['streams'][0]['avg_frame_rate'] == '8/1'
assert float(probe['format']['duration']) == 6.0
print(json.dumps({'accepted': False, 'movie': str(movie.resolve()), 'SHA256': sha(movie),
                  'recipeSHA256': sha(__file__), 'bytes': movie.stat().st_size, 'ffprobe': probe}), flush=True)
