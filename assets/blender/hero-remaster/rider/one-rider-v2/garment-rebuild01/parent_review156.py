"""Independent parent checks on frozen local repair and finite source evidence."""
from pathlib import Path
import hashlib, json, struct
import numpy as np
REPO = Path('/Users/raynos/projects/games/rockhop')
BASE = REPO/'docs/evidence/hero-remaster/one-rider-v2/garment-rebuild01'
PRIVATE = Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/garment-rebuild01')
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
a = np.load(PRIVATE/'cuff-ankle-transition155/transition155.npz')
b = np.load(PRIVATE/'wrist-local156/wrist-local156.npz')
assert all(a[k].dtype == b[k].dtype and a[k].shape == b[k].shape and a[k].tobytes() == b[k].tobytes() for k in a.files)
Q = b['native_retained_quads']
old = np.concatenate([Q[:,[0,1,2]], Q[:,[0,2,3]]])
new = b['native_triangles']
changed = np.flatnonzero(np.any(old != new, axis=1))
assert len(changed) == 4
P,W = b['native_positions'], b['native_weights19']
M = np.fromfile(PRIVATE/'full-motion155/body0-joint-matrices.f64', dtype='<f8').reshape(480,19,4,4).transpose(0,1,3,2)
X = np.einsum('vj,jab,vb->va', W, M[39,:,:3,:], np.c_[P,np.ones(len(P))])
ratios = []
for quadID in [1248,1820]:
    j = int(np.flatnonzero(b['native_retained_quad_ids'] == quadID)[0])
    tri = new[[j,j+len(Q)]]
    rest, posed = P[tri], X[tri]
    area = np.linalg.norm(np.cross(posed[:,1]-posed[:,0],posed[:,2]-posed[:,0]),axis=1)
    base = np.linalg.norm(np.cross(rest[:,1]-rest[:,0],rest[:,2]-rest[:,0]),axis=1)
    ratios.append({'quad':quadID,'areaRatios':(area/base).tolist()})
assert min(ratios[0]['areaRatios']) < .25 < min(ratios[1]['areaRatios'])
# Verify embedded source image payloads, not only matching texture table IDs.
def image_hashes(path):
    raw = path.read_bytes(); n = struct.unpack_from('<I',raw,12)[0]
    j = json.loads(raw[20:20+n]); binary = raw[28+n:]
    result = []
    for im in j.get('images',[]):
        assert 'bufferView' in im, 'External image paths require separate verification'
        v = j['bufferViews'][im['bufferView']]; start = v.get('byteOffset',0)
        result.append(hashlib.sha256(binary[start:start+v['byteLength']]).hexdigest())
    return result
TASK = Path('/Users/raynos/Documents/Codex/2026-10-01/task-3')
sourceImages = image_hashes(TASK/'deliverables/C19.glb')
imageChecks = {}
for name in ['rider-foundation-v5.glb','rider-compression-v6.glb']:
    imageChecks[name] = image_hashes(TASK/'hoodie-repair02/deliverables'/name) == sourceImages
assert all(imageChecks.values())
yoke = json.loads((BASE/'upper-yoke156/rest-audit.json').read_text())
assert yoke['strictIntersectionAudit']['strictNoncoplanarCrossings'] == 568
ship = json.loads((BASE/'ship156/ship-gate156.json').read_text())
assert not ship['errors'] and len(ship['runs']) == 2
assert len({r['finishTimeFloat64LE'] for r in ship['runs']}) == 1
assert all(r['crashRestart']['crashed'] and r['crashRestart']['restartMs'] <= 4 for r in ship['runs'])
report = {'kind':'Parent verdict156: retain fresh rig, reject incomplete garment repairs',
    'original155ArrayFieldsByteExact':len(a.files), 'changedTriangleRows':changed.tolist(),
    'independentFrame39AreaRatios':ratios,'collapseThresholdUnchanged':.25,
    'wristDecision':'Regional right wrist clears; left remains below threshold. No whole character acceptance.',
    'yokeDecision':'Reject at rest:568 strict crossings/137 reversals. Construct new routed panels rather than deform existing crewneck topology.',
    'v5v6EmbeddedImagesByteExactToC19':imageChecks,'sourceImageHashes':sourceImages,
    'authoredFilmReview':{'all49UniqueFramesReviewedInOrder':True,'frameInventoryTotal':85,
        'views':['front','side','rear'],'observation':'V6 sleeve/chest profile fuller and cleaner; hip/crotch/seat shape still wrong through seated transition.',
        'inspectionMethod':'Ordered frame montages; no continuous human playback or appearance score.'},
    'v7ExternalSnapshot':'Other chat reports upper cloth/cuff/collar crossing checks clear on111 snapshots; hips and saddle still fail. V7 is not audited or adopted by this checkpoint.',
    'ship156':'Retained34 cold boot, byte-identical finish, crash103ticks/restart4ms low/3ms high, errors0.',
    'rigDirection':'C19 with explicit19bone/14child-axis/source sockets adapter34 retained; physical posing/leaning unchanged.',
    'next':'Audit frozen external v7 and static v5 source preservation, then test reusable shape/weights in actual physics. Authored49frame morphs require explicit pose driver and heldouts. Native alternative uses new anatomically routed panels.',
    'limits':['No complete garment export, textured bake, new in-game candidate or player promotion.',
        'No new face/full-body mockup score, Garage, moving visible contacts, phone or LOD pass.',
        'No fresh sitting clip from the old11 rig can substitute for a C19 evaluation.']}
(BASE/'parent-review156.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'fields':len(a.files),'changedTriangles':changed.tolist(),'frame39':ratios,'imagesExact':imageChecks,'ship':'pass'}))
