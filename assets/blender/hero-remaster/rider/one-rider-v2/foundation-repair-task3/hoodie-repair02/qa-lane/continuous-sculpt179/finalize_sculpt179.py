from pathlib import Path
import json,hashlib,shutil
R=Path('/Users/raynos/projects/games/rockhop/assets/blender/hero-remaster/rider/one-rider-v2/foundation-repair-task3');O=R/'hoodie-repair02/qa-lane/continuous-sculpt179';p=O/'independent-export-topology.json';d=json.loads(p.read_text());e=d['exact_POSITION_weld_topology']['bad_edge_witnesses']
for w in e:
 w['distinct_actual_export_face_ids']=sorted(set(w['actual_export_face_ids']));w['edge_incidence_counts_directed_occurrences_not_unique_faces']=True;w['zero_length_self_edge']=w['physical_vertices'][0]==w['physical_vertices'][1]
d['winding_flags_all_on_zero_length_self_edges']=all(w['zero_length_self_edge']for w in e if w['same_direction_two_face_winding']);d['unique_authored_face_ID_matches_actual_export_face_ID_for_every_face']=True
d['exact_collapsed_raw_vertex_pairs']=[{'raw_vertices':v,'cause':'distinct raw vertices share exactly one POSITION after cuff correspondence; all are authored original raw IDs','at_glTF_height_m':.9134999513626099}for v in [[963,18771],[10588,18804],[12217,18827],[1852,18721]]]
for variant in ['exact_POSITION_weld_topology','virtual_only_drop8_zero_area_faces']:
 for loop in d[variant]['boundary_loops']:
  lo,hi=loop['bounds_m'];loop['anatomical_label_from_position_only']='hem'if abs(lo[1]-.95)<1e-6 else 'neck'if lo[1]>1.45 else 'cuff_negativeZ'if hi[2]<0 else 'cuff_positiveZ';loop['donor_attachment_not_qualified']=True
d['same_bug_as178']='179 has four exact coincident raw cuff-vertex pairs, each collapsing adjacent triangles. No near-distinct coordinates within0.2µm. It repeats the broad failure to reject collapsed faces/shared physical ownership, but not178 independent-panel119nm seam interpolation or center-back collinear tessellation-ear mechanism.'
d['conclusion']='REJECTED actual unrigged rest. All8nonmanifold occurrence-count edges,4zero-length self-edge winding flags and6boundarycomponents are explained by8exact collapsed cuff triangles. VirtualONLY dropping8 faces yields0edge errors and four degree2 cycles(hem104,neck170,cuffs63/63). No actual correction/export performed; four remaining intended openings still require garment donor sewing and standing/rest acceptance.'
d['repair_targets']=['Original construction owner preserves source cuff ordered-edge provenance when mapping shell boundary samples; prevent distinct cut samples collapsing to identical target rows without consistent triangle remeshing.','Reject zero-area/identical-physical-vertex triangles and audit physical, not raw UV/normal index, topology after final cuff mapping and actual export.','Regenerate explicit ordered cuff/neck/hem loops and sewn-donor references after real repair; hem remains an open detached construction boundary until sewing is demonstrated.','Rest/standing identity must pass before any rigging; no actual4, skinning, support, motion or runtime acceptance is asserted.']
p.write_text(json.dumps(d,indent=2)+'\n')
(O/'HANDOFF.txt').write_text('''Sculpt179 bounded actual-export QA — REJECTED before rigging.

Frozen shell SHA92cafa51ec1d4127741c173958e1eb7136f341db9fa1e7d147fc76ec02f859c3.
Owned copies only; original source/build files untouched; no render/rig/build or broad selfcollision rerun.

19000 actual exported vertices exactly match quantized authored positions under Blender(X,Z,-Y);37604 actual/authored triangle multiset and per-face ancestry match. Exact-position topology:8nonmanifold occurrence-count edges,4zero-length self-edge direction flags,8collapsed triangles,394boundaryedges/6components. All failures sit at cuff height .913499951m. Raw coincident pairs963/18771,10588/18804,12217/18827,1852/18721 collapse adjacent faces1696,21494,37393,37394,37427,37560,37565,37582. Edge incident lists include repeated edge occurrences within collapsed faces; unique face lists are provided separately.

READ-ONLY virtual removal of these8zero-area faces alone yields0nonmanifold/0winding/0collapsed triangles,400boundaryedges/four simple degree2 loops:hem104,neck170,cuffs63each. No distinct near-coordinate pairs<=.2micrometers; coalescence adds nothing. This differs from draft178 precision seam mismatch/collinear back-ear cause. No repaired asset produced or accepted.

Next original-builder targets: prevent cuff angular/correspondence mapping from collapsing distinct cut samples without consistent triangle remeshing; reject collapsed physical triangles; retain explicit ordered source-edge ancestry and qualify real donor cuff/neck/hem sewing. Hem remains open/unattached; normals/UV numerical finite checks are not standing appearance approval. No support, skinning, motion or runtime certificate.

Evidence: independent-export-topology.json (all8edge+4self-edge,8face and ordered-loop witnesses), freeze-manifest.json, qualification_sculpt179.py. Parent's strict selfcross0 audit remains separate and was not duplicated.
''')
shutil.copyfile(Path(__file__),O/'finalize_sculpt179.py')
print(json.dumps({'report':str(p),'report_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'handoff_sha256':hashlib.sha256((O/'HANDOFF.txt').read_bytes()).hexdigest(),'script_sha256':hashlib.sha256((O/'qualification_sculpt179.py').read_bytes()).hexdigest()},indent=2))
