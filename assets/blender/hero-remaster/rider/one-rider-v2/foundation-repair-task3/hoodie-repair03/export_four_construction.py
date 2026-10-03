"""Guarded stock-four diagnostic export. No driver or art acceptance.

Protected primitives retain original accessors byte-for-byte. New source-edge
rows interpolate attributes/morphs from their explicit source parents. Refuse
five influences rather than silently selecting a largest-four approximation.
"""
from pathlib import Path
import hashlib, json, sys
import numpy as np
sys.dont_write_bytecode = True

ROOT = Path('/Users/raynos/projects/games/rockhop/assets/blender/hero-remaster/rider/one-rider-v2/foundation-repair-task3')
sys.path.insert(0, str(ROOT / 'scripts'))
from glb import GLB

candidate, output = map(Path, sys.argv[1:3])
assert not output.exists(), 'Fresh output required'
z = np.load(candidate)
g = GLB(ROOT / 'deliverables/C19.glb')
primitives = [p for m in g.j['meshes'] for p in m['primitives']]
DT = {5126: '<f4', 5125: '<u4', 5123: '<u2', 5121: 'u1'}
SIZE = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}

def decode(ai):
    ac = g.j['accessors'][ai]
    a = g.array(ai).copy() if 'bufferView' in ac else np.zeros((ac['count'], SIZE[ac['type']]), dtype=DT[ac['componentType']])
    if 'sparse' in ac:
        sp = ac['sparse']
        bv = g.j['bufferViews'][sp['indices']['bufferView']]
        ix = np.frombuffer(g.bin, DT[sp['indices']['componentType']], count=sp['count'], offset=bv.get('byteOffset', 0) + sp['indices'].get('byteOffset', 0)).copy()
        bv = g.j['bufferViews'][sp['values']['bufferView']]
        values = np.frombuffer(g.bin, DT[ac['componentType']], count=sp['count'] * SIZE[ac['type']], offset=bv.get('byteOffset', 0) + sp['values'].get('byteOffset', 0)).reshape(-1, SIZE[ac['type']]).copy()
        a[ix] = values
    return a

def add(a, ac):
    a = np.ascontiguousarray(a, dtype=DT[ac['componentType']])
    g.bin.extend(b'\0' * (-len(g.bin) % 4))
    vi = len(g.j['bufferViews'])
    g.j['bufferViews'].append({'buffer': 0, 'byteOffset': len(g.bin), 'byteLength': a.nbytes})
    g.bin.extend(a.tobytes())
    out = {k: ac[k] for k in ['componentType', 'type']}
    out.update(bufferView=vi, count=len(a))
    if 'normalized' in ac:
        out['normalized'] = ac['normalized']
    if ac['componentType'] == 5126:
        out.update(min=a.min(0).tolist(), max=a.max(0).tolist())
    ai = len(g.j['accessors'])
    g.j['accessors'].append(out)
    return ai

def expanded(a, i, semantic):
    old = z[f'oldVertex{i}']; valid = old >= 0
    v = np.zeros((len(old), a.shape[1]), dtype=a.dtype)
    v[valid] = a[old[valid]]
    parents = z.get(f'sourceVertexParents{i}')
    bary = z.get(f'sourceVertexBarycentric{i}')
    if semantic.startswith('COLOR'):
        v[~valid] = np.median(a, axis=0).astype(a.dtype)
    if parents is not None:
        ids = np.flatnonzero((parents >= 0).all(1))
        q = (a[parents[ids]] * bary[ids, :, None]).sum(1)
        if a.dtype.kind in 'ui':
            q = np.rint(q)
        v[ids] = q.astype(a.dtype)
    return v

inventory = []
for i, p in enumerate(primitives):
    w = z[f'W{i}']
    assert np.isfinite(w).all() and (w >= 0).all()
    assert np.max(np.abs(w.sum(1) - 1)) < 1e-12
    assert (w != 0).sum(1).max() <= 4, 'Five-influence input refused without writing'
    ids = np.argsort(w, axis=1, kind='stable')[:, -4:][:, ::-1]
    weights = np.take_along_axis(w, ids, axis=1)
    reconstructed = np.zeros_like(w)
    np.put_along_axis(reconstructed, ids, weights, axis=1)
    assert np.array_equal(reconstructed, w), 'No dropped mass permitted'
    if i in (1, 3):
        assert np.array_equal(z[f'oldVertex{i}'], np.arange(len(w)))
        for key, semantic in [('p', 'POSITION'), ('n', 'NORMAL'), ('uv', 'TEXCOORD_0')]:
            assert np.array_equal(z[f'{key}{i}'].astype(decode(p['attributes'][semantic]).dtype), decode(p['attributes'][semantic]))
        assert np.array_equal(z[f'tr{i}'].reshape(-1), decode(p['indices']).reshape(-1))
        source_w = np.zeros_like(w)
        np.put_along_axis(source_w, decode(p['attributes']['JOINTS_0']).astype(int), decode(p['attributes']['WEIGHTS_0']), axis=1)
        assert np.max(np.abs(source_w - w)) < 1e-7
        inventory.append({'primitive': i, 'protectedAllAccessorsUnchanged': True})
        continue
    for semantic, ai in list(p['attributes'].items()):
        ac = g.j['accessors'][ai]
        if semantic == 'POSITION': v = z[f'p{i}']
        elif semantic == 'NORMAL': v = z[f'n{i}']
        elif semantic == 'TEXCOORD_0': v = z[f'uv{i}']
        elif semantic == 'JOINTS_0': v = ids
        elif semantic == 'WEIGHTS_0': v = weights
        else: v = expanded(decode(ai), i, semantic)
        p['attributes'][semantic] = add(v, ac)
    p['indices'] = add(z[f'tr{i}'].reshape(-1, 1), {'componentType': 5125, 'type': 'SCALAR'})
    for target in p.get('targets', []):
        for semantic, ai in list(target.items()):
            target[semantic] = add(expanded(decode(ai), i, semantic), g.j['accessors'][ai])
    inventory.append({'primitive': i, 'vertices': len(w), 'triangles': len(z[f'tr{i}']), 'maxInfluences': int((w != 0).sum(1).max())})

g.j.pop('animations', None)
metadata = {'productionApproved': False, 'shapeAccepted': False, 'driverIncluded': False,
            'sourceSHA256': hashlib.sha256(g.raw).hexdigest(),
            'candidateNPZSHA256': hashlib.sha256(candidate.read_bytes()).hexdigest(),
            'binding': 'Exact four nonzero weights; no discarded mass or normalization',
            'protectedPrimitives': 'All source accessors retained byte-for-byte',
            'newAttributes': 'Source-edge barycentric attributes and grip morphs; free cloth color source median, other free attributes zero',
            'limits': 'Standard LBS only. Responding material surface is not encoded or certified. Shape/motion/contact/continuous gates pending.'}
g.j['asset'].setdefault('extras', {})['constructionDiagnostic'] = metadata
g.j['buffers'][0]['byteLength'] = len(g.bin)
output.parent.mkdir(parents=True, exist_ok=True)
g.write(output)
report = dict(metadata, output=str(output), outputSHA256=hashlib.sha256(output.read_bytes()).hexdigest(), inventory=inventory)
output.with_suffix('.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
