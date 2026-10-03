"""Bounded generic sleeve-construction rest gate; input must be announced frozen.
No source writes, rendering, weights fitting, topology surgery, pose acceptance.
"""
from pathlib import Path
import sys,json,hashlib,numpy as np
ROOT=Path('/Users/raynos/projects/games/rockhop/assets/blender/hero-remaster/rider/one-rider-v2/foundation-repair-task3');Q=ROOT/'hoodie-repair02/qa-lane';HERE=ROOT/'hoodie-repair02/shape-lane/volume-lane/sleeve-tube03'
path=Path(sys.argv[1]);expected_sha=sys.argv[2];label=sys.argv[3]
assert hashlib.sha256(path.read_bytes()).hexdigest()==expected_sha,'Unannounced or changed freeze'
ns={};code=(Q/'scripts/tube06_rest_qualify.py').read_text();exec(code[:code.index('\nsource_weld =')],ns);audit=ns['audit'];source=ns['b'];shape=ns['shape'];g=ns['g'];pr=ns['primitives']
def read(p):
 with np.load(p) as z:return {k:z[k] for k in z.files}
d=read(path);cut=read(HERE/'sleeve-cut-inventory.npz');expand=read(HERE/'expanded-torso-cut-inventory.npz')
checks={};inventory=[];clip_normals=[];retained_face_errors=[]
for i in range(5):
 n=len(source[f'p{i}']);old_uv=g.array(pr[i]['attributes']['TEXCOORD_0']).astype(float);uv=d[f'uv{i}'];p=d[f'p{i}'];tri=d[f'tr{i}'];W=d[f'W{i}'];norm=d[f'n{i}'];parent=d[f'sourceVertexParents{i}'];bary=d[f'sourceVertexBarycentric{i}']
 for key,base in [('p',source[f'p{i}']),('W',source[f'W{i}']),('n',shape[f'n{i}']),('uv',old_uv)]:checks[f'p{i}_source_{key}_prefix_exact']=np.array_equal(d[key+str(i)][:n],base)
 checks[f'p{i}_all_attributes_finite']=all(np.isfinite(d[key+str(i)]).all() for key in ['p','W','n','uv'])
 checks[f'p{i}_weights_nonnegative_and_unit']=bool((W>=0).all() and abs(W.sum(1)-1).max()<1e-12)
 checks[f'p{i}_original_vertex_ancestry_exact']=np.array_equal(d[f'oldVertex{i}'][:n],np.arange(n))
 if i not in [0,2]:checks[f'p{i}_protected_all_geometry_attrs_exact']=all(np.array_equal(d[key+str(i)],base) for key,base in [('p',source[f'p{i}']),('W',source[f'W{i}']),('n',shape[f'n{i}']),('uv',old_uv),('tr',source[f'tr{i}'])])
 actual_area=np.linalg.norm(np.cross(p[tri[:,1]]-p[tri[:,0]],p[tri[:,2]]-p[tri[:,0]]),axis=1);checks[f'p{i}_declared_area_actual']=np.allclose(actual_area,d[f'restDoubleArea{i}'],rtol=1e-10,atol=1e-14)
 for fi,ancestry in enumerate(d[f'sourceFaceAncestry{i}']):
  if ancestry<0:continue
  original_vertices=set(source[f'tr{i}'][ancestry].tolist())
  for v in tri[fi]:
   lineage=parent[v][parent[v]>=0]
   if not len(lineage) or not set(lineage.tolist()).issubset(original_vertices):retained_face_errors.append([i,fi,int(ancestry),int(v),lineage.tolist()])
  # Chart-only clones must not alter retained source-clipped texture corners.
  if str(d[f'faceKind{i}'][fi]).startswith('retained'):
   for v in tri[fi]:
    lineage=parent[v];valid=lineage>=0;expected=(old_uv[lineage[valid]]*bary[v,valid,None]).sum(0)
    if abs(expected-uv[v]).max()>1e-12:retained_face_errors.append([i,fi,int(ancestry),int(v),'retained-source-UV-change'])
 ids=np.flatnonzero((parent>=0).all(1))
 if len(ids):
  ep=(source[f'p{i}'][parent[ids]]*bary[ids,:,None]).sum(1);ew=(source[f'W{i}'][parent[ids]]*bary[ids,:,None]).sum(1);en=(shape[f'n{i}'][parent[ids]]*bary[ids,:,None]).sum(1);en/=np.maximum(np.linalg.norm(en,axis=1)[:,None],1e-30);an=norm[ids]/np.maximum(np.linalg.norm(norm[ids],axis=1)[:,None],1e-30);angle=np.degrees(np.arccos(np.clip((en*an).sum(1),-1,1)))
  checks[f'p{i}_source_edge_bary_P_W_exact']=bool(abs(ep-p[ids]).max()<1e-12 and abs(ew-W[ids]).max()<1e-12)
  for v,e,ang in zip(ids,en,angle):clip_normals.append({'primitive':i,'vertex':int(v),'source_parents':parent[v].tolist(),'expected_normal':e.tolist(),'actual_normal':norm[v].tolist(),'angle_degrees':float(ang)})
 inventory.append({'primitive':i,'vertices':len(p),'triangles':len(tri),'exact_nonzero_max_influences':int((W!=0).sum(1).max()),'more_than4_at1e_minus8':int(((W>1e-8).sum(1)>4).sum())})
checks['retained_face_source_parent_and_UV_ancestry_valid']=not retained_face_errors
pos=[d[f'p{i}'] for i in range(5)];tri=[d[f'tr{i}'] for i in range(5)];weld=[d[f'physicalWeld{i}'] for i in range(5)];ancestry=[d[f'sourceFaceAncestry{i}'] for i in range(5)];kind=[d[f'faceKind{i}'] for i in range(5)]
dense,boundary=audit(label,pos,tri,weld,ancestry,kind);f32,boundary32=audit(label+'-f32',[p.astype('f4').astype(float) for p in pos],tri,weld,ancestry,kind)
# Original boundary physical identities come from exact source aliases; do not accept equal count alone.
alias=ns['source_alias'];off=ns['source_offsets'];srcw=np.r_[alias[off[0]:off[1]],alias[off[2]:off[3]]];srcp=np.r_[source['p0'],source['p2']];srct=np.r_[source['tr0'],source['tr2']+len(source['p0'])];wt=srcw[srct];edges,n=np.unique(np.sort(np.r_[wt[:,[0,1]],wt[:,[1,2]],wt[:,[2,0]]],axis=1),axis=0,return_counts=True);coords={int(k):p for k,p in zip(srcw,srcp)};srcboundary={tuple(np.array(sorted([coords[int(a)].tolist(),coords[int(b)].tolist()])).ravel()) for a,b in edges[n==1]}
checks['source_boundary_coordinate_set_exact']=boundary==srcboundary
for label2,r in [('dense',dense),('float32',f32)]:checks[label2+'_literal_rest_clear']=r['strict_zero_shared_weld_crossings']==r['strict_one_shared_weld_crossings']==0;checks[label2+'_physical_topology_manifold_winding']=r['nonmanifold_edges']==r['incoherent_two_face_winding_edges']==r['degenerate_weld_triangles']==0
aliases=np.r_[weld[0],weld[2]];W=np.r_[d['W0'],d['W2']];_,group=np.unique(aliases,return_inverse=True);lo=np.full((group.max()+1,19),np.inf);hi=np.full_like(lo,-np.inf);np.minimum.at(lo,group,W);np.maximum.at(hi,group,W);Wspread=float(abs(hi-lo).max());checks['physical_alias_weights_match']=Wspread<1e-12;checks['physical_alias_positions_match']=dense['same_weld_position_bbox_max_m']<1e-12
cap_sew=[]
for side in ['L','R']:
 rows=d['tubeRows'+side];root=d['bodyOpeningVertices'+side];cap_sew.append({'side':side,'root_same_physical_ids':bool(np.array_equal(d['physicalWeld0'][root],d['physicalWeld0'][rows[0]])),'root_P_exact':bool(np.array_equal(d['p0'][root],d['p0'][rows[0]])),'end_source_ring_max_m':float(np.linalg.norm(d['p0'][rows[-1]]-cut['ringRestPositions'+side][d['tubeEndSourceNodes'+side]],axis=1).max())})
checks['actual_root_and_source_end_sewn']=all(x['root_same_physical_ids'] and x['root_P_exact'] and x['end_source_ring_max_m']<1e-12 for x in cap_sew)
allowed=expand['deletedSourceFacesL']|expand['deletedSourceFacesR'];clip=set(np.r_[cut['clippedTubeFaceIDsL'],cut['clippedTubeFaceIDsR']]);cancel=set(map(tuple,d['oppositeDuplicateCancelledSourceFaces'].tolist()));unsupported=[]
for i in [0,2]:
 missing=set(range(len(source[f'tr{i}'])))-set(d[f'sourceFaceAncestry{i}'][d[f'sourceFaceAncestry{i}']>=0]);offset=0 if i==0 else len(source['tr0'])
 for f in missing:
  if not allowed[offset+f] and offset+f not in clip and (i,f) not in cancel:unsupported.append([i,f])
checks['source_face_removals_only_declared_margin_clip_cancellations']=not unsupported
# Normal ancestry is a separate gate. Prefix preservation does not prove clipped-source normals.
normal_max=max((x['angle_degrees'] for x in clip_normals),default=0);normal_preserved=normal_max<1e-4
report={'status':'BOUNDED_REST_SOURCE_GEOMETRY_PASS' if all(checks.values()) else 'FAIL','candidate_path':str(path),'candidate_sha256':expected_sha,'checks':{k:bool(v) for k,v in checks.items()},'candidate':dense,'float32_POSITION_candidate':f32,'source_attribute_inventory':inventory,'retained_face_ancestry_errors':retained_face_errors,'unsupported_source_face_removals':unsupported,'physical_alias_W_spread_max':Wspread,'root_and_end_contracts':cap_sew,'source_clipped_NORMAL_ancestry_pass':normal_preserved,'source_clipped_NORMAL_max_angle_degrees':normal_max,'source_clipped_NORMAL_witnesses':clip_normals,'limits':['Strict transverse intersections only; coplanar/tangent contact/thickness unclassified.','Separate normal ancestry and UV/appearance reports are required; geometry/sourceprefix PASS is not material/shading PASS.','Harmonic geometry gradients are not skin weights. Dense5-influence new caps require explicit runtime choice, never truncation.','No broad poses,actual304,continuous export,volume/support,saddle or art acceptance.']}
(Q/f'uv-lower01/{label}-independent-rest.json').write_text(json.dumps(report,indent=2));print(report['status'],'failed',[k for k,v in checks.items() if not v],'clipped-normal-max',normal_max,flush=True)
