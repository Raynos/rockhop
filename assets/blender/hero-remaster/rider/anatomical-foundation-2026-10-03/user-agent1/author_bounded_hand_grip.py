"""One bounded glove binding/contact pose candidate; no render or scope expansion."""
import hashlib,json
from pathlib import Path
import bpy,numpy as np
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
root=Path(__file__).resolve().parents[6];owned=Path(__file__).resolve().parent;ev=root/'docs/evidence/hero-remaster/anatomical-foundation-2026-10-03/user-agent1';scopepath=ev/'hand-grip104/scope.json';scope=json.loads(scopepath.read_text());out=ev/'hand-grip106';out.mkdir(parents=True,exist_ok=True);native=owned/'hand-grip01/bounded-full-four.blend';native.parent.mkdir(parents=True,exist_ok=True);assert not native.exists()
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();n=np.load(ev/'hand-grip104/source-fields.npz');names=n['boneNames'].tolist();allowed=[names.index(x) for x in scope['scope']['weightBoneNames']];outside=np.setdiff1d(np.arange(51),allowed);source=root/scope['immutableControl']['path'];finitepath=root/scope['physicalChecks']['actualSurfaceSource'];driverpath=ev/'hand-grip105/actual-driver.json';exportfield=root/'docs/evidence/hero-remaster/user-agent3-qa-2026-10-03/grip74/export-hand-fields.npz';helper=root/'docs/evidence/hero-remaster/user-agent3-qa-2026-10-03/neck62/read-native.py';queryrecipe=root/'docs/evidence/hero-remaster/user-agent3-qa-2026-10-03/grip74/measure-grip.py'
inputs=[source,scopepath,ev/'hand-grip104/source-fields.npz',finitepath,driverpath,exportfield,helper,queryrecipe];driver=json.loads(driverpath.read_text());inputs += [root/c['file'] for c in driver['cases']];pins={str(p.relative_to(root)):sha(p) for p in inputs};assert sha(source)==scope['immutableControl']['sha256']
for p,h in scope['pins'].items():assert sha(root/p)==h,p
qtext=queryrecipe.read_text();qh=dict(np=np);exec(compile(qtext[qtext.index('def point_query('):qtext.index('# Native rest ancestry:')],str(queryrecipe),'exec'),qh);query=qh['point_query']
text=helper.read_text();h=dict(bpy=bpy,np=np,hashlib=hashlib);exec(compile(text[text.index('def digest('):text.index('for label,path in paths.items():')],str(helper),'exec'),h)
bpy.ops.wm.open_mainfile(filepath=str(source));control=json.loads((ev/'hand-grip104/immutable-control.json').read_text());orig=bpy.data.objects[scope['objects']['glove']['object']];rig=bpy.data.objects['Independent anatomical foundation rig'];assert {o.name:h['state'](o) for o in bpy.data.objects}==control['objects'];assert h['materials']()==control['materials']
P=n['gloveXYZ'].astype(float);body=n['bodyXYZ'].astype(float);bt=n['bodyTriangles'];bw=n['bodyWeights'].astype(float);old=n['gloveWeights'];full=old.astype(float).copy();ancestry=[];barys=[];distance=[];fallback=[];tree=BVHTree.FromPolygons(body.tolist(),bt.tolist(),all_triangles=True,epsilon=0.)
for i,p in enumerate(P):
 q,normal,ti,d=tree.find_nearest(Vector(p));t=bt[ti];v=body[t];uv=np.linalg.lstsq(np.column_stack([v[1]-v[0],v[2]-v[0]]),np.array(q)-v[0],rcond=None)[0];b=np.clip([1-uv.sum(),uv[0],uv[1]],0,1);b/=b.sum();row=b@bw[t][:,allowed];mass=float(old[i,allowed].sum())
 if row.sum()>0:full[i,allowed]=row/row.sum()*mass
 else:fallback.append(i)
 ancestry.append(int(ti));barys.append(b);distance.append(float(d))
full=full.astype(np.float32);assert np.array_equal(full[:,outside],old[:,outside]);assert np.isfinite(full).all()
four=full.copy();removed=[]
for i,row in enumerate(full):
 fixed=int((row[outside]>0).sum());slots=4-fixed;assert slots>0;ids=sorted((j for j in allowed if row[j]>0),key=lambda j:(-row[j],j));keep=ids[:slots];drop=ids[slots:];lost=float(row[drop].sum());removed.append(lost);four[i,allowed]=0
 if keep:four[i,keep]=row[keep]*(float(row[allowed].sum())/float(row[keep].sum()))
assert np.array_equal(four[:,outside],old[:,outside]);assert (four>0).sum(1).max()<=4;assert np.max(np.abs(full.sum(1)-old.sum(1)))<1e-6 and np.max(np.abs(four.sum(1)-old.sum(1)))<1e-6
newrig=rig.copy();newrig.data=rig.data.copy();newrig.name='Bounded actual-grip01 original51 rig, unaccepted';bpy.context.collection.objects.link(newrig);newrig.animation_data_clear();objects=[];fields=[]
for label,weights in [('full',full),('four',four)]:
 o=orig.copy();o.data=orig.data.copy();o.name='Bounded actual-grip01 glove '+label+', unaccepted';bpy.context.collection.objects.link(o)
 for v in o.data.vertices:
  for j in allowed:
   g=o.vertex_groups[names[j]]
   if weights[v.index,j]>0:g.add([v.index],float(weights[v.index,j]),'REPLACE')
   else:g.remove([v.index])
 for mod in o.modifiers:
  if mod.type=='ARMATURE':mod.object=newrig
 o.hide_render=True;o.hide_set(True);objects.append(o.name);measured=np.zeros_like(weights)
 for v in o.data.vertices:
  for g in v.groups:
   name=o.vertex_groups[g.group].name
   if name in names:measured[v.index,names.index(name)]=g.weight
 assert np.array_equal(measured,weights);fields.append(measured)
# Native rest/file conversion is pinned; actual source37 driver is transferred as
# effective skin applied to THIS exact native rest, not a byte-identity claim.
C=np.array([[1,0,0,0],[0,0,1,0],[0,-1,0,0],[0,0,0,1]],float);rest=C@n['rigWorld']@n['rigRest'];gloveFile=(np.column_stack([P,np.ones(len(P))])@(C@n['gloveWorld']).T)[:,:3];native_rest=n['rigRest'];parents=n['parents'];e=np.load(exportfield);eo=e['jointNames'].tolist();order=[eo.index(s) for s in names];ib=e['inverseBinds'][order];actualRest=np.linalg.inv(ib);rigResidual=float(np.abs(actualRest-rest).max());assert rigResidual<5e-6
rows=[]
for case in driver['cases']:
 data=json.loads((root/case['file']).read_text());assert sha(root/case['file'])==case['sha256']
 for row in data['samples']:rows.append((case['id'],row))
finite=json.loads(finitepath.read_text())['bikes'][0];assert finite['file']=='bike-rookie.glb';grips={g['side']:g for g in finite['grips']};local=np.array([np.linalg.inv(rest[int(parents[j])])@rest[j] if parents[j]>=0 else rest[j] for j in range(51)])
unit=lambda v:v/np.linalg.norm(v)
def rotate(axis,angle):
 x,y,z=unit(axis);K=np.array([[0,-z,y],[z,0,-x],[-y,x,0]]);R=np.eye(4);R[:3,:3]=np.eye(3)+np.sin(angle)*K+(1-np.cos(angle))*(K@K);return R
# Select actual source glove palm ray point from own anatomical MCP/thumbnail cues.
palms={};widths={};signs={};targets={};glovetree=BVHTree.FromPolygons(gloveFile.tolist(),n['gloveTriangles'].tolist(),all_triangles=True)
for side in ['L','R']:
 ix=lambda s:names.index(s+'.'+side)
 wrist=rest[ix('hand'),:3,3];mcp=rest[ix('middle_01'),:3,3];width=unit(rest[ix('pinky_01'),:3,3]-rest[ix('index_01'),:3,3]);long=unit((mcp-wrist)-width*np.dot(width,mcp-wrist));cross=unit(np.cross(width,long));thumb=rest[ix('thumb_02'),:3,3]-(wrist+.55*(mcp-wrist));sign=1 if np.dot(thumb,cross)>0 else -1;palmar=sign*cross;center=wrist+.55*(mcp-wrist);q,nn,ti,dist=glovetree.ray_cast(Vector(center),Vector(palmar),.10)
 if q is None:q,nn,ti,dist=glovetree.find_nearest(Vector(center));method='ray miss: exact nearest finite glove fallback, no semantic acceptance'
 else:method='actual finite glove first ray hit from source wrist-to-middleMCP55% along thumb-sided palmar normal'
 tri=n['gloveTriangles'][ti];v=gloveFile[tri];uv=np.linalg.lstsq(np.column_stack([v[1]-v[0],v[2]-v[0]]),np.array(q)-v[0],rcond=None)[0];b=np.array([1-uv.sum(),uv[0],uv[1]]);palms[side]={'sourceGloveTriangleID':int(ti),'nativeVertexIDs':tri.tolist(),'barycentric':b.tolist(),'sourcePointFileWorldM':list(q),'selection':method,'sourcePalmarNormalFile':palmar.tolist()};widths[side]=(width,long,cross);signs[side]=sign
# ONE fixed finger flex candidate, no angle sweep. Targets/skin are measured below.
angles={'index':[55,80,65],'middle':[55,80,65],'ring':[55,80,65],'pinky':[55,80,65],'thumb':[50,55,60]};flex={}
for side in ['L','R']:
 for finger,degs in angles.items():
  for segment,deg in zip(['01','02','03'],degs):
   j=names.index(finger+'_'+segment+'.'+side);axis=rest[j,:3,:3].T@widths[side][0];R=rotate(axis,np.radians(signs[side]*deg))
   if finger=='thumb' and segment=='01':R=rotate(rest[j,:3,:3].T@widths[side][1],np.radians(35*signs[side]))@R
   flex[j]=R

def pose(row):
 obs=row['observation'];B=np.array(obs['bikeFrameWorld']).reshape(4,4).T;obsnames=[r['name'] for r in obs['bones']];exportnames=[s.replace('.','') for s in names];assert len(set(exportnames))==51 and set(exportnames)==set(obsnames);W=np.array([obs['bones'][obsnames.index(s)]['world'] for s in exportnames]).reshape(51,4,4).transpose(0,2,1);candidate=W@ib@rest;source_retarget=candidate.copy();correspondences={}
 for side in ['L','R']:
  g=grips[side];width=unit(np.array(g['fit']['outwardAxisFileFrame']));hi=names.index('hand.'+side);fi=names.index('forearm.'+side);forearm=unit((np.linalg.inv(B)@candidate[fi])[:3,1]);length=unit(forearm-width*np.dot(width,forearm));normal=unit(np.cross(width,length));radial=-signs[side]*normal;center=(np.array(g['fit']['innerRingCenterBikeFrame'])+np.array(g['fit']['outerRingCenterBikeFrame']))*.5
  d,inside,which,q=query([center+radial*.05],np.array(g['trianglesBikeFrame']));R=np.column_stack([width,length,normal])@np.column_stack(widths[side]).T;anchor=np.array(palms[side]['sourcePointFileWorldM']);desired=np.eye(4);desired[:3,:3]=R;desired[:3,3]=q[0]+radial*.0005-R@anchor;S=B@desired;candidate[hi]=S@rest[hi]
  correspondences[side]={'targetBikeFrameM':(q[0]+radial*.0005).tolist(),'finiteGripPointBikeFrameM':q[0].tolist(),'sourceGripTriangleOrdinal':g['sourceTriangleOrdinals'][int(which[0])],'clearanceM':.0005,'wristTargetWorld':candidate[hi,:3,3].tolist()}
  for finger in angles:
   for segment in ['01','02','03']:
    j=names.index(finger+'_'+segment+'.'+side);candidate[j]=candidate[int(parents[j])]@local[j]@flex[j]
 assert np.array_equal(candidate[outside],source_retarget[outside])
 return B,candidate,correspondences
B,first,first_targets=pose(rows[0][1]);basis={}
for j in allowed:
 pi=int(parents[j]);base=np.linalg.inv(local[j])@np.linalg.inv(first[pi])@first[j];pb=newrig.pose.bones[names[j]];pb.rotation_mode='QUATERNION';pb.matrix_basis=Matrix(base.tolist());basis[names[j]]=np.array(pb.matrix_basis).tolist()
# All originals remain EXACT. Copied rig only listed poses changed.
for j in outside:assert h['state'](rig)['armature']['pose'][names[j]]==h['state'](newrig)['armature']['pose'][names[j]]
for name,state in control['objects'].items():assert h['state'](bpy.data.objects[name])==state,name
assert h['materials']()==control['materials'];bpy.ops.wm.save_as_mainfile(filepath=str(native),compress=True);bpy.ops.wm.open_mainfile(filepath=str(native))
for name,state in control['objects'].items():assert h['state'](bpy.data.objects[name])==state,name
for oname,weights in zip(objects,fields):
 o=bpy.data.objects[oname];measured=np.zeros_like(weights)
 for v in o.data.vertices:
  for g in v.groups:
   name=o.vertex_groups[g.group].name
   if name in names:measured[v.index,names.index(name)]=g.weight
 assert np.array_equal(measured,weights);assert np.array_equal(np.array([v.co[:] for v in o.data.vertices],np.float32),n['gloveXYZ'])
np.savez_compressed(out/'candidate-fields.npz',sourceGloveXYZ=n['gloveXYZ'],gloveTriangles=n['gloveTriangles'],fullWeights=fields[0],fourWeights=fields[1],bodyTriangleAncestry=np.array(ancestry),bodyBarycentrics=np.array(barys),bodyDistanceM=np.array(distance),removedMass=np.array(removed),rigRestFile=rest,actualControlInverseBind=ib,sourceRigRestNative=native_rest,parents=parents,boneNames=n['boneNames'],firstBikeFrame=B,firstCandidateBoneWorld=first)
recipe=Path(__file__);report={'status':'UNACCEPTED_ONE_HAND_CANDIDATE_FROZEN_SURFACE_QUALIFICATION_PENDING','recipeSHA256':sha(recipe),'pins':pins,'scopeSHA256':sha(scopepath),'native':str(native.relative_to(root)),'nativeSHA256':sha(native),'fieldsSHA256':sha(out/'candidate-fields.npz'),'newObjects':objects,'newRig':newrig.name,'all34OriginalObjectsExactAfterSaveReopen':True,'all51RestBindExact':True,'outside19SavedBonePosesExact':True,'topologyUVPBRRawAttributesUnedited':True,'sourcePositionsAllExact':True,'outside19WeightColumnsExact':True,'fullInfluenceMaximum':int((full>0).sum(1).max()),'fourInfluenceMaximum':int((four>0).sum(1).max()),'removedWeightMassPercentiles':np.percentile(removed,[0,50,95,100]).tolist(),'bodyAncestryDistancePercentilesM':np.percentile(distance,[0,50,95,100]).tolist(),'fallbackRetainedSourceWeightNativeIDs':fallback,'distalPositiveRows':{s:{label:int((a[:,j]>0).sum()) for label,a in [('source',old),('full',full),('four',four)]} for j,s in enumerate(names) if '_03.' in s},'palms':palms,'firstFiniteTargets':first_targets,'fixedFingerFlexAnglesDeg':angles,'thumbFirstOppositionDeg':35,'newHandPoseBasisFirstObservedFrame':basis,'actualSource37VsNative26RestMaximumElementDifference':rigResidual,'driverMapping':'Each directly observed source37 world bone multiplied by its OWN inverse bind and the exact native26 rest. Only listed32 candidate bones replaced. Outside19 bone worlds match this explicit effective-skin driver bytewise. Actual bike.frame independently recorded, never reconstructed. This is a native candidate replay on an actual control driver, not actual engine consumption of a candidate export.','limits':['One unchanged-rest-geometry barycentric anatomical binding field and one fixed flex candidate. Finger angles unqualified design choices, no sweep.','Palm skeletal ray selects an actual finite glove point; target precision is not deformed skin contact. Finite surface/penetration/enclosure/wrist/moving full-four qualification follows before capture.','No body/neck/hoodie/handlebar/global transform/newbone/rest-bind/normal edits, inference/GPU/job/install or promotion; allM0-M5 open/root sole played judge.']};(out/'authoring.json').write_text(json.dumps(report,indent=2)+'\n');assert pins=={str(p.relative_to(root)):sha(p) for p in inputs};print(json.dumps({k:report[k] for k in ['status','nativeSHA256','fullInfluenceMaximum','fourInfluenceMaximum','removedWeightMassPercentiles','bodyAncestryDistancePercentilesM','distalPositiveRows']},indent=2))
