"""Read-only anatomy/cut-outline comparison before one construction proposal.

All derived points below are diagnostic ray/plane samples, never authored
candidate positions, a nearest-point projection or new source pose/capture.
"""
import hashlib
import json
from pathlib import Path
import numpy as np

root = Path(__file__).resolve().parents[6]
ev = root / 'docs/evidence/hero-remaster/anatomical-foundation-2026-10-03/user-agent1'
qa = root / 'docs/evidence/hero-remaster/user-agent3-qa-2026-10-03'
out = ev / 'neck-interface101'; out.mkdir(parents=True, exist_ok=True)
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
inputs = [qa / 'body59/proposal.json', qa / 'body52/native-fields.npz', qa / 'body59/assessment.json',
    qa / 'body59/neck-witnesses.npz', ev / 'neck-interface96/ordered-boundaries.npz',
    ev / 'neck-interface27/unused.json'] if False else [qa / 'body59/proposal.json', qa / 'body52/native-fields.npz',
        qa / 'body59/assessment.json', qa / 'body59/neck-witnesses.npz', ev / 'neck-interface96/ordered-boundaries.npz',
        ev / 'neck-interface100/restoration.json', ev / 'neck-interface99/played/movie.json']
assert sha(inputs[0]) == '5f563c032791a9426c0447a2b8c818b140fd62e56a621fd4b81efd461cfdefa6'
proposal = json.loads(inputs[0].read_text()); scope = proposal['preciseInitialAuthoringMargin']
pins = {str(p.relative_to(root)): sha(p) for p in inputs}
n = np.load(qa / 'body52/native-fields.npz')
r = np.load(ev / 'neck-interface96/ordered-boundaries.npz')
fields = np.load(root / 'assets/blender/hero-remaster/rider/anatomical-foundation-2026-10-03/user-agent1/neck-interface27/triangulated-neck-fields.npz')
canonical = n['originalFullXYZ'].astype(np.float64)
ct = n['originalFullTriangles']; cp = canonical[ct]
hp = n['protectedHeadXYZ']; ht = n['protectedHeadTriangles']
body_ids = np.array(scope['bodyExistingRenderedNativeVertices'])
head_ids = np.array(scope['headInitialBoundaryLedNativeVertexIDs'])
body_cut = r['bodyCutOrderedNativeIDs']; outer = r['outerHeadOrderedNativeRepresentatives']
inner = r['innerHeadOrderedNativeRepresentatives']
assert np.array_equal(n['renderedBodyXYZ'], n['originalFullXYZ'][n['renderedBodySourceIDs']])
assert np.array_equal(fields['headRestXYZ'][:len(hp)], hp)
# The frozen rejection conformed the body's existing cut onto donor outline.
changed_body = np.flatnonzero((fields['bodyRestXYZ'][:9037] != n['renderedBodyXYZ']).any(axis=1))
assert set(changed_body) == set(body_cut)


def section(z):
    faces = cp[(cp[:, :, 2].min(axis=1) < z) & (cp[:, :, 2].max(axis=1) >= z)]
    points = []
    for i, j in [(0, 1), (1, 2), (2, 0)]:
        valid = (faces[:, i, 2] < z) != (faces[:, j, 2] < z)
        a, b = faces[valid, i], faces[valid, j]
        points.append(a + (b - a) * ((z - a[:, 2]) / (b[:, 2] - a[:, 2]))[:, None])
    # Collect per-triangle pairs separately; never connect points by proximity.
    segments = []
    for face in faces:
        hits = []
        for i, j in [(0, 1), (1, 2), (2, 0)]:
            if (face[i, 2] < z) != (face[j, 2] < z):
                hits.append(face[i] + (face[j] - face[i]) * ((z - face[i, 2]) / (face[j, 2] - face[i, 2])))
        assert len(hits) == 2
        segments.append(hits)
    return np.array(segments), np.concatenate(points)

names = n['boneNames'].tolist(); neck = n['rigRest'][names.index('neck'), :3, 3]
head = n['rigRest'][names.index('head'), :3, 3]


def axis(z):
    return (neck + (head - neck) * ((z - neck[2]) / (head[2] - neck[2])))[:2]


def radial_diagnostic(vertex, p):
    segments, _ = section(float(p[2]))
    origin = axis(p[2]); direction = p[:2] - origin
    radius = float(np.linalg.norm(direction)); direction /= radius
    hits = []
    for a, b in segments[:, :, :2]:
        edge = b - a; matrix = np.column_stack([direction, -edge])
        if abs(np.linalg.det(matrix)) < 1e-14: continue
        distance, fraction = np.linalg.solve(matrix, a - origin)
        if distance > 0 and -1e-9 <= fraction <= 1 + 1e-9: hits.append(float(distance))
    hits = sorted(set(round(d, 10) for d in hits))
    assert len(hits) == 1, (vertex, p.tolist(), hits)
    anatomical = np.r_[origin + direction * hits[0], p[2]]
    return {'nativeVertex': int(vertex), 'sourcePositionM': p.tolist(), 'canonicalSectionRayPositionM': anatomical.tolist(),
        'axisXYM': origin.tolist(), 'sourceMinusCanonicalRadiusM': radius - hits[0],
        'sourceMinusCanonicalXYZM': (p - anatomical).tolist()}

head_incident = ht[scope['headInitialBoundaryLedNativeTriangleIDs']]
fixed = np.setdiff1d(np.unique(head_incident), head_ids)
alias = r['headPositionAlias']; virtual = np.unique(alias[head_ids]); editable = set(head_ids)
partial = [int(v) for v in virtual if not set(np.flatnonzero(alias == v)) <= editable]
pinned_inside = head_ids[np.isin(alias[head_ids], partial)]
outside_aliases = np.flatnonzero(np.isin(alias, partial) & ~np.isin(np.arange(len(alias)), head_ids))
protected_triangles = np.flatnonzero(hp[ht, 2].max(axis=1) > 1.60)
assert not set(head_ids) & set(np.unique(ht[protected_triangles]))
body_incident = n['renderedBodyTriangles'][scope['bodyExistingRenderedTriangleIDs']]
body_fixed = np.setdiff1d(np.unique(body_incident), body_ids)
outer_rows = [radial_diagnostic(v, hp[v].astype(float)) for v in outer]
fixed_rows = [radial_diagnostic(v, hp[v].astype(float)) for v in fixed]
sections = []
for z in [1.525, 1.53, 1.54, 1.55, 1.56, 1.57, 1.58, 1.59, 1.60]:
    _, p = section(z); sections.append({'nativeZ': z, 'widthYM': float(np.ptp(p[:, 1])),
        'depthXM': float(np.ptp(p[:, 0])), 'boundsM': [p.min(axis=0).tolist(), p.max(axis=0).tolist()]})


def summary(rows):
    radial = np.array([row['sourceMinusCanonicalRadiusM'] for row in rows])
    return {'vertices': len(rows), 'radialDifferenceMinM': float(radial.min()), 'medianM': float(np.median(radial)),
        'maximumM': float(radial.max()), 'maximumOutwardWitness': rows[int(radial.argmax())],
        'maximumInwardWitness': rows[int(radial.argmin())]}

body_delta = fields['bodyRestXYZ'][body_cut] - n['renderedBodyXYZ'][body_cut]
report = {'status': 'READ_ONLY_SOURCE_DIAGNOSIS_FOR_ONE_UNBUILT_PROPOSAL', 'pins': pins, 'recipeSHA256': sha(__file__),
    'frame': 'Native metres +Xforward/+Zup/-Yleft. Canonical and donor local positions share file frame; no transform is authored.',
    'sourceDistinction': json.loads((qa / 'body59/assessment.json').read_text())['headAncestry'],
    'canonicalHorizontalSections': sections, 'donorOuterComparedAtSameHeight': summary(outer_rows),
    'fixedHeadOneCornerComparedAtSameHeight': summary(fixed_rows),
    'frozen27BodyConformation': {'existingHeadPositionsExactlyOriginal': True, 'changedExistingBodyVertices': len(changed_body),
        'changedIDsExactlyOriginalBodyCut': True, 'maxExistingBodyPositionDeltaM': float(np.linalg.norm(body_delta, axis=1).max()),
        'bodyCutWidthBeforeM': float(np.ptp(n['renderedBodyXYZ'][body_cut, 1])),
        'bodyCutWidthAfterM': float(np.ptp(fields['bodyRestXYZ'][body_cut, 1])),
        'outerDonorWidthM': float(np.ptp(hp[outer, 1])), 'outerDonorDepthM': float(np.ptp(hp[outer, 0]))},
    'exactProtectionConstraints': {'bodyEditableVertices': body_ids.tolist(), 'headEditableVertices': head_ids.tolist(),
        'bodyFixedOneCornerVertices': body_fixed.tolist(), 'headFixedOneCornerVertices': fixed.tolist(),
        'partialHeadUVPositionAliasClassesPinned': partial, 'admittedHeadAliasMembersThatMustStayPinned': pinned_inside.tolist(),
        'protectedOutsideAliasMembers': outside_aliases.tolist(), 'editableHeadAbove1_60TriangleTouches': 0,
        'bodyAvailableBandBoundsM': [n['renderedBodyXYZ'][body_ids].min(axis=0).tolist(), n['renderedBodyXYZ'][body_ids].max(axis=0).tolist()],
        'headAvailableBandBoundsM': [hp[head_ids].min(axis=0).tolist(), hp[head_ids].max(axis=0).tolist()],
        'fixedHeadOneCornerBoundsM': [hp[fixed].min(axis=0).tolist(), hp[fixed].max(axis=0).tolist()]},
    'limits': ['Canonical ray/plane samples distinguish source anatomy from donor cut shape, not nearest surface projection or authored candidate positions.',
        'Frozen27 copied the existing donor outline into body boundary; comparison does not prove the cause of every moving ledge or guarantee correction within this short margin.',
        'Partial source UV alias classes must be pinned entirely while outside IDs remain protected. Fixed rear anchors may limit feasible anatomical fairing; no scope expansion inferred.',
        'Root rejected moving art. Independent Agent3 cause/preservation QA and root scope decision remain required before any new candidate/capture.',
        'No source mutation, new pose/capture, weight solve, export, install, worker/model/GPU job or promotion. All M0-M5/contact/identity/art/engine/device/player gates open.']}
(out / 'diagnosis.json').write_text(json.dumps(report, indent=2) + '\n')
(out / 'source-section-witnesses.json').write_text(json.dumps({'outer': outer_rows, 'fixedHeadOneCorner': fixed_rows}, indent=2) + '\n')
assert pins == {p: sha(root / p) for p in pins}
print(json.dumps({k: report[k] for k in ['status', 'donorOuterComparedAtSameHeight', 'fixedHeadOneCornerComparedAtSameHeight', 'frozen27BodyConformation']}, indent=2))
