"""Read-only native CC0 eyelid topology extraction, without analytic lid rings."""
from pathlib import Path
from collections import Counter, defaultdict
import hashlib,json
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components

ROOT=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/rig-adapter01/anatomical-eye-donor01')
OUT=Path('/Users/raynos/projects/games/rockhop/docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/anatomical-eye-donor01')
BASE=Path('/Users/raynos/Library/Application Support/Blender/5.1/extensions/user_default/mpfb/data/3dobjs/base.obj')
ROOT.mkdir(parents=True,exist_ok=True);OUT.mkdir(parents=True,exist_ok=True)
raw=BASE.read_bytes();verts=[];uvs=[];polys=[];poly_uv=[];groups=[];group=''
for line in raw.decode().splitlines():
    parts=line.split()
    if not parts:continue
    if parts[0]=='v':verts.append([float(x) for x in parts[1:4]])
    elif parts[0]=='vt':uvs.append([float(x) for x in parts[1:3]])
    elif parts[0]=='g':group=' '.join(parts[1:])
    elif parts[0]=='f':
        polys.append([int(x.split('/')[0])-1 for x in parts[1:]])
        poly_uv.append([int(x.split('/')[1])-1 for x in parts[1:]])
        groups.append(group)
v=np.array(verts);uv=np.array(uvs);groups=np.array(groups)
body=np.flatnonzero(groups=='body');body_edges=defaultdict(list)
for fi in body:
    poly=polys[fi]
    for a,b in zip(poly,poly[1:]+poly[:1]):body_edges[tuple(sorted((a,b)))].append(int(fi))
boundary=np.array([edge for edge,faces in body_edges.items() if len(faces)==1],dtype=int).reshape(-1,2)
if not len(boundary):
    diagnostic={'status':'Native open-aperture assumption rejected; diagnostic only, no rider repair attempted',
        'source':str(BASE),'sourceSHA256':hashlib.sha256(raw).hexdigest(),
        'bodyQuads':len(body),'bodyBoundaryEdges':0,
        'finding':'Native body is closed; anatomical lids surround closed posterior socket cups. Follow native face topology to remove the cup and extract actual lid strips.',
        'nextRecipe':'inspect_native.py then extract_patch.py',
        'sourceUnchanged':BASE.read_bytes()==raw}
    (OUT/'open-boundary-assumption.json').write_text(json.dumps(diagnostic,indent=2)+'\n')
    print(json.dumps(diagnostic,indent=2))
    raise SystemExit(0)
adj=coo_matrix((np.ones(len(boundary)),(boundary[:,0],boundary[:,1])),shape=(len(v),len(v))).tocsr()
_,labels=connected_components(adj,directed=False)
loops=[]
for label in np.unique(labels[np.unique(boundary)]):
    ids=np.unique(boundary[labels[boundary[:,0]]==label]);degree=Counter(boundary[labels[boundary[:,0]]==label].ravel())
    loops.append({'vertexIDs':ids.tolist(),'vertices':len(ids),'boundsRaw':[v[ids].min(0).tolist(),v[ids].max(0).tolist()],
        'centerRaw':v[ids].mean(0).tolist(),'degrees':dict(Counter(degree.values()))})
face_neighbors=defaultdict(set)
for faces in body_edges.values():
    if len(faces)==2:
        face_neighbors[faces[0]].add(faces[1]);face_neighbors[faces[1]].add(faces[0])
eyes=[]
for side in ['l','r']:
    joint_polys=np.flatnonzero(groups=='joint-'+side+'-eye')
    joint_ids=np.unique([i for fi in joint_polys for i in polys[fi]])
    center=v[joint_ids].mean(0)
    nearest=min(loops,key=lambda loop:np.linalg.norm(np.array(loop['centerRaw'])-center))
    eye_ids=set(nearest['vertexIDs'])
    current=set(fi for edge,faces in body_edges.items() if set(edge)<=eye_ids for fi in faces)
    selected=set(current); layers=[]
    for depth in range(1,7):
        if depth>1:
            current={b for a in current for b in face_neighbors[a]}-selected
            selected|=current
        edges=Counter(edge for fi in selected for edge in [tuple(sorted((a,b))) for a,b in zip(polys[fi],polys[fi][1:]+polys[fi][:1])])
        patch_boundary=np.array([edge for edge,n in edges.items() if n==1])
        patch_adj=coo_matrix((np.ones(len(patch_boundary)),(patch_boundary[:,0],patch_boundary[:,1])),shape=(len(v),len(v))).tocsr()
        _,patch_labels=connected_components(patch_adj,directed=False)
        local_loops=[]
        for label in np.unique(patch_labels[np.unique(patch_boundary)]):
            ids=np.unique(patch_boundary[patch_labels[patch_boundary[:,0]]==label])
            degree=Counter(patch_boundary[patch_labels[patch_boundary[:,0]]==label].ravel())
            local_loops.append({'vertices':len(ids),'vertexIDs':ids.tolist(),'degrees':dict(Counter(degree.values())),
                'boundsRaw':[v[ids].min(0).tolist(),v[ids].max(0).tolist()]})
        used=np.unique([i for fi in selected for i in polys[fi]])
        layers.append({'layersFromAperture':depth,'quads':len(selected),'vertices':len(used),
            'sourceFaceIDs':sorted(selected),'boundaryLoops':local_loops,
            'boundsRaw':[v[used].min(0).tolist(),v[used].max(0).tolist()]})
    eyes.append({'side':side,'jointEyeCenterRaw':center.tolist(),'aperture':nearest,'nativeFaceLayers':layers})
report={'status':'Read-only anatomical donor feasibility; no graft or appearance acceptance',
    'source':str(BASE),'sha256':hashlib.sha256(raw).hexdigest(),'sourceHeader':raw.decode().splitlines()[:16],
    'license':'Explicit CC0 September2020 in source OBJ header','bodyQuads':len(body),
    'bodyBoundaryLoops':loops,'eyes':eyes,
    'units':'Native OBJ raw units; MPFB customary .1 scale converts to meters, but donor fit must be measured independently.',
    'limits':['Native body orbital quad strip, not historical production rider.',
        'Raw Basis source shape; no baked age/gender/race macro or accepted source-fit claim.',
        'No head/body source changes, GPU, Blender render, new analytic lid rings or model generation.']}
assert BASE.read_bytes()==raw
(OUT/'audit.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:val for k,val in report.items() if k not in ['bodyBoundaryLoops','eyes']},indent=2))
for eye in eyes:
    print(eye['side'],'joint',eye['jointEyeCenterRaw'],'aperture',eye['aperture'])
    print([{k:val for k,val in layer.items() if k not in ['sourceFaceIDs','boundaryLoops']}|{'loops':[(l['vertices'],l['degrees']) for l in layer['boundaryLoops']]} for layer in eye['nativeFaceLayers']])
