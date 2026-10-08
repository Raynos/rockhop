"""Read-only reproduction of the frozen final cuff-sector assertion failure.

Runs exact freeze main until its LEFT orientation assertion and captures locals.
Any attempted output by that recipe is blocked. Only this diagnostic writes here.
"""
import hashlib
import json
import runpy
import sys
import warnings
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[5]
HERE = Path(__file__).resolve().parent
SOURCE = ROOT/'assets/blender/rider-rebuild/glove-cuff-fit06/freeze.py'
namespace = runpy.run_path(str(SOURCE))
original_save = np.savez_compressed
captured = {}

def no_recipe_write(*args, **kwargs):
    raise RuntimeError('Diagnostic refuses all recipe outputs')

def trace(frame, event, value):
    if frame.f_code is namespace['main'].__code__:
        if event == 'exception' and isinstance(value[1], AssertionError):
            captured.update(frame.f_locals)
            captured['assertion'] = repr(value[1])
        return trace
    return None

np.savez_compressed = no_recipe_write
sys.settrace(trace)
try:
    with warnings.catch_warnings(record=True) as recorded:
        warnings.simplefilter('always')
        try:
            namespace['main']()
        except AssertionError as error:
            assert 'orientation reversal' in str(error), repr(error)
        else:
            raise RuntimeError('Expected exact frozen orientation failure did not occur')
finally:
    sys.settrace(None)
    np.savez_compressed = original_save
assert captured['side'] == 'L'
assert not (SOURCE.parent/'controls.json').exists()
assert not list(SOURCE.parent.glob('cuff-sector-offsets-*.npz'))
# Preserve every original recipe warning above. NumPy's matmul status flags
# also warn on finite diagnostic inputs; inspect actual arrays explicitly.
np.seterr(all='ignore')
faces = captured['faces']; points = captured['points']; corrected = captured['corrected']
dots = captured['dots']; bad = np.flatnonzero(dots<=0)
protected = captured['protected']; world = captured['world']
linear = captured['linear']; offsets = captured['offsets']
world_after = corrected.astype(float)@linear.T+captured['translation']
_, protected_owner, _ = namespace['distances'](captured['neighbors'],np.flatnonzero(protected))
old = set(captured['control']['oldLipAnchors']); centerline = set(captured['centerline'])
local = captured['local']['offsets']; selected = captured['original_selected']

def protection(index):
    return {'oldLipAnchor':int(index) in old,
            'priorLocal04Edited':bool(np.any(local[index]!=0)),
            'protectedNonCuff':bool(selected[index,1]>=-.52)}

world_direct = np.sum(points[:,None,:]*linear[None,:,:], axis=2)+captured['translation']
radial_direct = world-captured['wrist']-np.sum((world-captured['wrist'])*captured['axis'],axis=1)[:,None]*captured['axis']
offset_direct = np.sum((-captured['radial']*captured['scale'][:,None])[:,None,:]*np.linalg.inv(linear)[None,:,:],axis=2)
# Recipe replaces eight measured-control vectors and fixes protected points.
for index, row in captured['measured'].items(): offset_direct[index] = row['linearizedSourceOffsetFor1p5mmInside']
offset_direct[protected] = 0.
rows = []
for identity in bad:
    ids = faces[identity]
    before_edges = [float(np.linalg.norm(world[ids[(j+1)%3]]-world[ids[j]])) for j in range(3)]
    after_edges = [float(np.linalg.norm(world_after[ids[(j+1)%3]]-world_after[ids[j]])) for j in range(3)]
    rows.append({'guideTriangle':int(identity),'guideVertices':ids.tolist(),'normalDot':float(dots[identity]),
        'normalBefore':captured['normals_before'][identity].tolist(),'normalAfter':captured['normals_after'][identity].tolist(),
        'nativeEdgesBeforeM':before_edges,'nativeEdgesAfterM':after_edges,
        'sourceTriangleAreaBefore':float(np.linalg.norm(captured['normals_before'][identity])/2),
        'sourceTriangleAreaAfter':float(np.linalg.norm(captured['normals_after'][identity])/2),
        'vertices':[{'guideVertex':int(index),'sourceBefore':points[index].tolist(),'sourceAfterFloat32':corrected[index].tolist(),
            'nativeBefore':world[index].tolist(),'nativeAfter':world_after[index].tolist(),
            'nativeOffsetM':float(np.linalg.norm(linear@offsets[index])),
            'contractionScale':float(captured['scale'][index]),'brushWeight':float(captured['brush'][index]),
            'centerline':int(index) in centerline,'nearestCenterlineVertex':int(captured['owner'][index]),
            'centerlineDistanceM':float(captured['distance'][index]),
            'protected':bool(protected[index]),'protection':protection(index),
            'protectedDistanceM':float(captured['protect_distance'][index]),
            'nearestProtectedVertex':int(protected_owner[index]),'nearestProtection':protection(protected_owner[index])}
            for index in ids]})
finite = {name:bool(np.isfinite(captured[name]).all()) for name in
          ('points','world','radial','brush','scale','offsets','corrected','normals_before','normals_after','dots')}
finite['consumedCenterlineFractions'] = bool(np.isfinite(captured['fractions'][captured['owner']]).all())
output = {'acceptedArt':False,'operation':'READ_ONLY_REPRODUCTION_FINAL_CUFF_SECTOR_FAILURE',
    'source':{'path':str(SOURCE.relative_to(ROOT)),'sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest()},
    'diagnosticSHA256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    'inputSHA256':hashlib.sha256((SOURCE.parent/'input.json').read_bytes()).hexdigest(),
    'assertion':captured['assertion'],'side':'L','guideTriangles':len(faces),
    'reversedGuideTriangles':len(bad),'minimumNormalDot':float(dots.min()),
    'finiteArrays':finite,'unexpectedNonfinite':not all(finite.values()),
    'explicitThreeTermSumReadbackMaximumResidual':{
        'world':float(np.max(abs(world_direct-world))),
        'radial':float(np.max(abs(radial_direct-captured['radial']))),
        'offsets':float(np.max(abs(offset_direct-offsets)))},
    'warnings':[{'category':row.category.__name__,'message':str(row.message),'line':row.lineno} for row in recorded],
    'protectedDistanceFullStrengthM':float(captured['full_distance']),
    'badTriangleVertices':sorted(set(map(int,faces[bad].ravel()))),
    'badTrianglesContainingProtectedVertices':sum(bool(protected[faces[i]].any()) for i in bad),
    'badTrianglesContainingCenterlineVertices':sum(bool(set(map(int,faces[i]))&centerline) for i in bad),
    'rows':rows,'recipeOutputWritten':False,'nativeOrRecipeChanged':False,
    'limits':['Exact LEFT failure reproduced before any recipe output; RIGHT remains unexecuted.',
              'No alternate radius, attenuation, control amount, weight or topology experiment was performed.',
              'This evidence rejects this second/final offset mechanism; it is not permission to weaken the orientation gate.']}
(HERE/'receipt.json').write_text(json.dumps(output,indent=2)+'\n')
print(json.dumps({key:output[key] for key in ('side','reversedGuideTriangles','minimumNormalDot','finiteArrays','warnings','protectedDistanceFullStrengthM','badTriangleVertices','badTrianglesContainingProtectedVertices','badTrianglesContainingCenterlineVertices')},indent=2))
