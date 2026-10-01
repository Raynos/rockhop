"""Exact seam rings and proper runtime frame remap, read-only CPU2."""
import hashlib,json
from pathlib import Path
import bpy,numpy as np
from mathutils import Vector,Matrix
from mathutils.kdtree import KDTree
ROOT=Path('/Users/raynos/projects/games/rockhop');BASE=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2');OUT=ROOT/'docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/native-landmarks'
BODY=BASE/'glove-cleanup/glove-material/isolated-correction01/bodyPBR.blend';COMPLETE=BASE/'parent-assembly/donor-fit05/rider.blend';ASSEMBLY=ROOT/'docs/evidence/hero-remaster/one-rider-v2/glove-cleanup/neutral-assembly/report.json';PROOF=ASSEMBLY.parent/'native-weight-proof.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
before={str(p):sha(p) for p in [BODY,COMPLETE,ASSEMBLY,PROOF]};assembly=json.loads(ASSEMBLY.read_text());proof=json.loads(PROOF.read_text());landmarks=json.loads((OUT/'report.json').read_text());surface=json.loads((OUT/'surface-witness.json').read_text())
bpy.ops.wm.open_mainfile(filepath=str(BODY));body=next(o for o in bpy.context.scene.objects if o.type=='MESH');vs=np.array([body.matrix_world@v.co for v in body.data.vertices]);groups={g.index:g.name for g in body.vertex_groups};prefix=assembly['sourceVertexPrefixCount'];source_rings=[]
for h in proof['hands']:
 side=h['side'];first=h['firstNativeVertexIndex'];last=first+h['nativeVertices'];cage=BASE/f'glove-cleanup/mpfb-trial2/neutral-anatomy/display-complete/neutral-complete-{side}.npz';d=np.load(cage)
 ids={'sourceCutRing':[v.index for v in body.data.vertices[:prefix] if any(groups[g.group]=='wrist.'+side and g.weight>.999 for g in v.groups)],'transitionRing':list(range(last,last+22)),'nativeWristRim':[first+int(i) for i in d['wristLoop']]};source_rings.append((side,ids,cage,sha(cage)))
bpy.ops.wm.open_mainfile(filepath=str(COMPLETE));body=next(o for o in bpy.context.scene.objects if o.type=='MESH' and o.name.startswith('NEW protected'));complete=np.array([body.matrix_world@v.co for v in body.data.vertices]);tree=KDTree(len(complete))
for i,p in enumerate(complete):tree.insert(Vector(p),i)
tree.balance();rings=[]
for side,idsets,cage,cagehash in source_rings:
 h=next(h for h in landmarks['hands'] if h['nativeAnatomicalSide']==side);wrist=np.array(h['wristJoint']);axis=np.array(h['palmLongAxisWristToMCP']);rows={}
 for name,ids in idsets.items():
  p=vs[ids];hits=[tree.find(Vector(q)) for q in p];err=max(x[2] for x in hits);assert err<1e-6;axial=(p-wrist)@axis;radial=(p-wrist)-axial[:,None]*axis
  rows[name]={'sourceVertexCount':len(ids),'sourceVertexIds':ids,'completeVertexIds':[i for q,i,d in hits],'maximumPositionErrorM':err,'centroid':p.mean(0).tolist(),'bounds':[p.min(0).tolist(),p.max(0).tolist()],'axialDistanceFromWristM':[float(axial.min()),float(axial.max())],'radialDistanceFromWristAxisM':[float(np.linalg.norm(radial,axis=1).min()),float(np.linalg.norm(radial,axis=1).max())]}
 gap=float(np.dot(np.array(rows['nativeWristRim']['centroid'])-np.array(rows['sourceCutRing']['centroid']),axis));rings.append({'side':side,'sourceCage':str(cage),'sourceCageSHA256':cagehash,'rings':rows,'axialCentroidSeparationSourceCutToNativeRimM':gap,'status':'Three connected exact physical mesh seam rings. This is a connected collar/transition, not a two-shell sleeve overlap.','limits':['Hoodie cuff top is a texture boundary on source garment, not a separately named anatomical mesh boundary.','No claim that these ring envelopes prove moving cuff clearance; dynamic deformation remains required.']})
# Proper rotation: source->glTF->runtime orientation, then file-origin offset.
rotation=np.array([[0.,-1.,0.],[0.,0.,1.],[-1.,0.,0.]]);assert np.linalg.det(rotation)==1
runtime=[]
for h,s in zip(landmarks['hands'],surface['surfaces']):
 native=h['nativeAnatomicalSide'];semantic='R' if h['currentBodyXSign']==1 else 'L';palm=next(q for q in s['hits'] if q['canonicalNormalSign']==-1)
 def point(p):
  p=rotation@np.array(p);return {'axleMidpointFrame':p.tolist(),'fileRearAxleOriginFrame':(p+np.array([.65,0,0])).tolist()}
 runtime.append({'nativeSide':native,'runtimeContractSide':semantic,'wrist':point(h['wristJoint']),'skeletalPalmCentre':point(h['skeletalPalmCentre']),'actualPalmSurfaceWitness':point(palm['point']),'palmFacingAxis':(rotation@(-np.array(h['sourceCanonicalNormalMapped']))).tolist(),'fingerLongAxis':(rotation@np.array(h['palmLongAxisWristToMCP'])).tolist(),'thumbProximal':point(h['bones'][f'finger1-1.{native}']['bodyHead']),'bones':{k:{'head':point(v['bodyHead']),'tail':point(v['bodyTail'])} for k,v in h['bones'].items()},'sideEvidence':'Parent verified runtime contract +Z=L / -Z=R; proper rotation maps original +X/nativeL to runtime -Z/R and -X/nativeR to runtime +Z/L. Apply explicit name remap; do not reflect mesh.'})
after={p:sha(Path(p)) for p in before};assert before==after
(OUT/'cuff-runtime-frames.json').write_text(json.dumps({'status':'Exact source-native seam mapping and proper handed runtime orientation; no applied rig','sourceHashesBefore':before,'sourceHashesAfter':after,'rotationSourceBlenderToRuntime':rotation.tolist(),'determinant':float(np.linalg.det(rotation)),'fileRearAxleOffset':[.65,0,0],'runtimeSceneTranslation':[-.65,0,0],'normalOrientationEvidence':'Actual gray fronts show fingernails at red(+canonical) surface witness; actual rears show creases/pads at blue(-canonical) witness. Thus +canonical is dorsal and -canonical is palm. Parent judges independently.','rings':rings,'runtimeHands':runtime,'recipeSHA256':sha(Path(__file__))},indent=2)+'\n');print('EXACT_CUFF_RUNTIME_FRAME_FROZEN',flush=True)
