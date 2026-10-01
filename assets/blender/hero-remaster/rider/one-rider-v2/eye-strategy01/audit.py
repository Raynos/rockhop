"""CPU-only read-only eye topology audit; proposal coordinates are explicit seeds.

Run with the existing UniMate Python (NumPy/SciPy/Pillow). No Blender, GPU,
retopology, geometry edits, or generated replacement assets are performed.
"""
from pathlib import Path
import hashlib
import json
import struct
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components

REPO = Path('/Users/raynos/projects/games/rockhop')
SOURCE = Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/rig-adapter01/body-bind11/guarded-correction01/rider.glb')
OUT = REPO / 'docs/evidence/hero-remaster/one-rider-v2/eye-strategy01'
OUT.mkdir(parents=True, exist_ok=True)
raw = SOURCE.read_bytes()
jlen = struct.unpack_from('<I', raw, 12)[0]
doc = json.loads(raw[20:20+jlen]); binary = raw[28+jlen:]


def array(index):
    a = doc['accessors'][index]; v = doc['bufferViews'][a['bufferView']]
    width = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}[a['type']]
    dtype = {5126: '<f4', 5125: '<u4', 5123: '<u2', 5121: 'u1'}[a['componentType']]
    step = np.dtype(dtype).itemsize
    return np.ndarray((a['count'], width), dtype=dtype, buffer=binary,
        offset=v.get('byteOffset', 0) + a.get('byteOffset', 0),
        strides=(v.get('byteStride', width * step), step)).copy()


p = doc['meshes'][1]['primitives'][0]
v = array(p['attributes']['POSITION']).astype(float)
tri = array(p['indices']).reshape(-1, 3).astype(int)
uv = array(p['attributes']['TEXCOORD_0'])
joints = array(p['attributes']['JOINTS_0'])
weights = array(p['attributes']['WEIGHTS_0'])
positions, weld = np.unique(v, axis=0, return_inverse=True)
wt = weld[tri]
all_edges = np.concatenate([wt[:,[0,1]],wt[:,[1,2]],wt[:,[2,0]]])
all_adjacency = coo_matrix((np.ones(len(all_edges)),(all_edges[:,0],all_edges[:,1])),shape=(len(positions),len(positions))).tocsr()
_, whole_labels = connected_components(all_adjacency,directed=False)
whole_components=[]
for label in np.unique(whole_labels):
    pv=positions[whole_labels==label]
    fm=whole_labels[wt[:,0]]==label
    whole_components.append({'component':int(label),'vertices':len(pv),'triangles':int(fm.sum()),
        'boundsM':[pv.min(0).tolist(),pv.max(0).tolist()]})
centroid = v[tri].mean(1)
normal = np.cross(v[tri[:,1]]-v[tri[:,0]], v[tri[:,2]]-v[tri[:,0]])
normal /= np.maximum(np.linalg.norm(normal, axis=1)[:,None], 1e-15)
yz = v[tri][:,:,1:]


def front_hit(y, z):
    point = np.array([y,z])
    candidates = np.flatnonzero((yz.min(1) <= point).all(1) & (yz.max(1) >= point).all(1))
    t = yz[candidates]; a=t[:,1]-t[:,0]; b=t[:,2]-t[:,0]; d=point-t[:,0]
    det=a[:,0]*b[:,1]-a[:,1]*b[:,0]
    usable=np.abs(det)>1e-15
    candidates=candidates[usable]; a=a[usable]; b=b[usable]; d=d[usable]; det=det[usable]
    u=(d[:,0]*b[:,1]-d[:,1]*b[:,0])/det
    q=(a[:,0]*d[:,1]-a[:,1]*d[:,0])/det
    bary=np.column_stack([1-u-q,u,q]); inside=bary.min(1)>=-1e-9
    candidates=candidates[inside]; bary=bary[inside]
    if not len(candidates): return None
    depth=(bary*v[tri[candidates],0]).sum(1)
    i=int(depth.argmax())
    order=np.argsort(-depth)
    return {'x':float(depth[i]), 'face':int(candidates[i]), 'barycentric':bary[i].tolist(),
        'allHitsDescendingX':[{'x':float(depth[k]),'face':int(candidates[k]),
            'normalX':float(normal[candidates[k],0])} for k in order]}


def topology(faces):
    edges=np.concatenate([faces[:,[0,1]],faces[:,[1,2]],faces[:,[2,0]]])
    edges=np.sort(edges,axis=1)
    unique, counts=np.unique(edges,axis=0,return_counts=True)
    boundary=unique[counts==1]
    points, degree=np.unique(boundary,return_counts=True)
    if len(boundary):
        adjacency=coo_matrix((np.ones(len(boundary)),(boundary[:,0],boundary[:,1])),shape=(len(positions),len(positions))).tocsr()
        _, labels=connected_components(adjacency,directed=False)
        components=len(np.unique(labels[points]))
    else: components=0
    loops=[]
    for label in np.unique(labels[points]) if len(boundary) else []:
        ids=points[labels[points]==label]; pv=positions[ids]
        loops.append({'vertices':len(ids),'boundsM':[pv.min(0).tolist(),pv.max(0).tolist()],
            'meanM':pv.mean(0).tolist()})
    return {'triangles':len(faces),'boundaryEdges':len(boundary),'boundaryComponents':components,
        'boundaryDegreeHistogram':{str(int(k)):int((degree==k).sum()) for k in np.unique(degree)},
        'nonmanifoldEdges':int((counts>2).sum()), 'boundaryVertexIDs':points.tolist(),
        'boundaryLoops':loops}


eyes=[]
# These seeds were manually read from the source front projection, NOT mockups,
# anatomy detection, eye centers or approved reconstruction landmarks.
for name, cy, cz in [('positiveZ',1.6965,.0320),('negativeZ',1.6970,-.0332)]:
    center=front_hit(cy,cz)
    profiles={}
    for axis in ['horizontal','vertical']:
        offsets=np.linspace(-.020,.020,41) if axis=='horizontal' else np.linspace(-.012,.012,25)
        values=[]
        for delta in offsets:
            hit=front_hit(cy+(delta if axis=='vertical' else 0),cz+(delta if axis=='horizontal' else 0))
            values.append({'offsetM':float(delta),'frontXM':hit['x'] if hit else None})
        profiles[axis]=values
    # A small face-center mask is only a topology feasibility proposal; it does
    # NOT identify or cut actual eyelid margins. Source triangles remain intact.
    ellipse=((centroid[:,1]-cy)/.00425)**2+((centroid[:,2]-cz)/.013)**2
    candidates=np.flatnonzero((ellipse<1)&(normal[:,0]>.25)&(centroid[:,0]>.70))
    visible=[]
    for fi in candidates:
        hit=front_hit(centroid[fi,1],centroid[fi,2])
        if hit and abs(hit['x']-centroid[fi,0])<.0002: visible.append(int(fi))
    selected=np.array(visible,dtype=int)
    # Canonical-edge adjacency checks whether this proposal opens one disk.
    edges={}
    for local, fi in enumerate(selected):
        for a,b in [(0,1),(1,2),(2,0)]: edges.setdefault(tuple(sorted(wt[fi,[a,b]])),[]).append(local)
    pairs=np.array([(items[0],items[1]) for items in edges.values() if len(items)==2],dtype=int).reshape(-1,2)
    if len(selected):
        adjacency=coo_matrix((np.ones(len(pairs)),(pairs[:,0],pairs[:,1])),shape=(len(selected),len(selected))).tocsr()
        n,labels=connected_components(adjacency,directed=False)
        counts=np.bincount(labels); keep=labels==counts.argmax()
        selected=selected[keep]
    else: n=0; counts=np.array([])
    stats=topology(wt[selected])
    patch_vertices=np.unique(tri[selected])
    head_joint_totals={str(int(j)):float(weights[patch_vertices][joints[patch_vertices]==j].sum()) for j in np.unique(joints[patch_vertices])}
    boundary=positions[stats.pop('boundaryVertexIDs')]
    alternative_masks=[]
    surgical=((centroid[:,1]-cy)/.009)**2+((centroid[:,2]-cz)/.018)**2
    for label, selection in [('all-front-surface-in-ellipse', (ellipse<1)&(centroid[:,0]>.72)),
            ('wider-front-surface-in-ellipse', (ellipse<1.44)&(centroid[:,0]>.72)),
            ('surgical-36x18mm-full-thickness', (surgical<1)&(centroid[:,0]>.72))]:
        indices=np.flatnonzero(selection)
        alternative_masks.append({'name':label,
            'topology':{k:value for k,value in topology(wt[indices]).items() if k!='boundaryVertexIDs'},
            'faceIndices':indices.tolist()})
    eyes.append({'name':name,'proposalSeedYZM':[cy,cz], 'seedFrontHit':center,
        'proposalEllipseFullWidthHeightM':[.026,.0085],
        'allSelectedConnectedComponents':int(n),'componentTriangleCounts':counts.tolist(),
        'largestComponent':stats,'boundaryBoundsM':[boundary.min(0).tolist(),boundary.max(0).tolist()] if len(boundary) else None,
        'allPatchWeightTotalsByJointIndex':head_joint_totals,
        'patchVertexCount':int(len(patch_vertices)),
        'profiles':profiles, 'proposedRemovedFaceIndices':selected.tolist(),
        'alternativeMasks':alternative_masks})

donor=Path('/Users/raynos/projects/weights/makehuman/system-cc0/eyes/high-poly/high-poly.obj')
verts=[]; polys=[]
for line in donor.read_text().splitlines():
    if line.startswith('v '): verts.append([float(x) for x in line.split()[1:4]])
    if line.startswith('f '): polys.append([int(x.split('/')[0])-1 for x in line.split()[1:]])
dv=np.array(verts); dedges=np.array([(a,b) for poly in polys for a,b in zip(poly,poly[1:]+poly[:1])])
adjacency=coo_matrix((np.ones(len(dedges)),(dedges[:,0],dedges[:,1])),shape=(len(dv),len(dv))).tocsr()
count, labels=connected_components(adjacency,directed=False)
donor_parts=[]
for part in range(count):
    points=dv[labels==part]
    # Sphere fit is a quantitative diagnostic. Cornea is not a perfect sphere.
    a=np.column_stack([2*points,np.ones(len(points))]); b=(points**2).sum(1)
    fit=np.linalg.lstsq(a,b,rcond=None)[0]; center=fit[:3]; radius=np.sqrt(fit[3]+(center**2).sum())
    residual=np.linalg.norm(points-center,axis=1)-radius
    donor_parts.append({'part':part,'vertices':len(points),'sphereCenterRaw':center.tolist(),
        'sphereRadiusRaw':float(radius),'sphereRMSResidualRaw':float(np.sqrt((residual**2).mean())),
        'sphereMaxAbsoluteResidualRaw':float(np.abs(residual).max()),
        'uniformScaleFor12mmRadius':float(.012/radius)})

skin=doc['skins'][0]
report={'source':str(SOURCE),'sourceSHA256':hashlib.sha256(raw).hexdigest(),
    'readOnly':True,'originalGLBUntouched':SOURCE.read_bytes()==raw,
    'headPrimitive':{'mesh':1,'primitive':0,'vertices':len(v),'exactWeldedPositions':len(positions),'triangles':len(tri)},
    'wholeHeadConnectedComponents':whole_components,
    'wholeHeadTopology':{k:value for k,value in topology(wt).items() if k!='boundaryVertexIDs'},
    'skinJointIndexNames':{str(i):doc['nodes'][node].get('name','') for i,node in enumerate(skin['joints'])},
    'seedSeparationM':float(abs(eyes[0]['proposalSeedYZM'][1]-eyes[1]['proposalSeedYZM'][1])),
    'eyes':eyes,'CC0Donor':{'path':str(donor),'sha256':hashlib.sha256(donor.read_bytes()).hexdigest(),'components':donor_parts},
    'limits':['Seed locations are manually selected surface features, not anatomical globe centers.',
        'Ellipse face selection is a disk feasibility audit, not accepted eyelid boundary detection.',
        'CPU source profiles do not judge PBR appearance or moving character.',
        'No geometry, UVs, weights, textures, materials, nodes, rig, neck or body changed.']}
(OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:value for k,value in report.items() if k!='eyes'},indent=2))
for eye in eyes: print(json.dumps({k:value for k,value in eye.items() if k not in ['profiles','proposedRemovedFaceIndices','alternativeMasks']},indent=2))
for eye in eyes:
    print(eye['name'], json.dumps([{k:value for k,value in alternative.items() if k!='faceIndices'} for alternative in eye['alternativeMasks']]))
