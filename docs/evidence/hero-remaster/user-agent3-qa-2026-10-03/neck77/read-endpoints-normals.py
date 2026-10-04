"""Independent immutable endpoint/corner audit and archived transient probes.

Only previously archived alpha values are decoded on unlinked copies. No
source actor editing, pose changes, save, solve, render or new candidate.
"""
import bpy,numpy as np,json,hashlib
from pathlib import Path
from mathutils.bvhtree import BVHTree
out=Path(__file__).resolve().parent;qa=out.parent;root=Path.cwd();ev=root/'docs/evidence/hero-remaster/anatomical-foundation-2026-10-03/user-agent1';prep=json.loads((qa/'neck76/preparation.json').read_text());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
for p,h in prep['pins'].items():assert sha(root/p)==h['sha256'],p
f=np.load(ev/'neck-interface102/candidate-fields-ancestry-corrected.npz');w=np.load(ev/'neck-interface102/solve-witnesses.npz');archive=np.load(ev/'neck-interface103/path-geometry-and-candidates.npz');probes=np.load(ev/'neck-interface103/decoded-normal-probes.npz');owner=json.loads((ev/'neck-interface103/path-samples.json').read_text());scope=json.loads((qa/'body59/proposal.json').read_text())['preciseInitialAuthoringMargin'];boundary=np.load(ev/'neck-interface96/ordered-boundaries.npz');prior=np.load(qa/'neck71/native-rest-read.npz');P0=archive['P0'];P1=archive['P1'];D=P1-P0;mapping=archive['rawPhysicalMap'];NB=len(f['bodyRestXYZ']);assert np.array_equal(P0,w['referenceXYZ']) and np.array_equal(P1,w['solvedXYZ']) and np.array_equal(mapping,w['physicalRawToNode']);parts={}
for part in ['body','head']:
 m=mapping[:NB] if part=='body' else mapping[NB:];assert np.array_equal(P1[m].astype(np.float32),f[part+'RestXYZ']) and np.array_equal(f[part+'RestXYZ'],prior[part+'Positions']);assert np.array_equal(archive[part+'ReferenceTriangles'],f[part+'FixedReferenceTriangles']);assert np.array_equal(f[part+'Triangles'],prior[part+'Triangles']);parts[part]={'map':m,'reference':archive[part+'ReferenceTriangles'],'final':f[part+'Triangles'],'local':set(map(int,f[part+'LocalTriangleIDs']))}
# Standard segment-plane crossing plus finite barycentric containment.
def proper(A,B):
 for edges,face in [(A,B),(B,A)]:
  origin=face[0];u=face[1]-origin;v=face[2]-origin;n=np.cross(u,v);length=np.linalg.norm(n)
  if length<1e-20:continue
  n/=length;gram=np.array([[u@u,u@v],[u@v,v@v]]);det=np.linalg.det(gram)
  if det<=0:continue
  for ei,ej in [(0,1),(1,2),(2,0)]:
   a=edges[ei];b=edges[ej];da=(a-origin)@n;db=(b-origin)@n
   if da*db>=0 or abs(da)<=1e-10 or abs(db)<=1e-10:continue
   q=a+(b-a)*(da/(da-db));r=q-origin;rhs=np.array([r@u,r@v]);uv=np.array([(gram[1,1]*rhs[0]-gram[0,1]*rhs[1])/det,(gram[0,0]*rhs[1]-gram[0,1]*rhs[0])/det])
   if uv[0]>=-1e-9 and uv[1]>=-1e-9 and sum(uv)<=1+1e-9:return True
 return False
families={'bodySelf':('body','body'),'headSelf':('head','head'),'bodyHead':('body','head')}
def pairs(P,template):
 ds={}
 for part,s in parts.items():
  t=s[template];p=P[s['map']];ds[part]=(p[t],s['map'][t],BVHTree.FromPolygons(p.tolist(),t.tolist(),all_triangles=True,epsilon=0.))
 result={}
 for kind,(a,b) in families.items():
  A,B=ds[a],ds[b];found=[]
  for i,j in A[2].overlap(B[2]):
   if a==b and i>=j:continue
   if i not in parts[a]['local'] and j not in parts[b]['local']:continue
   if set(A[1][i])&set(B[1][j]):continue
   if proper(A[0][i],B[0][j]):found.append([int(i),int(j)])
  result[kind]=sorted(found)
 return result
allpairs={}
for label,P,tess in [('referenceStart',P0,'reference'),('referenceFinal',P1,'reference'),('finalTemplateStart',P0,'final'),('finalNativeEndpoint',P1,'final'),('alpha1e-6',P0+1e-6*D,'reference'),('alpha0.01',P0+.01*D,'reference')]:
 result=pairs(P,tess);allpairs[label]=result;print('INDEPENDENT_PROPER_PAIRS',label,{k:len(v) for k,v in result.items()},flush=True)
for kind in families:
 assert allpairs['referenceStart'][kind]==sorted(owner['startingReferenceProperPairs'][kind]);assert allpairs['referenceFinal'][kind]==sorted(owner['finalReferenceProperPairs'][kind])
 for label,key in [('referenceStart','referenceStartProper'),('referenceFinal','referenceFinalProper'),('finalTemplateStart','finalTessStartProper'),('finalNativeEndpoint','finalTessFinalProper')]:assert len(allpairs[label][kind])==owner['endpoints'][kind][key]
for sample in owner['samples']:
 label='alpha1e-6' if sample['alpha']==1e-6 else 'alpha0.01' if sample['alpha']==.01 else None
 if label:
  for kind in families:assert len(allpairs[label][kind])==sample['kinds'][kind]['properPairs'];assert sorted(set(map(tuple,allpairs[label][kind]))-set(map(tuple,allpairs['referenceStart'][kind])))==list(map(tuple,sample['kinds'][kind]['introducedPairIDs']))
# Source-scope versus archived approximate tangent freedoms, independently.
dof=np.zeros(len(P0),int);np.add.at(dof,w['freePhysicalNodes'][w['variableOwner']],1);free=set(map(int,w['freePhysicalNodes']));scopeRows={}
for kind,(a,b) in families.items():
 rows=[]
 for i,j in allpairs['referenceStart'][kind]:
  nodes=np.r_[parts[a]['map'][parts[a]['reference'][i]],parts[b]['map'][parts[b]['reference'][j]]];rows.append({'triangleIDs':[i,j],'physicalNodeIDs':nodes.tolist(),'allScopePinned':not any(int(n) in free for n in nodes),'allArchivedTangentZeroDOF':not np.any(dof[nodes]),'tangentDOFByCorner':dof[nodes].tolist()})
 scopeRows[kind]={'pairs':len(rows),'allScopePinnedPairs':sum(z['allScopePinned'] for z in rows),'allArchivedTangentZeroDOFPairs':sum(z['allArchivedTangentZeroDOF'] for z in rows),'rows':rows}
ownerstart=json.loads((ev/'neck-interface103/starting-contact-constraints.json').read_text())
for kind in families:
 for key in ['pairs','allScopePinnedPairs','allArchivedTangentZeroDOFPairs']:assert scopeRows[kind][key]==ownerstart[kind][key]
 assert sorted(scopeRows[kind]['rows'],key=lambda z:z['triangleIDs'])==sorted(ownerstart[kind]['rows'],key=lambda z:z['triangleIDs'])
# Retrieve read-only raw attribute helpers; none of their execution loops run.
helper=(qa/'neck62/read-native.py').read_text();ns={'np':np,'bpy':bpy,'hashlib':hashlib};exec(compile(helper[helper.index('def digest('):helper.index('for label,path in paths.items():')],'immutable-attribute-readers','exec'),ns)
asset=root/'assets/blender/hero-remaster/rider/anatomical-foundation-2026-10-03/user-agent1';source=asset/'neck-interface28/auxiliary-restored.blend';native=asset/'neck-interface29/geometry-only-feasibility.blend';bpy.ops.wm.open_mainfile(filepath=str(source));normalrows=[];baseStates={};rawattr={};alias=boundary['headPositionAlias'];headallowed=set(scope['headInitialBoundaryLedNativeVertexIDs']);partial={int(v) for v in np.unique(alias[list(headallowed)]) if not set(np.flatnonzero(alias==v))<=headallowed};pinnedInside=[v for v in headallowed if int(alias[v]) in partial];world=[]
for part,s in parts.items():
 name=('Bounded neck28 auxiliary-preserved body ' if part=='body' else 'Bounded neck27 triangulated head ')+'four, unaccepted';obj=bpy.data.objects[name];m=obj.data;baseStates[part]=ns['state'](obj);rawattr[part]=ns['attrs'](m);world.append(np.array(obj.matrix_world));loops=np.array([z.vertex_index for z in m.loops]);pos=np.array([v.co[:] for v in m.vertices],np.float32);assert np.array_equal(pos,P0[s['map']].astype(np.float32));base=np.array([v.vector[:] for v in m.corner_normals],np.float32);assert np.array_equal(base,probes[part+'BaseDecodedNormals']);m.calc_loop_triangles();assert np.array_equal(np.array([z.vertices[:] for z in m.loop_triangles]),s['reference']);original=9037 if part=='body' else len(alias);allowed=set(scope['bodyExistingRenderedNativeVertices' if part=='body' else 'headInitialBoundaryLedNativeVertexIDs'])|set(range(original,len(m.vertices)));allowed-=set(pinnedInside) if part=='head' else set();mask=~np.isin(loops,list(allowed));assert np.array_equal(np.flatnonzero(mask),probes[part+'ProtectedCornerIDs']);transient=m.copy()
 for alpha in [0.,1e-6,.01,1.]:
  transient.vertices.foreach_set('co',((P0+alpha*D)[s['map']]).astype(np.float32).ravel());transient.update();decoded=np.array([v.vector[:] for v in transient.corner_normals],np.float32);assert np.array_equal(decoded,probes[part+'Alpha'+str(alpha)+'DecodedNormals']);changed=(decoded!=base).any(1)&mask;delta=np.linalg.norm(decoded.astype(float)-base,axis=1);arch=next(z for z in owner['protectedNormalProbes'] if z['part']==part and z['alpha']==alpha);assert int(changed.sum())==arch['protectedDecodedCornersChanged'];assert abs((float(delta[changed].max()) if changed.any() else 0.)-arch['maximumVectorDelta'])<1e-15;assert ns['attrs'](transient).keys()==rawattr[part].keys()
  actualattrs=ns['attrs'](transient)
  for key,attr in rawattr[part].items():
   if key=='position':continue
   for field,values in attr['fields'].items():assert np.array_equal(actualattrs[key]['fields'][field],values),(part,key,field)
  normalrows.append({'part':part,'alpha':alpha,'protectedCorners':int(mask.sum()),'changed':int(changed.sum()),'maxVectorDelta':float(delta[changed].max()) if changed.any() else 0.,'allDecodedArrayBytesMatchArchived':True,'allRawNonPositionAttributesUnedited':True})
 bpy.data.meshes.remove(transient);assert ns['state'](obj)==baseStates[part]
assert np.array_equal(world[0],world[1]);bpy.ops.wm.open_mainfile(filepath=str(native));nativeNormal=[]
for part in parts:
 obj=bpy.data.objects['Bounded neck29 geometry-only '+part+' four, unaccepted'];decoded=np.array([z.vector[:] for z in obj.data.corner_normals],np.float32);assert np.array_equal(decoded,probes[part+'Alpha1.0DecodedNormals']);attrs=ns['attrs'](obj.data)
 for key,attr in rawattr[part].items():
  if key=='position':continue
  for field,values in attr['fields'].items():assert np.array_equal(attrs[key]['fields'][field],values)
 nativeNormal.append({'part':part,'native29ActualDecodedBytesMatchAlpha1':True,'rawNonPositionAttributeFieldsExactToSource28':True})
summary={}
for kind in families:
 st=set(map(tuple,allpairs['referenceStart'][kind]));en=set(map(tuple,allpairs['referenceFinal'][kind]));summary[kind]={'start':len(st),'final':len(en),'introduced':len(en-st),'resolved':len(st-en),'persistent':sorted(st&en),'finalTemplateStart':len(allpairs['finalTemplateStart'][kind]),'finalNativeEndpoint':len(allpairs['finalNativeEndpoint'][kind])}
r={'status':'INDEPENDENT_SOURCE_ENDPOINT_AND_NATIVE_DECODER_AUDIT','recipeSHA256':sha(__file__),'blender':bpy.app.version_string,'endpointAncestryExact':True,'sourceBodyAndHeadWorldMatricesEqual':True,'referenceVsFinalTemplateChangedTriangleRows':{part:int((parts[part]['reference']!=parts[part]['final']).any(1).sum()) for part in parts},'properCrossingSummary':summary,'sourcePinnedAndTangentZeroPairCounts':{k:{a:v for a,v in z.items() if a!='rows'} for k,z in scopeRows.items()},'partialPinnedAdmittedHeadVertices':len(pinnedInside),'normalProbes':normalrows,'actualFinalNativeDecoderControls':nativeNormal,'sourceObjectsUnchangedInMemory':True,'inputPinsUnchangedAfter':True,'limits':['Only archived chord alphas decoded on unlinked diagnostic copies, not new candidates or a fitting path. No source save, solve, normal/actor edit, pose/render/capture.','Finite proper-crossing thresholds reproduce existing103/102 semantics; not complete continuous collision, all contacts or played visual acceptance.','No decoded-normal Jacobian/rank, feasible seed or proposedSQP feasibility proof. AllM0-M5open; root alone decides.']}
for p,h in prep['pins'].items():assert sha(root/p)==h['sha256'],p
(out/'endpoint-normal-audit.json').write_text(json.dumps(r,indent=2)+'\n');(out/'proper-pairs.json').write_text(json.dumps(allpairs)+'\n');(out/'starting-constraint-audit.json').write_text(json.dumps(scopeRows)+'\n');print('ALL_ENDPOINTS_NORMALS_RAW_FIELDS_MATCH',flush=True)
