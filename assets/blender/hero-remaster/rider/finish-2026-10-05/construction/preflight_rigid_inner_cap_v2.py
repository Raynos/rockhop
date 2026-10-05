"""Read-only prediction of303 cap-loop plus17 coincident derived aliases.

Uses already measured own51 skin matrices; writes a proposal receipt/mask,
never a Blender master. Every coincident derived lining alias shares the cap field. Original source
rows and every row outside the declared320 remain immutable.
"""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import time

import numpy as np

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--out', required=True)
args = parser.parse_args()
out = Path(args.out)
assert not out.exists()
started = time.monotonic()
owned = Path(__file__).resolve().parent
root = owned.parents[5]
fields_path = owned / 'body05/authored-neck-fields.npz'
foundation_path = root / 'docs/evidence/hero-remaster/finish-2026-10-05/construction/foundation-source.npz'
source = owned / 'body05/natural-foundation.blend'
intake = root / 'harness/out/rider-finish/body05-intake01'
sha = lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest()
assert sha(source) == '58c59f6e8b3e1a3c792e628040a137714fcf62f9ff8989578e2429a038e59661'
assert sha(fields_path) == '36277520249bcd2a8058a76c2f4a7595d7c460d3196e9bc59b3aa3a31690cb2d'
assert sha(foundation_path) == 'b6eaa2ccee77a9e6f6395daa1fc473da3f6099f26f79895f288e1300b3fba3ae'
fields, foundation = np.load(fields_path), np.load(foundation_path)
report_path = intake / 'report.json'
native = json.loads(report_path.read_text())
rest_path = intake / native['rest']['path']
assert sha(rest_path) == native['rest']['sha256']
rest = json.loads(gzip.decompress(rest_path.read_bytes()))
names = rest['jointOrder']
assert names == fields['boneNames'].tolist() == foundation['boneNames'].tolist()
head_bone, neck_bone = names.index('head'), names.index('neck')
part = rest['parts']['head']
xyz = fields['headRestXYZ'].astype(float)
triangles = fields['headTriangles'].astype(int)
full_raw = np.array(part['fullRawWeights'], np.float32)
four_raw = np.array(part['fourRawWeights'], np.float32)
assert np.array_equal(full_raw, fields['headFullWeights'])
assert np.array_equal(four_raw, fields['headFourWeights'])
assert np.array_equal(full_raw, four_raw)
assert np.array_equal(np.array(part['xyz']), xyz)
assert np.array_equal(np.array(part['faces']), triangles)
original_count = len(foundation['headXYZ'])
assert original_count == 43707
assert np.array_equal(full_raw[:original_count], foundation['headWeights'])
inner = fields['headInnerCutNativeIDs'].astype(int)
outer = fields['headOuterCutNativeIDs'].astype(int)
assert len(inner) == len(np.unique(inner)) == 303
assert np.all(inner >= original_count) and not np.intersect1d(inner, outer).size
ancestry = fields['headAttributeEdgeSources']
source_vertices = np.unique(ancestry[inner, :2].astype(int))
assert set(source_vertices) <= set(foundation['headEditableIDs'].tolist())
assert not np.intersect1d(source_vertices, foundation['headProtectedIDs']).size
in_mask = np.isin(triangles, inner)
cap_faces = np.flatnonzero(in_mask.all(axis=1))
lining_faces = np.flatnonzero(in_mask.any(axis=1) & ~in_mask.all(axis=1))
assert np.array_equal(cap_faces, np.arange(68704, 69005))
assert len(cap_faces) == 301 and len(lining_faces) == 455
assert np.all(fields['headTriangleSourcePolygonIDs'][cap_faces] == -1)
assert np.all(fields['headTriangleSourcePolygonIDs'][lining_faces] >= 0)
assert not np.intersect1d(fields['headTriangleSourcePolygonIDs'][lining_faces],
                         foundation['headUpperIncidentTriangles']).size
proposal = full_raw.copy()
proposal[inner] = 0
proposal[inner, head_bone] = 1
changed = np.flatnonzero(np.any(proposal != full_raw, axis=1))
assert set(changed) <= set(inner) and len(changed) == 5
assert np.array_equal(proposal[:original_count], full_raw[:original_count])
outside = np.setdiff1d(np.arange(len(xyz)), inner)
assert np.array_equal(proposal[outside], full_raw[outside])
keys = {tuple(xyz[v]): int(v) for v in inner}
cut_rows = np.flatnonzero((np.arange(len(xyz)) >= original_count) & (ancestry[:, 0] >= 0))
aliases = np.array([v for v in cut_rows if v not in set(inner) and tuple(xyz[v]) in keys], int)
alias_representatives = np.array([keys[tuple(xyz[v])] for v in aliases], int)
assert len(aliases) == 17
mask_ids = np.unique(np.r_[inner, aliases])
assert len(mask_ids) == 320 and np.all(mask_ids >= original_count)
assert not np.intersect1d(mask_ids, outer).size
expanded_ancestry = np.unique(ancestry[mask_ids, :2].astype(int))
assert set(expanded_ancestry) <= set(foundation['headEditableIDs'].tolist())
assert not np.intersect1d(expanded_ancestry, foundation['headProtectedIDs']).size
assert np.all(ancestry[mask_ids, 0] >= 0)
proposal[mask_ids] = 0
proposal[mask_ids, head_bone] = 1
changed = np.flatnonzero(np.any(proposal != full_raw, axis=1))
assert len(changed) == 7 and set(changed) <= set(mask_ids)
assert np.array_equal(proposal[:original_count], full_raw[:original_count])
outside = np.setdiff1d(np.arange(len(xyz)), mask_ids)
assert np.array_equal(proposal[outside], full_raw[outside])
expanded_face_mask = np.isin(triangles, mask_ids)
assert np.array_equal(np.flatnonzero(expanded_face_mask.all(axis=1)), cap_faces)
lining_faces = np.flatnonzero(expanded_face_mask.any(axis=1) & ~expanded_face_mask.all(axis=1))
assert np.all(fields['headTriangleSourcePolygonIDs'][lining_faces] >= 0)
assert not np.intersect1d(fields['headTriangleSourcePolygonIDs'][lining_faces],
                         foundation['headUpperIncidentTriangles']).size
alias_faces = np.flatnonzero(np.isin(triangles, aliases).any(axis=1))
weights = np.array(part['fullWeights'])
rig_world = np.array(rest['rigWorldRows'])
local_to_rig = np.linalg.inv(rig_world) @ np.array(part['objectWorld'])
homogeneous = np.c_[xyz, np.ones(len(xyz))] @ local_to_rig.T
rest_tri = xyz[triangles]
rest_cross = np.cross(rest_tri[:, 1]-rest_tri[:, 0], rest_tri[:, 2]-rest_tri[:, 0])
rest_area = np.linalg.norm(rest_cross, axis=1)
affected = np.unique(np.r_[cap_faces, lining_faces])
targets = np.unique(np.r_[inner, aliases, triangles[lining_faces].ravel(), outer])
records = []
pins = {str(p.relative_to(root)): sha(p) for p in [source, fields_path, foundation_path, report_path, rest_path]}
for pin in native['samples']:
    path = intake / pin['path']
    assert sha(path) == pin['sha256']
    pins[str(path.relative_to(root))] = pin['sha256']
    sample = json.loads(gzip.decompress(path.read_bytes()))
    skin = np.array(sample['skinNativeRows'])
    current = np.array(sample['parts']['head']['full']['xyzWorld'])
    predicted_current = np.einsum('vj,jab,vb->va', weights[targets], skin,
                                  homogeneous[targets], optimize=True) @ rig_world.T
    error = np.linalg.norm(predicted_current[:, :3]-current[targets], axis=1).max()
    assert error < 2e-6
    rigid_matrix = rig_world @ skin[head_bone] @ local_to_rig
    rigid = (np.c_[xyz, np.ones(len(xyz))] @ rigid_matrix.T)[:, :3]
    predicted = current.copy()
    predicted[mask_ids] = rigid[mask_ids]
    transformed_rest_cross = rest_cross @ np.linalg.inv(rigid_matrix[:3, :3])
    transformed_rest_cross *= np.linalg.det(rigid_matrix[:3, :3])
    def fans(points, face_ids):
        t = points[triangles[face_ids]]
        cross = np.cross(t[:, 1]-t[:, 0], t[:, 2]-t[:, 0])
        area = np.linalg.norm(cross, axis=1)
        reference = transformed_rest_cross[face_ids]
        cosine = np.einsum('ij,ij->i', cross, reference) / (area*np.linalg.norm(reference, axis=1))
        return {'minimumArea2M2': float(area.min()),
                'minimumAreaRatioToRest': float((area/rest_area[face_ids]).min()),
                'maximumAreaRatioToRest': float((area/rest_area[face_ids]).max()),
                'minimumNormalDotExpectedHeadRigid': float(cosine.min()),
                'opposedToExpectedHeadRigidFaces': face_ids[cosine < 0].tolist()}
    alias_current = np.linalg.norm(current[aliases]-current[alias_representatives], axis=1)
    alias_proposed = np.linalg.norm(predicted[aliases]-predicted[alias_representatives], axis=1)
    head_frame = (np.c_[current[outer], np.ones(len(outer))] @ np.linalg.inv(rigid_matrix).T)[:, :3]
    a, b = head_frame[:, :2], np.roll(head_frame[:, :2], -1, axis=0)
    edge = b-a
    point = xyz[inner, :2]
    fractions = np.clip(np.einsum('pij,ij->pi', point[:, None, :]-a[None, :, :], edge)/np.einsum('ij,ij->i', edge, edge), 0, 1)
    distances = np.linalg.norm(point[:, None, :]-a[None, :, :]-fractions[:, :, None]*edge[None, :, :], axis=2)
    inside = np.zeros(len(inner), bool)
    for v, w in zip(a, b):
        crosses = ((v[1] > point[:, 1]) != (w[1] > point[:, 1]))
        if w[1] != v[1]:
            inside ^= crosses & (point[:, 0] < (w[0]-v[0])*(point[:, 1]-v[1])/(w[1]-v[1])+v[0])
    body_cut = fields['bodyPlaneCutNativeIDs'].astype(int)
    body_points = np.array(sample['parts']['body']['four']['xyzWorld'])[body_cut]
    body_head_frame = (np.c_[body_points, np.ones(len(body_points))] @ np.linalg.inv(rigid_matrix).T)[:, :3]
    records.append({'index': sample['index'], 'case': sample['case'], 'phase': sample['phase'],
        'currentManualNativeTargetMaxM': float(error),
        'headAffineDeterminant': float(np.linalg.det(rigid_matrix[:3, :3])),
        'headAffineOrthogonalityMaximumError': float(np.max(np.abs(rigid_matrix[:3, :3].T@rigid_matrix[:3, :3]-np.eye(3)))),
        'capCurrent': fans(current, cap_faces), 'capProposed': fans(predicted, cap_faces),
        'liningCurrent': fans(current, lining_faces), 'liningProposed': fans(predicted, lining_faces),
        'changedRowsMaximumDisplacementM': float(np.linalg.norm(predicted[changed]-current[changed], axis=1).max()),
        'aliasCurrentMaximumSeparationM': float(alias_current.max()),
        'aliasProposedMaximumSeparationM': float(alias_proposed.max()),
        'aliasProposedSeparationsM': alias_proposed.tolist(),
        'outerRingProjectedContainment': {'capVerticesOutsideProjectedOuterLoop': int((~inside).sum()),
            'minimumProjectedBoundaryDistanceM': float(distances.min()),
            'outerPlaneMaximumDeviationM': float(np.abs(head_frame[:, 2]-xyz[inner[0], 2]).max()),
            'limit': 'Head-rigid-plane projection only; not signed complete-surface contact or continuous-time clearance.'},
        'bodyCutToRigidCapPlane': {'minimumPlaneSeparationM': float((xyz[inner[0], 2]-body_head_frame[:, 2]).min()),
            'maximumPlaneSeparationM': float((xyz[inner[0], 2]-body_head_frame[:, 2]).max()),
            'limit': 'Only104 body-plane cut points; excludes complete body triangles and self/lining/cap coplanar contacts.'}})
    print('CAP_PREFLIGHT_SAMPLE', sample['index'], 'aliasGapM', float(alias_proposed.max()), flush=True)
out.mkdir(parents=True)
mask = out / 'exact-mask-and-reference.npz'
np.savez_compressed(mask, headInner303NativeIDs=inner, expanded320NativeIDs=mask_ids, actualChanged7NativeIDs=changed,
    originalRawFullRows=full_raw[mask_ids], originalRawFourRows=four_raw[mask_ids], proposedHeadOnlyRows=proposal[mask_ids],
    expandedPointSourceEdgeAncestry=ancestry[mask_ids], capTriangleIDs=cap_faces,
    capTriangles=triangles[cap_faces], adjacentLiningTriangleIDs=lining_faces,
    adjacentLiningSourcePolygonIDs=fields['headTriangleSourcePolygonIDs'][lining_faces],
    adjacentLiningTriangles=triangles[lining_faces], additionalInnerNativeAliases=aliases,
    aliasRepresentativeNativeIDs=alias_representatives, aliasReferenceRawRows=full_raw[aliases],
    aliasIncidentTriangleIDs=alias_faces)
result = {'status': 'READ_ONLY320_DERIVED_ALIAS_CLOSED_FIELD_PROPOSAL_UNACCEPTED',
    'sourcePins': pins, 'recipeSHA256': sha(__file__), 'maskSHA256': sha(mask),
    'boneOrder': names, 'headOnlyBone': 'head', 'proposedMaskNativeIDs': mask_ids.tolist(), 'inner303NativeIDs': inner.tolist(),
    'actualChangedNativeIDs': changed.tolist(), 'capFaceIDs': cap_faces.tolist(),
    'adjacentLiningFaceIDs': lining_faces.tolist(),
    'adjacentLiningOriginalSourcePolygonIDs': np.unique(fields['headTriangleSourcePolygonIDs'][lining_faces]).tolist(),
    'all320RowsDerivedAndOutsideProtectedF0': True, 'all320SourceEdgeEndpointsWhollyF0Editable': True, 'original43707RawFULLFOURReferenceExactAndUnchanged': True,
    'outside320ProposalWeightRowsExact': True,
    'original43707RawReferenceSHA256': hashlib.sha256(full_raw[:original_count].tobytes()).hexdigest(), 'outer313LoftBodyBoxerFieldsUnchanged': True,
    'exactRestXYZUVTrianglesMaterialsRawDecodedNormalsPreservation': 'No source mutation or new master; all existing source bytes remain pinned. Actual trial must independently verify every field.',
    'additionalInnerAliases': [{'nativeID': int(v), 'representativeNativeID': int(r),
        'rawNeckWeight': float(full_raw[v, neck_bone]), 'rawHeadWeight': float(full_raw[v, head_bone])}
        for v, r in zip(aliases, alias_representatives)],
    'samples': records, 'elapsedSeconds': time.monotonic()-started,
    'sourceSaved': False, 'candidateMasterWritten': False,
    'limits': ['Expanded mask includes303 derived cap rows plus17 coincident derived lining aliases; all have editable-only edge ancestry. Seven rows effectively change, with all original43707 and outside320 fields exact. No candidate written or trial admission.',
        'Uniform head-only cap and aliases are one constant proper affine skin transform; face winding is compared to that transformed reference, not a fixed world-Z test. Float64 prediction is distinct from actual native Float32 evaluation.',
        'Predicted winding/area and finite projection/plane proxies are not native evaluated normals or proper surface contacts. No normal/contact/art qualification.',
        'Existing source upper face/cheek, original34, own51/rest/binds, materials/images, rest normals, body/boxer/outer313/loft and all original head rows remain untouched.',
        'Ten saved FK diagnostic skins only; grounded stream, continuous time, engine/GPU and phone not evaluated.']}
assert all(sha(root / path) == digest for path, digest in pins.items())
(out / 'preflight.json').write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')
print('READ_ONLY_CAP_PREFLIGHT_READY', result['elapsedSeconds'], flush=True)
