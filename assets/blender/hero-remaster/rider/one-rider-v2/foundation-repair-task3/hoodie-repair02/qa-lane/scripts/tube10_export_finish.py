from pathlib import Path
import json,hashlib,numpy as np
ROOT=Path('/Users/raynos/projects/games/rockhop/assets/blender/hero-remaster/rider/one-rider-v2/foundation-repair-task3');Q=ROOT/'hoodie-repair02/qa-lane';OUT=Q/'uv-lower01/tube10-export'
code=(ROOT/'runtime/prepare_references.py').read_text();ns={};exec('import struct,json,copy,hashlib\nfrom pathlib import Path\nimport numpy as np\n'+code[code.index('def decode('):code.index("manifest={'tolerance_m'")],ns)
config=json.loads((OUT/'manifest.json').read_text());report=json.loads((OUT/'stock-three-conditioning.json').read_text());binds=[]
for v in config['variants']:
 doc,bin,sha=ns['decode'](v['path']);nodes,world=ns['pose'](doc,bin,{'channels':[],'samplers':[]},0);sk=doc['skins'][0];ib=ns['array'](doc,bin,sk['inverseBindMatrices']).reshape(-1,4,4).transpose(0,2,1);b=[]
 for j,ni in enumerate(sk['joints']):
  M=world[ni];b.append({'slot':j,'name':nodes[ni]['name'],'rest_inverse_bind_identity_error':float(abs(M@ib[j]-np.eye(4)).max()),'rest_basis_orthogonality_error':float(abs(M[:3,:3].T@M[:3,:3]-np.eye(3)).max()),'rest_basis_determinant':float(np.linalg.det(M[:3,:3]))})
 binds.append({'variant':v['id'],'sha256':sha,'nineteen_joints':len(b)==19,'bones':b,'max_inverse_bind_identity_error':max(x['rest_inverse_bind_identity_error'] for x in b)})
report['independent_rest_binds']=binds;report['raw_attribute_contract_path']='raw-contract.json';report['authored_skinning_compatibility']='PASS at rest/open+closed and archived304closed,all95184 vertices';report['current_unconditional_production_conditioning_compatible']=False;report['required_integration_cost']='Mapped canonical names activate conditioner. Integration owner must explicitly honor rockhopRiderSkinConditioned metadata or use a verified path that preserves authored weights and physical aliases; local fresh names are not a production adapter substitute.';report['driver_distinction']='This GLB includes standard4-influence LBS and original2grip morphs. It does not encode RespondingSleeve.deform harmonic cap/cubic rotation-minimizing material response; LBS parity does not qualify that different method.'
(OUT/'stock-three-conditioning.json').write_text(json.dumps(report,indent=2));print('inversebind errors',[b['max_inverse_bind_identity_error'] for b in binds])
text='''Independent tube10 stock-four export wiring review (2026-10-02 UTC)

Scope: diagnostic wiring only. Sleeve10 standing appearance remains REJECTED. No source/runtime edits, no GPU, broad pose suite or nonlinear responding-driver certification.

Frozen input four-cap-carrier10-rmf.npz SHA25623b36939d1f2de197638f0df6e546e35e5c900341609ee5a96e882a14a1a5f0e.
Local GLB SHA256b6fbfa9537af7950a492fdc7720c3869e8f6f9341d27b0be7576ac9d89f39e44.
Mapped private GLB SHA256MAPPED_SHA256.

Stock Three.js r186, installed Node24.18.1, actual GLTFLoader and SkinnedMesh.getVertexPosition. Independent raw sparse/normalized accessor+morph-before-LBS evaluator. All95184 vertices checked at rest-open, rest-closed, exact archived world matrices304 with closed grips. Both local and mapped exports have maximum discrepancy7.762615802172348e-8m. All19 source inverse binds retained, protected primitives1/3 original accessors unchanged, original BIN prefix exact, normalized flags retained. Expanded original grip targets match explicit source-edge parents. No dropped weight mass or5-influence input approximation. Explicitly restoring authored geometry reproduces bypass frame304 vertices exactly and confirms original geometry weights unchanged. Conditioner release alone is lifecycle cleanup, not a weight reset. These are finite CPU LBS/attribute/bind wiring results, not GPU shader/material parity.

Authored bypass:15764 actual referenced physical-alias groups; maximum gap0,weightspread0. Local fresh.* bone names make conditioner no-op.

CURRENT PRODUCTION CONDITIONER INCOMPATIBILITY: mapped canonical names activate actual src/render/hero/sleeveSkin.ts, imported read-only. Current gltfRider constructor calls it unconditionally; rockhopRiderSkinConditioned=1 is not consulted. It changes5990p0 and1138p2 rows, with maximum weight delta.6177513 and maximum frame304 point displacement74.9515mm. It opens151 referenced alias groups over1micrometre. Worst true sewn gap18.6514505mm between primitive0vertex24276 andprimitive2vertex2967,physicalWeld2132; weights differ.142107874. This occurs despite the authored export seam being exact. Integration owner must explicitly honor metadata or choose a verified path preserving authored weights; changing source runtime is outside this QA task.

The exported GLB is standard LBS plus the original grip morphs. RespondingSleeve harmonic cap and cubic/RMF tube response is not encoded. The LBS diagnostic proves neither that driver nor shape/motion/collision/volume/contacts/saddle support. No production/art acceptance.

Evidence: raw-contract.json,stock-three-conditioning.json,manifest.json,all-vertex expected/stockf64 arrays in this directory. Repro scripts: ../../scripts/tube10_export_prepare.py,tube10_stock_export.mjs,tube10_export_finish.py.
'''
# Insert the independently measured mapped export hash.
text=text.replace('MAPPED_SHA256',config['variants'][1]['sha256'])
(OUT/'HANDOFF.txt').write_text(text)
