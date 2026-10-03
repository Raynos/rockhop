from pathlib import Path
import numpy as np,json,sys,hashlib,struct,copy
from scipy.spatial import cKDTree
ROOT=Path('/Users/raynos/projects/games/rockhop/assets/blender/hero-remaster/rider/one-rider-v2/foundation-repair-task3')
OUT=ROOT/'hoodie-repair02/qa-lane/continuous-shell178'
sys.path.insert(0,str(ROOT/'scripts'));from glb import GLB
s=(ROOT/'runtime/prepare_references.py').read_text();ns={'np':np,'json':json,'struct':struct,'copy':copy,'hashlib':hashlib,'Path':Path};exec(s[s.index('def decode('):s.index("manifest={'tolerance_m'")],ns)
rawarray=ns['array']; pose=ns['pose']
s=(ROOT/'hoodie-repair02/qa-lane/scripts/geometry_gate.py').read_text();ns2={'np':np,'EPS':1e-9};exec(s[s.index('def crossing'):s.index('def region_geom')],ns2);crossing=ns2['crossing']
def loads(name):
 g=GLB(OUT/(name+'.glb'));nodes,world=pose(g.j,g.bin,{'channels':[]},0);return g,world
source,sw=loads('source-C19');shell,hw=loads('shell01');assembly,aw=loads('neutral-assembly01')
def parts(g,world):
 result=[]
 for mi,m in enumerate(g.j['meshes']):
  nodes=[ni for ni,n in enumerate(g.j['nodes'])if n.get('mesh')==mi]
  assert len(nodes)==1
  ni=nodes[0]
  for pi,pr in enumerate(m['primitives']):
   p=rawarray(g.j,g.bin,pr['attributes']['POSITION']);p=(np.c_[p,np.ones(len(p))]@world[ni].T)[:,:3]
   tr=rawarray(g.j,g.bin,pr['indices']).astype(int).reshape(-1,3)
   result.append({'p':p,'tr':tr,'mesh':mi,'primitive':pi,'node':ni,'attrs':pr['attributes'],'pr':pr})
 return result
sp=parts(source,sw);hp=parts(shell,hw)[0];ap=parts(assembly,aw)
a=np.load(OUT/'drafted-shell01.npz');authored=np.c_[a['p'][:,0],a['p'][:,2],-a['p'][:,1]];tree=cKDTree(authored);dist,ids=tree.query(hp['p']);print('export vertex mapping',dist.max(),flush=True)
assert dist.max()<1e-7
# Export triangle ancestry by sorted authored vertex IDs; degeneracies can create duplicate ambiguous keys.
lookup={}
for fi,tri in enumerate(a['f']):lookup.setdefault(tuple(sorted(tri)),[]).append(fi)
parents=[lookup.get(tuple(sorted(ids[t])),[])for t in hp['tr']]
assert all(parents)
usedparents=set(f for pa in parents for f in pa)
missing=sorted(set(range(len(a['f'])))-usedparents)
def topology(p,tr,alias,panel=None):
 wt=alias[tr];d=np.r_[wt[:,[0,1]],wt[:,[1,2]],wt[:,[2,0]]];edges,inv,counts=np.unique(np.sort(d,1),axis=0,return_inverse=True,return_counts=True)
 signed=np.bincount(inv,weights=np.where(d[:,0]<d[:,1],1,-1));coord={int(v):p[i]for i,v in enumerate(alias)}
 fi=np.tile(np.arange(len(tr)),3);witness=[]
 for e in np.flatnonzero(counts>2):
  f=fi[inv==e];witness.append({'physical_vertices':edges[e].tolist(),'coordinates_m':[coord[int(x)].tolist()for x in edges[e]],'incident_exported_faces':f.tolist(),'incident_authored_faces':[parents[i]for i in f]if panel is not None else None,'incident_panels':[sorted(set(str(a['panel'][x])for x in parents[i]))for i in f]if panel is not None else None,'incidence':int(counts[e])})
 be=edges[counts==1];adj={}
 for x,y in be:
  adj.setdefault(int(x),set()).add(int(y));adj.setdefault(int(y),set()).add(int(x))
 components=[];remaining=set(adj)
 while remaining:
  todo=[remaining.pop()];vs=set(todo)
  while todo:
   x=todo.pop()
   for y in adj[x]:
    if y in remaining:remaining.remove(y);vs.add(y);todo.append(y)
  coords=np.array([coord[x]for x in vs]);deg=[len(adj[x])for x in vs]
  components.append({'vertices':len(vs),'edges':sum(deg)//2,'simple_cycle':all(v==2 for v in deg),'degree_histogram':{str(x):deg.count(x)for x in sorted(set(deg))},'bounds_m':[coords.min(0).tolist(),coords.max(0).tolist()]})
 q=p[tr];area=np.linalg.norm(np.cross(q[:,1]-q[:,0],q[:,2]-q[:,0]),axis=1)
 return {'triangles':len(tr),'referenced_raw_vertices':len(np.unique(tr)),'physical_vertices':len(np.unique(wt)),'boundary_edges':int((counts==1).sum()),'boundary_components':components,'nonmanifold_edges':int((counts>2).sum()),'nonmanifold_witnesses':witness,'two_face_same_direction_edges':int(((counts==2)&(signed!=0)).sum()),'zero_area_below_1e_minus12':np.flatnonzero(area<1e-12).tolist(),'minimum_double_area_m2':float(area.min()),'degenerate_weld_triangles':np.flatnonzero((wt[:,0]==wt[:,1])|(wt[:,0]==wt[:,2])|(wt[:,1]==wt[:,2])).tolist()}
def intervals(t1,t2):
 n1=np.cross(t1[1]-t1[0],t1[2]-t1[0]);n2=np.cross(t2[1]-t2[0],t2[2]-t2[0]);n1/=np.linalg.norm(n1);n2/=np.linalg.norm(n2);line=np.cross(n1,n2);ln=np.linalg.norm(line)
 if ln<1e-14:return {'planes_angle_sine':float(ln),'overlap_segment_m':None}
 line/=ln;vals=[]
 for tri,n,plane in [(t1,n2,t2[0]),(t2,n1,t1[0])]:
  ds=(tri-plane)@n; pts=[]
  for i,j in [(0,1),(1,2),(2,0)]:
   if ds[i]*ds[j]<0:pts.append(tri[i]+ds[i]/(ds[i]-ds[j])*(tri[j]-tri[i]))
   if abs(ds[i])<1e-14:pts.append(tri[i])
  x=np.array(pts)@line if pts else np.array([]);vals.append((x.min(),x.max())if len(x)else (np.nan,np.nan))
 lo=max(v[0]for v in vals);hi=min(v[1]for v in vals)
 return {'planes_angle_sine':float(ln),'overlap_segment_m':float(max(0,hi-lo)),'max_vertex_plane_distance_m':float(max(abs((t1-t2[0])@n2).max(),abs((t2-t1[0])@n1).max()))}
def literal(p,tr,alias,labels):
 q=p[tr];lo=q.min(1);hi=q.max(1);centres=q.mean(1);radius=np.linalg.norm(q-centres[:,None],axis=2).max(1);tree=cKDTree(centres);wt=alias[tr];hits=[];n=0
 for start in range(0,len(q),64):
  js=tree.query_ball_point(centres[start:start+64],radius[start:start+64]+radius.max());pairs=np.array([(start+i,j)for i,ls in enumerate(js)for j in ls if start+i<j],int).reshape(-1,2)
  if not len(pairs):continue
  pairs=pairs[((lo[pairs[:,0]]<=hi[pairs[:,1]])&(lo[pairs[:,1]]<=hi[pairs[:,0]])).all(1)];shared=np.array([len(set(wt[x]).intersection(wt[y]))for x,y in pairs]);keep=shared<2;pairs=pairs[keep];shared=shared[keep];n+=len(pairs)
  if not len(pairs):continue
  h=crossing(q[pairs[:,0]],q[pairs[:,1]])
  for (x,y),k in zip(pairs[h],shared[h]):hits.append({'faces':[int(x),int(y)],'labels':[labels[x],labels[y]],'shared_exact_weld_vertices':int(k),'triangles_m':[q[x].tolist(),q[y].tolist()],**intervals(q[x],q[y])})
 return {'strict_zero_shared_crossings':sum(h['shared_exact_weld_vertices']==0 for h in hits),'strict_one_shared_crossings':sum(h['shared_exact_weld_vertices']==1 for h in hits),'AABB_nonedge_pairs_tested':n,'witnesses':hits}
p=hp['p'];tr=hp['tr'];_,alias=np.unique(p,axis=0,return_inverse=True)
top=topology(p,tr,alias,True);labels=[{'exported_face':i,'authored_faces':pa,'panels':sorted(set(str(a['panel'][x])for x in pa))}for i,pa in enumerate(parents)]
lit=literal(p,tr,alias,labels)
# Precision-only union is an explicit diagnostic; it does not repair/export anything.
near=cKDTree(p).query_pairs(2e-7,output_type='ndarray');uf=np.arange(len(p))
def find(x):
 while uf[x]!=x:uf[x]=uf[uf[x]];x=uf[x]
 return x
for x,y in near:uf[find(y)]=find(x)
virtual=np.array([find(i)for i in range(len(p))]);merged=topology(p,tr,virtual,True)
near_nonzero=[{'vertices':[int(x),int(y)],'gap_m':float(np.linalg.norm(p[x]-p[y])),'positions_m':[p[x].tolist(),p[y].tolist()]}for x,y in near if not np.array_equal(p[x],p[y])]
# Source-prefix and accessor contracts; compare decoded and descriptors without mutating glTF.
protected=[]
for i in [1,2,3,4]:
 s=sp[i]['pr'];t=ap[i]['pr'];checks={'primitive_descriptor_exact':s==t,'world_matrix_exact':np.array_equal(sw[sp[i]['node']],aw[ap[i]['node']]),'all_accessors_exact':True}
 for k,access in s['attributes'].items():checks['all_accessors_exact'] &= source.j['accessors'][access]==assembly.j['accessors'][t['attributes'][k]] and np.array_equal(rawarray(source.j,source.bin,access),rawarray(assembly.j,assembly.bin,t['attributes'][k]))
 protected.append({'source_flat_primitive':i,'checks':checks,'bounds_m':[sp[i]['p'].min(0).tolist(),sp[i]['p'].max(0).tolist()]})
metadata=json.loads((OUT/'original-assembly.json').read_text()); source0=sp[0];q0=source0['p'][source0['tr']];mask=(q0[:,:,1]<=.965).all(1);clause=(q0[:,:,1].max(1)<=.955)&(abs(q0[:,:,2]).min(1)>=.28);selected=np.flatnonzero(mask|clause)
shellcopy=ap[5];assemblycontract={'source_BIN_prefix_exact':bytes(assembly.bin[:len(source.bin)])==bytes(source.bin),'source_material_image_texture_sampler_prefix_exact':{k:assembly.j.get(k,[])[:len(source.j.get(k,[]))]==source.j.get(k,[])for k in ['materials','images','textures','samplers']},'protected_inventory':protected,'all_source_primitive0_attributes_exact':all(source0['pr']['attributes'][k]==ap[0]['pr']['attributes'][k] and np.array_equal(rawarray(source.j,source.bin,x),rawarray(assembly.j,assembly.bin,ap[0]['pr']['attributes'][k]))for k,x in source0['pr']['attributes'].items()),'mask_selected_count':len(selected),'mask_indices_exact_to_source_faces':np.array_equal(ap[0]['tr'],source0['tr'][selected]),'retained_face_ID_metadata_exact':selected.tolist()==metadata['sourcePrimitive0RetainedTriangleIDs'],'purported_cuff_clause_adds_triangles':int((clause&~mask).sum()),'assembly_shell_POSITION_world_exact':np.array_equal(shellcopy['p'],p),'assembly_shell_indices_exact':np.array_equal(shellcopy['tr'],tr),'assembly_shell_NORMAL_accessor_values_exact':np.array_equal(rawarray(assembly.j,assembly.bin,shellcopy['attrs']['NORMAL']),rawarray(shell.j,shell.bin,hp['attrs']['NORMAL'])),'active_mesh_nodes_with_skin':sum('skin'in n for n in assembly.j['nodes']if 'mesh'in n),'animation_count':len(assembly.j.get('animations',[])),'shell_attributes':list(hp['attrs']),'shell_material':shell.j['materials'][hp['pr']['material']]}
report={'status':'REJECTED_REST_DRAFT_NOT_RIGGED','freeze_manifest':'freeze-manifest.json','coordinate_mapping':'Authored Blender (X,Y,Z) mapped to glTF (X,Z,-Y); all903 exported vertices nearest authored match; actual node-world transforms evaluated.','vertex_mapping_max_m':float(dist.max()),'authored_triangles':len(a['f']),'exported_triangles':len(tr),'missing_authored_faces':missing,'missing_authored_panels':{str(a['panel'][i]):sum(a['panel'][j]==a['panel'][i]for j in missing)for i in missing},'export_face_ancestry':labels,'actual_export_exact_weld_topology':top,'actual_export_literal_crossings':lit,'precision_diagnostic_2e_minus7_m':{'near_nonzero_vertex_pairs':near_nonzero,'virtual_union_topology':merged,'limitation':'Diagnostic connectivity only. No position edit, weld, regenerated normals, export or crossing approval.'},'assembly_contract':assemblycontract,'limits':['Static exported topology and strict transverse triangle crossings only. Coplanar/tangent contact and fabric thickness are unclassified.','Exact-position weld is declared;2e-7 virtual union is reported separately, never silently excludes crossings.','No rigging/weights/motion/render recipes executed; assembly is explicitly unskinned with no animations.','Head/glove/material identity proof does not establish hood/cuff/hem physical sewing, standing appearance, support or runtime acceptance.']}
(OUT/'independent-export-rest.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'exported_faces':len(tr),'missing_authored':missing,'topology':{k:v for k,v in top.items()if k not in ['nonmanifold_witnesses','boundary_components']},'boundary_components':len(top['boundary_components']),'literal':{k:v for k,v in lit.items()if k!='witnesses'},'max_cross_segment_m':max([h['overlap_segment_m']or 0 for h in lit['witnesses']],default=0),'near_pairs':len(near_nonzero),'virtual_boundary_components':len(merged['boundary_components']),'assembly':assemblycontract},indent=2),flush=True)
