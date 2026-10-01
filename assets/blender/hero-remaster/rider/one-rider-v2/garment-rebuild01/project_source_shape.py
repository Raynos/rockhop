"""One CPU semantic/normal-aware fit; original quad mesh fields stay frozen."""
import bpy, hashlib, json, time
from pathlib import Path
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

repo = Path('/Users/raynos/projects/games/rockhop')
root = Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/garment-rebuild01')
run = root/'silhouette02'; out = repo/'docs/evidence/hero-remaster/one-rider-v2/garment-rebuild01/silhouette02'
frozen = (root/'fit01.npz').read_bytes(); fit = np.load(root/'fit01.npz')
P = fit['positions']; W = fit['weights']; Q = fit['quads']
data = np.load(run/'source-target.npz'); S = data['positions']; T = data['triangles']
tri = np.concatenate([Q[:,[0,1,2]], Q[:,[0,2,3]]])
cross = np.cross(P[tri[:,1]]-P[tri[:,0]],P[tri[:,2]]-P[tri[:,0]])
normal = np.zeros_like(P)
for i in range(3): np.add.at(normal,tri[:,i],cross)
normal /= np.maximum(np.linalg.norm(normal,axis=1,keepdims=True),1e-20)
topo = json.loads((out.parent/'native02-topology-audit.json').read_text())
jeans = np.zeros(len(P),dtype=bool)
for c in topo['components']:
    if c['vertices']==886: jeans[np.unique(Q[c['sourceFaceIndices']])]=True
assert jeans.sum()==886
labels=[]
for i in range(len(P)):
    if jeans[i]: label='jeans'
    elif W[i,[6,7,8]].sum()>.4: label='shirtL'
    elif W[i,[10,11,12]].sum()>.4: label='shirtR'
    else: label='shirtTorso'
    labels.append(label)
trees={name:BVHTree.FromPolygons(S.tolist(),T[data[name]].tolist(),all_triangles=True)
       for name in ['shirtL','shirtR','shirtTorso','jeans']}
target=np.zeros_like(P); rows=[]; start=time.monotonic()
for i,(point,label) in enumerate(zip(P,labels)):
    candidates=trees[label].find_nearest_range(Vector(point),.16)
    accepted=[]
    for pos,nor,face,distance in candidates:
        dot=float(normal[i]@np.array(nor))
        if dot>.2: accepted.append((distance*distance+.0004*(1-dot)**2,pos,distance,dot))
    if not accepted:
        raise RuntimeError(f'No oriented semantic source within16cm: vertex{i} {label}')
    cost,pos,distance,dot=min(accepted,key=lambda x:x[0]);target[i]=pos
    rows.append({'vertex':i,'scope':label,'sourceDistanceM':float(distance),'normalDot':dot})
    assert time.monotonic()-start<900,'Own CPU correspondence batch stopped at15minutes'
# Smooth displacements, not the source or topology. Fixed one-pass mechanism;
# no parameter search. Native boundary follows chosen target before stitching.
neighbors=[set() for _ in P]
for quad in Q:
    for a,b in zip(quad,np.roll(quad,-1)):
        neighbors[a].add(int(b));neighbors[b].add(int(a))
delta=target-P
for _ in range(8):
    average=np.array([delta[list(ids)].mean(0) for ids in neighbors])
    delta=.8*(target-P)+.2*average
result=P+delta
restEdge=np.linalg.norm(P[tri]-np.roll(P[tri],-1,axis=1),axis=2)
newEdge=np.linalg.norm(result[tri]-np.roll(result[tri],-1,axis=1),axis=2)
newCross=np.cross(result[tri[:,1]]-result[tri[:,0]],result[tri[:,2]]-result[tri[:,0]])
dots=(newCross*cross).sum(1)/np.maximum(np.linalg.norm(newCross,axis=1)*np.linalg.norm(cross,axis=1),1e-20)
ratio=newEdge/np.maximum(restEdge,1e-20)
path=run/'fit02.npz';assert not path.exists()
np.savez_compressed(path,positions=result,weights=W,quads=Q,uvLoops=fit['uvLoops'],
                    sourceCorrespondence=target,scope=np.array(labels))
assert (root/'fit01.npz').read_bytes()==frozen
updated=np.load(path)
for key in ['weights','quads','uvLoops']:assert np.array_equal(updated[key],fit[key])
bpy.ops.wm.read_factory_settings(use_empty=True)
mesh=bpy.data.meshes.new('Clean_garment_source_silhouette02')
mesh.from_pydata([(p[0],-p[2],p[1]) for p in result],[],Q.tolist());mesh.update()
obj=bpy.data.objects.new('Source_fitted_clean_garment02_UNACCEPTED',mesh);bpy.context.collection.objects.link(obj)
layer=mesh.uv_layers.new(name='Native_garment_bake_UV')
for loop,uv in zip(layer.data,fit['uvLoops']):loop.uv=uv
canonical=['pelvis','spine','chest','neck','head','shoulder.L','upperArm.L','forearm.L','hand.L','shoulder.R','upperArm.R','forearm.R','hand.R','thigh.L','shin.L','foot.L','thigh.R','shin.R','foot.R']
for name in canonical:obj.vertex_groups.new(name=name)
for i,weights in enumerate(W):
    for j,w in enumerate(weights):
        if w>0:obj.vertex_groups[j].add([i],float(w),'REPLACE')
for polygon in mesh.polygons:polygon.use_smooth=True
bpy.ops.wm.save_as_mainfile(filepath=str(run/'fit02.blend'),compress=True)
report={'status':'One source-semantic silhouette fit; unaccepted construction master',
        'seconds':time.monotonic()-start,'vertices':len(P),'quads':len(Q),
        'sourceFit01SHA256':hashlib.sha256(frozen).hexdigest(),
        'fit02SHA256':hashlib.sha256(path.read_bytes()).hexdigest(),
        'geometryChangedOnly':True,'weightsUVTopologyExact':True,
        'scopeCounts':{k:labels.count(k) for k in trees},
        'displacementQuantilesM':np.quantile(np.linalg.norm(result-P,axis=1),[0,.5,.9,.99,1]).tolist(),
        'fitResidualQuantilesM':np.quantile(np.linalg.norm(result-target,axis=1),[0,.5,.9,.99,1]).tolist(),
        'restNormalOpposition':int((dots<-.2).sum()),
        'restEdgeChangeQuantiles':np.quantile(ratio,[0,.5,.9,.99,1]).tolist(),
        'settings':{'radiusM':.16,'minimumNormalDot':.2,'normalPenaltyM2':.0004,
                    'nativeRoleBranchThreshold':.4,'fixedDisplacementRegularization':.2,'iterations':8},
        'limits':['Not stitched or textured; no complete asset or accepted riding deformation.',
                  'Source detail and protected head/hood/glove/shoe meshes remain untouched.',
                  'Correspondence geometry/shape gate and actual C19 pose audit required; no inherited quality pass.'],
        'correspondence':rows}
(out/'fit-report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k!='correspondence'}))
