from pathlib import Path
import sys,json,hashlib,io
import numpy as np
from PIL import Image
ROOT=Path('/Users/raynos/projects/games/rockhop/assets/blender/hero-remaster/rider/one-rider-v2/foundation-repair-task3');Q=ROOT/'hoodie-repair02/qa-lane';OUT=Q/'uv-lower01';sys.path.insert(0,str(ROOT/'scripts'));from glb import GLB
s=(Q/'scripts/geometry_gate.py').read_text();ns={'np':np,'EPS':1e-9};exec(s[s.index('def crossing'):s.index('def region_geom')],ns);crossing=ns['crossing']
paths=[('C19',Q/'C19-source.glb'),('preferred_body11',Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/rig-adapter01/body-bind11/guarded-correction01/rider.glb')),('V7',ROOT/'hoodie-repair02/deliverables/rider-compression-v7.glb')];rows=[];reference=None;pairs=[(28,67),(29,67),(29,68)]
def hits(t1,t2):
 out=[]
 for side,(aa,bb)in enumerate([(t1,t2),(t2,t1)]):
  e1,e2=bb[1]-bb[0],bb[2]-bb[0]
  for i,k in [(0,1),(1,2),(2,0)]:
   o,d=aa[i],aa[k]-aa[i];p=np.cross(d,e2);det=np.dot(e1,p)
   if abs(det)<=1e-14:continue
   inv=1/det;v0=o-bb[0];u=np.dot(v0,p)*inv;q=np.cross(v0,e1);v=np.dot(d,q)*inv;t=np.dot(e2,q)*inv
   if min(u,v,t,1-t,1-u-v)>1e-9:out.append({'edge_triangle_in_pair':side,'edge_local_vertices':[i,k],'edge_fraction':float(t),'target_barycentric':[float(1-u-v),float(u),float(v)],'point_m':(o+d*t).tolist()})
 return out
for name,path in paths:
 g=GLB(path);pr=[p for m in g.j['meshes']for p in m['primitives']];p=pr[2];P=g.array(p['attributes']['POSITION']).astype(float);T=g.array(p['indices']).astype(int).reshape(-1,3);N=g.array(p['attributes']['NORMAL']).astype(float);UV=g.array(p['attributes']['TEXCOORD_0']).astype(float);fullP=np.concatenate([g.array(r['attributes']['POSITION']).astype(float)for r in pr]);off=np.r_[0,np.cumsum([len(g.array(r['attributes']['POSITION']))for r in pr])];U,A=np.unique(fullP,axis=0,return_inverse=True);mat=g.j['materials'][p['material']];image=g.j['images'][g.j['textures'][mat['pbrMetallicRoughness']['baseColorTexture']['index']]['source']];bv=g.j['bufferViews'][image['bufferView']];raw=bytes(g.bin[bv.get('byteOffset',0):bv.get('byteOffset',0)+bv['byteLength']]);im=np.asarray(Image.open(io.BytesIO(raw)).convert('RGBA'))
 faces=[]
 for f in [28,29,67,68]:
  ids=T[f];q=P[ids];normal=np.cross(q[1]-q[0],q[2]-q[0]);area=np.linalg.norm(normal)/2;normal/=max(np.linalg.norm(normal),1e-20);vn=N[ids];dots=vn@normal;faces.append({'source_primitive':2,'source_face':f,'source_vertex_ids':ids.tolist(),'exact_alias_ids_full_source':A[ids+off[2]].tolist(),'positions_m':q.tolist(),'UVs':UV[ids].tolist(),'vertex_normals':vn.tolist(),'geometric_unit_normal':normal.tolist(),'normal_dot_geometric_per_corner':dots.tolist(),'area_mm2':float(area*1e6)})
 pairrows=[]
 for a,b in pairs:
  shared=set(A[T[a]+off[2]]).intersection(A[T[b]+off[2]]);sharedaliases=[]
  for vi in shared:
   vs=np.flatnonzero(A==vi);sharedaliases.append({'exact_alias_id':int(vi),'rest_position_m':U[vi].tolist(),'all_primitive_source_vertices':[[int(np.searchsorted(off,v,side='right')-1),int(v-off[np.searchsorted(off,v,side='right')-1])]for v in vs]})
  h=hits(P[T[a]],P[T[b]])
  for hh in h:
   targetface=[b,a][hh['edge_triangle_in_pair']];uv=np.array(hh['target_barycentric'])@UV[T[targetface]];xy=np.floor((uv%1)*[im.shape[1],im.shape[0]]).astype(int);hh['target_face']=targetface;hh['target_uv']=uv.tolist();hh['target_original_atlas_rgba']=im[xy[1],xy[0]].tolist()
  pairrows.append({'source_primitive_faces':[a,b],'shared_exact_source_alias_count':len(shared),'shared_exact_source_aliases':sharedaliases,'strict_interior_crossing':bool(crossing(P[T[[a]]],P[T[[b]]])[0]),'intersection_witnesses':h})
 if reference is None:reference=(P.copy(),T.copy(),N.copy(),UV.copy())
 row={'variant':name,'path':str(path),'sha256':hashlib.sha256(g.raw).hexdigest(),'affected_positions_byte_exact_to_C19':np.array_equal(P[np.unique(T[[28,29,67,68]])],reference[0][np.unique(reference[1][[28,29,67,68]])]),'affected_triangles_exact_to_C19':np.array_equal(T[[28,29,67,68]],reference[1][[28,29,67,68]]),'entire_p2_positions_exact_to_C19':np.array_equal(P,reference[0]),'entire_p2_triangles_exact_to_C19':np.array_equal(T,reference[1]),'affected_normal_rows_exact_to_C19':np.array_equal(N[np.unique(T[[28,29,67,68]])],reference[2][np.unique(reference[1][[28,29,67,68]])]),'affected_UV_rows_exact_to_C19':np.array_equal(UV[np.unique(T[[28,29,67,68]])],reference[3][np.unique(reference[1][[28,29,67,68]])]),'material':mat,'atlas_sha256':hashlib.sha256(raw).hexdigest(),'faces':faces,'pairs':pairrows};rows.append(row)
 print(name,'crosses',[r['strict_interior_crossing']for r in pairrows],'shared',[r['shared_exact_source_alias_count']for r in pairrows],'areas',[round(f['area_mm2'],5)for f in faces])
# Independent wider bounded source-rest sweep, candidate phase AABB only, strict predicate same.
g=GLB(paths[0][1]);pr=[p for m in g.j['meshes']for p in m['primitives']];P=np.concatenate([g.array(p['attributes']['POSITION']).astype(float)for p in pr]);off=np.r_[0,np.cumsum([len(g.array(p['attributes']['POSITION']))for p in pr])];T=np.concatenate([g.array(pr[i]['indices']).astype(int).reshape(-1,3)+off[i]for i in [0,2]]);_,A=np.unique(P,axis=0,return_inverse=True);q=P[T];mask=((q[:,:,1]>1.08)&(q[:,:,1]<1.62)&(abs(q[:,:,2])<.405)).all(1);ids=np.flatnonzero(mask);rt=T[mask];q=P[rt];lo,hi=q.min(1),q.max(1);cand=[]
for a in range(len(rt)):
 b=np.flatnonzero((lo[a]<=hi[a+1:]).all(1)&(hi[a]>=lo[a+1:]).all(1))+a+1
 cand.extend((a,int(bi))for bi in b)
cand=np.array(cand,int).reshape(-1,2);share=np.array([len(set(A[rt[a]]).intersection(A[rt[b]]))for a,b in cand]);use=cand[share<2];h=crossing(q[use[:,0]],q[use[:,1]]);outpairs=use[h];outshared=share[share<2][h];p0count=len(g.array(pr[0]['indices']))//3
sweep={'source':'C19 rest','explicit_mask':'all three corners 1.08<y<1.62, abs(z)<.405; cloth0+2','triangles':len(rt),'AABB_candidates':len(cand),'strict_transverse_crossings_no_shared_alias':int((outshared==0).sum()),'strict_transverse_crossings_one_shared_alias':int((outshared==1).sum()),'all_crossing_primitive_face_pairs':[[[0,int(f)]if f<p0count else[2,int(f-p0count)]for f in ids[pair]]for pair in outpairs],'source_face_pair_alias_counts':outshared.tolist(),'limits':'Finite strict transverse test; shared-two-corner pairs excluded as topological neighbors; coplanar/tangent contacts and thickness unclassified.'};print('WIDER SWEEP',sweep)
out={'target_pairs':pairs,'rows':rows,'expanded_bounded_source_rest_sweep':sweep,'correction':'Previous clear findings covered explicit cropped ROIs/finite poses, not entire rest upper mesh. These inherited defects lie outside the old crop because at least one corner exceeds its upper y bound. No whole-rest upper zero claim is supported.','causal_conclusion':'Actual triangle interiors intersect in preferred original body11, C19 and V7 rest geometry. UVs/normal attributes affect visible shading, but cannot remove literal geometry crossing. Material is DoubleSided and original p2 has no normalTexture; opaque atlas colors do not make these crossings transparency.','limits':['Exact named source triangle ancestry, not claimed same vertex-order for arbitrary later remesh.','Broader source sweep uses the explicit expanded bound only; not whole character or full rest acceptance.','New construction cap/body interactions and posed support require new freeze and separate tests.']};(OUT/'inherited-neck-rest-crossings.json').write_text(json.dumps(out,indent=2))
