from pathlib import Path
import numpy as np,json,sys,hashlib,collections,shutil
from scipy.spatial import cKDTree
R=Path('/Users/raynos/projects/games/rockhop/assets/blender/hero-remaster/rider/one-rider-v2/foundation-repair-task3');O=R/'hoodie-repair02/qa-lane/continuous-sculpt179';SRC=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/clean-upper-shell01/continuous-sculpt179');O.mkdir(exist_ok=True)
expected='92cafa51ec1d4127741c173958e1eb7136f341db9fa1e7d147fc76ec02f859c3';manifest=[]
for name in ['shell01.glb','sculpt-shell01.npz','authored-private-boundaries.json','exported-private-boundaries.json','cuff-correspondence-private.json']:
 raw=(SRC/name).read_bytes();sha=hashlib.sha256(raw).hexdigest()
 if name=='shell01.glb':assert sha==expected
 (O/name).write_bytes(raw);manifest.append({'source_read_only':str(SRC/name),'owned_copy':str(O/name),'sha256':sha,'bytes':len(raw)})
(O/'freeze-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');sys.path.insert(0,str(R/'scripts'));from glb import GLB
g=GLB(O/'shell01.glb');pr=g.j['meshes'][0]['primitives'][0];assert len(g.j['meshes'])==1 and len(g.j['nodes'])==1;assert not any(k in g.j['nodes'][0]for k in ['matrix','translation','rotation','scale','skin'])
p=g.array(pr['attributes']['POSITION']).astype(float);f=g.array(pr['indices']).reshape(-1,3).astype(int);a=np.load(O/'sculpt-shell01.npz');ap=np.c_[a['p'][:,0],a['p'][:,2],-a['p'][:,1]].astype('f4').astype(float)
coords,allalias=np.unique(np.r_[p,ap],axis=0,return_inverse=True);al=allalias[:len(p)];aa=allalias[len(p):];tree=cKDTree(ap);dist,nearids=tree.query(p);assert dist.max()==0
source_face_map=collections.defaultdict(list)
for i,tri in enumerate(a['f']):source_face_map[tuple(sorted(aa[tri]))].append(i)
parents=[source_face_map[tuple(sorted(al[tri]))]for tri in f];assert all(parents)
authoredpoly=lambda faces: sorted(set(int(a['polygon'][j])for i in faces for j in parents[i]))
q=p[f];area=np.linalg.norm(np.cross(q[:,1]-q[:,0],q[:,2]-q[:,0]),axis=1);zeros=np.flatnonzero(area<1e-12)
def topo(points,tri,alias,originalIDs,withwitness):
 wt=alias[tri];dr=np.r_[wt[:,[0,1]],wt[:,[1,2]],wt[:,[2,0]]];edges,inv,count=np.unique(np.sort(dr,1),axis=0,return_inverse=True,return_counts=True);sg=np.bincount(inv,weights=np.where(dr[:,0]<dr[:,1],1,-1));fi=np.tile(originalIDs,3);coord={int(v):points[i]for i,v in enumerate(alias)};witness=[]
 for ei in np.flatnonzero((count>2)|((count==2)&(sg!=0))):
  ids=fi[inv==ei].tolist();witness.append({'physical_vertices':edges[ei].tolist(),'coordinates_m':[coord[int(x)].tolist()for x in edges[ei]],'incidence':int(count[ei]),'same_direction_two_face_winding':bool(count[ei]==2 and sg[ei]!=0),'actual_export_face_ids':ids,'authored_face_ids':[parents[i]for i in ids],'authored_polygon_ids':authoredpoly(ids),'zero_area_incident_faces':[i for i in ids if i in zeros]})
 adj={}
 for x,y in edges[count==1]:adj.setdefault(int(x),set()).add(int(y));adj.setdefault(int(y),set()).add(int(x))
 rem=set(adj);loops=[]
 while rem:
  stack=[rem.pop()];vs=set(stack)
  while stack:
   for y in adj[stack.pop()]:
    if y in rem:rem.remove(y);vs.add(y);stack.append(y)
  pts=np.array([coord[i]for i in vs]);deg=[len(adj[i])for i in vs];simple=all(v==2 for v in deg);order=[]
  if simple:
   start=min(vs);order=[start];last=None;cur=start
   while True:
    nxt=next(v for v in sorted(adj[cur])if v!=last)
    if nxt==start:break
    order.append(nxt);last,cur=cur,nxt
    if len(order)>len(vs):raise ValueError('boundary walk')
  loops.append({'edges':sum(deg)//2,'vertices':len(vs),'simple_degree2_cycle':simple,'degree_histogram':{str(v):deg.count(v)for v in sorted(set(deg))},'bounds_m':[pts.min(0).tolist(),pts.max(0).tolist()],'ordered_exact_physical_vertex_ids':order if withwitness else None,'ordered_positions_m':[coord[i].tolist()for i in order]if withwitness else None})
 return {'triangles':len(tri),'physical_vertices_referenced':len(np.unique(wt)),'boundary_edges':int((count==1).sum()),'boundary_components':len(loops),'boundary_loops':loops,'nonmanifold_edges':int((count>2).sum()),'wrong_two_face_winding_edges':int(((count==2)&(sg!=0)).sum()),'degenerate_alias_triangles':int(((wt[:,0]==wt[:,1])|(wt[:,0]==wt[:,2])|(wt[:,1]==wt[:,2])).sum()),'bad_edge_witnesses':witness if withwitness else None}
exact=topo(p,f,al,np.arange(len(f)),True);keep=np.ones(len(f),bool);keep[zeros]=False;drop=topo(p,f[keep],al,np.flatnonzero(keep),True)
# Explicit ONLY virtual precision coalescence, preserving report of actual geometry.
near=cKDTree(p).query_pairs(2e-7,output_type='ndarray');uf=np.arange(len(p))
def find(x):
 while uf[x]!=x:uf[x]=uf[uf[x]];x=uf[x]
 return x
for x,y in near:uf[find(y)]=find(x)
av=np.array([find(i)for i in range(len(p))]);pv=p.copy()
for v in np.unique(av):pv[av==v]=p[np.flatnonzero(av==v)[0]]
coalesced=topo(pv,f,av,np.arange(len(f)),False);both=topo(pv,f[keep],av,np.flatnonzero(keep),False)
nearnew=[{'vertices':[int(x),int(y)],'distance_m':float(np.linalg.norm(p[x]-p[y])),'authored_vertex_candidates':[np.flatnonzero(aa==al[x]).tolist(),np.flatnonzero(aa==al[y]).tolist()]}for x,y in near if not np.array_equal(p[x],p[y])]
zw=[{'actual_export_face':int(i),'authored_faces':parents[i],'authored_polygons':authoredpoly([i]),'raw_vertices':f[i].tolist(),'physical_vertices':al[f[i]].tolist(),'positions_m':q[i].tolist(),'double_area_m2':float(area[i])}for i in zeros]
normal=g.array(pr['attributes']['NORMAL']).astype(float);uv=g.array(pr['attributes']['TEXCOORD_0']).astype(float)
counts=collections.Counter(tuple(sorted(al[t]))for t in f);authcount=collections.Counter(tuple(sorted(aa[t]))for t in a['f']);mappedexact=counts==authcount
report={'status':'REJECTED_REST_NOT_RIGGED','actual_shell_sha256':expected,'freeze_manifest':'freeze-manifest.json','coordinate_convention':'Authored Blender(X,Y,Z) to glTF(X,Z,-Y); exactly one identity-transform unskinned node.','all19000_actual_vertices_match_quantized_authored_positions_exact':bool(dist.max()==0),'actual_authored_triangle_multiset_exact':mappedexact,'authored_export_triangles':[len(a['f']),len(f)],'exact_POSITION_weld_topology':exact,'actual_zero_area_below1e_minus12_count':len(zeros),'actual_zero_area_witnesses':zw,'virtual_only_drop8_zero_area_faces':drop,'virtual_only_2e_minus7_m_coalescence':{'new_nonzero_gap_vertex_pairs':nearnew,'max_position_move_m':float(np.linalg.norm(pv-p,axis=1).max()),'topology':coalesced,'then_drop_zero_area_topology':both,'explicit_no_artifact_modified':True},'normal_and_UV_inventory':{'all_NORMAL_finite':bool(np.isfinite(normal).all()),'NORMAL_max_unit_length_error':float(abs(np.linalg.norm(normal,axis=1)-1).max()),'all_UV_finite':bool(np.isfinite(uv).all()),'attributes':list(pr['attributes']),'uv_or_standing_appearance_not_qualified':True},'same_bug_as178':'Both involve degenerate triangles/shared physical node ownership;179 causal attribution must use actual face/polygon/cuff provenance. No claim they share identical subdivision mechanism.','limits':['No broad literal-selfcollision audit repeated; parent strict0 proof remains separate.','Exact-position aliasing is declared; near2e-7 virtual union/dropping zero faces are diagnostics only, never repaired export.','Unskinned and no clip; donor sewing, detached hem support, textures/standing image and actual4 runtime not accepted.','Original authored recipes not executed or modified.']}
(O/'independent-export-topology.json').write_text(json.dumps(report,indent=2)+'\n');shutil.copyfile(Path(__file__),O/'qualification_sculpt179.py')
print(json.dumps({'actual_sha':expected,'triangles':len(f),'multiset_exact':mappedexact,'exact':{k:v for k,v in exact.items()if k not in ['boundary_loops','bad_edge_witnesses']},'zeroarea_faces':zeros.tolist(),'virtual_drop':{k:v for k,v in drop.items()if k not in ['boundary_loops','bad_edge_witnesses']},'virtual_coalesce_nonzero_pairs':len(nearnew),'coalesce_drop':{k:v for k,v in both.items()if k not in ['boundary_loops','bad_edge_witnesses']},'report_sha256':hashlib.sha256((O/'independent-export-topology.json').read_bytes()).hexdigest()},indent=2),flush=True)
