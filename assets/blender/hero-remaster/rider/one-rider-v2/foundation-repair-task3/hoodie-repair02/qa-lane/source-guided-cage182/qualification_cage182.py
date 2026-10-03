from pathlib import Path
import numpy as np,json,sys,hashlib,collections,shutil
R=Path('/Users/raynos/projects/games/rockhop/assets/blender/hero-remaster/rider/one-rider-v2/foundation-repair-task3');O=R/'hoodie-repair02/qa-lane/source-guided-cage182';O.mkdir(exist_ok=True);S=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/clean-upper-shell01/source-guided-cage182');D=Path('/Users/raynos/projects/games/rockhop/docs/evidence/hero-remaster/one-rider-v2/clean-upper-shell01');expected='8f1816bb3a87677487c4869b69dc2bb361ae0bc3ef934acacc1672c908501fa3';manifest=[]
paths=[(S/n,n)for n in ['cage01.npz','neutral-assembly01.glb','lower-cut-ancestry.json','quad-face-tags.json']]+[(D/'source-guided-cage182/parent-contract.json','parent-contract.json'),(D/'source-boundaries181/CONSTRUCTION_DECISION.md','CONSTRUCTION_DECISION.md'),(Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/clean-upper-shell01/source-boundaries181/source-boundary-profiles.npz'),'source-boundary-profiles.npz')]
for source,name in paths:
 raw=source.read_bytes();sha=hashlib.sha256(raw).hexdigest()
 if name=='cage01.npz':assert sha==expected
 (O/name).write_bytes(raw);manifest.append({'source_read_only':str(source),'owned_copy':name,'sha256':sha,'bytes':len(raw)})
(O/'freeze-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');a=np.load(O/'cage01.npz');p=a['p'].astype(float);f=a['f'].astype(int);coords,al,count=np.unique(p,axis=0,return_inverse=True,return_counts=True);q=p[f];area=np.linalg.norm(np.cross(q[:,1]-q[:,0],q[:,2]-q[:,0]),axis=1);zero=np.flatnonzero(area<1e-12)
def topo(alias):
 wt=alias[f];dr=np.r_[wt[:,[0,1]],wt[:,[1,2]],wt[:,[2,0]]];ed,inv,co=np.unique(np.sort(dr,1),axis=0,return_inverse=True,return_counts=True);sg=np.bincount(inv,weights=np.where(dr[:,0]<dr[:,1],1,-1));fi=np.tile(np.arange(len(f)),3);w=[];coord={int(v):p[i]for i,v in enumerate(alias)}
 for ei in np.flatnonzero((co>2)|((co==2)&(sg!=0))):
  faces=fi[inv==ei].tolist();w.append({'physical_or_raw_vertex_ids':ed[ei].tolist(),'coordinates_m':[coord[int(v)].tolist()for v in ed[ei]],'edge_occurrence_count':int(co[ei]),'unique_incident_faces':sorted(set(faces)),'incident_face_occurrences':faces,'same_direction_two_face_flag':bool(co[ei]==2 and sg[ei]!=0),'zero_length_self_edge':bool(ed[ei,0]==ed[ei,1]),'zero_area_incident_faces':sorted(set(faces).intersection(zero.tolist()))})
 adj={}
 for x,y in ed[co==1]:adj.setdefault(int(x),set()).add(int(y));adj.setdefault(int(y),set()).add(int(x))
 rem=set(adj);loops=[]
 while rem:
  st=[rem.pop()];vs=set(st)
  while st:
   for y in adj[st.pop()]:
    if y in rem:rem.remove(y);vs.add(y);st.append(y)
  pts=np.array([coord[x]for x in vs]);dg=[len(adj[x])for x in vs];loops.append({'edges':sum(dg)//2,'vertices':len(vs),'degree2_cycle':all(v==2 for v in dg),'degree_histogram':{str(v):dg.count(v)for v in sorted(set(dg))},'bounds_m':[pts.min(0).tolist(),pts.max(0).tolist()]})
 result={'triangles':len(f),'referenced_vertices':len(np.unique(wt)),'unused_raw_vertices':sorted(set(range(len(p)))-set(f.ravel())),'edge_count':len(ed),'Euler_V_minus_E_plus_F':len(np.unique(wt))-len(ed)+len(f),'boundary_edges':int((co==1).sum()),'boundary_components':len(loops),'boundary_loops':loops,'nonmanifold_edges_occurrence_count_gt2':int((co>2).sum()),'nonmanifold_nonzero_edges':int(((co>2)&(ed[:,0]!=ed[:,1])).sum()),'same_direction_two_face_flags':int(((co==2)&(sg!=0)).sum()),'true_nonzero_two_face_winding_conflicts':int(((co==2)&(sg!=0)&(ed[:,0]!=ed[:,1])).sum()),'collapsed_alias_triangles':int(((wt[:,0]==wt[:,1])|(wt[:,0]==wt[:,2])|(wt[:,1]==wt[:,2])).sum()),'all_bad_edge_witnesses':w};return result,(ed,co,sg,inv,fi)
rawtop,_=topo(np.arange(len(p)));physical,(ed,co,sg,inv,fi)=topo(al);lookup={tuple(edge):i for i,edge in enumerate(ed)};named={};covered=set();profiles=np.load(O/'source-boundary-profiles.npz')
for key,sourcekey in [('hoodIDs','hood_bodyCycle0Float32Positions'),('cuffLIDs','cuff_body_gloveCycle0Float32Positions'),('cuffRIDs','cuff_body_gloveCycle1Float32Positions'),('hemIDs',None)]:
 ids=a[key].astype(int);rows=[]
 for k,(x,y)in enumerate(zip(ids,np.roll(ids,-1))):
  edge=tuple(sorted([int(al[x]),int(al[y])]))
  if edge not in lookup:rows.append({'cycle_edge':k,'raw_vertices':[int(x),int(y)],'missing_edge':True});continue
  ei=lookup[edge];covered.add(edge);face=fi[inv==ei].tolist();rows.append({'cycle_edge':k,'raw_vertices':[int(x),int(y)],'physical_vertices':list(edge),'positions_m':[p[x].tolist(),p[y].tolist()],'cage_edge_incidence':int(co[ei]),'cage_incident_faces':face,'edge_direction_balance_in_sorted_order':float(sg[ei])})
 named[key]={'nodes':len(ids),'injective_final_float32_nodes':len(np.unique(al[ids]))==len(ids),'each_named_edge_exactly_one_cage_face':all(x.get('cage_edge_incidence')==1 for x in rows),'bad_cycle_edge_witnesses':[x for x in rows if x.get('cage_edge_incidence')!=1],'all_cycle_edge_inventory':rows,'source_position_rows_exact_in_order':bool(np.array_equal(a['p'][ids],profiles[sourcekey]))if sourcekey else None}
# Any physical boundary not declared hood/cuff/hem.
unknown=[{'physical_vertices':edge.tolist(),'positions_m':coords[edge].tolist()}for edge,c in zip(ed,co)if c==1 and tuple(edge)not in covered]
# Actual assembly counterpart seams only: no all-pair literal broad gate.
sys.path.insert(0,str(R/'scripts'));from glb import GLB
g=GLB(O/'neutral-assembly01.glb');prim=[pr for m in g.j['meshes']for pr in m['primitives']];assert len(prim)==6;assert all(not any(k in n for k in ['matrix','translation','rotation','scale','skin'])for n in g.j['nodes']if 'mesh'in n)
ap=[g.array(pr['attributes']['POSITION']).astype(float)for pr in prim];at=[g.array(pr['indices']).reshape(-1,3).astype(int)for pr in prim];assemblysame=np.array_equal(ap[5],p)and np.array_equal(at[5],f)
def keyedge(pa,pb):return tuple(sorted((tuple(pa),tuple(pb))))
sewn={}
for name,donor in [('hoodIDs',2),('cuffLIDs',1),('cuffRIDs',1),('hemIDs',0)]:
 rows=named[name]['all_cycle_edge_inventory'];desired={keyedge(x['positions_m'][0],x['positions_m'][1]):i for i,x in enumerate(rows)if 'positions_m'in x};observed=collections.defaultdict(list);pp=ap[donor]
 for face,t in enumerate(at[donor]):
  for x,y in [(t[0],t[1]),(t[1],t[2]),(t[2],t[0])]:
   k=keyedge(pp[x],pp[y])
   if k in desired:observed[k].append({'donor_face':face,'raw_vertices':[int(x),int(y)],'signed_lex_position_direction':1 if tuple(pp[x])<tuple(pp[y])else -1})
 bad=[];complete=0;opposed=0
 for row in rows:
  if 'positions_m'not in row:bad.append(row);continue
  k=keyedge(*row['positions_m']);don=observed[k];cfaces=row['cage_incident_faces'];cdirs=[]
  for face in cfaces:
   for x,y in [(f[face,0],f[face,1]),(f[face,1],f[face,2]),(f[face,2],f[face,0])]:
    if keyedge(p[x],p[y])==k:cdirs.append(1 if tuple(p[x])<tuple(p[y])else -1)
  ok=len(cdirs)==1 and len(don)==1;opp=ok and cdirs[0]+don[0]['signed_lex_position_direction']==0;complete+=ok;opposed+=opp
  if not opp:bad.append({'cycle_edge':row['cycle_edge'],'positions_m':row['positions_m'],'cage_faces':cfaces,'cage_directions':cdirs,'donor_edge_occurrences':don,'one_face_each_side':ok,'opposite_winding':opp})
 sewn[name]={'expected_edges':len(rows),'represented_donor_flat_primitive':donor,'one_face_each_side_edges':int(complete),'one_face_each_opposite_winding_edges':int(opposed),'all_failure_witnesses':bad}
dups=[{'physical_vertex':int(i),'position_m':coords[i].tolist(),'raw_vertices':np.flatnonzero(al==i).tolist()}for i in np.flatnonzero(count>1)]
report={'status':'FAIL_TOPOLOGY_DO_NOT_RENDER_OR_RIG','cage_sha256':expected,'freeze_manifest':'freeze-manifest.json','final_POSITION_dtype':'float32 already frozen','coordinate_convention':'All cage and assembly POSITION glTF Xforward,Yup,Zlateral metres; active mesh-node transforms identity.','raw_index_topology':rawtop,'exact_POSITION_physical_topology':physical,'double_area_below1e_minus12_count':len(zero),'all_degenerate_face_witnesses':[{'face':int(i),'raw_vertices':f[i].tolist(),'physical_vertices':al[f[i]].tolist(),'positions_m':q[i].tolist(),'double_area_m2':float(area[i])}for i in zero],'minimum_double_area_m2':float(area.min()),'exact_duplicate_position_groups':dups,'duplicate_position_excess_raw_rows':int(sum(count-1)),'named_boundary_contract':named,'undeclared_physical_boundary_edges':unknown,'actual_assembly_cage_POSITION_and_indices_exact_to_NPZ':bool(assemblysame),'actual_assembly_sewn_named_seams':sewn,'limits':['Bounded topology and named actual-donor edge-incidence qualification only. No broadcollision/render/build recipes executed.','Exact-coordinate physical quotient separate raw UV/normal rows; occurrencecounts and unique incident faces separately recorded.','Protected donor/source attribute and profile/cut ancestry handled by construction worker; no duplicated anatomical/cut reconstruction.','Float32 degeneracy or sewnedge winding failure stops dependent art/rig stages. No claim of pose/support/runtime quality.']}
(O/'independent-topology-seams.json').write_text(json.dumps(report,indent=2)+'\n');shutil.copyfile(Path(__file__),O/'qualification_cage182.py')
print(json.dumps({'zeroareas':len(zero),'raw_summary':{k:v for k,v in rawtop.items()if k not in ['all_bad_edge_witnesses','boundary_loops','unused_raw_vertices']},'physical_summary':{k:v for k,v in physical.items()if k not in ['all_bad_edge_witnesses','boundary_loops','unused_raw_vertices']},'duplicate_groups':len(dups),'duplicate_excess_rows':int(sum(count-1)),'named_sewn_summary':{k:{kk:vv for kk,vv in v.items()if kk!='all_failure_witnesses'}for k,v in sewn.items()},'undeclared_boundaries':len(unknown),'report_sha256':hashlib.sha256((O/'independent-topology-seams.json').read_bytes()).hexdigest()},indent=2),flush=True)
