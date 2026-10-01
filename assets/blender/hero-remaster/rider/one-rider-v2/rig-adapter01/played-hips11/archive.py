"""Freeze all original pixels and ordered decoded movie boards, including setup failure."""
from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import sys
from PIL import Image, ImageDraw

folder = Path(sys.argv[1]).resolve()
base = Path('/Users/raynos/projects/games/rockhop/docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/played-hips11')
private = Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/rig-adapter01/played-hips11/decoded-evidence') / folder.relative_to(base)
private.mkdir(parents=True, exist_ok=True)
frames = sorted((folder / 'frames').glob('*.png'))
assert len(frames) == 264
original = private / 'original'
original.mkdir(exist_ok=True)
receipt = []
for frame in frames:
    dest = original / frame.name
    if dest.exists():
        assert dest.read_bytes() == frame.read_bytes()
    else:
        shutil.copy2(frame, dest)
    receipt.append({'frame': frame.name, 'sha256': hashlib.sha256(frame.read_bytes()).hexdigest()})
decoded = private / 'decoded'
decoded.mkdir(exist_ok=True)
assert not list(decoded.glob('*.png'))
subprocess.run(['ffmpeg', '-v', 'error', '-threads', '2', '-i', str(folder / 'played.mp4'), '-threads', '2', str(decoded / '%04d.png')], check=True)
decoded_frames = sorted(decoded.glob('*.png'))
assert len(decoded_frames) == len(frames)
boards = []
for start in range(0, len(decoded_frames), 24):
    board = Image.new('RGB', (1920, 1800), (24,24,24))
    draw = ImageDraw.Draw(board)
    for k, frame in enumerate(decoded_frames[start:start+24]):
        im = Image.open(frame).convert('RGB')
        im.thumbnail((480,270))
        x, y = (k % 4)*480, (k // 4)*300
        board.paste(im, (x,y))
        draw.text((x+8,y+275), f'sample {start+k}', fill='white')
    dest = folder / f'decoded-{start//24:03d}.jpg'
    board.save(dest, quality=94)
    boards.append(dest.name)
(folder / 'frames-archive.json').write_text(json.dumps({'privateOriginalFrames':str(original),
    'privateDecodedFrames':str(decoded), 'originalFrames':receipt, 'decodedBoards':boards,
    'sourcePixelsExact':True, 'limits':'All264 actual frames retained. Movie decoded boards preserve ordered evidence; no repaint or pose substitution.'},indent=2)+'\n')
for frame in frames:
    frame.unlink()
(folder / 'frames').rmdir()
print(json.dumps({'folder':str(folder),'archivedFrames':len(frames),'decodedFrames':len(decoded_frames)}))
