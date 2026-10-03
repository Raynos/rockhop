"""Offline responding-surface snapshot with declared normal transport.

This is a diagnostic material driver, not a stock skinning export. Preserve
source shader normals; transport appended authored normals using the polar
fit of adjacent physical edges. Identity must reproduce the authored surface.
"""
from pathlib import Path
import sys, json, hashlib, time
import numpy as np
sys.dont_write_bytecode = True

R = Path('/Users/raynos/projects/games/rockhop/assets/blender/hero-remaster/rider/one-rider-v2/foundation-repair-task3')
HERE = R/'hoodie-repair02/shape-lane/volume-lane/sleeve-tube03'
sys.path.insert(0, str(HERE))
from responding_surface22 import RespondingSleeve

source, output = map(Path, sys.argv[1:3])
state = sys.argv[3]
assert state in ['rest', '304']
assert not output.exists(), 'Fresh diagnostic path required'
driver = RespondingSleeve(source)
f = driver.f
identity = np.broadcast_to(np.eye(4), (19, 4, 4)).copy()
neutral = driver.deform(identity)
neutral_error = max(float(abs(neutral[i] - f[f'p{i}']).max()) for i in range(5))
assert neutral_error < 1e-10, neutral_error
controls = R/'hoodie-repair03/inputs/source34-authoritative168-matrices.npz'
D = identity if state == 'rest' else np.load(controls)['D'][304]
start = time.perf_counter()
q = driver.deform(D, closed=state == '304')
elapsed = time.perf_counter() - start
# Hold the original recorded glove control, as in the matched baseline.
if state == '304':
    q[1] = np.load(R/'hoodie-repair03/poses/game304-v7-plain.npz')['p1']
n = []
for i in range(5):
    v = np.einsum('vj,jab,vb->va', f[f'W{i}'], D[:, :3, :3], f[f'n{i}'], optimize=False)
    v /= np.maximum(np.linalg.norm(v, axis=1, keepdims=True), 1e-20)
    n.append(v)
# Newly clipped source rows shade from the actual posed source edge too.
# Averaging rest P/W/N and then skinning is a different operation.
source_like = []
for i in [0, 2]:
    par = f[f'sourceVertexParents{i}']
    bary = f[f'sourceVertexBarycentric{i}']
    clipped = np.flatnonzero((par >= 0).all(axis=1))
    if len(clipped):
        value = (n[i][par[clipped]] * bary[clipped, :, None]).sum(axis=1)
        value /= np.maximum(np.linalg.norm(value, axis=1, keepdims=True), 1e-20)
        n[i][clipped] = value
    source_like.append((np.arange(len(par)) < len(driver.c.pos[i])) | (par >= 0).all(axis=1))

# Fit one rotation per physical cloth vertex, using the actual material edges.
P = np.r_[f['p0'], f['p2']]
Q = np.r_[q[0], q[2]]
aliases = np.r_[f['physicalWeld0'], f['physicalWeld2']]
_, representatives, groups = np.unique(aliases, return_index=True, return_inverse=True)
tri = np.r_[f['tr0'], f['tr2'] + len(f['p0'])]
edges = np.unique(np.sort(np.r_[groups[tri[:, [0, 1]]], groups[tri[:, [1, 2]]], groups[tri[:, [2, 0]]]], axis=1), axis=0)
edges = edges[edges[:, 0] != edges[:, 1]]
E = P[representatives[edges[:, 1]]] - P[representatives[edges[:, 0]]]
F = Q[representatives[edges[:, 1]]] - Q[representatives[edges[:, 0]]]
weight = 1 / np.maximum(np.linalg.norm(E, axis=1), .002)**2
cov = np.zeros((len(representatives), 3, 3))
dyad = np.einsum('ni,nj->nij', F, E) * weight[:, None, None]
np.add.at(cov, edges[:, 0], dyad)
np.add.at(cov, edges[:, 1], dyad)
u, _, vh = np.linalg.svd(cov)
fix = np.broadcast_to(np.eye(3), cov.shape).copy()
fix[:, 2, 2] = np.linalg.det(u @ vh)
rot = u @ fix @ vh
active = np.unique(tri)
prefix = np.r_[np.arange(len(f['p0'])) >= len(driver.c.pos[0]), np.arange(len(f['p2'])) >= len(driver.c.pos[2])]
new = active[prefix[active]]
source_like = np.r_[source_like[0], source_like[1]]
free_new = new[~source_like[new]]
authored = np.r_[f['n0'], f['n2']]
normals = np.r_[n[0], n[2]]
normals[free_new] = np.einsum('nij,nj->ni', rot[groups[free_new]], authored[free_new])

# Boundary shading uses the actual referenced source-side normal donor.
# Choose by REST normal, preserving intentionally different hard-edge normals.
donors = {}
for row in active[source_like[active]]:
    donors.setdefault(int(aliases[row]), []).append(row)
for row in free_new:
    if int(aliases[row]) in donors:
        choices = np.array(donors[int(aliases[row])])
        donor = choices[np.argmax(authored[choices] @ authored[row])]
        normals[row] = normals[donor]
n[0], n[2] = normals[:len(f['p0'])], normals[len(f['p0']):]
if state == 'rest':
    # The frozen source normals are the authoritative neutral contract.
    # Polar-fit roundoff is measured before restoring their exact representation.
    normal_error = max(float(abs(n[i] - f[f'n{i}']).max()) for i in range(5))
    n = [f[f'n{i}'].copy() for i in range(5)]
else:
    normal_error = None
assert all(np.isfinite(a).all() for a in q + n)
output.parent.mkdir(parents=True, exist_ok=True)
np.savez_compressed(output, **{f'p{i}': q[i] for i in range(5)}, **{f'n{i}': n[i] for i in range(5)})
report = {'status': 'UNACCEPTED exact material diagnostic', 'state': state,
          'sourceSHA256': hashlib.sha256(source.read_bytes()).hexdigest(),
          'driverRecipeSHA256': hashlib.sha256((HERE/'responding_surface22.py').read_bytes()).hexdigest(),
          'poseSHA256': hashlib.sha256(output.read_bytes()).hexdigest(),
          'controlSHA256': hashlib.sha256(controls.read_bytes()).hexdigest(),
          'neutralIdentityErrorM': neutral_error, 'neutralPolarNormalRoundoff': normal_error,
          'driverWarmSingleCallSeconds': elapsed,
          'normals': 'Source weighted shader normals fixed; clipped source normals use normalized posed-parent barycentric interpolation. Free appended authored normals transported by proper polar fit of neighboring physical material edges; exact source-side seam shading donor chosen by authored rest normal. Neutral frozen normals restored after roundoff measurement.',
          'limits': 'Offline diagnostic, no stock skinning/runtime/performance/collision/contact certificate. Polar shading cannot repair bad physical faces. Recorded glove shape held.'}
output.with_suffix('.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
