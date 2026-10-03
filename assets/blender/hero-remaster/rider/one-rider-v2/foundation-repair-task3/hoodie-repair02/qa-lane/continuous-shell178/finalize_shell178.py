from pathlib import Path
import json,numpy as np,sys,hashlib,shutil
from scipy.spatial import cKDTree
R=Path('/Users/raynos/projects/games/rockhop/assets/blender/hero-remaster/rider/one-rider-v2/foundation-repair-task3');O=R/'hoodie-repair02/qa-lane/continuous-shell178';sys.path.insert(0,str(R/'scripts'));from glb import GLB
d=json.loads((O/'independent-export-rest.json').read_text());g=GLB(O/'shell01.glb');pr=g.j['meshes'][0]['primitives'][0];p=g.array(pr['attributes']['POSITION']).astype(float);tr=g.array(pr['indices']).reshape(-1,3).astype(int);uf=np.arange(len(p))
def find(x):
 while uf[x]!=x:uf[x]=uf[uf[x]];x=uf[x]
 return x
for x,y in cKDTree(p).query_pairs(2e-7,output_type='ndarray'):uf[find(y)]=find(x)
al=np.array([find(i)for i in range(len(p))]);zero=d['actual_export_exact_weld_topology']['zero_area_below_1e_minus12'];good=np.ones(len(tr),bool);good[zero]=False;t=al[tr[good]];dire=np.r_[t[:,[0,1]],t[:,[1,2]],t[:,[2,0]]];ed,iv,co=np.unique(np.sort(dire,1),axis=0,return_inverse=True,return_counts=True);signed=np.bincount(iv,weights=np.where(dire[:,0]<dire[:,1],1,-1));adj={}
for x,y in ed[co==1]:adj.setdefault(int(x),set()).add(int(y));adj.setdefault(int(y),set()).add(int(x))
remain=set(adj);cycles=[]
while remain:
 stack=[remain.pop()];vs=set(stack)
 while stack:
  for y in adj[stack.pop()]:
   if y in remain:remain.remove(y);vs.add(y);stack.append(y)
 cycles.append({'edges':sum(len(adj[i])for i in vs)//2,'degree2_simple_cycle':all(len(adj[i])==2 for i in vs),'height_range_m':[float(p[list(vs),1].min()),float(p[list(vs),1].max())]})
d['precision_diagnostic_2e_minus7_m']['virtual_only_drop9_export_zero_area_faces']={'removed_exported_faces':zero,'boundary_edges':int((co==1).sum()),'nonmanifold_edges':int((co>2).sum()),'winding_conflicts':int(((co==2)&(signed!=0)).sum()),'opening_cycles':cycles,'explicit_no_artifact_change':True}
for h in d['actual_export_literal_crossings']['witnesses']:
 span=h['overlap_segment_m'];h['projected_overlap_area_divided_by_intersection_span_m']=h['projected_lateral_height_overlap_area_m2']/span if span else None
for h in d['actual_export_exact_weld_topology']['wrong_winding_edge_witnesses']:h['touches_zero_area_face']=any(f in zero for f in h['incident_exported_faces'])
d['repair_targets']=['Original construction owner rejects collinear back-center tessellation ear before subdivision. Nine surviving zero-area faces must not rely on glTF export omission.','Use canonical shared parent-edge ID and integer subdivision k/n registry before float32 conversion. Avoid independent panel interpolation/round7 keys; never tolerance-weld unrelated garment sheets.','Regenerate normal/source panel ancestry after actual repair and audit actual exported topology, explicit opening loops and retained hood/cuff/hem attachment.','Assembly cuff mask clause adds zero triangles beyond height mask; replace label assumption with actual retained cuff/hood/hem source-loop references.','Once valid rest and standing images exist, original owner owns four-influence rig/19-bind and actual-container conditioner parity followed by continuous fixture/contact gates.']
(O/'independent-export-rest.json').write_text(json.dumps(d,indent=2)+'\n')
contract={'scope':'Reusable bounded static shell QA handoff, not an alternate fixture or shell builder','frozen_source_sha256':hashlib.sha256((O/'source-C19.glb').read_bytes()).hexdigest(),'protected_source_flat_primitives':[1,3,4],'retained_source_hood_flat_primitive':2,'coordinate_convention':'glTF Y-up; source mesh-node world matrices exact; authored Blender XYZ mapped X,Z,-Y','rest_required':['Explicit physical garment/weld IDs and source/new panel/face ancestry. Raw index seam splits separate from physical seams.','No zero-area, nonmanifold or incoherent winding edges on actual exported surface. Intentional boundaries named and ordered; neck/hem/cuffs physically explained.','Strict nonadjacent and one-shared-corner transverse triangle gates on actual float32 POSITION; coplanar/tangent/thickness limits explicit.','Normals finite/unit and seam shading separate from positional closure. New UV/material identity and retained donor panel references explicit.','Head/glove geometry, all attrs including normalized color flags, original image bytes and original two grip morphs preserved.'],'after_rest_and_images':['Exactly <=4 nonzero joint influences with no unreported truncation, normalized weights and authoritative 19-joint mapping/rest inverse binds.','Owning-container runtime conditioner bypass metadata must be checked in actual stock runtime; parent-verified conditioner174 fix is current, old damage historical.','Independent stock loader rest and world end-effector matched pose parity, referenced-weld position/weight gaps, original grip closure.','Original owner continuous fixture: literal cloth triangles, strain/collapse, head/collar and cuff/glove actual face contacts, hips/saddle/sole/grip support. Finite pose coverage explicitly bounded.'],'current_export_qualified_for_rigging':False,'current_static_failure_report':'independent-export-rest.json'}
(O/'future-shell-qa-contract.json').write_text(json.dumps(contract,indent=2)+'\n')
text='''Frozen draft178 static QA — REJECTED, no rigging or motion qualification.

Actual shell01 GLB SHA7dd903e0280bc5cb536c061f600ce25798e3be8352902dc3803f73d3ad1a8f2a.
Assembly SHA629930598ae5e8299ad4207c6a292f6fb35f04b0d5840a6289ef4dc94bed532f.
Original assets unchanged; all checks used owned copies.

Actual export: 1634 triangles vs1650 authored. Export omits16 duplicated collinear-ear children, retains9 zero-area faces. Unlike authored13 nonmanifold edges, actual GLB has0 >2-incidence edges but9 winding conflicts, each touching a surviving zero-area face.
Exact POSITION seams:252 boundary edges in26 components. Forty-five near-distinct vertex pairs differ59.6–119.2nm. Twelve strict stored crossings (8 no-shared,4 one-corner) are precision slivers; each extra one-corner pair has a second near-identical endpoint. The49.7mm intersection span is NOT penetration. Largest projected overlap area1.4901e-9m² (~30nm area/span). All12 disappear only in a read-only virtual coordinate-coalescing diagnostic, max119.2nm move. Removing9 zero-area exported faces virtually then gives85 edges/four degree2 openings and0 winding/nonmanifold. No repaired asset is produced or accepted.

Protected assembly: source BIN prefix, material/image/texture/sampler prefixes, source head/glove/hood descriptors and world attributes, source primitive0 attributes pass exact checks. Retained19553 primitive0 triangles match declared source IDs. The purported cuff mask clause adds0 beyond y<=.965; it is no independent anatomical cuff proof. Shell copy matches standalone geometry/normals exactly. Unskinned/no animations; shell has POSITION/NORMAL only and plain unbaked warm material.

Original construction owner repair targets: reject collinear center-back ear; canonical parent-edge/integerk/n split registry BEFORE quantization; regenerate normals and explicit loop/panel ancestry; verify actual donor hood/cuff/hem attachment and standing identity before rigging. No competing shell was built. Coplanar contact, thickness, standing images, poses/support and runtime acceptance remain unqualified.

Evidence: independent-export-rest.json, freeze-manifest.json, future-shell-qa-contract.json.
Reproduction scripts run only owned files with installed numerical Python; no original build/render recipe executed.
'''
(O/'HANDOFF.txt').write_text(text)
for name in ['qualification_shell178.py','refine_shell178.py','finalize_shell178.py']:shutil.copyfile(Path('/Users/raynos/Documents/Codex/2026-10-01/task-3')/name,O/name)
print(json.dumps({'report_sha256':hashlib.sha256((O/'independent-export-rest.json').read_bytes()).hexdigest(),'handoff_sha256':hashlib.sha256((O/'HANDOFF.txt').read_bytes()).hexdigest(),'virtual_final':d['precision_diagnostic_2e_minus7_m']['virtual_only_drop9_export_zero_area_faces']},indent=2))
