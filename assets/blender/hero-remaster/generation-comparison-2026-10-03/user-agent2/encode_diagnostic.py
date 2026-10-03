"""Label derived frames without changing source pixels; encode silent paired video."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

from PIL import Image, ImageDraw, ImageFont

parser = argparse.ArgumentParser()
parser.add_argument('--orbit', required=True)
parser.add_argument('--model-label', required=True)
parser.add_argument('--movie', required=True)
args = parser.parse_args()
root = Path(args.orbit)
movie = Path(args.movie)
report = json.loads((root / 'orbit.json').read_text())
if movie.exists() or any((root / (family + '-labeled')).exists() for family in ['canonical', 'donor']):
    raise FileExistsError('Fresh derived frame/movie destinations required')
for family in ['canonical', 'donor']:
    rows = [row for row in report['rows'] if row['family'] == family]
    if sorted(row['frame'] for row in rows) != list(range(48)):
        raise ValueError('Incomplete or duplicate source frame family')
    for row in rows:
        if hashlib.sha256(Path(row['path']).read_bytes()).hexdigest() != row['sha256']:
            raise ValueError('Pinned source frame changed')
font = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf', 16)
for family, title, caption in [
        ('canonical', 'Neutral grey, lighting on', 'Same geometry, camera and normals'),
        ('donor', 'Sampled colour, lighting off', 'Emission only; no PBR or shading')]:
    output = root / (family + '-labeled')
    output.mkdir()
    files = sorted((root / family).glob('*.png'))
    if len(files) != 48:
        raise ValueError('Expected complete 48-frame family')
    for path in files:
        original = Image.open(path).convert('RGB')
        if original.size != (320, 320):
            raise ValueError('Expected 320-square original frame')
        frame = Image.new('RGB', (320, 384), (20, 25, 33))
        frame.paste(original, (0, 32))
        draw = ImageDraw.Draw(frame)
        draw.text((12, 8), title, font=font, fill='white')
        draw.text((12, 358), caption, font=font, fill='white')
        if frame.crop((0, 32, 320, 352)).tobytes() != original.tobytes():
            raise ValueError('Labeling changed original rendered pixels')
        frame.save(output / path.name)
movie.parent.mkdir(parents=True, exist_ok=True)
subprocess.run(['ffmpeg', '-n', '-loglevel', 'error', '-framerate', '8',
                '-i', str(root / 'canonical-labeled/%03d.png'), '-framerate', '8',
                '-i', str(root / 'donor-labeled/%03d.png'), '-filter_complex',
                '[0:v][1:v]hstack=inputs=2[v]', '-map', '[v]', '-an', '-c:v', 'libx264',
                '-crf', '20', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', str(movie)], check=True)
probe = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries',
                                          'stream=codec_type,codec_name,width,height,avg_frame_rate,nb_frames:format=duration,size',
                                          '-of', 'json', str(movie)], text=True))
if (len(probe['streams']) != 1 or probe['streams'][0]['codec_type'] != 'video' or
        probe['streams'][0]['nb_frames'] != '48' or
        probe['streams'][0]['avg_frame_rate'] != '8/1' or
        float(probe['format']['duration']) != 6.0):
    raise ValueError('Movie must have 48 video frames and no audio')
print(json.dumps({'movie': str(movie), 'sha256': hashlib.sha256(movie.read_bytes()).hexdigest(),
                  'bytes': movie.stat().st_size, 'ffprobe': probe}))
