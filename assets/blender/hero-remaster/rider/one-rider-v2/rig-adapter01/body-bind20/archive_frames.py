"""Retain every original played PNG privately and indexed film boards in evidence."""
from pathlib import Path
import hashlib
import json
import shutil
import sys
import subprocess
from PIL import Image, ImageDraw

repo = Path('/Users/raynos/projects/games/rockhop')
folder = Path(sys.argv[1]).resolve()
base = repo / 'docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/body-bind20'
relative = folder.relative_to(base)
archive = Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/rig-adapter01/body-bind20/decoded-evidence') / relative / 'frames'
frames = sorted((folder / 'frames').glob('*.png'))
assert len(frames) == 72
archive.mkdir(parents=True, exist_ok=True)
manifest = []
for frame in frames:
    dest = archive / frame.name
    if dest.exists():
        assert dest.read_bytes() == frame.read_bytes()
    else:
        shutil.copy2(frame, dest)
    manifest.append({'name': frame.name, 'sha256': hashlib.sha256(frame.read_bytes()).hexdigest()})
decoded=archive.parent/'decoded';decoded.mkdir(exist_ok=True);assert not list(decoded.glob('*.png'))
subprocess.run(['ffmpeg','-v','error','-threads','2','-i',str(folder/'played.mp4'),'-threads','2',str(decoded/'%04d.png')],check=True)
movieFrames=sorted(decoded.glob('*.png'));assert len(movieFrames)==72
boards = []
for start in range(0, len(frames), 24):
    board = Image.new('RGB', (1920, 1800), (24, 24, 24))
    draw = ImageDraw.Draw(board)
    for k, frame in enumerate(movieFrames[start:start + 24]):
        im = Image.open(frame).convert('RGB')
        im.thumbnail((480, 270))
        x, y = (k % 4) * 480, (k // 4) * 300
        board.paste(im, (x, y))
        draw.text((x + 8, y + 275), str(start+k), fill='white')
    dest = folder / ('decoded-%03d.jpg' % (start // 24))
    board.save(dest, quality=94)
    boards.append(dest.name)
(folder / 'frames-archive.json').write_text(json.dumps({'privateLosslessFrames': str(archive),
    'privateMovieDecodedFrames':str(decoded), 'frames': manifest, 'decodedBoards': boards,
    'limits': 'Every original frame retained exactly. Boards are ordered decoded movie frames; no repainting or pose substitution.'}, indent=2) + '\n')
for frame in frames:
    frame.unlink()
(folder / 'frames').rmdir()
print('Archived72 exact frames:', folder)
