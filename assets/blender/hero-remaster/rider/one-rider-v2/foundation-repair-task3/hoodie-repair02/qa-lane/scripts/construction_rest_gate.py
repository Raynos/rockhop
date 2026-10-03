from pathlib import Path
import sys,json,hashlib
import numpy as np
from mathutils.bvhtree import BVHTree
ROOT=Path('/Users/raynos/projects/games/rockhop/assets/blender/hero-remaster/rider/one-rider-v2/foundation-repair-task3');Q=ROOT/'hoodie-repair02/qa-lane';OUT=Q/'uv-lower01';sys.path.insert(0,str(ROOT/'scripts'));from glb import GLB
s=(Q/'scripts/geometry_gate.py').read_text();ns={'np':np,'EPS':1e-9};exec(s[s.index('def crossing'):s.index('def region_geom')],ns);crossing=ns['crossing']
CP=ROOT/'hoodie-repair02/shape-lane/volume-lane/armhole-construction/armhole-chart-outward.npz';C=np.load(CP);BP=CP.parent/'frozen-v7-bind.npz';B=np.load(BP);SP=ROOT/'hoodie-repair02/v7-shape-input.npz';S=np.load(SP);G=GLB(Q/'C19-source.glb');PR=[p for m in G.j['meshes']for p in m['primitives']];GP=[G.array(p['attributes']['POSITION']).astype(float)for p in PR];GT=[G.array(p['indices']).astype(int).reshape(-1,3)for p in PR]
def gate(name,pos,tris,physical=None,ancestry=None,kinds=None):
 P=np.concatenate([pos[0],pos[2]]);OFF=len(pos[0]);T=np.concatenate([tris[0],tris[2]+OFF]);p0faces=len(tris[0]);_,alias=np.unique(P,axis=0,return_inverse=True);alias=np.concatenate([physical[0],physical[2]])if physical is not None else alias
 fullq=P[T];mask=(fullq[:,:,1]>=1.08).any(1);ids=np.flatnonzero(mask);RT=T[mask];lo=P[RT].min(1);hi=P[RT].max(1);candidate_pairs=[]
 for ai in range(len(RT)):
  bis=np.flatnonzero((lo[ai]<=hi[ai+1:]).all(1)&(hi[ai]>=lo[ai+1:]).all(1))+ai+1
  candidate_pairs.extend((ai,int(bi))for bi in bis)
 pairs=np.array(candidate_pairs,int).reshape(-1,2);al=alias[RT];shared=np.array([len(set(al[a]).intersection(al[b]))for a,b in pairs]);keep=shared<2;cp=pairs[keep];sh=shared[keep];hit=crossing(P[RT[cp[:,0]]],P[RT[cp[:,1]]]);hp=cp[hit];hs=sh[hit];wit=[]
 for pair,n in zip(ids[hp],hs):
  fs=[]
  for f in pair:
   pi,fi=(0,int(f))if f<p0faces else(2,int(f-p0faces));tri=tris[pi][fi];fs.append({'primitive':pi,'face':fi,'source_face_ancestry':int(ancestry[pi][fi])if ancestry is not None else fi,'face_kind':str(kinds[fi-p0faces+len(kinds)])if False else('source'if kinds is None or pi!=0 or fi<33968 else str(kinds[fi-33968])),'vertex_ids':tri.tolist(),'positions_m':pos[pi][tri].tolist()})
  wit.append({'shared_physical_weld_count':int(n),'faces':fs})
 weldtri=alias[T];ed=np.concatenate([weldtri[:,[0,1]],weldtri[:,[1,2]],weldtri[:,[2,0]]]);sorteded=np.sort(ed,axis=1);uniq,inv,count=np.unique(sorteded,axis=0,return_inverse=True,return_counts=True);direction=np.where(ed[:,0]<ed[:,1],1,-1);wind=np.bincount(inv,weights=direction,minlength=len(uniq));coord={int(v):q for v,q in zip(alias,P)};boundary=[sorted([coord[int(a)].tolist(),coord[int(b)].tolist()])for a,b in uniq[count==1]]
 row={'variant':name,'region':'All cloth0+2 triangles with ANY corner y>=1.08; no upper y crop','triangles_tested':len(RT),'candidate_phase':'float64 AABB, avoiding float32 BVH rejection of inherited thin face28','strict_zero_shared_physical_weld_crossings':int((hs==0).sum()),'strict_one_shared_physical_weld_crossings':int((hs==1).sum()),'all_crossing_witnesses':wit,'full_cloth_boundary_edges':int((count==1).sum()),'full_cloth_nonmanifold_edges':int((count>2).sum()),'full_cloth_incoherent_two_face_winding_edges':int(((count==2)&(wind!=0)).sum()),'physical_weld_coordinate_max_diameter_m':0.}
 _,group=np.unique(alias,return_inverse=True);ng=group.max()+1;low=np.full((ng,3),np.inf);high=np.full((ng,3),-np.inf);np.minimum.at(low,group,P);np.maximum.at(high,group,P);row['physical_weld_coordinate_max_diameter_m']=float(np.linalg.norm(high-low,axis=1).max())
 print(name,len(RT),'crosses',row['strict_zero_shared_physical_weld_crossings'],row['strict_one_shared_physical_weld_crossings'],flush=True)
 return row,{tuple(np.array(e).ravel())for e in boundary}
rows=[];r,oldbd=gate('C19-original-source',GP,GT);rows.append(r);r,v7bd=gate('V7-frozen-construction-input',[B[f'p{i}']for i in range(5)],[B[f'tr{i}']for i in range(5)]);rows.append(r);r,newbd=gate('armhole-chart-outward',[C[f'p{i}']for i in range(5)],[C[f'tr{i}']for i in range(5)],[C[f'physicalWeld{i}']for i in range(5)],[C[f'sourceFaceAncestry{i}']for i in range(5)],C['newFaceKind']);rows.append(r)
protected=[]
for i in range(5):
 n=len(B[f'p{i}']);uv=G.array(PR[i]['attributes']['TEXCOORD_0']).astype(float);margin=C[f'sourceConstructionMargin{i}'];mask=~margin;checks={}
 for key,ref in [('p',B[f'p{i}']),('W',B[f'W{i}']),('n',S[f'n{i}']),('uv',uv)]:checks[f'{key}_outside_declared_margin_exact']=bool(np.array_equal(C[f'{key}{i}'][:n][mask],ref[mask]));
 checks['old_vertex_prefix_ancestry_exact']=bool(np.array_equal(C[f'oldVertex{i}'][:n],np.arange(n)));checks['declared_rest_double_area_matches_geometry']=bool(np.allclose(C[f'restDoubleArea{i}'],np.linalg.norm(np.cross(C[f'p{i}'][C[f'tr{i}'][:,1]]-C[f'p{i}'][C[f'tr{i}'][:,0]],C[f'p{i}'][C[f'tr{i}'][:,2]]-C[f'p{i}'][C[f'tr{i}'][:,0]]),axis=1),rtol=1e-10,atol=1e-14));protected.append({'primitive':i,'checks':checks,'new_vertex_count':len(C[f'p{i}'])-n,'weight_sum_max_error':float(abs(C[f'W{i}'].sum(1)-1).max()),'max_positive_influences':int((C[f'W{i}']>1e-8).sum(1).max())})
out={'candidate_path':str(CP),'candidate_sha256':hashlib.sha256(CP.read_bytes()).hexdigest(),'source_input_path':str(BP),'source_input_sha256':hashlib.sha256(BP.read_bytes()).hexdigest(),'rows':rows,'candidate_boundary_positions_exact_to_V7':newbd==v7bd,'source_C19_boundary_positions_exact_to_V7':oldbd==v7bd,'protected_attribute_inventory':protected,'limits':['Full upper cloth rest finite strict-transverse test only. Coplanar/tangent contact and thickness unclassified. Head/body/cuff mutual contacts require separate masks.','Crossing exclusion uses physicalWeld rather than inherited source ancestry; newly separated garments cannot be hidden by source-parent identity.','No pose, support, GPU/material render or whole-character acceptance. New construction face ancestry may require multilateral parent supplements.']};(OUT/'armhole-chart-outward-independent-rest.json').write_text(json.dumps(out,indent=2));print('PROTECTED',protected,'BOUNDARY EXACT',newbd==v7bd,flush=True)
