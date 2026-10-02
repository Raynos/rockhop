"""Parent verifies matched frozen moving inputs and composes diagnostic clips."""
from pathlib import Path
import hashlib
import json
import struct
import subprocess
import sys
import numpy as np
from PIL import Image, ImageDraw

R = Path('/Users/raynos/projects/games/rockhop')
B = Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2')
E = R / 'docs/evidence/hero-remaster/one-rider-v2/source-preserving-garment187'
P = B / 'source-preserving-garment187/parent-review'
assert not P.exists(), 'Never overwrite completed parent evidence'
P.mkdir(parents=True)
sys.path.insert(0, str(R / 'assets/blender/hero-remaster/rider/one-rider-v2/candidate-handoff170'))
from map_candidate import GLB, worlds, resolved_materials
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
freeze = json.loads((E / 'freeze.json').read_text())
for rec in freeze['files']:
    p = Path(rec['path'])
    assert p.stat().st_size == rec['bytes'] and sha(p) == rec['sha256'], str(p)
source = GLB(B / 'source-preserving-garment185/operator/rider.glb')
candidate = GLB(B / 'candidate-handoff170/hood-fixed185-187/rider.glb')
baseline = GLB(B / 'rig-adapter01/body-bind34/rider.glb')
assert source.bin == candidate.bin
assert {k:v for k,v in source.j.items() if k != 'nodes'} == {k:v for k,v in candidate.j.items() if k != 'nodes'}
changed = []
for mi, mesh in enumerate(candidate.j['meshes']):
    for pi, primitive in enumerate(mesh['primitives']):
        other = baseline.j['meshes'][mi]['primitives'][pi]
        assert primitive['attributes'].keys() == other['attributes'].keys()
        for key, ai in primitive['attributes'].items():
            assert np.array_equal(candidate.array(ai), baseline.array(other['attributes'][key]))
        assert len(primitive.get('targets', [])) == len(other.get('targets', []))
        for target, control in zip(primitive.get('targets', []), other.get('targets', [])):
            assert target.keys() == control.keys()
            for key, ai in target.items():
                assert np.array_equal(candidate.array(ai), baseline.array(control[key]))
        a = candidate.array(primitive['indices']).reshape(-1, 3)
        b = baseline.array(other['indices']).reshape(-1, 3)
        ids = np.flatnonzero(np.any(a != b, axis=1)).tolist()
        if ids:
            changed.append({'mesh': mi, 'primitive': pi, 'slots': ids})
assert changed == [{'mesh': 0, 'primitive': 2, 'slots': [28,29,3813,3829,3847,3848,4105,4106]}]
cs, bs = candidate.j['skins'][0], baseline.j['skins'][0]
assert np.array_equal(candidate.array(cs['inverseBindMatrices']), baseline.array(bs['inverseBindMatrices']))
cw, bw = worlds(candidate.j), worlds(baseline.j)
assert all(np.array_equal(cw[a], bw[b]) for a,b in zip(cs['joints'], bs['joints']))
assert resolved_materials(candidate) == resolved_materials(baseline)
reports = [json.loads((E / f'{n}-capture-report.json').read_text()) for n in ['candidate', 'baseline']]
fixture = json.loads((B / 'source-preserving-garment187/fixture-three-families.json').read_text())
full = json.loads((B / 'basic-pose-gate158/fixture-v4-asymmetric-halfsteps.json').read_text())
assert fixture['frames'] == [f for family in ['overhead.L','forward','sit'] for f in full['frames'] if f['family'] == family]
assert len(fixture['frames']) == 579
for report, glb in zip(reports, [candidate, baseline]):
    assert report['sourceSHA256'] == sha(glb.path) and report['loaded'] == [sha(glb.path)]
    assert len(report['frames']) == 579 and not report['errors'] and 'failure' not in report
for frame, a, b in zip(fixture['frames'], *[r['frames'] for r in reports]):
    assert (a['family'], a['frame']) == (b['family'], b['frame']) == (frame['family'], frame['frame'])
    assert a['jointMatrices'] == b['jointMatrices']
    assert a['matrixError'] < 1e-8 and b['matrixError'] < 1e-8
films = []
for index, family in enumerate(['overhead.L', 'forward', 'sit']):
    for asset in ['candidate', 'baseline']:
        played = json.loads((E / f'parent-playback/played-{index*2+(asset=="baseline")}.json').read_text())
        movie = E / f'{asset}-{family}.mp4'
        assert played['SHA256'] == sha(movie) and played['video']['ended'] and played['video']['muted']
        assert not played['errors'] and played['video']['error'] is None
    # Preserve the six-view aspect and every encoded frame in the comparison.
    out = E / f'matched-before-after-{family}.mp4'
    assert not out.exists()
    subprocess.run(['/opt/homebrew/bin/ffmpeg','-v','error','-threads','2','-i',str(E/f'baseline-{family}.mp4'),'-threads','2','-i',str(E/f'candidate-{family}.mp4'),'-filter_complex','[0:v][1:v]hstack=inputs=2[v]','-map','[v]','-frames:v','193','-r','48','-an','-c:v','libx264','-threads','2','-crf','19','-pix_fmt','yuv420p','-movflags','+faststart',str(out)], check=True)
    # Nine diagnostic samples supplement full movies; never a passing pose gate.
    sheet = Image.new('RGB', (1440, 1020), '#222222')
    draw = ImageDraw.Draw(sheet)
    for j, offset in enumerate([0,24,48,72,96,120,144,168,192]):
        frame = B / f'source-preserving-garment187/candidate/frames/{index*193+offset:04d}.png'
        im = Image.open(frame)
        assert im.size == (1440, 960)
        x, y = (j%3)*480, (j//3)*340
        sheet.paste(im.convert('RGB').resize((480,320)), (x,y))
        draw.text((x+4,y+322), f'{family} / frame {offset} / {offset/48:.3f}s — UNACCEPTED', fill='white')
    sheet.save(P / f'{family}-diagnostic-nine.jpg', quality=93)
    films.append({'family': family, 'comparison': str(out), 'sha256': sha(out), 'frames': 193, 'fps': 48, 'beforeLeftAfterRight': True})
result = {'status':'MATCHED_EXPORTED_CONTROLS_VERIFIED_PARENT_MOVING_JUDGMENT_PENDING', 'frozenFilesVerified':len(freeze['files']), 'sourceSHA256':sha(source.path), 'candidateSHA256':sha(candidate.path), 'baselineSHA256':sha(baseline.path), 'sourceBINAndNonNodeJSONExact':True, 'allFivePrimitiveAttributesMorphsPBRAnd19BindsExactBaseline':True, 'changedIndices':changed, 'matched579WorldMatricesByteEqual':True, 'exact579FixtureRowsCopied':True, 'actualLoadedHashesVerified':True, 'sixSourceFilmsPlayedToEnd':True, 'comparisons':films, 'diagnosticSheets':str(P), 'limits':'Authored finite stress only. No actual Garage/physics/contact/mobile or continuous-time collision pass. Nine-frame sheets locate failures; they cannot pass anatomy or motion.'}
(E / 'parent-review.json').write_text(json.dumps(result, indent=2)+'\n')
print(json.dumps({'frozenFilesVerified':len(freeze['files']), 'matchedFrames':579, 'comparisons':len(films)}))
