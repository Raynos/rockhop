from pathlib import Path
import numpy as np,json,sys,collections,hashlib
from scipy.spatial import cKDTree
R=Path('/Users/raynos/projects/games/rockhop/assets/blender/hero-remaster/rider/one-rider-v2/foundation-repair-task3');O=R/'hoodie-repair02/qa-lane/continuous-shell178';sys.path.insert(0,str(R/'scripts'));from glb import GLB
g=GLB(O/'shell01.glb');pr=g.j['meshes'][0]['primitives'][0];p=g.array(pr['attributes']['POSITION']).astype(float);tr=g.array(pr['indices']).reshape(-1,3).astype(int);a=np.load(O/'drafted-shell01.npz');pa=np.c_[a['p'][:,0],a['p'][:,2],-a['p'][:,1]];_,ids=cKDTree(pa).query(p);d=json.loads((O/'independent-export-rest.json').read_text());srcmap=collections.defaultdict(list);exmap=collections.defaultdict(list)
for i,t in enumerate(a['f']):srcmap[tuple(sorted(t))].append(i)
for i,t in enumerate(tr):exmap[tuple(sorted(ids[t]))].append(i)
deficits=[]
for k,ls in srcmap.items():
 diff=len(ls)-len(exmap[k])
 if diff:deficits.append({'authored_vertex_key':[int(v)for v in k],'authored_face_ids':ls,'exported_face_ids':exmap[k],'omitted_face_multiplicity':diff,'ancestry_ambiguous_due_to_identical_triangle':len(ls)>1})
d['missing_authored_faces']=None;d['missing_authored_panels']=None;d['export_removed_triangle_multiplicity']=sum(x['omitted_face_multiplicity']for x in deficits);d['export_removed_triangle_groups']=deficits;d['export_face_ancestry_limit']='Per-face list includes all authored faces with identical vertex triple; dropped16 duplicates are proven by multiplicity, not uniquely attributable amongst identical triangles.'
# Pure convex projection intersection, coordinates translated to a common local origin to reduce cancellation.
def cross(a,b):return a[0]*b[1]-a[1]*b[0]
def polygon_clip(subject,clip):
 subject=[x.copy()for x in subject];clip=np.array(clip);signed=sum(cross(clip[i],clip[(i+1)%3])for i in range(3));clip=clip if signed>0 else clip[::-1]
 for i in range(3):
  c,e=clip[i],clip[(i+1)%3];old=subject;subject=[]
  if not old:break
  for j,b in enumerate(old):
   aa=old[j-1];da=cross(e-c,aa-c);db=cross(e-c,b-c);ina=da>=0;inb=db>=0
   if ina!=inb:subject.append(aa+(b-aa)*(da/(da-db)))
   if inb:subject.append(b)
 return np.array(subject)
def area(poly):return abs(sum(cross(poly[i],poly[(i+1)%len(poly)])for i in range(len(poly))))*.5 if len(poly)>2 else 0.
for h in d['actual_export_literal_crossings']['witnesses']:
 x,y=h['faces'];t1,t2=p[tr[x]],p[tr[y]];origin=t1[0,[1,2]];proj1=t1[:,[1,2]]-origin;proj2=t2[:,[1,2]]-origin;poly=polygon_clip(proj1,proj2);ar=area(poly)
 near=[]
 for i,v in enumerate(tr[x]):
  for j,w in enumerate(tr[y]):
   gap=float(np.linalg.norm(p[v]-p[w]));
   if gap<2e-7:near.append({'vertex_ids':[int(v),int(w)],'corner_numbers':[i,j],'distance_m':gap,'exact_same_index':bool(v==w)})
 h['projected_lateral_height_overlap_area_m2']=ar;h['span_is_not_penetration']='Intersection line span can be long for a submicrometer shared-edge sliver; projected overlap area and near-identical endpoints reported separately.';h['near_endpoint_pairs_2e_minus7_m']=near
# Explicit geometry coalescence is virtual only, used to establish numeric cause of raw stored intersections.
pairs=cKDTree(p).query_pairs(2e-7,output_type='ndarray');uf=np.arange(len(p))
def find(x):
 while uf[x]!=x:uf[x]=uf[uf[x]];x=uf[x]
 return x
for x,y in pairs:uf[find(y)]=find(x)
alias=np.array([find(i)for i in range(len(p))]);pv=p.copy()
for group in np.unique(alias):pv[alias==group]=p[np.flatnonzero(alias==group)[0]]
s=(R/'hoodie-repair02/qa-lane/scripts/geometry_gate.py').read_text();n={'np':np,'EPS':1e-9};exec(s[s.index('def crossing'):s.index('def region_geom')],n)
q=pv[tr];low=q.min(1);high=q.max(1);virtualpairs=np.array([(i,j)for i in range(len(tr))for j in range(i+1,len(tr))if len(set(alias[tr[i]]).intersection(alias[tr[j]]))<2 and (low[i]<=high[j]).all()and(low[j]<=high[i]).all()],int).reshape(-1,2);hits=n['crossing'](q[virtualpairs[:,0]],q[virtualpairs[:,1]])
d['precision_diagnostic_2e_minus7_m'].update({'virtual_coordinate_coalescing_max_move_m':float(np.linalg.norm(pv-p,axis=1).max()),'virtual_coordinate_coalescing_strict_crossing_pairs':virtualpairs[hits].tolist(),'retained_zero_area_export_faces':9,'explicit_no_artifact_change':True})
# Identify wrong directed edges and their zero-area relation.
wt=tr;directed=np.r_[wt[:,[0,1]],wt[:,[1,2]],wt[:,[2,0]]];ed,inv,count=np.unique(np.sort(directed,1),axis=0,return_inverse=True,return_counts=True);signed=np.bincount(inv,weights=np.where(directed[:,0]<directed[:,1],1,-1));fi=np.tile(np.arange(len(tr)),3);bad=np.flatnonzero((count==2)&(signed!=0));zero=set(d['actual_export_exact_weld_topology']['zero_area_below_1e_minus12']);w=[]
for i in bad:
 faces=fi[inv==i].tolist();w.append({'raw_vertices':ed[i].tolist(),'incident_exported_faces':faces,'both_faces_zero_area':all(f in zero for f in faces)})
d['actual_export_exact_weld_topology']['wrong_winding_edge_witnesses']=w
norm=g.array(pr['attributes']['NORMAL']).astype(float);d['actual_export_NORMAL_contract']={'all_finite':bool(np.isfinite(norm).all()),'unit_norm_max_error':float(abs(np.linalg.norm(norm,axis=1)-1).max()),'zero_norm_rows':int((np.linalg.norm(norm,axis=1)==0).sum()),'no_appearance_qualification':True}
d['conclusion']='REJECTED actual rest draft. Export filters16 duplicated collinear-ear triangles but retains9 zero-area faces and9 winding conflicts. Precision seams explain26 boundary components and all12 strict crossings: four extra one-corner pairs have a second nearly coincident endpoint. Virtual coordinate coalescing removes transverse intersections only; no actual repair or promotion.'
(O/'independent-export-rest.json').write_text(json.dumps(d,indent=2)+'\n')
print(json.dumps({'removed_triangle_multiplicity':d['export_removed_triangle_multiplicity'],'removed_groups':deficits,'all_wrong_winding_edges_have_zero_area_faces':all(x['both_faces_zero_area']for x in w),'virtual_crossing_count':int(hits.sum()),'virtual_move_max':float(np.linalg.norm(pv-p,axis=1).max()),'crossing_projected_area_range':[min(x['projected_lateral_height_overlap_area_m2']for x in d['actual_export_literal_crossings']['witnesses']),max(x['projected_lateral_height_overlap_area_m2']for x in d['actual_export_literal_crossings']['witnesses'])],'normal':d['actual_export_NORMAL_contract']},indent=2))
