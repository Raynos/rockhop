"""Freeze fresh native morph result; UV and anatomy counts are not art approval."""
import argparse,hashlib,json,shutil
from pathlib import Path
from collections import defaultdict
import numpy as np
import trimesh
from PIL import Image,ImageDraw
ap=argparse.ArgumentParser(description=__doc__)
ap.add_argument('--runtime',required=True);ap.add_argument('--evidence',required=True)
a=ap.parse_args();source=Path(a.runtime);out=Path(a.evidence);out.mkdir(parents=True,exist_ok=True)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
construction=json.loads((source/'construction.json').read_text())
d=np.load(source/'head-skin.npz');v=d['vertices'];f=d['faces']
edges,counts=np.unique(np.sort(np.concatenate([f[:,[0,1]],f[:,[1,2]],f[:,[2,0]]]),axis=1),axis=0,return_counts=True)
adj=defaultdict(list)
for i,j in edges[counts==1]:adj[int(i)].append(int(j));adj[int(j)].append(int(i))
seen=set();boundaries=[]
for i in adj:
    if i in seen:continue
    stack=[i];ids=[]
    while stack:
        j=stack.pop()
        if j in seen:continue
        seen.add(j);ids.append(j);stack.extend(adj[j])
    boundaries.append(dict(vertices=len(ids),degrees=sorted(set(len(adj[j]) for j in ids)),
        bounds=[v[ids].min(0).tolist(),v[ids].max(0).tolist()]))
area=np.linalg.norm(np.cross(v[f[:,1]]-v[f[:,0]],v[f[:,2]]-v[f[:,0]]),axis=1)/2
scene=trimesh.load(source/'head.glb',force='scene',process=False)
eyes=min(scene.geometry.values(),key=lambda m:len(m.faces))
centers=[]
for side in [-1,1]:
    q=eyes.vertices[eyes.vertices[:,0]*side>0];centers.append((q.min(0)+q.max(0))/2)
ipd=float(np.linalg.norm(centers[1]-centers[0]))
for sub in ['gray','closeups']:
    dest=out/sub;dest.mkdir(exist_ok=True)
    for p in (source/sub).glob('*'):
        if p.suffix in ['.png','.json']:shutil.copy2(p,dest/p.name)
    canvas=Image.new('RGB',(1024,1666),(20,23,26));draw=ImageDraw.Draw(canvas)
    draw.text((12,10),'MPFB evaluated native young-adult male: '+sub,fill='white')
    draw.text((12,30),'ACTUAL CPU GRAY | UNACCEPTED | no bake or neck join',fill=(255,180,130))
    for n in range(4):
        img=Image.open(dest/f'{n:04d}.png').convert('RGB');img.thumbnail((512,768))
        x=(n%2)*512+(512-img.width)//2;y=54+(n//2)*806
        canvas.paste(img,(x,y));draw.text(((n%2)*512+12,y+776),['Front','Three-quarter','Profile','Rear'][n],fill='white')
    canvas.save(out/f'{sub}-four-views.jpg',quality=94)
shutil.copy2(source/'construction.json',out/'construction.json')
uv_report={}
for name,mesh in scene.geometry.items():
    uv=getattr(mesh.visual,'uv',None)
    uv_report[name]=dict(present=uv is not None,coordinates=0 if uv is None else len(uv),
        finite=False if uv is None else bool(np.isfinite(uv).all()),
        bounds=None if uv is None else [uv.min(0).tolist(),uv.max(0).tolist()])
report=dict(status='UNACCEPTED fresh evaluated native young-adult male; parent gray judgment required',
    verifierSHA256=sha(__file__),construction=construction,
    skinTopology=dict(vertices=len(v),triangles=len(f),boundaryEdges=int(np.sum(counts==1)),
        nonmanifoldEdges=int(np.sum(counts>2)),zeroAreaTriangles=int(np.sum(area<1e-12)),boundaries=boundaries),
    actualEyeSidedBoundingCentersNative=[p.tolist() for p in centers],
    actualEyeSidedCenterDistanceNative=ipd,estimatedWorldIPDMetersAtScale042=ipd*.42,
    exportedUVs=uv_report,
    masterHashes={str(p):sha(p) for p in [source/'fresh-native-source.blend',source/'head.blend',source/'head.glb',source/'head-skin.npz']},
    sourceProof={p:dict(before=s,after=sha(p),unchanged=sha(p)==s) for p,s in construction['sources'].items()},
    observed=['Actual installed male/young macro mix baked BEFORE anatomy extraction; no Basis bypass.',
        'Natural neutral expression, coherent jaw/nose, real eye/lip/ear loops and continuous scalp.',
        'No Gaussian facial shaping or dense snapping; prior two manual failures remain stopped.',
        'Adult male target likeness remains unaccepted; this is a NEW native anatomical alternative.',
        'Source-derived jagged neck base remains unjoined.',
        'Native source UV layers retained, but no skin texture, buzz material, bake, rig or moving evidence.'],
    limits=['Topology counts do not prove likeness or self-intersection freedom.',
        'Only uniform IPD scaling and translation; no initial manual anatomical deformation or dense fit.',
        'Both earlier head methods and all prior topology/appearance failures remain frozen.'])
assert all(x['unchanged'] for x in report['sourceProof'].values())
(out/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'status':report['status'],'evidence':str(out),'actualIPDNative':ipd,'sourceUnchanged':True}))
