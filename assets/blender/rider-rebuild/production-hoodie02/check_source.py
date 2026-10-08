"""Cheap source/pin/PBR intake only; never launches Blender or writes natives."""
import ast
import hashlib
import json
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
controls = json.loads((HERE/'controls.json').read_text())
for key, pin in controls['pins'].items():
    assert sha(ROOT/pin['path']) == pin['sha256'], ('Changed intake', key)
spec = json.loads((ROOT/controls['pins']['frozenInputs']['path']).read_text())
for key in ('selectedNative', 'originalDensePaint', 'nativeMaster', 'nativeArrays', 'geometricControlReceipt'):
    assert sha(ROOT/spec[key]['path']) == spec[key]['sha256'], ('Changed actual source', key)
for path in HERE.glob('*.py'):
    tree = ast.parse(path.read_text(), filename=str(path))
    if path.name == 'prepare_dense.py':
        calls = [ast.unparse(n.func) for n in ast.walk(tree) if isinstance(n, ast.Call)]
        assert not any('bake' in call or 'render' in call or 'smart_project' in call for call in calls)
receipt = json.loads((ROOT/controls['pins']['authorReceipt']['path']).read_text())
assert receipt['recipeSHA256'] == controls['pins']['repairAuthor']['sha256']
assert receipt['native']['sha256'] == controls['pins']['authoredNative']['sha256']
assert {k:v for k,v in receipt['inputs'].items() if k != 'targetHemZ'} == spec
original = ROOT/spec['originalDensePaint']['path']
with original.open('rb') as handle:
    magic, version, total, size, kind = struct.unpack('<5I', handle.read(20))
    assert magic == 0x46546C67 and version == 2 and total == original.stat().st_size
    assert kind == 0x4E4F534A
    gltf = json.loads(handle.read(size))
    binary_size, binary_kind = struct.unpack('<2I', handle.read(8))
    assert binary_kind == 0x004E4942
    binary_start = handle.tell()
    image_receipts = []
    for image in gltf['images']:
        assert image['mimeType'] == 'image/png'
        view = gltf['bufferViews'][image['bufferView']]
        handle.seek(binary_start+view.get('byteOffset', 0))
        data = handle.read(view['byteLength'])
        assert data[:8] == b'\x89PNG\r\n\x1a\n'
        pixels = list(struct.unpack('>2I', data[16:24]))
        assert pixels == controls['originalImagesExpectedPixels']
        image_receipts.append({'pixels': pixels, 'embeddedPNG_SHA256': hashlib.sha256(data).hexdigest(),
                               'bytes': len(data), 'gltfImage': image})
assert len(gltf['nodes']) == len(gltf['meshes']) == 1
node = gltf['nodes'][0]
assert node['mesh'] == 0 and not any(k in node for k in ('matrix','rotation','translation','scale','skin'))
primitive = gltf['meshes'][0]['primitives']
assert len(primitive) == 1
position = gltf['accessors'][primitive[0]['attributes']['POSITION']]
assert position['count'] == controls['originalPositionVertices']
report = {'accepted': False, 'stage': 'SOURCE_ONLY_AST_AND_ACTUAL_ORIGINAL_PBR_INTAKE_PASSED',
          'pythonASTPassed': True, 'allInputPinsPassed': True, 'noHeavyJobExecuted': True,
          'authorTargetGeometrySHA256': receipt['targetGeometrySHA256'],
          'bodyAnd75RigSignature': receipt['bodyAnd75RigSignature'],
          'sources': {str(p.relative_to(ROOT)): sha(p) for p in sorted(HERE.iterdir()) if p.is_file()},
          'controls': controls, 'originalGLTF': {'positionAccessor': position, 'identityNode': node,
                                              'materials': gltf['materials'], 'images': image_receipts},
          'axisEvidence': ['Identity original glTF node; Y-up positions are converted by Blender to (X,-Z,Y).',
                           'Historical frame recipe explicitly records imported donor (X,-Z,Y).',
                           'Frozen original dense controls use this Blender frame directly.',
                           'Authored selectedNative -90° Z cancels historical anatomical display +90° Z.',
                           'Runtime prep asserts imported world bounds match raw accessor conversion before fitting.'],
          'readiness': {'next': 'Parent checkpoint then bounded serial CPU2 fitted-native preparation.',
                        'nativeOutput': 'Fresh harness/out/rider-rebuild/production-hoodie02/prebake01/fitted-original-dense-pbr.blend',
                        'parentReviewBeforeBake': True, 'cpuThreads': 2,
                        'guardSecondsAllowedWhenAssigned': [180, 600]},
          'limits': controls['limits']}
out = ROOT/'docs/evidence/rider-rebuild/production-hoodie02/source-checkpoint.json'
out.write_text(json.dumps(report, indent=2)+'\n')
print(json.dumps({k: report[k] for k in ('stage','pythonASTPassed','allInputPinsPassed','noHeavyJobExecuted')}))
