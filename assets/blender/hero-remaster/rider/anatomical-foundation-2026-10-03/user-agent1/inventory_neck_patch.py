"""Freeze exact admitted neck boundary roles before any construction.

Reads original arrays only. No Blender, geometry, attachment or capture write.
The virtual position quotient is a diagnostic registry, not physical welding.
"""
import hashlib
import json
from pathlib import Path

import numpy as np

root = Path(__file__).resolve().parents[6]
qa = root / 'docs/evidence/hero-remaster/user-agent3-qa-2026-10-03'
out = root / 'docs/evidence/hero-remaster/anatomical-foundation-2026-10-03/user-agent1/neck-interface96'
out.mkdir(parents=True, exist_ok=True)
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
proposal_path = qa / 'body59/proposal.json'
assert sha(proposal_path) == '5f563c032791a9426c0447a2b8c818b140fd62e56a621fd4b81efd461cfdefa6'
proposal = json.loads(proposal_path.read_text())
for rel, pin in proposal['evidencePins'].items():
    assert sha(qa / rel) == pin, rel
scope = proposal['preciseInitialAuthoringMargin']
n = np.load(qa / 'body52/native-fields.npz')
assessment = json.loads((qa / 'body59/assessment.json').read_text())
witness = np.load(qa / 'body59/neck-witnesses.npz')
pins = {str(p.relative_to(root)): sha(p) for p in [proposal_path,
    qa / 'body52/native-fields.npz', qa / 'body59/assessment.json',
    qa / 'body59/neck-witnesses.npz']}

def ordered_boundary(triangles):
    directed = np.concatenate([triangles[:, [0, 1]], triangles[:, [1, 2]], triangles[:, [2, 0]]])
    undirected = np.sort(directed, axis=1)
    _, inverse, counts = np.unique(undirected, axis=0, return_inverse=True, return_counts=True)
    boundary = directed[counts[inverse] == 1]
    following = {int(a): int(b) for a, b in boundary}
    assert len(following) == len(boundary), 'Branching boundary'
    loops = []
    seen = set()
    for seed in sorted(following):
        if seed in seen:
            continue
        loop = []
        v = seed
        while v not in seen:
            seen.add(v)
            loop.append(v)
            v = following[v]
        assert v == seed, 'Open boundary'
        loops.append(np.array(loop, dtype=np.int32))
    return loops

hp, ht, hw = [n['protectedHead' + k] for k in ['XYZ', 'Triangles', 'Weights']]
unique, representative, alias = np.unique(hp, axis=0, return_index=True, return_inverse=True)
virtual_triangles = alias[ht]
loops = ordered_boundary(virtual_triangles)
lower = [loop for loop in loops if unique[loop, 2].max() < 1.55]
assert len(lower) == 2
admitted = np.array(scope['headInitialBoundaryLedNativeVertexIDs'], dtype=np.int32)
body_admitted = np.array(scope['bodyExistingRenderedNativeVertices'], dtype=np.int32)
body_source_ids = n['renderedBodySourceIDs'].astype(np.int32)
assert np.array_equal(body_source_ids[body_admitted], scope['bodyExistingFullSourceVertexIDs'])
bp, bt = n['renderedBodyXYZ'], n['renderedBodyTriangles']
body_loops = ordered_boundary(bt)
assert len(body_loops) == 1 and len(body_loops[0]) == 56
assert set(body_loops[0]) <= set(body_admitted)

rows = []
arrays = {'headPositionAlias': alias, 'headAliasRepresentative': representative,
    'bodyCutOrderedNativeIDs': body_loops[0], 'bodyCutOrderedFullSourceIDs': body_source_ids[body_loops[0]],
    'headEditableNativeIDs': admitted, 'bodyEditableNativeIDs': body_admitted}
for loop in lower:
    face_ids = np.flatnonzero(np.isin(virtual_triangles, loop).any(axis=1))
    pts = hp[ht[face_ids]]
    cross = np.cross(pts[:, 1] - pts[:, 0], pts[:, 2] - pts[:, 0])
    radial = pts.mean(axis=1) - unique[loop].mean(axis=0)
    radial[:, 2] = 0
    dot = np.einsum('ij,ij->i', cross, radial)
    assert np.all(dot > 0) or np.all(dot < 0)
    role = 'outer' if np.all(dot > 0) else 'inner'
    native_ids = np.flatnonzero(np.isin(alias, loop))
    assert set(native_ids) <= set(admitted)
    assert set(face_ids) <= set(scope['headInitialBoundaryLedNativeTriangleIDs'])
    arrays[role + 'HeadOrderedVirtualIDs'] = loop
    arrays[role + 'HeadOrderedNativeRepresentatives'] = representative[loop]
    arrays[role + 'HeadBoundaryNativeAliases'] = native_ids
    arrays[role + 'HeadBoundaryIncidentTriangleIDs'] = face_ids
    alias_weight_max = max(float(np.abs(hw[np.flatnonzero(alias == v)] - hw[representative[v]]).max()) for v in loop)
    rows.append({'role': role, 'orderedVirtualVertices': len(loop), 'rawNativeAliases': len(native_ids),
        'incidentTriangles': len(face_ids), 'radialDotSign': 'positive' if role == 'outer' else 'negative',
        'allAdjacentFacesAgree': True, 'areaWeightedRadialDotM3': float(dot.sum()),
        'boundaryAreaVectorM2': (.5 * np.cross(unique[loop], np.roll(unique[loop], -1, axis=0)).sum(axis=0)).tolist(),
        'boundsNativeM': [unique[loop].min(axis=0).tolist(), unique[loop].max(axis=0).tolist()],
        'maximumExistingAliasWeightDifference': alias_weight_max,
        'originalDonorVertexIDsSHA256': hashlib.sha256(witness['headOriginalDonorVertexIDs'][native_ids].tobytes()).hexdigest()})
np.savez_compressed(out / 'ordered-boundaries.npz', **arrays)
head_faces = ht[scope['headInitialBoundaryLedNativeTriangleIDs']]
protected = np.flatnonzero(hp[ht].max(axis=1)[:, 2] > 1.60)
report = {'status': 'UNACCEPTED_PRECONSTRUCTION_BOUNDARY_INVENTORY', 'proposalSHA256': sha(proposal_path),
    'pins': pins, 'recipeSHA256': sha(__file__), 'orderedRegistrySHA256': sha(out / 'ordered-boundaries.npz'),
    'headBoundaryRoles': rows, 'bodyCutVertices': 56, 'bodyCutAreaVectorM2':
        (.5 * np.cross(bp[body_loops[0]], np.roll(bp[body_loops[0]], -1, axis=0)).sum(axis=0)).tolist(),
    'admittedCounts': scope['counts'], 'headIncidentFacesWithOutsideCorner': int((~np.isin(head_faces, admitted).all(axis=1)).sum()),
    'editableHeadVerticesTouchingProtectedAbove1_60Triangles': int(len(set(admitted) & set(np.unique(ht[protected])))),
    'constructionIntent': ['One outer body/head seam only, using ordered boundary correspondence and a declared split registry.',
        'Inner loop remains a distinct inward surface; determine a bounded closure before freezing any derivative.',
        'Record split/new ancestry separately; preserve outside corners and face attributes exactly.',
        'No garment, normal camouflage or global transfer; native four and full control remain separate.'],
    'limits': ['Exact-position quotient is diagnostic: no physical source welding or head watertightness inferred.',
        'No candidate geometry/weight/bind changes, new capture or repair sufficiency claim.',
        '663 one-corner boundary faces stay included in subsequent local checks. All M0-M5 and art gates remain open.']}
assert report['editableHeadVerticesTouchingProtectedAbove1_60Triangles'] == 0
(out / 'inventory.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({k: report[k] for k in ['status', 'headBoundaryRoles', 'bodyCutVertices', 'headIncidentFacesWithOutsideCorner']}, indent=2))
