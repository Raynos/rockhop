from pathlib import Path
import sys,json,hashlib
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
ROOT=Path('/Users/raynos/projects/games/rockhop/assets/blender/hero-remaster/rider/one-rider-v2/foundation-repair-task3');Q=ROOT/'hoodie-repair02/qa-lane';OUT=Q/'uv-lower01';sys.path.insert(0,str(ROOT/'scripts'));from glb import GLB
G=GLB(Q/'C19-source.glb');PR=[p for m in G.j['meshes']for p in m['primitives']];P=[G.array(p['attributes']['POSITION']).astype(float)for p in PR];TR=[G.array(p['indices']).astype(int).reshape(-1,3)for p in PR];RAW=np.concatenate([P[0],P[2]]);T=np.concatenate([TR[0],TR[2]+len(P[0])]);U,A=np.unique(RAW,axis=0,return_inverse=True);WT=A[T]
E=np.sort(np.concatenate([WT[:,[0,1]],WT[:,[1,2]],WT[:,[2,0]]]),axis=1);F=np.tile(np.arange(len(T)),3);order=np.lexsort((E[:,1],E[:,0]));E=E[order];F=F[order];uniq,start,count=np.unique(E,axis=0,return_index=True,return_counts=True);emap={tuple(e):i for i,e in enumerate(uniq)}
rows=[]
for name in ['geometry','texture-clues']:
 path=ROOT/'hoodie-repair03/lower-foundation/seam-proposals'/f'{name}.npz';a=np.load(path);cycle=a['cycle'];edges=np.sort(a['cutEdges'],axis=1);edgekeys={tuple(e)for e in edges};ordered=np.sort(np.stack([cycle,np.roll(cycle,-1)],axis=1),axis=1);orderedkeys={tuple(e)for e in ordered};deg={int(i):0 for i in np.unique(edges)}
 for x,y in edges:deg[int(x)]+=1;deg[int(y)]+=1
 ids=[emap.get(tuple(e),-1)for e in edges];adj=[];witness=[]
 for e,i in zip(edges,ids):
  fs=[]if i<0 else F[start[i]:start[i]+count[i]].tolist();aliases=[]
  for vi in e:
   sourceids=np.flatnonzero(A==vi);aliases.append({'source_weld_id':int(vi),'rest_m':U[vi].tolist(),'primitive_vertices':[[0,int(v)]if v<len(P[0])else[2,int(v-len(P[0]))]for v in sourceids]})
  witness.append({'source_weld_edge':e.tolist(),'source_combined_faces':fs,'primitive_faces':[[0,int(f)]if f<len(TR[0])else[2,int(f-len(TR[0]))]for f in fs],'edge_aliases':aliases})
 for e,s,n in zip(uniq,start,count):
  if tuple(e)in edgekeys:continue
  fs=F[s:s+n]
  for i in range(len(fs)):
   for j in range(i+1,len(fs)):adj.append((int(fs[i]),int(fs[j])))
 ij=np.array(adj,int);graph=coo_matrix((np.ones(len(ij)*2),(np.r_[ij[:,0],ij[:,1]],np.r_[ij[:,1],ij[:,0]])),shape=(len(T),len(T))).tocsr();nc,labels=connected_components(graph,directed=False);sizes=np.bincount(labels);shirt=np.asarray(a['shirtFaces'],bool);face_y=RAW[T][:,:,1];z=RAW[T][:,:,2];upper=(face_y>1.15).all(1);leftleg=(face_y<.5).all(1)&(z>.02).all(1);rightleg=(face_y<.5).all(1)&(z<-.02).all(1);upper_labels=np.unique(labels[upper]);left_labels=np.unique(labels[leftleg]);right_labels=np.unique(labels[rightleg]);shirtid=int(labels[np.flatnonzero(shirt)[0]]);label_match=np.array_equal(shirt,labels==shirtid);splitlabels=np.unique(labels);bnd=set();
 for e,s,n in zip(uniq,start,count):
  fs=F[s:s+n]
  if len(set(labels[fs]))>1:bnd.add(tuple(e))
 winding={'shirt':[],'pants':[]}
 for x,y in zip(cycle,np.roll(cycle,-1)):
  fs=np.flatnonzero((WT==x).any(1)&(WT==y).any(1))
  for f in fs:
   tri=WT[f];ix=int(np.flatnonzero(tri==x)[0]);winding['shirt'if shirt[f]else'pants'].append(1 if tri[(ix+1)%3]==y else -1)
 cycU=U[cycle];area_xz=.5*np.sum(cycU[:,0]*np.roll(cycU[:,2],-1)-np.roll(cycU[:,0],-1)*cycU[:,2]);checks={'source_points_exact':np.array_equal(a['sourcePoints'],U),'all_source_aliases_exact_and_complete':np.array_equal(a['aliases'],A),'all_source_face_ancestry_exact':np.array_equal(a['sourceCombinedFaces'],T),'weld_face_ancestry_exact':np.array_equal(a['sourceWeldTriangles'],WT),'cycle_unique_vertices':len(np.unique(cycle))==len(cycle),'cycle_all_degree_two':all(v==2 for v in deg.values()),'ordered_cycle_matches_cut_edges':orderedkeys==edgekeys and len(edges)==len(edgekeys),'all_cut_edges_are_two_face_source_edges':all(i>=0 and count[i]==2 for i in ids),'exactly_two_face_components':nc==2,'root_shirt_mask_is_exact_recomputed_component':label_match,'all_upper_torso_seeds_in_shirt':bool(shirt[upper].all()),'left_leg_seeds_all_in_pants':bool((~shirt[leftleg]).all()),'right_leg_seeds_all_in_pants':bool((~shirt[rightleg]).all()),'both_legs_same_pants_component':len(left_labels)==1 and np.array_equal(left_labels,right_labels) and left_labels[0]!=shirtid,'entire_partition_boundary_exactly_cut':bnd==edgekeys,'source_face_winding_consistent_opposite_across_cut':len(winding['shirt'])==len(cycle) and len(winding['pants'])==len(cycle) and len(set(winding['shirt']))==1 and len(set(winding['pants']))==1 and winding['shirt'][0]==-winding['pants'][0]}
 # Input proposal only contains source references/labels; no changed mesh attrs or indices.
 raw_seam_ids=np.flatnonzero(np.isin(A,cycle));ownership=[]
 for v in raw_seam_ids:
  fs=np.flatnonzero((T==v).any(1));ownership.append({'primitive_vertex':[0,int(v)]if v<len(P[0])else[2,int(v-len(P[0]))],'source_weld_id':int(A[v]),'shirt_combined_faces':fs[shirt[fs]].tolist(),'pants_combined_faces':fs[~shirt[fs]].tolist()})
 ownership_counts={'both_sides':sum(bool(r['shirt_combined_faces'])and bool(r['pants_combined_faces'])for r in ownership),'shirt_only':sum(bool(r['shirt_combined_faces'])and not r['pants_combined_faces']for r in ownership),'pants_only':sum(bool(r['pants_combined_faces'])and not r['shirt_combined_faces']for r in ownership)}
 row={'proposal':name,'proposal_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'checks':{k:bool(v)for k,v in checks.items()},'edge_count':len(edges),'cycle_vertex_count':len(cycle),'cycle_y_range_m':[float(cycU[:,1].min()),float(cycU[:,1].max())],'ordered_cycle_signed_xz_area_m2':float(area_xz),'source_face_winding_relative_to_ordered_cycle':{k:sorted(set(v))for k,v in winding.items()},'face_component_sizes':sizes.tolist(),'shirt_face_count':int(shirt.sum()),'pants_face_count':int((~shirt).sum()),'source_seed_face_counts':{'upper_torso':int(upper.sum()),'left_leg':int(leftleg.sum()),'right_leg':int(rightleg.sum())},'seed_component_labels':{'upper':upper_labels.tolist(),'left_leg':left_labels.tolist(),'right_leg':right_labels.tolist()},'cut_source_alias_instances':sum(len(x['primitive_vertices'])for w in witness for x in w['edge_aliases'])//2,'cut_vertices_with_multiple_source_aliases':int(sum(np.sum(A==i)>1 for i in cycle)),'raw_seam_vertex_side_ownership_counts':ownership_counts,'raw_seam_vertex_side_ownership':ownership,'full_source_edge_face_alias_witnesses':witness,'status':'REST_SEAM_TOPOLOGY_PASS'if all(checks.values())else'FAIL'};rows.append(row);print({k:v for k,v in row.items()if k not in ['full_source_edge_face_alias_witnesses','raw_seam_vertex_side_ownership']})
out={'source_sha256':hashlib.sha256(G.raw).hexdigest(),'cloth_source_primitives':[0,2],'source_topology_reference_only':True,'source_socket_preservation':'No mesh edits in proposal NPZ. Raw source face indices and every source alias are independently exact. Actual split export must separately prove preserved original attribute rows/socket indices or supply explicit map.','visual_review':'All six parent CPU rest overlays inspected. Magenta follows bottom gold rib-band/jeans boundary; cyan follows upper rib-band. Side sleeve occludes short segment, covered by topology proof. Existing gold/blue atlas contamination remains.','rows':rows,'limits':['Rest-loop topology and location only; no skinning, motion, normal/UV continuity, pressure or saddle support acceptance.','No anatomical pelvis shell exists in source; planned cap anatomy is new construction.','Separated garment duplication must retain all per-side alias instances but assign distinct physical garment weld groups.']};(OUT/'seam-proposal-independent-proof.json').write_text(json.dumps(out,indent=2))
