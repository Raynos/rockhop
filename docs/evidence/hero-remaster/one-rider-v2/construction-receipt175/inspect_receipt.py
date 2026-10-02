#!/usr/bin/env python3
"""Read-only frozen-artifact inventory; writes only this specialist receipt."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import struct

ROOT = Path('/Users/raynos/projects/games/rockhop')
OUT = ROOT / 'docs/evidence/hero-remaster/one-rider-v2/construction-receipt175'
OWNER = ROOT / 'assets/blender/hero-remaster/rider/one-rider-v2/foundation-repair-task3'
SHAPE = OWNER / 'hoodie-repair02/shape-lane/volume-lane/sleeve-tube03'
QA = OWNER / 'hoodie-repair02/qa-lane/uv-lower01/tube10-export'
LOCAL = Path('/Users/raynos/Documents/Codex/2026-10-01/task-3/deliverables/tube10-four-diagnostic.glb')
MAPPED = Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/candidate-handoff170/task3-tube10-four-diagnostic01/rider.glb')
TUBE10 = 'b077a27ceba5040e4c0388a3501b3815984ee21a13da58640d2d03b319fb4dee'

def freeze(path):
    data = path.read_bytes()
    return {'path': str(path), 'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)}

def read(path):
    info = freeze(path)
    return info, json.loads(path.read_bytes())

def glb(path):
    data = path.read_bytes()
    magic, version, length = struct.unpack_from('<III', data)
    assert magic == 0x46546c67 and version == 2 and length == len(data)
    jlen, jtype = struct.unpack_from('<II', data, 12)
    assert jtype == 0x4e4f534a
    j = json.loads(data[20:20+jlen])
    blen, btype = struct.unpack_from('<II', data, 20+jlen)
    assert btype == 0x004e4942
    b = data[28+jlen:28+jlen+blen]
    attrs = [p for m in j['meshes'] for p in m['primitives']]
    return {'file': freeze(path), 'BIN_sha256': hashlib.sha256(b).hexdigest(),
            'skin_joint_counts': [len(s['joints']) for s in j['skins']],
            'vertex_counts': [j['accessors'][p['attributes']['POSITION']]['count'] for p in attrs],
            'morph_counts': [len(p.get('targets', [])) for p in attrs],
            'animation_count': len(j.get('animations', [])),
            'conditioned_nodes': [{'name': n.get('name'), 'value': n['extras']['rockhopRiderSkinConditioned']} for n in j['nodes'] if 'rockhopRiderSkinConditioned' in n.get('extras', {})]}, j, b

started = datetime.now(timezone.utc).isoformat()
rows = []
for n in range(10, 18):
    candidates = sorted(SHAPE.glob(f'source-sleeve-tube-rest{n:02d}-*.npz'))
    assert len(candidates) == 1, (n, candidates)
    p = candidates[0]
    provenance, j = read(p.with_name(p.stem+'-provenance.json'))
    f = freeze(p)
    assert f['sha256'] == j['candidateSHA256']
    gp = p.with_name(p.stem+'.rest-gate.json')
    row = {'number': n, 'source': f, 'provenance': provenance,
           'status': j['status'], 'declared_parent_sha256': j.get('parentSHA256'),
           'method': j.get('method'), 'gate_present': gp.exists()}
    if gp.exists():
        gf, g = read(gp)
        assert g['candidateSHA256'] == f['sha256']
        row.update({'gate': gf, 'stored_gate': {k: v for k, v in g.items() if k != 'witnessCombinedFacePairs'}})
    rows.append(row)
local, lj, lb = glb(LOCAL)
mapped, mj, mb = glb(MAPPED)
assert mapped['file']['sha256'] == TUBE10
assert local['file']['sha256'] == 'b6fbfa9537af7950a492fdc7720c3869e8f6f9341d27b0be7576ac9d89f39e44'
assert lb == mb
assert mapped['skin_joint_counts'] == [19] and sum(mapped['vertex_counts']) == 95184
assert mapped['morph_counts'] == [2, 2, 2, 0, 0]
assert mapped['animation_count'] == 0
assert any(n['value'] == 1 for n in mapped['conditioned_nodes'])
reports = [freeze(QA/n) for n in ['HANDOFF.txt','raw-contract.json','stock-three-conditioning.json','manifest.json']]
carrier_path = OWNER / 'hoodie-repair03/tube03-four-bind/four-cap-carrier10-rmf.npz'
carrier = freeze(carrier_path)
assert carrier['sha256'] == '23b36939d1f2de197638f0df6e546e35e5c900341609ee5a96e882a14a1a5f0e'
other = [freeze(SHAPE/'CONSTRUCTION-STATUS10.json'), freeze(OWNER/'hoodie-repair02/qa-lane/uv-lower01/sleeve-tube10-independent-rest.json'), freeze(ROOT/'docs/evidence/hero-remaster/one-rider-v2/foundation-repair-task3/current-construction03-checkpoint.txt')]
export_inventory = []
for root in [OWNER, Path('/Users/raynos/Documents/Codex/2026-10-01/task-3')]:
    for p in sorted(root.rglob('*.glb')):
        export_inventory.append({'path': str(p), 'bytes': p.stat().st_size, 'mtime_utc': datetime.fromtimestamp(p.stat().st_mtime, timezone.utc).isoformat()})
# Verify the files read have remained frozen; live owner work is not mutated.
all_f = [x['source'] for x in rows] + [x['provenance'] for x in rows] + [x['gate'] for x in rows if 'gate' in x] + reports + other + [carrier, local['file'], mapped['file']]
assert all(freeze(Path(x['path'])) == x for x in all_f)
report = {'status': 'NO_NEW_EXPORT_QUALIFIED_FOR_MATCHED_MOTION_AT_THIS_SNAPSHOT',
          'started_utc': started, 'finished_utc': datetime.now(timezone.utc).isoformat(),
          'rows': rows, 'latest_observed_npz': rows[-1],
          'tube10_lineage': {'source': rows[0]['source'], 'four_cap_carrier': carrier, 'local': local, 'mapped': mapped, 'local_mapped_BIN_identical': True},
          'owner_reports': reports+other, 'GLB_inventory': export_inventory,
          'limits': ['Stored rest counts are owner findings verified against file hashes, not newly recomputed collision results.', 'Tube10 has zero strict rest crossings but rejected standing underarm silhouette; rest numeric pass is not art acceptance.', 'Variants11-16 have failed stored rest gates;17 is pending unless a new gate appears after this snapshot.', 'No newer GLB export observed; newer five-influence NPZs cannot enter the stock-four gate without explicit verified carrier or driver.', 'Tube10 stock-four GLB omits nonlinear responding material driver; CPU finite parity does not establish its collision, shading or performance.', 'No GPU, Blender, playback, garment repairs, public asset modifications or production acceptance performed.']}
OUT.mkdir(parents=True, exist_ok=True)
(OUT/'receipt.json').write_text(json.dumps(report, indent=2)+'\n')
print(json.dumps({'status': report['status'], 'finished_utc': report['finished_utc'], 'latest': rows[-1]['source'], 'latest_gate_present': rows[-1]['gate_present'], 'mapped_sha256': mapped['file']['sha256'], 'owner_report_count': len(reports+other)}))
