"""Archived endpoints + a reconstructed affine path, never solver chronology.

BVH/normal decoding is diagnostic in transient unlinked mesh copies. No
native actor, fitting solve, source save, pose, rendering or capture.
"""
import hashlib,json,time
from pathlib import Path
import bpy,numpy as np
from mathutils.bvhtree import BVHTree
root=Path(__file__).resolve().parents[6];owned=Path(__file__).resolve().parent
ev=root/'docs/evidence/hero-remaster/anatomical-foundation-2026-10-03/user-agent1';qa=root/'docs/evidence/hero-remaster/user-agent3-qa-2026-10-03';out=ev/'neck-interface103';out.mkdir(parents=True,exist_ok=True)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
field=ev/'neck-interface102/candidate-fields-ancestry-corrected.npz';math=ev/'neck-interface102/solve-witnesses.npz';source=owned/'neck-interface28/auxiliary-restored.blend';native=owned/'neck-interface29/geometry-only-feasibility.blend';scope_file=qa/'body59/proposal.json'
inputs=[field,math,source,native,scope_file,qa/'neck71/FINDING.md',qa/'neck71/crossing-constraint-classification.json']
pins={str(p.relative_to(root)):sha(p) for p in inputs};assert sha(field)=='3727d0fd77a106443cf46536f8981daad5a01fb0a984bab4fd45e3b5c6ca5e4b'
assert not (out/'path-samples.json').exists()
f=dict(np.load(field));w=np.load(math);mapping=w['physicalRawToNode'];P0=w['referenceXYZ'].astype(float);P1=w['solvedXYZ'].astype(float);D=P1-P0;NB=len(f['bodyRestXYZ']);scope=json.loads(scope_file.read_text())['preciseInitialAuthoringMargin']
parts={key:{'map':mapping[:NB] if key=='body' else mapping[NB:],'reference':f[key+'FixedReferenceTriangles'],'final':f[key+'Triangles'],'local':set(f[key+'LocalTriangleIDs'].tolist())} for key in ['body','head']}
families={'bodySelf':('body','body'),'headSelf':('head','head'),'bodyHead':('body','head')}
def proper(A,B):
 for s,t in [(A,B),(B,A)]:
  a,b,c=t;n=np.cross(b-a,c-a);length=np.linalg.norm(n)
  if length<1e-20:continue
  n/=length;u=b-a;v=c-a;aa=u@u;ab=u@v;bb=v@v;det=aa*bb-ab*ab
  for i,j in [(0,1),(1,2),(2,0)]:
   x,y=s[i],s[j];dx=(x-a)@n;dy=(y-a)@n
   if dx*dy>=0 or min(abs(dx),abs(dy))<=1e-10:continue
   q=x+(y-x)*(dx/(dx-dy));e=q-a;bx=((e@u)*bb-(e@v)*ab)/det;by=((e@v)*aa-(e@u)*ab)/det
   if bx>=-1e-9 and by>=-1e-9 and bx+by<=1+1e-9:return True
 return False

def enumerate_pairs(P,tess):
 data={}
 for key,s in parts.items():
  t=s[tess];p=P[s['map']];data[key]={'tri':p[t],'phys':s['map'][t],'bvh':BVHTree.FromPolygons(p.tolist(),t.tolist(),all_triangles=True,epsilon=0.)}
 result={}
 for name,(a,b) in families.items():
  A,B=data[a],data[b];pairs=[];raw=0
  for i,j in A['bvh'].overlap(B['bvh']):
   if a==b and i>=j:continue
   if i not in parts[a]['local'] and j not in parts[b]['local']:continue
   if np.intersect1d(A['phys'][i],B['phys'][j]).size:continue
   raw+=1
   if proper(A['tri'][i],B['tri'][j]):pairs.append((int(i),int(j)))
  result[name]={'raw':raw,'proper':pairs}
 return result
start=enumerate_pairs(P0,'reference');final_reference=enumerate_pairs(P1,'reference');start_final_tess=enumerate_pairs(P0,'final');final=enumerate_pairs(P1,'final')
summary={name:{'referenceStartRaw':start[name]['raw'],'referenceStartProper':len(start[name]['proper']),'referenceFinalProper':len(final_reference[name]['proper']),'referenceIntroducedFinal':len(set(final_reference[name]['proper'])-set(start[name]['proper'])),'referenceResolvedStarting':len(set(start[name]['proper'])-set(final_reference[name]['proper'])),'finalTessStartProper':len(start_final_tess[name]['proper']),'finalTessFinalProper':len(final[name]['proper'])} for name in families}
print('ENDPOINTS',summary,flush=True)
samples=[];bound=1.
for alpha in [1e-6,1e-4,.001,.01,.03,.1,.3,1.]:
 result=enumerate_pairs(P0+alpha*D,'reference');row={'alpha':alpha,'kinds':{}}
 for name in families:
  pairset=set(result[name]['proper']);new=sorted(pairset-set(start[name]['proper']));row['kinds'][name]={'properPairs':len(pairset),'introducedRelativeToStart':len(new),'introducedPairIDs':new,'resolvedStartingPairs':len(set(start[name]['proper'])-pairset)}
 samples.append(row);print('CHORD_SAMPLE',alpha,{k:v['introducedRelativeToStart'] for k,v in row['kinds'].items()},flush=True)
 if any(v['introducedRelativeToStart'] for v in row['kinds'].values()):bound=alpha;break
# Swept AABBs up to this bound include all local candidates, not only final pairs.
A=P0;B=P0+bound*D;boxes={}
for key,s in parts.items():
 t=s['reference'];ap=A[s['map']][t];bp=B[s['map']][t];boxes[key]=(np.minimum(ap.min(axis=1),bp.min(axis=1)),np.maximum(ap.max(axis=1),bp.max(axis=1)))
universe={}
for name,(a,b) in families.items():
 lo,hi=boxes[a];bl,bh=boxes[b];candidates=set()
 # local A versus whole B plus whole A versus local B, canonical pair order.
 for inverse in [False,True] if a!=b else [False]:
  first,second=(b,a) if inverse else (a,b);fl,fh=boxes[first];sl,sh=boxes[second]
  for i in parts[first]['local']:
   ids=np.flatnonzero((sl<=fh[i]).all(axis=1)&(sh>=fl[i]).all(axis=1))
   for j in ids:
    x,y=(int(j),int(i)) if inverse else (int(i),int(j))
    if a==b:x,y=sorted((x,y))
    if x==y and a==b:continue
    candidates.add((x,y))
 rows=[];ta=parts[a]['map'][parts[a]['reference']];tb=parts[b]['map'][parts[b]['reference']];starting=set(start[name]['proper'])
 for i,j in sorted(candidates):
  if (i,j) in starting or np.intersect1d(ta[i],tb[j]).size:continue
  if not np.any(D[np.r_[ta[i],tb[j]]]):continue
  rows.append((i,j))
 universe[name]=np.array(rows,dtype=np.int32).reshape(-1,2);print('SWEPT_NEW_PAIR_UNIVERSE',name,len(rows),flush=True)
# Decode exact protected normals on ephemeral unlinked copies, rounded to native Float32.
bpy.ops.wm.open_mainfile(filepath=str(source));normal_rows=[];normal_arrays={};r=np.load(ev/'neck-interface96/ordered-boundaries.npz');alias=r['headPositionAlias'];he=set(scope['headInitialBoundaryLedNativeVertexIDs']);partial={int(v) for v in np.unique(alias[list(he)]) if not set(np.flatnonzero(alias==v))<=he}
for key,s in parts.items():
 obj=bpy.data.objects[('Bounded neck28 auxiliary-preserved body ' if key=='body' else 'Bounded neck27 triangulated head ')+'four, unaccepted'];m=obj.data.copy();original=len(alias) if key=='head' else 9037;allowed=set(scope['headInitialBoundaryLedNativeVertexIDs' if key=='head' else 'bodyExistingRenderedNativeVertices']);allowed.update(range(original,len(m.vertices)))
 if key=='head':allowed.difference_update(v for v in he if int(alias[v]) in partial)
 loops=np.array([l.vertex_index for l in m.loops]);protected=~np.isin(loops,list(allowed));base=np.array([v.vector[:] for v in obj.data.corner_normals],dtype=np.float32)
 original_positions=np.array([v.co[:] for v in obj.data.vertices],dtype=np.float32);assert np.array_equal(original_positions,P0[s['map']].astype(np.float32))
 polygons=np.repeat(np.arange(len(m.polygons)),np.array([p.loop_total for p in m.polygons]));normal_arrays[key+'ProtectedCornerIDs']=np.flatnonzero(protected);normal_arrays[key+'BaseDecodedNormals']=base
 for alpha in sorted(set([0.,1e-6,bound,1.])):
  positions=(P0[s['map']]+alpha*D[s['map']]).astype(np.float32);m.vertices.foreach_set('co',positions.ravel());m.update();decoded=np.array([v.vector[:] for v in m.corner_normals],dtype=np.float32)
  if alpha==0:assert np.array_equal(decoded,base),'Zero-alpha decoder must equal frozen native source'
  changed=(decoded!=base).any(axis=1)&protected;delta=np.linalg.norm(decoded.astype(float)-base,axis=1);ids=np.flatnonzero(changed);best=int(ids[np.argmax(delta[ids])]) if len(ids) else None
  row={'part':key,'alpha':alpha,'protectedDecodedCornersChanged':len(ids),'maximumVectorDelta':float(delta[ids].max()) if len(ids) else 0.,'witness':None}
  if best is not None:
   face=m.polygons[int(polygons[best])];vertices=list(face.vertices);row['witness']={'nativeCornerID':best,'nativeVertexID':int(loops[best]),'candidatePolygonID':int(polygons[best]),'checkpointPolygonID':int(f[key+'CandidatePolygonToCheckpointPolygon'][int(polygons[best])]),'nativePolygonVertexIDs':vertices,'protectedPositionExactlyPinned':bool(np.array_equal(positions[loops[best]],original_positions[loops[best]])),'originalDecodedNormal':base[best].tolist(),'reconstructedDecodedNormal':decoded[best].tolist(),'rawCustomNormalFieldUnedited':True,'sourceCornerAncestry':f[key+'CornerAttributeEdgeSources'][best].tolist()}
  normal_rows.append(row);normal_arrays[key+'Alpha'+str(alpha)+'DecodedNormals']=decoded
 bpy.data.meshes.remove(m)
np.savez_compressed(out/'path-geometry-and-candidates.npz',P0=P0,P1=P1,rawPhysicalMap=mapping,bodyReferenceTriangles=parts['body']['reference'],headReferenceTriangles=parts['head']['reference'],**{k+'SweptNewPairs':v for k,v in universe.items()})
np.savez_compressed(out/'decoded-normal-probes.npz',**normal_arrays)
report={'status':'READ_ONLY_RECONSTRUCTED_CHORD_NOT_RECORDED_SOLVER_ITERATES','recipeSHA256':sha(__file__),'pins':pins,'path':'P(alpha)=frozenReferenceXYZ+alpha*(frozenSolvedFloat32XYZ-referenceXYZ), 0<=alpha<=1. Continuous Float64 collision path; normal probes round to native Float32. This is an analyst reconstruction, not recorded solver chronology.','endpoints':summary,'startingReferenceProperPairs':{k:v['proper'] for k,v in start.items()},'finalReferenceProperPairs':{k:v['proper'] for k,v in final_reference.items()},'samples':samples,'introducedEventUpperAlpha':bound,'sweptNewPairCounts':{k:len(v) for k,v in universe.items()},'protectedNormalProbes':normal_rows,'archiveSHA256':sha(out/'path-geometry-and-candidates.npz'),'normalProbeSHA256':sha(out/'decoded-normal-probes.npz'),'limits':['Starting geometry already intersects; source defect sets remain distinct from introduced/resolved pairs.','Actual native tessellation changes6body/2head rows. Reconstructed chronology uses fixed reference triangles; final-tess endpoint control is separate, not an intermediate retessellation history.','No intermediate optimizer iterates, line-search records or native intermediate tessellations were archived. First event of the actual solver execution cannot be certified from endpoints.','No fitting/skin solve, new native candidate/source save/pose/capture/render/scope expansion/normal edit. Transient unlinked mesh copies exist only to read Blender normal decoding. AllM0-M5 remain open.']}
(out/'path-samples.json').write_text(json.dumps(report,indent=2)+'\n');assert pins=={p:sha(root/p) for p in pins};print('NORMAL_PROBES',[(r['part'],r['alpha'],r['protectedDecodedCornersChanged']) for r in normal_rows],flush=True)
