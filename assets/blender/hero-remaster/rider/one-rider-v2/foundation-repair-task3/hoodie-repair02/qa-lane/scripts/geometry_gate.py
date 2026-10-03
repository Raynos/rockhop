"""Literal finite geometry gates; run CPU Blender only. Does not render."""
from pathlib import Path
import sys,json,hashlib,time
import numpy as np
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[3];Q=ROOT/'hoodie-repair02/qa-lane';sys.path.insert(0,str(ROOT/'scripts'));from glb import GLB
early_args=sys.argv[sys.argv.index('--')+1:]if '--'in sys.argv else[]
meta=json.loads(Path(early_args[1]).read_text())if early_args and early_args[0]=='external'else{}
topology_path=Path(meta['topology_path'])if 'topology_path'in meta else None
G=GLB(Q/'C19-source.glb');PR=[p for m in G.j['meshes']for p in m['primitives']];POS=[G.array(p['attributes']['POSITION']).astype(float)for p in PR];TRI=[G.array(p['indices']).astype(int).reshape(-1,3)for p in PR];TRI=[np.load(topology_path)[f'tr{i}'].astype(int)for i in range(5)]if topology_path else TRI;OFF=np.r_[0,np.cumsum([len(p)for p in POS])];base=np.concatenate(POS);tri=np.concatenate([TRI[i]+OFF[i]for i in [0,2]]);_,alias=np.unique(base,axis=0,return_inverse=True)
# Strict-interior segment/triangle predicate, independent narrow phase.
EPS=1e-9

def crossing(t1,t2):
 hit=np.zeros(len(t1),bool)
 for aa,bb in [(t1,t2),(t2,t1)]:
  e1=bb[:,1]-bb[:,0];e2=bb[:,2]-bb[:,0]
  for i,k in [(0,1),(1,2),(2,0)]:
   o=aa[:,i];d=aa[:,k]-o;p=np.cross(d,e2);det=np.einsum('ij,ij->i',e1,p);valid=abs(det)>1e-14;inv=np.divide(1,det,out=np.zeros_like(det),where=valid);s=o-bb[:,0];u=np.einsum('ij,ij->i',s,p)*inv;q=np.cross(s,e1);v=np.einsum('ij,ij->i',d,q)*inv;t=np.einsum('ij,ij->i',e2,q)*inv;hit|=valid&(u>EPS)&(v>EPS)&(u+v<1-EPS)&(t>EPS)&(t<1-EPS)
 return hit

def region_geom(points,rests,mask):
 rt=tri[mask];al=alias[rt];bvh=BVHTree.FromPolygons(points.tolist(),rt.tolist(),all_triangles=True,epsilon=0.)
 pairs=np.array(sorted(set(tuple(sorted(x))for x in bvh.overlap(bvh)if x[0]!=x[1])),int).reshape(-1,2)
 shared=np.array([len(set(al[a]).intersection(al[b]))for a,b in pairs],int)
 cornerpairs=pairs[shared==1];cornerhits=crossing(points[rt[cornerpairs[:,0]]],points[rt[cornerpairs[:,1]]])if len(cornerpairs)else np.zeros(0,bool)
 pairs=pairs[shared==0]
 hit=crossing(points[rt[pairs[:,0]]],points[rt[pairs[:,1]]])if len(pairs)else np.zeros(0,bool)
 edges=np.unique(np.sort(np.concatenate([rt[:,[0,1]],rt[:,[1,2]],rt[:,[0,2]]]),1),axis=0);lr=np.linalg.norm(rests[edges[:,0]]-rests[edges[:,1]],axis=1);lp=np.linalg.norm(points[edges[:,0]]-points[edges[:,1]],axis=1);use=lr>=.002;ratio=lp[use]/lr[use]
 a=lambda x:np.linalg.norm(np.cross(x[rt[:,1]]-x[rt[:,0]],x[rt[:,2]]-x[rt[:,0]]),axis=1);a0=a(rests);area=a(points)/np.maximum(a0,1e-15)
 n0=np.cross(points[rt[pairs[:,0],1]]-points[rt[pairs[:,0],0]],points[rt[pairs[:,0],2]]-points[rt[pairs[:,0],0]])if len(pairs)else np.zeros((0,3));n1=np.cross(points[rt[pairs[:,1],1]]-points[rt[pairs[:,1],0]],points[rt[pairs[:,1],2]]-points[rt[pairs[:,1],0]])if len(pairs)else n0
 parallel=np.linalg.norm(np.cross(n0,n1),axis=1)<=1e-12*np.maximum(np.linalg.norm(n0,axis=1)*np.linalg.norm(n1,axis=1),1e-15)
 return {'triangles':len(rt),'strict_transverse_crossings':int(hit.sum()),'one_shared_source_vertex_strict_transverse_crossings':int(cornerhits.sum()),'one_corner_witness_source_combined_faces':np.flatnonzero(mask)[cornerpairs[cornerhits][:10]].tolist(),'crossing_faces':int(len(np.unique(pairs[hit]))),'unclassified_parallel_candidates':int(parallel.sum()),'witness_source_combined_faces':np.flatnonzero(mask)[pairs[hit][:5]].tolist(),'edge_ge_2mm_max':float(ratio.max())if len(ratio)else None,'edge_ge_2mm_p99':float(np.quantile(ratio,.99))if len(ratio)else None,'area_below_quarter':int(((area<.25)&(a0>1e-12)).sum()),'gate':'FAIL'if hit.any()or cornerhits.any()or(len(ratio)and ratio.max()>2.5)or((area<.25)&(a0>1e-12)).any()else'NUMERIC_ONLY_CLEAR'}

# Actual cuff boundary from complete cloth material sets, exact original weld.
weldtri=alias[tri];ed=np.sort(np.concatenate([weldtri[:,[0,1]],weldtri[:,[1,2]],weldtri[:,[0,2]]]),1);ue,ct=np.unique(ed,axis=0,return_counts=True);unique,inv=np.unique(base,axis=0,return_inverse=True);boundary=ue[ct==1];bm=((unique[boundary,:,] if False else unique[boundary])[:,:,1]>.87).all(1)&(unique[boundary][:,:,1]<1.08).all(1)&(abs(unique[boundary][:,:,2])>.24).all(1);boundary=boundary[bm];first=np.full(len(unique),-1,int)
for i,j in enumerate(inv):
 if first[j]<0:first[j]=i
bidx=first[boundary];cuff_ids=np.unique(bidx)
source_cuff_fallback=(base[:,1]>.90)&(base[:,1]<.96)&(abs(base[:,2])>.25)&(np.arange(len(base))<OFF[1])
if not len(cuff_ids):cuff_ids=np.flatnonzero(source_cuff_fallback)
GLOVE_TRI=TRI[1]+OFF[1]
def cuff(points):
 bvh=BVHTree.FromPolygons(points.tolist(),GLOVE_TRI.tolist(),all_triangles=True,epsilon=0.)
 samples=np.concatenate([points[cuff_ids],points[bidx].mean(1)])if len(bidx)else points[cuff_ids];dist=np.array([bvh.find_nearest(p)[3]for p in samples]);ctmask=np.any(np.isin(tri,cuff_ids),axis=1);ct=tri[ctmask];cv=BVHTree.FromPolygons(points.tolist(),ct.tolist(),all_triangles=True,epsilon=0.);pairs=np.array(cv.overlap(bvh),int).reshape(-1,2);shares=np.array([len(set(alias[ct[a]]).intersection(alias[GLOVE_TRI[b]]))for a,b in pairs],int);cp=pairs[shares==1];ch=crossing(points[ct[cp[:,0]]],points[GLOVE_TRI[cp[:,1]]])if len(cp)else np.zeros(0,bool);pairs=pairs[shares==0];hit=crossing(points[ct[pairs[:,0]]],points[GLOVE_TRI[pairs[:,1]]])if len(pairs)else np.zeros(0,bool)
 return {'sample_basis':'complete-cloth exact-weld boundary vertices and edge midpoints'if len(bidx)else'explicit near-cuff garment selector, no open boundary found','boundary_edges':len(bidx),'samples':len(samples),'nearest_glove_surface_min_mm':float(dist.min()*1000)if len(dist)else None,'nearest_glove_surface_p50_mm':float(np.median(dist)*1000)if len(dist)else None,'nearest_glove_surface_max_mm':float(dist.max()*1000)if len(dist)else None,'strict_cuff_glove_crossings':int(hit.sum()),'one_shared_source_vertex_strict_cuff_glove_crossings':int(ch.sum()),'one_corner_witness_combined_cloth_faces':np.flatnonzero(ctmask)[cp[ch][:10,0]].tolist(),'one_corner_witness_glove_faces':cp[ch][:10,1].tolist(),'one_corner_witness_triangle_positions_m':[[points[ct[a]].tolist(),points[GLOVE_TRI[b]].tolist()]for a,b in cp[ch][:10]],'witness_combined_cloth_faces':np.flatnonzero(ctmask)[pairs[hit][:10,0]].tolist(),'witness_glove_faces':pairs[hit][:10,1].tolist(),'witness_triangle_positions_m':[[points[ct[a]].tolist(),points[GLOVE_TRI[b]].tolist()]for a,b in pairs[hit][:10]],'gate':'FAIL'if hit.any()or ch.any()or(len(dist)and np.quantile(dist,.9)>.015)else'VISUAL_REVIEW_REQUIRED','note':'Overlap is not seam equality. Intended insertion may penetrate glove interior; crossing counts require garment construction review.'}
# Bounded literal collar/head material-region gate. Source head primitive includes lower
# head/neck surface; labels are material/primitive provenance, not body anatomy truth.
collar_mask=((base[tri][:,:,1]>1.40)&(base[tri][:,:,1]<1.62)&(abs(base[tri][:,:,2])<.215)).all(1)
COLLAR_TRI=tri[collar_mask]
HEAD_TRI=np.concatenate([TRI[i]+OFF[i]for i in [3,4]])
HEAD_TRI=HEAD_TRI[(base[HEAD_TRI][:,:,1]<1.70).all(1)]
P=np.load(ROOT/'experiments/C19-bind.npz')['centres']
chest_selector=(base[:,1]>1.20)&(base[:,1]<1.38)&(abs(base[:,2])<.12)&(np.arange(len(base))<OFF[1])
def collar_head(points):
 cb=BVHTree.FromPolygons(points.tolist(),COLLAR_TRI.tolist(),all_triangles=True,epsilon=0.)
 hb=BVHTree.FromPolygons(points.tolist(),HEAD_TRI.tolist(),all_triangles=True,epsilon=0.)
 pairs=np.array(cb.overlap(hb),int).reshape(-1,2);n=len(pairs)
 shares=np.array([len(set(alias[COLLAR_TRI[a]]).intersection(alias[HEAD_TRI[b]]))for a,b in pairs],int);cp=pairs[shares==1];ch=crossing(points[COLLAR_TRI[cp[:,0]]],points[HEAD_TRI[cp[:,1]]])if len(cp)else np.zeros(0,bool);pairs=pairs[shares==0]
 hit=crossing(points[COLLAR_TRI[pairs[:,0]]],points[HEAD_TRI[pairs[:,1]]])if len(pairs)else np.zeros(0,bool)
 cv=np.unique(COLLAR_TRI); hv=np.unique(HEAD_TRI); shared=np.isin(alias[cv],alias[hv]); query=cv[~shared]; near=[hb.find_nearest(points[i])for i in query]; distances=np.array([x[3]for x in near]); worst=int(np.argmin(distances))if len(distances)else None
 return {'cloth_primitives':[0,2],'head_primitives':[3,4],'collar_triangles':len(COLLAR_TRI),'head_triangles':len(HEAD_TRI),'nonshared_collar_vertices_queried':len(query),'nearest_nonshared_collar_to_head_surface_min_mm':float(distances.min()*1000)if len(distances)else None,'nearest_nonshared_collar_to_head_surface_p50_mm':float(np.median(distances)*1000)if len(distances)else None,'nearest_witness_collar_vertex':int(query[worst])if worst is not None else None,'nearest_witness_head_face_restricted':int(near[worst][2])if worst is not None else None,'bvh_pairs':n,'strict_nonadjacent_transverse_crossings':int(hit.sum()),'one_shared_source_vertex_strict_transverse_crossings':int(ch.sum()),'one_corner_cloth_face_witnesses':np.flatnonzero(collar_mask)[cp[ch][:10,0]].tolist(),'one_corner_head_face_witnesses':cp[ch][:10,1].tolist(),'cloth_face_witnesses':np.flatnonzero(collar_mask)[pairs[hit][:10,0]].tolist(),'head_restricted_face_witnesses':pairs[hit][:10,1].tolist(),'witness_triangle_positions_m':[[points[COLLAR_TRI[a]].tolist(),points[HEAD_TRI[b]].tolist()]for a,b in pairs[hit][:10]],'gate':'LITERAL_CROSSING_VISUAL_REVIEW'if hit.any()or ch.any()else'FINITE_GEOMETRY_ONLY_CLEAR','limits':'Primitive/material-defined region. Intended tucked collar/hood layering requires witness review. Not head shape/appearance/anatomy acceptance; tangent/copanar contact and thickness unresolved.'}
def alignment(points,data):
 if 'matrices'not in data:return {'gate':'UNMEASURED','reason':'pose matrices missing'}
 D=data['matrices'];C=np.einsum('nij,nj->ni',D[:,:3,:],np.c_[P,np.ones(len(P))]);sh=(C[6]+C[10])*.5
 return {'joint_centres_m':C.tolist(),'head_minus_shoulder_forward_mm':float((C[4,0]-sh[0])*1000),'neck_minus_shoulder_forward_mm':float((C[3,0]-sh[0])*1000),'chest_joint_minus_shoulder_forward_mm':float((C[2,0]-sh[0])*1000),'front_chest_max_minus_shoulder_forward_mm':float((points[chest_selector,0].max()-sh[0])*1000),'torso_lean_degrees':float(np.degrees(np.arctan2(*(C[2]-C[0])[:2]))),'head_local_up_world':D[4,:3,1].tolist(),'neck_local_up_world':D[3,:3,1].tolist(),'gate':'MATCHED_SIDE_PROFILE_VISUAL_REVIEW_REQUIRED','limits':'Estimated C19 pivots and garment-selector extent, not clinical anatomy or head appearance qualification.'}

# Source seam aliases: conservative bounding-box diameter of each original group.
_,alias_counts=np.unique(base,axis=0,return_counts=True)
prim=np.repeat(np.arange(5),np.diff(OFF));amin=np.full(alias_counts.size,99);amax=np.full(alias_counts.size,-1);np.minimum.at(amin,alias,prim);np.maximum.at(amax,alias,prim)
def seams(points):
 lo=np.full((alias_counts.size,3),np.inf);hi=np.full_like(lo,-np.inf);np.minimum.at(lo,alias,points);np.maximum.at(hi,alias,points);gap=np.linalg.norm(hi-lo,axis=1);multi=alias_counts>1;cross=amin!=amax
 return {'exact_source_alias_groups':int(multi.sum()),'cross_primitive_alias_groups':int(cross.sum()),'all_alias_bbox_diagonal_max_mm':float(gap[multi].max()*1000),'cross_primitive_alias_bbox_diagonal_max_mm':float(gap[cross].max()*1000),'groups_over_0_05mm':int((gap[multi]>.00005).sum()),'gate':'FAIL'if (gap[multi]>.00005).any()else'FINITE_ALIAS_GEOMETRY_CLEAR','note':'Bounding-box diagonal conservatively bounds pairwise distance; exact0 means all alias points coincide. Does not certify neighbouring triangles or intended inserted cuffs.'}
BIKE={v['name']:v for v in json.loads((ROOT/'evidence/bike.json').read_text())};BP=np.array(BIKE['bodywork']['positions']);BT=np.array(BIKE['bodywork']['triangles']).reshape(-1,3);BQ=BP[BT];bn=np.cross(BQ[:,1]-BQ[:,0],BQ[:,2]-BQ[:,0]);bn/=np.maximum(np.linalg.norm(bn,axis=1,keepdims=True),1e-15);sm=((BQ[:,:,0]>=-.541)&(BQ[:,:,0]<=-.049)&(BQ[:,:,1]>=.5405)&(BQ[:,:,1]<=.631)&(abs(BQ[:,:,2])<=.069)).all(1)&(bn[:,1]>.3);SEAT=BQ[sm];assert len(SEAT)==48
seat_tri=np.arange(len(SEAT)*3).reshape(-1,3);seat_points=SEAT.reshape(-1,3);sbvh=BVHTree.FromPolygons(seat_points.tolist(),seat_tri.tolist(),all_triangles=True,epsilon=0.)
hip_mask=((base[tri][:,:,1]>.69)&(base[tri][:,:,1]<1.08)&(abs(base[tri][:,:,2])<.245)).all(1);hip_vertex=np.unique(tri[hip_mask])
def seat(points):
 h=points[hip_vertex];ys=np.full(len(h),-np.inf)
 for st in SEAT:
  m=np.array([[st[1,0]-st[0,0],st[2,0]-st[0,0]],[st[1,2]-st[0,2],st[2,2]-st[0,2]]]);det=np.linalg.det(m)
  if abs(det)<1e-12:continue
  uv=(h[:,[0,2]]-st[0,[0,2]])@np.linalg.inv(m).T;inside=(uv.min(1)>=-1e-7)&(uv.sum(1)<=1+1e-7);yy=st[0,1]+uv[:,0]*(st[1,1]-st[0,1])+uv[:,1]*(st[2,1]-st[0,1]);ys[inside]=np.maximum(ys[inside],yy[inside])
 valid=np.isfinite(ys);gap=h[valid,1]-ys[valid];ht=tri[hip_mask];hb=BVHTree.FromPolygons(points.tolist(),ht.tolist(),all_triangles=True,epsilon=0.);pairs=np.array(hb.overlap(sbvh),int).reshape(-1,2);hit=crossing(points[ht[pairs[:,0]]],SEAT[pairs[:,1]])if len(pairs)else np.zeros(0,bool)
 return {'seat_triangles':len(SEAT),'projected_hip_vertices':int(valid.sum()),'projected_skin_vertex_min_vertical_gap_mm':float(gap.min()*1000)if len(gap)else None,'strict_hip_saddle_triangle_crossings':int(hit.sum()),'hip_face_witnesses':np.flatnonzero(hip_mask)[pairs[hit][:5,0]].tolist(),'seat_face_witnesses':pairs[hit][:5,1].tolist(),'gate':'NOT_OVER_SADDLE'if not len(gap)else'FAIL_PENETRATION'if hit.any()or gap.min()<-.001 else'NO_SUPPORT_HOVER'if gap.min()>.003 else'POTENTIAL_CONTACT_REQUIRES_AREA_AND_FORCE','limits':'Actual48 upward saddle faces, fixed source hip garment region. Vertex vertical gap is not triangle clearance, area or rider support force. Neutral/arm poses are not expected seated.'}

regions={'shoulder_underarm':((base[tri][:,:,1]>1.08)&(base[tri][:,:,1]<1.49)&(abs(base[tri][:,:,2])<.405)).all(1),'hip':((base[tri][:,:,1]>.69)&(base[tri][:,:,1]<1.08)&(abs(base[tri][:,:,2])<.245)).all(1),'cuff_elbow':((base[tri][:,:,1]>.86)&(base[tri][:,:,1]<1.24)&(abs(base[tri][:,:,2])>.22)).all(1)}
args=sys.argv[sys.argv.index('--')+1:]if '--'in sys.argv else[]
if args and args[0]=='quick':
 rows=[{'variant':v,'probe':k,'fraction':t,'path':str(ROOT/'hoodie-repair02/poses'/f'r1-{v}-{k}-{t}.npz')}for v in ['control','shape','weights']for k,t in [('rest',0),('raise',.5),('raise',1),('sit',.5),('sit',1)]]
else:
 rows=json.loads(Path(args[1]).read_text())['rows']if args and args[0]=='external'else json.loads((Q/'pose-manifest.json').read_text())['rows']
 if args and args[0]=='source':rows=[r for r in rows if r['variant']=='source']
results=[]
for row in rows:
 f=Path(row['path']);d=np.load(f);points=np.concatenate([d[f'p{i}']for i in range(5)]);variant=row['variant'];restfile=ROOT/'hoodie-repair02/round1-bind.npz'if args and args[0]=='quick'and variant!='control'else Q/f'{variant}-bind.npz';rests=np.concatenate([np.load(restfile)[f'p{i}']for i in range(5)])if restfile.exists()else base
 out={**row,'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'regions':{k:region_geom(points,rests,m)for k,m in regions.items()},'cuff':cuff(points),'collar_head':collar_head(points),'alignment':alignment(points,d),'seams':seams(points),'seat':seat(points),'nonfinite':int((~np.isfinite(points)).sum())};results.append(out);print(json.dumps({'variant':variant,'probe':row['probe'],'fraction':row['fraction'],'regions':{k:[v['strict_transverse_crossings'],round(v['edge_ge_2mm_max'],3)]for k,v in out['regions'].items()},'cuff':out['cuff']}),flush=True)
 (Q/'results'/('quick-gate.json'if args and args[0]=='quick'else'source-gate.json'if args and args[0]=='source'else Path(args[1]).stem+'-gate.json'if args and args[0]=='external'else'canonical-gate.json')).write_text(json.dumps({'source':str(Q/'C19-source.glb'),'source_sha256':hashlib.sha256(G.raw).hexdigest(),'topology_path':str(topology_path)if topology_path else str(Q/'C19-source.glb'),'topology_sha256':hashlib.sha256(topology_path.read_bytes()).hexdigest()if topology_path else hashlib.sha256(G.raw).hexdigest(),'methods':'Combined clothing primitives0+2, original exact source aliases exclude adjacent faces; CPU Blender BVH + strict six-edge float64 crossing predicate. Edge ratios exclude rest edges shorter2mm. Cuff vertices AND edge midpoints queried against actual glove triangles.','limits':['Finite pose/frame samples; no CCD or full-body certification.','Coplanar contacts unclassified.','Region masks fixed from source anatomy estimates.','Cuff crossing might be intended insertion; visual review mandatory.','No GPU, PBR or gray appearance claims from numeric gates.'],'rows':results},indent=2))
print('QA COMPLETE')
