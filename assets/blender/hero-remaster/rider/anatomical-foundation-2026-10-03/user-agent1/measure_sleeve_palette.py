"""Compare same-rest source weights on all704 exact actual-game affine palettes."""
import argparse
import hashlib
import json
import sys
from pathlib import Path
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ap = argparse.ArgumentParser(description=__doc__)
for n in ['palette','handoff','attachments','baseline','out']:
    ap.add_argument('--'+n,required=True)
a = ap.parse_args(sys.argv[sys.argv.index('--')+1:]); pf,hf,af,baseline,out = [Path(getattr(a,n)).resolve() for n in ['palette','handoff','attachments','baseline','out']]
sha = lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest(); p,h,d = [json.loads(f.read_text()) for f in [pf,hf,af]]
stream = pf.parent/p['stream']; assert sha(stream)==p['streamSHA256']
pins = {str(f):sha(f) for f in [pf,hf,af,stream,baseline]}
matrices = np.fromfile(stream,dtype='<f8').reshape(704,51,4,4).swapaxes(-1,-2)
names = p['nativeJointOrderNames']; lookup = {n:i for i,n in enumerate(names)}
def apply(vertices,rows):
    points = np.column_stack([np.asarray(vertices,dtype=np.float64),np.ones(len(vertices))]); values = np.zeros((len(vertices),51))
    for i,row in enumerate(rows):
        pairs = row.items() if isinstance(row,dict) else row
        for name,w in pairs:
            values[i,lookup[name]] = w
    assert np.all(values.sum(1)>0)
    result = np.zeros((704,len(vertices),4))
    for j in range(51):
        active = values[:,j]>0
        if active.any():
            result[:,active] += np.einsum('fab,vb->fva',matrices[:,j],points[active])*values[active,j][None,:,None]
    result /= values.sum(1)[None,:,None]
    return result[:,:,:3]
vertices = h['pattern']['verticesNativeM']; faces = h['pattern']['triangleVertexIDs']
old = apply(vertices,h['pattern']['weights']); new = apply(vertices,[r['actualNativeAfterWeights'] for r in d['attachments']])
played = np.fromfile(baseline,dtype='<f4').reshape(703,288,3)
quantized_old = old[1:].astype('<f4'); exact = bool(np.array_equal(played,quantized_old))
maximum_baseline_delta = float(np.max(np.abs(played.astype(np.float64)-old[1:])))
assert maximum_baseline_delta<2e-6,'Palette/axes association differs from played control'
body = h['nativeConsumedColliders']['body']; body_rows = body['relevantArmVertices']; body_ids = [r['bodyVertexID'] for r in body_rows]
body_lookup = {v:i for i,v in enumerate(body_ids)}
body_faces = [[body_lookup[i] for i in r['bodyVertexIDs']] for r in body['relevantArmTriangles']]
body_world = apply([r['restNativeM'] for r in body_rows],[r['weights'] for r in body_rows])
def contacts(points,body_tree):
    tree = BVHTree.FromPolygons([Vector(v) for v in points],faces,all_triangles=True)
    body_pairs = tree.overlap(body_tree)
    self_pairs = [(i,j) for i,j in tree.overlap(tree) if i<j and not(set(faces[i])&set(faces[j]))]
    return {'bodyTrianglePairs':len(body_pairs),'selfTrianglePairs':len(self_pairs),'firstBodyPairs':body_pairs[:4],'firstSelfPairs':self_pairs[:4]}
frames = []
for frame in range(704):
    tree = BVHTree.FromPolygons([Vector(v) for v in body_world[frame]],body_faces,all_triangles=True)
    frames.append({'inputTick':frame,'baseline':contacts(old[frame],tree),'bodyWeights':contacts(new[frame],tree)})
    if frame%120==0:
        print('SLEEVE_ACTUAL_PALETTE',frame,frames[-1],flush=True)
assert pins=={f:sha(f) for f in pins}
np.savez_compressed(out.with_suffix('.npz'),baseline=old,bodyWeights=new,body=body_world)
report = {'status':'UNACCEPTED same-rest weighting actualpalette contact comparison; root/independent actualloader game review required',
    'pins':pins,'recipeSHA256':sha(__file__),'streamSHA256':sha(out.with_suffix('.npz')),'frames':frames,
    'baselinePlayedFloat32All703FramesByteExact':exact,'maximumFloat32PlayedVsComputedBaselineM':maximum_baseline_delta,
    'summary':{mode:{'maxBody':max(r[mode]['bodyTrianglePairs'] for r in frames),'maxSelf':max(r[mode]['selfTrianglePairs'] for r in frames),
        'bodyContactFrames':sum(r[mode]['bodyTrianglePairs']>0 for r in frames),'selfContactFrames':sum(r[mode]['selfTrianglePairs']>0 for r in frames)} for mode in ['baseline','bodyWeights']},
    'selectedTicks':[r for r in frames if r['inputTick'] in [0,430,490,670]],
    'limits':['ExactnativeREST-to-engineWORLD affine palette applied directly, no axis/root shift added. Both controls share geometry/body/input; only skinweights differ.',
        'Body check uses the same frozen1066 relevant native arm triangles, not every body or an accepted closed-volume collider.',
        'BVH triangle-pair/adjacency-filtered self proxies are not signed penetration/clearance or swept physical response; predicate differs from Agent3 runtime checker.',
        'No projection, body/bind replacement, physics/game mutation, cloth restart or moving-art acceptance. Agent3 independently checks actual consumed export and root judges visible windows/folds.']}
out.write_text(json.dumps(report,indent=2)+'\n');print('SLEEVE_PALETTE_RESULT',exact,report['summary'],flush=True)
