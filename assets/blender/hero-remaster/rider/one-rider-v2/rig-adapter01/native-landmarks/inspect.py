"""Read-only measured native hand bind mapping and current garment envelopes.

Envelope centroids do not measure joints hidden under clothing. No rig is built,
no source positions are edited, and no native finger curl is applied.
"""
import hashlib,json,math
from pathlib import Path
import bpy,numpy as np
from mathutils import Matrix,Vector
from mathutils.kdtree import KDTree
ROOT=Path('/Users/raynos/projects/games/rockhop');BASE=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2')
OUT=ROOT/'docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/native-landmarks';RUN=BASE/'rig-adapter01/native-landmarks'
NATIVE=BASE/'glove-cleanup/mpfb-trial2/fresh-anatomical-source.blend'
BODY=BASE/'glove-cleanup/glove-material/isolated-correction01/bodyPBR.blend'
COMPLETE=BASE/'parent-assembly/donor-fit05/rider.blend'
MAT=ROOT/'docs/evidence/hero-remaster/one-rider-v2/glove-cleanup/neutral-assembly/native-rig-adapter-matrices.json'
PROOF=ROOT/'docs/evidence/hero-remaster/one-rider-v2/glove-cleanup/neutral-assembly/native-weight-proof.json'
NEUTRAL=ROOT/'docs/evidence/hero-remaster/one-rider-v2/glove-cleanup/mpfb-trial2/neutral-anatomy/report.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rows(m):return [list(r) for r in m]
sources=[NATIVE,BODY,COMPLETE,MAT,PROOF,NEUTRAL];before={str(p):sha(p) for p in sources}
mat=json.loads(MAT.read_text());proof=json.loads(PROOF.read_text());neutral=json.loads(NEUTRAL.read_text())
bpy.ops.wm.open_mainfile(filepath=str(NATIVE));arm=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE')
nativebones={b.name:{'headLocal':list(b.head_local),'tailLocal':list(b.tail_local),'matrixLocal':rows(b.matrix_local),'parent':b.parent.name if b.parent else None,'useDeform':b.use_deform} for b in arm.data.bones}
allbones={'armatureName':arm.name,'nativeBoneCount':len(nativebones),'armatureMatrixWorld':rows(arm.matrix_world),'bones':nativebones,'sourceSHA256':before[str(NATIVE)]}
(OUT/'native-bones.json').write_text(json.dumps(allbones,indent=2)+'\n')
hands=[]
for h in mat['hands']:
 side=h['side'];m=Matrix(h['sourceArmatureLocalToBodyMatrix']);boneout={}
 for name,b in nativebones.items():
  if name==f'wrist.{side}' or ((name.startswith('finger') or name.startswith('metacarpal') or name.startswith('lowerarm')) and name.endswith('.'+side)):
   boneout[name]={**b,'bodyHead':list(m@Vector(b['headLocal'])),'bodyTail':list(m@Vector(b['tailLocal'])),'nativeBindToBody':rows(m@Matrix(b['matrixLocal']))}
 for name,b in h['nativeBones'].items():
  assert (Vector(boneout[name]['bodyHead'])-Vector(b['bodyHead'])).length<1e-6
 wrist=Vector(boneout[f'wrist.{side}']['bodyHead']);knuckles=[Vector(boneout[f'finger{i}-1.{side}']['bodyHead']) for i in range(2,6)]
 km=sum(knuckles,Vector())/4;palmcentre=(wrist+km)/2;length=(km-wrist).normalized();width=knuckles[0]-knuckles[-1];width=(width-length*width.dot(length)).normalized();normal=width.cross(length).normalized()
 f=next(r['nativeFrame'] for r in neutral['hands'] if r['side']==side)
 source_normal=m.to_3x3()@Vector(f['normal'])
 hands.append({'nativeAnatomicalSide':side,'currentBodyXSign':1 if wrist.x>0 else -1,'wristJoint':list(wrist),'knuckleCentroid':list(km),'skeletalPalmCentre':list(palmcentre),'skeletalPalmCentreDefinition':'Midpoint of native wrist and four actual MCP joint heads; not a surface contact point','palmLongAxisWristToMCP':list(length),'palmWidthIndexToLittle':list(width),'palmPlaneNormalCrossWidthLength':list(normal),'sourceCanonicalNormalMapped':list(source_normal),'palmNormalSignStatus':'Plane axis measured; palm-vs-dorsum sign requires surface witness, not inferred from color','sourceArmatureToBody':rows(m),'bones':boneout})
bpy.ops.wm.open_mainfile(filepath=str(BODY));body=next(o for o in bpy.context.scene.objects if o.type=='MESH');bodypoints=np.array([body.matrix_world@v.co for v in body.data.vertices]);groups={g.index:g.name for g in body.vertex_groups}
sourceweights=[]
for h in proof['hands']:
 first=h['firstNativeVertexIndex'];count=h['nativeVertices'];sourceweights.append((h['side'],bodypoints[first:first+count],[[[groups[g.group],g.weight] for g in v.groups] for v in body.data.vertices[first:first+count]]))
bpy.ops.wm.open_mainfile(filepath=str(COMPLETE));meshes=[o for o in bpy.context.scene.objects if o.type=='MESH'];inventory=[];vertices=[];triangles=[];offset=0
for o in meshes:
 o.data.calc_loop_triangles();p=np.array([o.matrix_world@v.co for v in o.data.vertices]);t=np.array([list(x.vertices) for x in o.data.loop_triangles],dtype=np.int64)
 inventory.append({'object':o.name,'vertices':len(p),'triangles':len(t),'matrixWorld':rows(o.matrix_world),'vertexGroups':len(o.vertex_groups),'armatureModifiers':sum(m.type=='ARMATURE' for m in o.modifiers),'bounds':[p.min(0).tolist(),p.max(0).tolist()]});vertices.append(p);triangles.append(t+offset);offset+=len(p)
vs=np.concatenate(vertices);tris=np.concatenate(triangles);tree=KDTree(len(vs))
for i,p in enumerate(vs):tree.insert(Vector(p),i)
tree.balance();matches=[]
for side,points,weights in sourceweights:
 actual=[tree.find(Vector(p)) for p in points];errors=[d for p,i,d in actual];ids=[i for p,i,d in actual]
 matches.append({'nativeSide':side,'nativeVertices':len(points),'maximumNearestPositionErrorM':max(errors),'matchedUniqueCompleteVertices':len(set(ids)),'allNativeVerticesPreservedWithin1Micron':max(errors)<1e-6,'completeVertexIds':ids,'nativeWeights':weights,'weightStatus':'Native authoring weights read from untouched protected body source; selected complete mesh has no proven runtime weights'})
 assert max(errors)<1e-6,'Native glove coordinates no longer match complete body'
(OUT/'native-weight-transfer-map.json').write_text(json.dumps({'status':'Read-only source weights and exact-position correspondence; no applied rig weights','matches':matches},indent=2)+'\n')
# Actual plane intersections, with connected edge chains. Quantization <=1 micron.
def section(z):
 points=vs[tris];d=points[:,:,2]-z;mask=(d.min(1)<0)&(d.max(1)>0);segs=[]
 for t,dd in zip(points[mask],d[mask]):
  q=[]
  for i,j in [(0,1),(1,2),(2,0)]:
   if dd[i]*dd[j]<0:q.append(t[i]+(-dd[i]/(dd[j]-dd[i]))*(t[j]-t[i]))
  if len(q)==2:segs.append(q)
 adj={};pos={};lengths={}
 for a,b in segs:
  ka=tuple(np.round(a,6));kb=tuple(np.round(b,6))
  if ka==kb:continue
  adj.setdefault(ka,set()).add(kb);adj.setdefault(kb,set()).add(ka);pos[ka]=a;pos[kb]=b;lengths[frozenset((ka,kb))]=float(np.linalg.norm(a-b))
 unseen=set(adj);out=[]
 while unseen:
  k=next(iter(unseen));pending=[k];ids={k};unseen.remove(k)
  while pending:
   for n in adj[pending.pop()]:
    if n in unseen:unseen.remove(n);ids.add(n);pending.append(n)
  pairs={frozenset((k,n)) for k in ids for n in adj[k]};total=sum(lengths[p] for p in pairs)
  if total<.01:continue
  centre=sum(((pos[list(p)[0]]+pos[list(p)[1]])*.5*lengths[p] for p in pairs),np.zeros(3))/total;p=np.array([pos[k] for k in ids])
  out.append({'arcLengthM':total,'arcWeightedSurfaceCentre':centre.tolist(),'bounds':[p.min(0).tolist(),p.max(0).tolist()],'vertices':len(ids),'closedLoop':all(len(adj[k])==2 for k in ids)})
 return sorted(out,key=lambda r:r['arcWeightedSurfaceCentre'][0])
sections=[{'planeZ':z,'status':'Measured garment/skin/sole surface envelope, not hidden skeletal joint','components':section(z)} for z in [.035,.06,.10,.14,.20,.30,.40,.45,.50,.55,.60,.70,.80,.90,.95,1.00,1.05,1.10,1.15,1.20,1.25,1.30,1.35,1.40,1.45,1.50]]
sole=[]
for side,sign in [('L',1),('R',-1)]:
 footids=np.flatnonzero((vs[:,0]*sign>.03)&(vs[:,2]<.12));p=vs[footids];minimum=float(p[:,2].min());contact=p[p[:,2]<=minimum+.002]
 sole.append({'nativeAnatomicalSide':side,'surfaceMinimumZ':minimum,'bottom2mmVertexCount':len(contact),'bottom2mmSurfaceBounds':[contact.min(0).tolist(),contact.max(0).tolist()],'bottom2mmVertexCentroid':contact.mean(0).tolist(),'definition':'Measured unweighted centroid of actual bottom2mm mesh vertices. Not yet a chosen biomechanical peg contact socket.','footEnvelopeBelow120mm':[p.min(0).tolist(),p.max(0).tolist()]})
(OUT/'body-envelope-sections.json').write_text(json.dumps({'canonicalFrame':'Current Blender authoring world: Z up; +X native anatomical L, -X native anatomical R; negativeY reference front','inventory':inventory,'sections':sections,'soleSurfaceWitnesses':sole,'limits':['Clothes obscure joint centres; no inferred hidden joint is labelled measured.','Native arm bones proximal to hand were transported rigidly with hand patch and are not the new body elbow joint.','No final19bone/socket/IK adaptation or runtime contact proof.']},indent=2)+'\n')
report={'status':'Measured source native hand landmarks and complete body envelope only; no appearance score or rig gate','sourceHashesBefore':before,'sourceHashesAfter':{str(p):sha(p) for p in sources},'recipeSHA256':sha(Path(__file__)),'nativeBoneCount':len(nativebones),'hands':hands,'completeMeshInventory':inventory,'nativeHandPositionCorrespondence':[ {k:v for k,v in m.items() if k not in ['nativeWeights','completeVertexIds']} for m in matches],'soleSurfaceWitnesses':sole,'bodyEnvelopeFile':'body-envelope-sections.json','limits':['Skeletal palm centre is not a visible palm/grip contact.','Palm-plane sign is explicitly unverified until native surface witness.','Bone positions for shoulders, elbow, hip, knee, ankle cannot be measured under clothes; use documented estimates and deformation tests.','No fixed curl, fingertip sockets or historical production donor.','No source was saved or altered.']}
assert report['sourceHashesBefore']==report['sourceHashesAfter']
(OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n');print('READ_ONLY_NATIVE_LANDMARKS_FROZEN',len(nativebones),flush=True)
