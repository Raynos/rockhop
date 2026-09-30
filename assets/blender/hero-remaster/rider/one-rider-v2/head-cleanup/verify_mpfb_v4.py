"""Freeze actual anatomical prototypes; counts are not art acceptance."""
import argparse, hashlib, json, shutil
from collections import defaultdict
from pathlib import Path
import numpy as np
import trimesh
from PIL import Image, ImageDraw

ap=argparse.ArgumentParser(description=__doc__)
ap.add_argument('--runtime', required=True)
ap.add_argument('--evidence', required=True)
a=ap.parse_args()
runtime=Path(a.runtime); evidence=Path(a.evidence)
evidence.mkdir(parents=True,exist_ok=True)
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def boundary_report(v,f):
    edges,counts=np.unique(np.sort(np.concatenate([f[:,[0,1]],f[:,[1,2]],f[:,[2,0]]]),axis=1),axis=0,return_counts=True)
    adj=defaultdict(list)
    for i,j in edges[counts==1]:adj[int(i)].append(int(j));adj[int(j)].append(int(i))
    seen=set(); loops=[]
    for i in adj:
        if i in seen:continue
        stack=[i];ids=[]
        while stack:
            j=stack.pop()
            if j in seen:continue
            seen.add(j);ids.append(j);stack.extend(adj[j])
        loops.append(dict(vertices=len(ids),degrees=sorted(set(len(adj[j]) for j in ids)),
            bounds=[v[ids].min(0).tolist(),v[ids].max(0).tolist()],center=v[ids].mean(0).tolist()))
    area=np.linalg.norm(np.cross(v[f[:,1]]-v[f[:,0]],v[f[:,2]]-v[f[:,0]]),axis=1)/2
    return dict(boundaryEdges=int(np.sum(counts==1)),nonmanifoldEdges=int(np.sum(counts>2)),
        boundaryComponents=loops,zeroAreaTriangles=int(np.sum(area<1e-12)))
def board(files,path,title):
    w,h=512,768
    canvas=Image.new('RGB',(2*w,2*(h+38)+54),(20,23,26)); draw=ImageDraw.Draw(canvas)
    draw.text((12,10),title,fill='white')
    draw.text((12,28),'ACTUAL CPU GRAY | UNACCEPTED | no texture bake or body join',fill=(255,180,130))
    for n,p in enumerate(files):
        img=Image.open(p).convert('RGB');img.thumbnail((w,h))
        x=(n%2)*w+(w-img.width)//2;y=54+(n//2)*(h+38)
        canvas.paste(img,(x,y));draw.text(((n%2)*w+12,y+h+8),['Front','Three-quarter','Profile','Rear'][n],fill='white')
    canvas.save(path,quality=94)
report={'status':'UNACCEPTED anatomical prototype; parent rejects fitted cheek/nose scar and likeness',
    'prototypes':{},'verifierSHA256':sha(__file__)}
for key in ['mpfb-v4-fast','mpfb-v4-eye-aligned']:
    source=runtime/key; dest=evidence/key; dest.mkdir(exist_ok=True)
    construction=json.loads((source/'construction.json').read_text())
    shutil.copy2(source/'construction.json',dest/'construction.json')
    d=np.load(source/'head-skin.npz');v=d['vertices'];f=d['faces']
    topology=boundary_report(v,f)
    scene=trimesh.load(source/'head.glb',force='scene',process=False)
    eyes=next(m for k,m in scene.geometry.items() if 'eyes' in k)
    # GLB is native Y-up, front +Z. Asset contains separate cornea/sclera
    # shells for each eye, so report both sided bounds, not a false 2-mesh claim.
    centers=[]
    for side in [-1,1]:
        points=eyes.vertices[eyes.vertices[:,0]*side>0]
        centers.append((points.min(0)+points.max(0))/2)
    actual_ipd=float(np.linalg.norm(centers[1]-centers[0]))
    eye_components=[]
    for component in eyes.split(only_watertight=False):
        eye_components.append(dict(vertices=len(component.vertices),triangles=len(component.faces),
            bounds=component.bounds.tolist(),**boundary_report(component.vertices,component.faces)))
    item=dict(runtime=str(source),construction=construction,skinTopology=topology,
        actualEyeSidedBoundingCentersNative=[x.tolist() for x in centers],
        actualEyeSidedCenterDistanceNative=actual_ipd,
        estimatedWorldIPDMetersAtScale042=actual_ipd*.42,eyeComponents=eye_components,
        noUVBake=True,UVLimit='Construction from_pydata drops source UV coordinates; no usable character UV/bake is claimed.',
        masterHashes={str(p):sha(p) for p in [source/'head.glb',source/'head.blend',source/'head-skin.npz',source/'fit-samples.npz']})
    for sub in ['gray','closeups']:
        target=dest/sub;target.mkdir(exist_ok=True)
        for p in sorted((source/sub).glob('*')):
            if p.suffix in ['.png','.json']:shutil.copy2(p,target/p.name)
        board([target/f'{n:04d}.png' for n in range(4)],dest/f'{sub}-four-views.jpg',f'{key}: {sub}')
    (dest/'verification.json').write_text(json.dumps(item,indent=2)+'\n')
    report['prototypes'][key]=item
report['remainingVisibleDefects']=['Aligned eyes improved, but visible left cheek/nose scar rejects bounded fit.',
    'Jaw/brow read delicate and generic compared with approved adult male target; no likeness acceptance.',
    'Single 224-edge anatomical neck base remains jagged and unjoined; no hood/body join.',
    'Neutral scalp has no buzz material, eyebrows, eyelashes, beard, or skin texture.',
    'Fresh eye surfaces are four source cornea/sclera components, not welded into face or individually rigged.']
report['preservedFailureCounts']='Two original head repairs, two unconstrained implementation gates, and rejected constrained cage remain frozen. This anatomical alternative does not reset them.'
report['sourceProof']={p:{'before':s,'after':sha(p),'unchanged':sha(p)==s} for p,s in construction['sources'].items()}
assert all(x['unchanged'] for x in report['sourceProof'].values())
(evidence/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'status':report['status'],'evidence':str(evidence),'sourcesUnchanged':True}))
