"""Render-only adapter for the local cut/resew NPZ; no gameplay acceptance.

Retain source embedded images, inverse binds and 19 joint bases. Extend all
vertex attributes and original grip morphs to the new counts, preserving
normalized flags. The frozen 49 V7 correctives are deliberately not copied:
they were fitted to a different topology.
"""
from pathlib import Path
import sys, json, hashlib
import numpy as np

ROOT = Path('/Users/raynos/projects/games/rockhop/assets/blender/hero-remaster/rider/one-rider-v2/foundation-repair-task3')
sys.path.insert(0, str(ROOT / 'scripts'))
from glb import GLB

candidate = Path(sys.argv[1])
output = Path(sys.argv[2])
assert output.is_relative_to(ROOT / 'hoodie-repair03'), output
output.parent.mkdir(parents=True, exist_ok=True)
data = np.load(candidate)
source = ROOT / 'deliverables/C19.glb'
g = GLB(source)
primitives = [p for m in g.j['meshes'] for p in m['primitives']]
DT = {5126: '<f4', 5125: '<u4', 5123: '<u2', 5121: 'u1'}
SIZE = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}

def decode(ai):
    ac = g.j['accessors'][ai]
    result = g.array(ai).copy() if 'bufferView' in ac else np.zeros((ac['count'], SIZE[ac['type']]), dtype=DT[ac['componentType']])
    if 'sparse' in ac:
        sp = ac['sparse']
        bv = g.j['bufferViews'][sp['indices']['bufferView']]
        ix = np.frombuffer(g.bin, DT[sp['indices']['componentType']], count=sp['count'], offset=bv.get('byteOffset', 0) + sp['indices'].get('byteOffset', 0))
        bv = g.j['bufferViews'][sp['values']['bufferView']]
        values = np.frombuffer(g.bin, DT[ac['componentType']], count=sp['count'] * SIZE[ac['type']], offset=bv.get('byteOffset', 0) + sp['values'].get('byteOffset', 0)).reshape(-1, SIZE[ac['type']])
        result[ix] = values
    return result

def add(array, typ, component=5126, normalized=None):
    array = np.ascontiguousarray(array, dtype=DT[component])
    g.bin.extend(b'\0' * (-len(g.bin) % 4))
    vi = len(g.j['bufferViews'])
    g.j['bufferViews'].append({'buffer': 0, 'byteOffset': len(g.bin), 'byteLength': array.nbytes})
    g.bin.extend(array.tobytes())
    ac = {'bufferView': vi, 'componentType': component, 'count': len(array), 'type': typ}
    if normalized is not None:
        ac['normalized'] = normalized
    if component == 5126:
        ac.update(min=array.min(0).tolist(), max=array.max(0).tolist())
    ai = len(g.j['accessors'])
    g.j['accessors'].append(ac)
    return ai

inventory = []
for i, pr in enumerate(primitives):
    old = data[f'oldVertex{i}']
    valid = old >= 0
    assert old[valid].max(initial=-1) < len(g.array(pr['attributes']['POSITION']))
    original = dict(pr['attributes'])
    for name, ai in original.items():
        ac = g.j['accessors'][ai]
        a = decode(ai)
        expanded = np.zeros((len(old), a.shape[1]), dtype=a.dtype)
        expanded[valid] = a[old[valid]]
        if name.startswith('COLOR'):
            # New fabric gets the nearby original cloth's constant vertex-color
            # donor. This assignment is declared; existing rows remain exact.
            expanded[~valid] = np.median(a, axis=0).astype(a.dtype)
        if name == 'POSITION':
            expanded = data[f'p{i}']
        elif name == 'NORMAL':
            expanded = data[f'n{i}']
        elif name == 'TEXCOORD_0':
            expanded = data[f'uv{i}']
        elif name == 'JOINTS_0':
            expanded = np.argsort(data[f'W{i}'], axis=1)[:, -4:][:, ::-1]
        elif name == 'WEIGHTS_0':
            ids = np.argsort(data[f'W{i}'], axis=1)[:, -4:][:, ::-1]
            expanded = np.take_along_axis(data[f'W{i}'], ids, axis=1)
            expanded /= expanded.sum(1, keepdims=True)
        pr['attributes'][name] = add(expanded, ac['type'], ac['componentType'], ac.get('normalized'))
    pr['indices'] = add(data[f'tr{i}'].reshape(-1, 1), 'SCALAR', 5125)
    for target in pr.get('targets', []):
        for semantic, ai in list(target.items()):
            a = decode(ai)
            expanded = np.zeros((len(old), a.shape[1]), dtype=a.dtype)
            expanded[valid] = a[old[valid]]
            target[semantic] = add(expanded, g.j['accessors'][ai]['type'])
    inventory.append({'primitive': i, 'vertices': len(old), 'originalMappedRows': int(valid.sum()), 'newFabricRows': int((~valid).sum()), 'triangles': len(data[f'tr{i}'])})

g.j.pop('animations', None)
g.j['asset'].setdefault('extras', {})['constructionDiagnostic'] = {
    'renderOnly': True, 'productionApproved': False,
    'sourceSHA256': hashlib.sha256(g.raw).hexdigest(),
    'candidateNPZSHA256': hashlib.sha256(candidate.read_bytes()).hexdigest(),
    'sourceImagesAnd19InverseBindsRetained': True,
    'vertexColorFlagsRetained': True,
    'newFabricVertexColors': 'Per-component median of the original primitive; existing mapped rows preserved.',
    'gripMorphs': 'Original source targets extended by source vertex mapping; new fabric has zero grip deltas.',
    'limits': 'No V7 corrective morphs, physics driver, pose or appearance acceptance. Fresh source aliases must be independently validated.'
}
g.j['buffers'][0]['byteLength'] = len(g.bin)
g.write(output)
report = {'output': str(output), 'sha256': hashlib.sha256(output.read_bytes()).hexdigest(), 'candidate': str(candidate), 'candidateSHA256': hashlib.sha256(candidate.read_bytes()).hexdigest(), 'inventory': inventory, 'status': 'render-only, unaccepted'}
output.with_suffix('.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
