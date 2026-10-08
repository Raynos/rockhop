"""Standalone lightweight source/pin verification; never import Blender/NumPy."""
import ast
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as handle:
        while block := handle.read(1024 * 1024):
            digest.update(block)
    return digest.hexdigest()


def pins(value):
    if isinstance(value, dict):
        if 'path' in value and 'sha256' in value:
            yield value
        else:
            for child in value.values():
                yield from pins(child)
    elif isinstance(value, list):
        for child in value:
            yield from pins(child)


manifest = json.loads((HERE/'author-inputs.json').read_text())
rows = list(pins(manifest))
for row in rows:
    assert sha(ROOT/row['path']) == row['sha256'], ('Changed pin', row['path'])
source = HERE/'author_region.py'
tree = ast.parse(source.read_text(), filename=str(source))
calls = [ast.unparse(node.func) for node in ast.walk(tree) if isinstance(node, ast.Call)]
assert not any(token in call.lower() for call in calls for token in ('render', 'bake', 'remesh', 'decimat', 'shrinkwrap'))
assert manifest['accepted'] is False and manifest['limits']['noFallback'] and manifest['limits']['noFullBootRemesh']
assert manifest['innerEaseM'] == .004 and manifest['minimumMeasuredClearanceM'] == .0025
assert manifest['objects']['boots'] == {s: 'Boots__LocallyRepairedSelectedDenseBoot.'+s for s in ('R', 'L')}
assert manifest['workingOutfit']['sha256'] == '9cedbcdbe0a953d116bafc80b41f8adb0538f21c1ecfca20598f3f079952aaf4'
assert manifest['canonicalArrays']['sha256'] == 'e62e9969503b7761e99463eccc3ca7be39e0c230a2948f2f87a224db52d0f9a2'
report = {'accepted': False, 'status': 'ONE_REGIONAL_CSG_AUTHOR_SOURCE_READY_UNEXECUTED',
          'pythonASTPassed': True, 'explicitSourcePinsPassed': len(rows),
          'noBlenderModelBakeRenderOrDenseArrayJobExecuted': True,
          'recipeSHA256': sha(source), 'controlsSHA256': sha(HERE/'author-inputs.json'),
          'command': ['/Applications/Blender.app/Contents/MacOS/Blender', '-b', '-t', '2',
                      '--python-exit-code', '1', '--python', str(source.relative_to(ROOT)),
                      '--', 'harness/out/rider-rebuild/boot-last-anatomical04/author01'],
          'leaseRequirement': 'Parent original CPU2/model lock/memory guard; unchanged180second job limit. This recipe never launches itself.',
          'supportedInputBounds': manifest['limits'],
          'runtimeGates': ['Exact actual selected mesh/UV/material state from successful extraction.',
                           'One connected watertight last/foot-cavity result, no zero-area faces.',
                           'Below-collar canonical foot contained by solid before cavity carving.',
                           'Canonical foot vertices and triangle centroids outside leather, measured>=2.5mm clearance.',
                           'Surviving original source faces keep exact cornerUV and sourceface ancestry.',
                           'Original rear tread held; selected lace/tongue and genuine4K maps retained.',
                           'All added exterior corners have same-side facing actual-source UV correspondence.',
                           'Whole working wearer/weights/UV/rest75/pose remains identical.',
                           'Native saved after union and cavity, before post-CSG/PBR gates; failures remain unaccepted.'],
          'reviewContract': 'Generated matched source/new original-PBR rest specs for both anatomical sides, toe, heel and top. Parent renders/plays separately; no art acceptance from numeric gates or stills.',
          'limits': ['No heavy job executed by source checker.',
                     '180second guard is a stopping limit, not a benchmark or prediction.',
                     'No fallback Boolean solver, full-boot remesh, bake, mobile final or player export.',
                     'New-region UVs are explicit original-map correspondence preview; final coherent unwrap/bake remains required.',
                     manifest['motionRequired']]}
path = ROOT/'docs/evidence/rider-rebuild/boot-last-anatomical04/author-source-checkpoint.json'
path.write_text(json.dumps(report, indent=2)+'\n')
print(json.dumps(report, indent=2))
