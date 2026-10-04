"""Read frozen Blender files and independently enumerate rest witnesses. No save."""
import hashlib,json
from pathlib import Path
import bpy,numpy as np
from mathutils.bvhtree import BVHTree
out=Path(__file__).resolve().parent;qa=out.parent;root=out.parents[4];asset=root/'assets/blender/hero-remaster/rider/anatomical-foundation-2026-10-03/user-agent1';ev=root/'docs/evidence/hero-remaster/anatomical-foundation-2026-10-03/user-agent1';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();prep=json.loads((qa/'neck70/preparation.json').read_text())
for p,h in prep['pins'].items():assert sha(root/p)==h['sha256'],p
helper=qa/'neck62/read-native.py';text=helper.read_text();reader=dict(bpy=bpy,np=np,hashlib=hashlib);exec(compile(text[text.index('def digest('):text.index('for label,path in paths.items():')],str(helper),'exec'),reader);state,flat=reader['state'],reader['flat'];digest=reader['digest'];jsondigest=lambda d:hashlib.sha256(json.dumps(d,sort_keys=True,separators=(',',':')).encode()).hexdigest()
c=dict(np.load(ev/'neck-interface102/candidate-fields-ancestry-corrected.npz'));w=dict(np.load(ev/'neck-interface102/solve-witnesses.npz'));f=dict(np.load(asset/'neck-interface27/triangulated-neck-fields.npz'));scope=json.loads((qa/'body59/proposal.json').read_text())['preciseInitialAuthoringMargin'];constraints=json.loads((qa/'neck68/source-assessment.json').read_text());owner=json.loads((ev/'neck-interface102/rest-candidate.json').read_text());classified=json.loads((ev/'neck-interface102/rest-shape-and-constraints.json').read_text());NB=len(c['bodyRestXYZ']);bone_names=c['boneNames'].tolist();arrays={}
def defs(o):return [[g.name,bool(g.lock_weight)] for g in o.vertex_groups]
def snapshot():
 return {'objects':{o.name:state(o) for o in bpy.data.objects},'definitions':{o.name:defs(o) for o in bpy.data.objects if o.type=='MESH'},'materials':reader['materials'](),'images':{i.name:{'packed':sha_bytes(bytes(i.packed_file.data)) if i.packed_file else None,'colour':i.colorspace_settings.name,'size':list(i.size),'path':i.filepath} for i in bpy.data.images}}
def sha_bytes(b):return hashlib.sha256(b).hexdigest()
def nonposition(d):
 d=json.loads(json.dumps(d));d['mesh'].pop('positions');d['mesh'].pop('cornerNormals');d['mesh']['attributes'].pop('position');return d
bpy.ops.wm.open_mainfile(filepath=str(asset/'neck-interface28/auxiliary-restored.blend'));baseline=snapshot();assert len(baseline['objects'])==44;oldnames={};oldnorm={};oldpositions={};oldstates={};olddefs={}
for part in ['body','head']:
 for label in ['full','four']:
  name=('Bounded neck28 auxiliary-preserved body ' if part=='body' else 'Bounded neck27 triangulated head ')+label+', unaccepted';o=bpy.data.objects[name];oldnames[part,label]=name;oldstates[part,label]=state(o);olddefs[part,label]=defs(o);oldnorm[part,label]=flat(o.data.corner_normals,'vector',3,np.float32);oldpositions[part,label]=flat(o.data.vertices,'co',3,np.float32)
print('READ_BASELINE44_CONTROLS',flush=True)
bpy.ops.wm.open_mainfile(filepath=str(asset/'neck-interface29/geometry-only-feasibility.blend'));after=snapshot();assert len(after['objects'])==48
for name,s in baseline['objects'].items():assert after['objects'][name]==s,name
for name,d in baseline['definitions'].items():assert after['definitions'][name]==d,name
assert after['images']==baseline['images'] and after['materials']==baseline['materials'];assert list(bpy.data.objects['Independent anatomical foundation rig'].data.bones.keys())==bone_names
parts={};preservation=[];norms=[]
for part in ['body','head']:
 for label in ['full','four']:
  name='Bounded neck29 geometry-only '+part+' '+label+', unaccepted';o=bpy.data.objects[name];s=state(o);assert nonposition(s)==nonposition(oldstates[part,label]);assert defs(o)==olddefs[part,label];m=o.data;m.calc_loop_triangles();p=flat(m.vertices,'co',3,np.float32);t=np.array([z.vertices[:] for z in m.loop_triangles],dtype=np.int32);polygons=np.array([z.polygon_index for z in m.loop_triangles],dtype=np.int32);loops=flat(m.loops,'vertex_index',1,np.int32).ravel();weights=np.zeros((len(p),51),dtype=np.float32);aux=[]
  for v in m.vertices:
   for g in v.groups:
    gn=o.vertex_groups[g.group].name
    if gn in bone_names:weights[v.index,bone_names.index(gn)]=g.weight
    else:aux.append([v.index,gn,float(g.weight)])
  assert np.array_equal(p,c[part+'RestXYZ']) and np.array_equal(t,c[part+'Triangles']) and np.array_equal(weights,c[part+label.title()+'Weights']);assert np.array_equal(c[part+'CandidatePolygonToCheckpointPolygon'][polygons],c[part+'TriangleCheckpointPolygonIDs']);orig=9037 if part=='body' else 43707;allowed=np.r_[scope['bodyExistingRenderedNativeVertices' if part=='body' else 'headInitialBoundaryLedNativeVertexIDs'],np.arange(orig,len(p))];outside=np.setdiff1d(np.arange(orig),allowed);assert np.array_equal(p[outside],oldpositions[part,label][outside]);current_norm=flat(m.corner_normals,'vector',3,np.float32);delta=np.linalg.norm(current_norm.astype(float)-oldnorm[part,label].astype(float),axis=1);protected=~np.isin(loops,allowed);partial=np.isin(loops,constraints['pinnedAdmittedHeadIDs']) if part=='head' else np.zeros(len(loops),dtype=bool);geometry_pinned=protected|partial;nd={'part':part,'field':label,'decodedProtectedCornersChanged':int(((delta>0)&protected).sum()),'maximumDecodedProtectedCornerDelta':float(delta[protected].max()),'decodedAllCornersChanged':int((delta>0).sum()),'decodedPartialPinnedAdmittedCornersChanged':int(((delta>0)&partial).sum()),'maximumDecodedPartialPinnedCornerDelta':float(delta[partial].max()) if partial.any() else 0.,'decodedAllScopePinnedCornersChanged':int(((delta>0)&geometry_pinned).sum()),'maximumDecodedAllScopePinnedCornerDelta':float(delta[geometry_pinned].max())};norms.append(nd)
  if label=='four':
   expected=next(x for x in owner['normalDerivedDifferences'] if x['part']==part);assert nd['decodedProtectedCornersChanged']==expected['decodedProtectedCornerChanged'] and abs(nd['maximumDecodedProtectedCornerDelta']-expected['maximumDecodedProtectedCornerDelta'])<1e-12
   world=np.column_stack([p,np.ones(len(p))])@np.array(o.matrix_world).T;physical=w['physicalRawToNode'][:NB] if part=='body' else w['physicalRawToNode'][NB:];local=np.flatnonzero(np.isin(t,allowed).any(axis=1));assert np.array_equal(local,c[part+'LocalTriangleIDs']);parts[part]={'p':p.astype(float),'world':world[:,:3],'t':t,'physical':physical,'local':set(map(int,local))};arrays[part+'Positions']=p;arrays[part+'Triangles']=t;arrays[part+'CornerNormalDelta']=delta;arrays[part+'ProtectedCornerIDs']=np.flatnonzero(protected)
  preservation.append({'part':part,'field':label,'outsideOriginalVertices':len(outside),'outsideStoredPositionsExact':True,'allRawNonPositionAttributesUVPBRTopologyBindingAndGroupsExact':True,'allDefinitionOrderNameLockAndMembershipWeightsExact':True,'semanticWeightsSHA256':digest(weights),'positiveSemanticSlotMaximum':int((weights>0).sum(1).max()),'auxiliaryMembershipCount':len(aux),'auxiliaryZeroMembershipCount':sum(x[2]==0 for x in aux),'hiddenByDefault':bool(o.hide_get() and o.hide_render),'nonpositionStateSHA256':jsondigest(nonposition(s))})
print('NATIVE48_PRESERVATION_EXACT_NORMAL_CHANGES',[(x['part'],x['field'],x['decodedProtectedCornersChanged']) for x in norms],flush=True)
# Independently collect full adjacency/incidence in the physical quotient.
all_t=np.vstack([d['physical'][d['t']] for d in parts.values()]);edges=np.vstack([all_t[:,[0,1]],all_t[:,[1,2]],all_t[:,[2,0]]]);u,inv,count=np.unique(np.sort(edges,axis=1),axis=0,return_inverse=True,return_counts=True);balance=np.zeros(len(u),dtype=int);np.add.at(balance,inv,np.where(edges[:,0]<edges[:,1],1,-1));edge_lookup={tuple(map(int,e)):int(z) for e,z in zip(u,count)};sid=f['bodySeamPhysicalIDs'];seam_nodes=np.array([parts['body']['physical'][np.flatnonzero(sid==i)[0]] for i in range(238)]);outer_edges=np.sort(np.column_stack([seam_nodes,np.roll(seam_nodes,-1)]),axis=1);assert all(edge_lookup[tuple(e)]==2 for e in outer_edges);inner=parts['head']['physical'][f['headInnerClosurePhysicalIDs']>=0];inner_edges=u[np.isin(u,inner).all(axis=1)];assert len(inner_edges)==383 and all(edge_lookup[tuple(e)]==2 for e in inner_edges)
top={'triangles':len(all_t),'unmatchedEdges':int((count==1).sum()),'nonmanifoldEdges':int((count>2).sum()),'twoIncidenceNonOpposed':int(((count==2)&(balance!=0)).sum())};assert all(top[k]==owner['currentRestTopology'][k] for k in top)
areas=[]
for part,d in parts.items():
 q=d['p'][d['t']];area=.5*np.linalg.norm(np.cross(q[:,1]-q[:,0],q[:,2]-q[:,0]),axis=1);a={'part':part,'localTriangles':len(d['local']),'minimumLocalAreaM2':float(area[list(d['local'])].min()),'localAtOrBelow1e_14':int((area[list(d['local'])]<=1e-14).sum())};areas.append(a);expected=next(x for x in owner['localAreas'] if x['part']==part);assert a['localTriangles']==expected['localTrianglesIncludingOneCorner'] and abs(a['minimumLocalAreaM2']-expected['minimumLocalAreaM2'])<1e-18;d['bvh']=BVHTree.FromPolygons(d['world'].tolist(),d['t'].tolist(),all_triangles=True,epsilon=0.)
# Proper finite edge-triangle witnesses use determinant barycentrics in both directions.
def crossings(A,B):
 hits=[]
 for source,target,which in [(A,B,'aToB'),(B,A,'bToA')]:
  a,b,c=target;e=b-a;f=c-a;normal=np.cross(e,f);length=np.linalg.norm(normal)
  if length<1e-20:continue
  normal/=length
  for i,j in [(0,1),(1,2),(2,0)]:
   start,end=source[i],source[j];ds=float((start-a)@normal);de=float((end-a)@normal)
   if ds*de>=0 or min(abs(ds),abs(de))<=1e-10:continue
   direction=end-start;v=np.cross(direction,f);den=float(e@v)
   if abs(den)<1e-20:continue
   z=start-a;u=float(z@v)/den;q=np.cross(z,e);vv=float(direction@q)/den;t=float(f@q)/den
   if -1e-9<=u and -1e-9<=vv and u+vv<=1+1e-9 and 0<t<1:hits.append({'direction':which,'edgeIDs':[i,j],'segmentFraction':t,'targetBarycentric':[1-u-vv,u,vv],'nativePositionM':(start+t*direction).tolist()})
 return hits
free=set(map(int,w['freePhysicalNodes']));cap_vertex=np.flatnonzero(f['headAttributeEdgeSources'][:,0]<0);cap_faces=set(np.flatnonzero(np.isin(parts['head']['t'],cap_vertex).any(axis=1)).tolist());contacts={}
for kind,a,b in [('bodySelf','body','body'),('headSelf','head','head'),('bodyHead','body','head')]:
 A,B=parts[a],parts[b];pairs=[]
 for i,j in A['bvh'].overlap(B['bvh']):
  if a==b and i>=j:continue
  if i not in A['local'] and j not in B['local']:continue
  if set(map(int,A['physical'][A['t'][i]]))&set(map(int,B['physical'][B['t'][j]])):continue
  pairs.append((int(i),int(j)))
 pairs=sorted(set(pairs));assert set(pairs)==set(map(tuple,owner['restContacts'][kind]['trianglePairs'])),kind;witnesses=[];freefree=capcount=0
 for i,j in pairs:
  hs=crossings(A['p'][A['t'][i]],B['p'][B['t'][j]]);assert hs,(kind,i,j);ff=set(map(int,A['physical'][A['t'][i]]))<=free and set(map(int,B['physical'][B['t'][j]]))<=free;cap=(a=='head' and i in cap_faces) or (b=='head' and j in cap_faces);freefree+=ff;capcount+=cap;witnesses.append({'triangleIDs':[i,j],'sourcePolygonIDs':[int(c[a+'TriangleSourcePolygonIDs'][i]),int(c[b+'TriangleSourcePolygonIDs'][j])],'checkpointPolygonIDs':[int(c[a+'TriangleCheckpointPolygonIDs'][i]),int(c[b+'TriangleCheckpointPolygonIDs'][j])],'freeFree':bool(ff),'innerCapParticipates':bool(cap),'properFiniteWitnesses':hs})
 contacts[kind]={'rawBVHPairs':len(pairs),'properFiniteCrossingPairs':len(witnesses),'freeFreePairs':int(freefree),'innerCapParticipatingPairs':int(capcount),'witnesses':witnesses};print('INDEPENDENT_REST_CROSSINGS',kind,len(pairs),'freefree',freefree,'cap',capcount,flush=True)
for p,h in prep['pins'].items():assert sha(root/p)==h['sha256'],p
np.savez_compressed(out/'native-rest-read.npz',**arrays)
report={'status':'FAILED_REST_CROSSINGS_INDEPENDENTLY_REPRODUCED_PRESERVATION_ONLY','recipeSHA256':sha(__file__),'pinnedReaderSHA256':sha(helper),'all30InputPinsUnchanged':True,'blenderVersion':bpy.app.version_string,'nativeReadNPZ_SHA256':sha(out/'native-rest-read.npz'),'original44ObjectStatesAndDefinitionsExact':True,'original51RigRestBindSavedPoseExact':True,'packedImagesExact':len(baseline['images']),'materialGraphsExact':len(baseline['materials']),'originalObjectStateSHA256':{name:jsondigest(s) for name,s in baseline['objects'].items()},'candidateNativeVerticesTrianglesAndWeightsMatchFrozenFields':True,'preservation':preservation,'decodedNormalDifferences':norms,'topology':top,'outer238EdgesIncidenceTwo':True,'inner383EdgesIncidenceTwoSeparateClosure':True,'localAreas':areas,'contacts':contacts,'limits':['Stored native rest data only; no pose/dependency-graph evaluation, save, export, capture, renderer or solve. Raw custom normal data exact does not imply decoded protected normals unchanged.','BVH enumeration excludes shared physical alias vertices and retains full admitted incident scope including pinned partial aliases. All reported pairs have finite noncoplanar crossing witnesses; not signed volume or visible-art judgment.','Snapshot excludes unenumerated RNA collections, animation F-curves/NLA and external linked contents. Native44controls are exact within this pinned reader contract.','No automatic expansion or claim whole scope infeasible. Source29 fails rest contact gate, all original99/490/M0-M5 remain open. Parent owns source decision.']}
(out/'native-preservation-crossings.json').write_text(json.dumps(report,indent=2)+'\n');print('READ_ONLY_QA_RESULT_WRITTEN',flush=True)
