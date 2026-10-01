"""Verify and encode matched gray turntables; no appearance acceptance implied."""
from pathlib import Path
import hashlib, json, subprocess
from PIL import Image, ImageDraw

repo = Path('/Users/raynos/projects/games/rockhop')
out = repo / 'docs/evidence/hero-remaster/one-rider-v2/garment-rebuild01/gray-fixture01'
report = json.loads((out / 'render-report.json').read_text())
assert len(report['rows']) == 146
for row in report['rows']:
    path = out / row['label'] / f"{row['frame']:04d}.png"
    assert hashlib.sha256(path.read_bytes()).hexdigest() == row['sha256']
    assert Image.open(path).size == (384, 512)
for frame in range(73):
    a, b = [next(r for r in report['rows'] if r['label'] == label and r['frame'] == frame)
            for label in ['source34', 'fit01']]
    assert a['camera'] == b['camera'] and a['cameraRotation'] == b['cameraRotation']

movies = []
for label in ['source34', 'fit01']:
    target = out / f'{label}-gray-turntable.mp4'
    assert not target.exists()
    subprocess.run(['ffmpeg', '-v', 'error', '-threads', '2', '-framerate', '12',
                    '-i', str(out / label / '%04d.png'), '-frames:v', '72', '-an',
                    '-c:v', 'libx264', '-threads', '2', '-crf', '20',
                    '-pix_fmt', 'yuv420p', '-movflags', '+faststart', str(target)], check=True)
    probe = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-count_frames',
                        '-show_streams', '-of', 'json', str(target)], text=True))
    assert len(probe['streams']) == 1
    stream = probe['streams'][0]
    assert stream['codec_type'] == 'video' and int(stream['nb_read_frames']) == 72
    assert float(stream['duration']) == 6
    movies.append({'file': target.name, 'sha256': hashlib.sha256(target.read_bytes()).hexdigest(),
                   'frames': 72, 'seconds': 6, 'audioStreams': 0})

def board(indices, name, title):
    cols = 3
    sheet = Image.new('RGB', (1152, 48 + ((len(indices)+cols-1)//cols)*282), '#17191d')
    draw = ImageDraw.Draw(sheet)
    draw.text((12, 12), title, fill='white')
    for n, frame in enumerate(indices):
        x, y = (n%cols)*384, 48+(n//cols)*282
        for side, label in enumerate(['source34', 'fit01']):
            im = Image.open(out / label / f'{frame:04d}.png').convert('RGB')
            sheet.paste(im.resize((192, 256)), (x+side*192, y+22))
            draw.text((x+side*192+5, y+4), f'{label} | frame {frame:02d}', fill='white')
    sheet.save(out / name, quality=92)

board([0,9,18,27,36,45,54,63,72], 'nine-angle-comparison.jpg',
      'MATCHED GRAY | source34 / incomplete fit01 | no stitching, texture or motion pass')
for start in range(0,72,12):
    board(list(range(start,start+12)), f'ordered-{start:02d}-{start+11:02d}.jpg',
          'ORDERED MOVIE FRAMES | source34 / unstitched fit01 | neutral rest diagnostic')
(out / 'archive-report.json').write_text(json.dumps({
    'sourceFrameHashesVerified': 146, 'matchedCameraPairs': 73, 'movies': movies,
    'orderedBoards': 6, 'extraElevatedFrameNotInMovies': 72,
    'limits': 'CPU gray rest geometry fixture only; no seated deformation or PBR/mockup grade.'
}, indent=2)+'\n')
print(json.dumps({'verifiedFrames':146, 'movies':movies, 'orderedBoards':6}))
