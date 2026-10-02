"""Verify frozen neutral inputs and compose matched actual movie evidence.

CPU-only, no source/art changes. Parent must separately inspect decoded frames.
"""
from pathlib import Path
import copy
import hashlib
import json
import struct
import subprocess
from PIL import Image, ImageDraw

R = Path('/Users/raynos/projects/games/rockhop')
E = R / 'docs/evidence/hero-remaster/one-rider-v2/source-preserving-garment186'
PRIVATE = Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2')
O = PRIVATE / 'source-preserving-garment186/parent-review'
assert not O.exists(), 'Preserve completed review evidence'
O.mkdir(parents=True)
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()

def glb(p):
    raw = Path(p).read_bytes()
    n = struct.unpack_from('<I', raw, 12)[0]
    return json.loads(raw[20:20+n]), raw[20+n:]

freeze = json.loads((E / 'render/freeze.json').read_text())
for rec in freeze['files']:
    p = Path(rec['path'])
    assert p.stat().st_size == rec['bytes'] and sha(p) == rec['sha256'], str(p)
prep = json.loads((E / 'render/preparation.json').read_text())
source, source_bin = glb(prep['source'])
neutral, neutral_bin = glb(prep['neutralGLB'])
expected = copy.deepcopy(source)
expected.pop('skins', None)
expected.pop('animations', None)
for node in expected['nodes']:
    node.pop('skin', None)
assert expected == neutral and source_bin == neutral_bin
assert sha(prep['source']) == prep['sourceSHA256']
assert sha(prep['neutralGLB']) == prep['neutralSHA256']
old = Path(prep['settingsRecipe']).read_text()
new = (R / 'assets/blender/hero-remaster/rider/one-rider-v2/source-preserving-garment186/render/render.py').read_text()
assert new.replace(str(PRIVATE / 'source-preserving-garment186/render'), str(PRIVATE / 'clean-upper-shell01/continuous-sculpt179')).replace(str(E / 'render'), str(R / 'docs/evidence/hero-remaster/one-rider-v2/clean-upper-shell01/continuous-sculpt179')) == old
films = []
for i, mode in enumerate(['pbr', 'gray']):
    movie = E / f'render/{mode}-turntable.mp4'
    playback = json.loads((E / f'parent-playback/played-{i}.json').read_text())
    assert playback['SHA256'] == sha(movie)
    assert playback['video']['ended'] and playback['video']['muted']
    assert playback['video']['duration'] == 4 and not playback['errors']
    assert playback['video']['error'] is None
    decoded = O / f'decoded-{mode}'
    decoded.mkdir()
    subprocess.run(['/opt/homebrew/bin/ffmpeg', '-v', 'error', '-threads', '2', '-i', str(movie), str(decoded / '%02d.png')], check=True)
    images = sorted(decoded.glob('*.png'))
    assert len(images) == 24
    for start in [0, 12]:
        canvas = Image.new('RGB', (800, 750), '#222222')
        draw = ImageDraw.Draw(canvas)
        for j, p in enumerate(images[start:start+12]):
            im = Image.open(p).convert('RGB').resize((200, 225))
            x, y = (j % 4)*200, (j // 4)*250
            canvas.paste(im, (x, y))
            draw.text((x+3, y+229), f'{mode} frame {j+start} / {(j+start)/6:.3f}s', fill='white')
        canvas.save(O / f'{mode}-aspect-correct-{start}.jpg', quality=92)
    before = R / f'docs/evidence/hero-remaster/one-rider-v2/clean-upper-shell01/neutral-control179/CONTROL-neutral-{mode}-turntable.mp4'
    header = Image.new('RGB', (800, 50), '#222222')
    draw = ImageDraw.Draw(header)
    draw.text((12, 7), 'SOURCE C19 BEFORE', fill='white')
    draw.text((412, 7), 'LOCAL HOOD INDEX REPAIR', fill='white')
    draw.text((12, 28), 'Matched actual neutral orbit; hips / moving poses unresolved', fill='#ffbb88')
    hp = O / f'{mode}-header.png'
    header.save(hp)
    out = E / f'matched-before-after-{mode}.mp4'
    assert not out.exists()
    subprocess.run(['/opt/homebrew/bin/ffmpeg', '-v', 'error', '-threads', '2', '-i', str(before), '-threads', '2', '-i', str(movie), '-loop', '1', '-i', str(hp), '-filter_complex', '[0:v][1:v]hstack=inputs=2[b];[2:v][b]vstack=inputs=2[v]', '-map', '[v]', '-t', '4', '-r', '6', '-c:v', 'libx264', '-threads', '2', '-pix_fmt', 'yuv420p', '-crf', '19', str(out)], check=True)
    films.append({'mode': mode, 'before': str(before), 'beforeSHA256': sha(before), 'after': str(movie), 'afterSHA256': sha(movie), 'comparison': str(out), 'comparisonSHA256': sha(out), 'decodedFrames': 24})
result = {
    'status': 'INPUTS_PLAYBACK_AND_MATCHED_COMPOSITION_VERIFIED_PARENT_VISUAL_JUDGMENT_PENDING',
    'frozenFilesVerified': len(freeze['files']),
    'freezeSHA256': sha(E / 'render/freeze.json'),
    'sourceSHA256': prep['sourceSHA256'],
    'neutralSHA256': prep['neutralSHA256'],
    'jsonOnlyNeutralDerivationExact': True,
    'matchedRenderRecipeExceptPathsExact': True,
    'films': films,
    'privateDecodedSheets': str(O),
    'limits': 'Neutral standing appearance only. No moving pose, hip, grip/sole, neck motion, target7/8, game or mobile acceptance. Comparison composition does not alter source frames or geometry.',
}
(E / 'parent-review.json').write_text(json.dumps(result, indent=2)+'\n')
print(json.dumps({'verifiedFrozenFiles': len(freeze['files']), 'actualDecodedFrames': 48, 'privateSheets': str(O)}))
