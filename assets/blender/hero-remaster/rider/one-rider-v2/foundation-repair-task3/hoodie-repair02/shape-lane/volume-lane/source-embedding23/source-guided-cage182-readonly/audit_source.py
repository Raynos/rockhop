"""Independent read-only source-contract checks; never executes original build."""
from pathlib import Path
import json,struct,hashlib,collections
import numpy as np
HERE=Path(__file__).resolve().parent

def glb(path):
 raw=path.read_bytes();n=struct.unpack_from('<I',raw,12)[0];return json.loads(raw[20:20+n]),raw[28+n:],raw

def acc(doc,buf,i):
 a=doc['accessors'][i];v=doc['bufferViews'][a['bufferView']];dt={5126:'<f4',5125:'<u4',5123:'<u2',5121:'u1'}[a['componentType']];k={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}[a['type']]
 return np.ndarray((a['count'],k),dtype=dt,buffer=buf,offset=v.get('byteOffset',0)+a.get('byteOffset',0),strides=(v.get('byteStride',np.dtype(dt).itemsize*k),np.dtype(dt).itemsize)).copy()
J,B,RAW=glb(HERE/'C19.glb');A,AB,AR=glb(HERE/'neutral-assembly01.glb');c=np.load(HERE/'cage01.npz');l=np.load(HERE/'lower-cut01.npz');m=np.load(HERE/'source-boundary-profiles.npz');ancestry=json.loads((HERE/'lower-cut-ancestry.json').read_text());p0=J['meshes'][0]['primitives'][0];P=acc(J,B,p0['attributes']['POSITION']);F=acc(J,B,p0['indices']).reshape(-1,3);LP=l['p'];LF=l['f'];U,physical=np.unique(P,axis=0,return_inverse=True)
assert hashlib.sha256((HERE/'cage01.npz').read_bytes()).hexdigest()=='8f1816bb3a87677487c4869b69dc2bb361ae0bc3ef934acacc1672c908501fa3'
assert np.array_equal(LP[:len(P)],P)
phi=P[:,1]-.940-.20*(P[:,0]-.640);byedge={};byphysical=collections.defaultdict(list);worst=0.;planeWorst=0.
for x in ancestry:
 a,b=x['sourceEdge'];t=x['edgeParameter'];row=x['newRow'];edge=tuple(sorted((a,b)));expectedPhysical=tuple(sorted((int(physical[a]),int(physical[b]))))
 assert tuple(x['physicalEdge'])==expectedPhysical and 0<t<1 and phi[a]*phi[b]<0
 assert abs(t-float(phi[a]/(phi[a]-phi[b])))<1e-15
 prediction=(P[a].astype(float)*(1-t)+P[b].astype(float)*t).astype('f4');worst=max(worst,float(np.linalg.norm(LP[row].astype(float)-prediction)))
 byedge[edge]=row;byphysical[expectedPhysical].append(row);q=LP[row].astype(float);planeWorst=max(planeWorst,abs(q[1]-.940-.20*(q[0]-.640)))
assert len(byedge)==len(ancestry)
for rows in byphysical.values():assert np.array_equal(LP[rows],np.repeat(LP[rows[:1]],len(rows),axis=0))
# Reconstruct source triangles' clipped polygons using only declared edge ancestry.
pre=[];sourceFace=[]
for fi,tri in enumerate(F):
 poly=[]
 for ai in range(3):
  a=int(tri[ai]);b=int(tri[(ai+1)%3]);
  if phi[a]<=0:poly.append(a)
  if phi[a]*phi[b]<0:poly.append(byedge[tuple(sorted((a,b)))])
 for k in range(1,len(poly)-1):pre.append((poly[0],poly[k],poly[k+1]));sourceFace.append(fi)
pre=np.asarray(pre);sourceFace=np.asarray(sourceFace);Q,inv=np.unique(LP,axis=0,return_inverse=True)
# Independently label exact-position components of clipped faces.
parent=np.arange(len(Q))
def find(i):
 while parent[i]!=i:parent[i]=parent[parent[i]];i=int(parent[i])
 return i
for tri in inv[pre]:
 a=find(int(tri[0]))
 for b in tri[1:]:parent[find(int(b))]=a
root=np.asarray([find(i) for i in range(len(Q))]);used=np.unique(inv[pre]);seeds=set(root[used[Q[used,1]<.8]].tolist());keep=np.asarray([int(root[inv[t[0]]]) in seeds for t in pre]);assert np.array_equal(pre[keep],LF)
np.savez(HERE/'derived-source-face-ancestry.npz',lowerFaceToSourceFace=sourceFace[keep],clippedAllFaceToSourceFace=sourceFace,retainedComponentMask=keep,sourceBodyRowsToPhysical=physical)
comp=[]
for r in sorted(set(root[used].tolist())):
 ids=used[root[used]==r];ff=root[inv[pre[:,0]]]==r;comp.append({'physicalVertices':len(ids),'clippedFaces':int(ff.sum()),'minimumY':float(Q[ids,1].min()),'maximumY':float(Q[ids,1].max()),'retainedByLegSeed':r in seeds})
# Every final original ordered boundary edge is retained, allowing only reversal/cyclic rotation.
def edges(pos):return {tuple(sorted((tuple(a),tuple(b)))) for a,b in zip(pos,np.roll(pos,-1,axis=0))}
boundaries=[]
for name,key in [('hoodIDs','hood_bodyCycle0Float32Positions'),('cuffLIDs','cuff_body_gloveCycle0Float32Positions'),('cuffRIDs','cuff_body_gloveCycle1Float32Positions')]:
 pos=c['p'][c[name]];src=m[key];assert len(pos)==len(src) and set(map(tuple,pos))==set(map(tuple,src)) and edges(pos)==edges(src)
 boundaries.append({'name':name,'nodes':len(pos),'exactSourceNodesAndCyclicEdges':True})
# Hem nodes must be precisely the retained lower cut boundary, not old sleeve or boot boundary.
ed=collections.Counter(tuple(sorted((int(a),int(b)))) for t in inv[LF] for a,b in zip(t,np.roll(t,-1)));boundaryEdges=[e for e,v in ed.items() if v==1];hem=c['p'][c['hemIDs']];hemEdges=edges(hem);sourceBoundaryEdges={tuple(sorted((tuple(Q[a]),tuple(Q[b])))) for a,b in boundaryEdges};assert hemEdges<=sourceBoundaryEdges
allHemOnDeclaredPlane=max(abs(hem[:,1].astype(float)-.940-.20*(hem[:,0].astype(float)-.640)))
# Exact raw protected attributes/accessors, materials/images and nineteen bone node references.
assert AB[:len(B)]==B
assert A['meshes'][0]['primitives'][1:]==J['meshes'][0]['primitives'][1:]
assert A['meshes'][1:len(J['meshes'])]==J['meshes'][1:]
assert A['images']==J['images'] and A['textures']==J['textures'] and A['materials'][:len(J['materials'])]==J['materials']
assert A['accessors'][:len(J['accessors'])]==J['accessors'] and A['bufferViews'][:len(J['bufferViews'])]==J['bufferViews']
joints=J['skins'][0]['joints'];assert len(joints)==19
assert all(A['nodes'][i]==J['nodes'][i] for i in joints)
assert all({k:v for k,v in A['nodes'][i].items() if k!='skin'}=={k:v for k,v in n.items() if k!='skin'} for i,n in enumerate(J['nodes']))
assert 'skins' not in A and 'animations' not in A and all('skin' not in n for n in A['nodes'])
# Distinguish guide sections from actual use. Each low ring samples only p0 near-height vertices.
profiles=[]
for ri,h in enumerate([.98,1.08,1.18,1.28],1):
 qrows=np.where((abs(P[:,1]-h)<.007)&(abs(P[:,2])<.225))[0];q=P[qrows];pos=c['p'][ri*64:(ri+1)*64];d=np.linalg.norm(pos[:,None,[0,2]]-q[None,:,[0,2]],axis=2);donors=qrows[d.argmin(1)];assert np.max(d.min(1))==0
 gap=np.abs(P[donors,1].astype(float)-h);segments=m[f'y{h:g}_p0SegmentsM'];closest=[]
 for v in pos.astype(float):
  x=segments[:,0];z=segments[:,1]-x;t=np.clip(((v-x)*z).sum(1)/np.maximum((z*z).sum(1),1e-30),0,1);closest.append(float(np.linalg.norm(v-x-t[:,None]*z,axis=1).min()))
 profiles.append({'Y':h,'candidateNodes':64,'uniqueSourceDonors':len(set(donors.tolist())),'sourcePrimitive':0,'maxVerticalProjectionM':float(gap.max()),'maxDistanceToMeasuredTriangleSectionM':max(closest),'sourceNodeRows':donors.tolist(),'profileSegmentBarycentricsUsed':False})
high=[]
for h in [1.37,1.43,1.49]:
 counts=[len(m[f'y{h:g}_p{i}SegmentsM']) for i in [0,2]];high.append({'Y':h,'sourceSegmentsP0':counts[0],'sourceSegmentsP2':counts[1],'directCageProfileRow':False,'p2GeometryRetainedEntire':True})
report={'status':'BOUNDARY_CUT_AND_PROTECTED_SOURCE_CONTRACT_PASS_WITH_PROFILE_PROVENANCE_LIMITS','inputs':json.loads((HERE/'frozen-inputs.json').read_text()),'cageCounts':{'vertices':len(c['p']),'triangles':len(c['f']),'quads':len(c['quads']),'hemNodes':len(hem)},'sourceCut':{'signedPlane':'Y=.940+.20*(X-.640)','sourceBodyRowsExact':True,'derivedAttributeRows':len(ancestry),'uniquePhysicalSourceEdges':len(byphysical),'allPhysicalEdgeAliasesFloat32Exact':True,'maxInterpolationDifferenceM':worst,'maxSignedPlaneFloat32ResidualM':planeWorst,'retainedFaces':len(LF),'preComponentFaces':len(pre),'discardedFaces':int((~keep).sum()),'retainedMaskIndependentlyExact':True,'components':comp,'ancestrySupplement':'derived-source-face-ancestry.npz','originalAncestryLimit':'Original lower-cut-ancestry.json records source edges/parameters, not per-output-face parent IDs. This read-only supplement recovers exact source-face ancestry. Physical source IDs are the p0-only exact-position quotient, not global source-boundary physical IDs; no semantic layer weld inferred.','hemExactRetainedLowerBoundaryEdges':len(hemEdges),'hemMaxSignedPlaneResidualM':float(allHemOnDeclaredPlane),'attributeRuntimeLimit':'Nearest-endpoint JOINTS plus interpolated WEIGHTS are declared unrigged diagnostic attributes, not a qualified skin or posed source-edge driver.'},'orderedSourceCycles':boundaries,'protectedDonors':{'originalBINPrefixExact':True,'allOriginalAccessorsBufferViewsExact':True,'gloveAndHoodPrimitivesExact':True,'headOtherMeshesExact':True,'imagesTexturesOriginalMaterialsExact':True,'jointNodes':len(joints),'nineteenJointNodeRecordsAndInverseBindAccessorRetainedExact':True,'skinAnimationsExplicitlyRemoved':True,'noRigAcceptance':True},'profileCoverage':{'lowRows':profiles,'highSections':high,'concreteLimit':'Build does not consume measured profile segments or triangle/barycentric provenance for its torso/sleeve interior. It projects nearby p0 vertices onto four levels; high 1.37/1.43/1.49 profiles, including posterior p2 segments, are not used as cage control rows. This does not remove posterior hood: complete p2 is retained byte-exact and paired to the original 307-node curve. Sleeve radii remain bounded heuristics from p0 extrema rather than measured material correspondence. These guide/coverage choices require actual silhouette judgment; no anatomical coverage or appearance PASS is inferred.','referenceClipIsNotAnatomicalWidth':True},'scope':'Frozen copies and independent read-only reconstruction/inventory only. No original edits, build execution, rigging, renders, geometry mutation or motion tests. QA agent owns final float32 incidence/winding/seam/collision judgments.'}
(HERE/'source-guided-cage182-source-contract.json').write_text(json.dumps(report,indent=2))
print(json.dumps({'reportSHA256':hashlib.sha256((HERE/'source-guided-cage182-source-contract.json').read_bytes()).hexdigest(),'cutRows':len(ancestry),'physicalEdges':len(byphysical),'components':comp,'profileSummary':[{k:v for k,v in x.items() if k!='sourceNodeRows'} for x in profiles],'protected19':True},indent=2))
