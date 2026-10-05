"""Independent array-only audit of literal303 and derived-alias320 proposals."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import numpy as np

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--out', required=True)
parser.add_argument('--manifest', required=True)
args = parser.parse_args()
root = Path(__file__).resolve().parents[2]
out, manifest = Path(args.out).resolve(), Path(args.manifest).resolve()
assert not out.exists() and not manifest.exists()
base = root / 'assets/blender/hero-remaster/rider/finish-2026-10-05/construction/body05'
evidence = root / 'docs/evidence/hero-remaster/finish-2026-10-05'
intake = root / 'harness/out/rider-finish/body05-intake01'
fields_path = base / 'authored-neck-fields.npz'
foundation_path = evidence / 'construction/foundation-source.npz'
source = base / 'natural-foundation.blend'
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert sha(fields_path) == '36277520249bcd2a8058a76c2f4a7595d7c460d3196e9bc59b3aa3a31690cb2d'
assert sha(source) == '58c59f6e8b3e1a3c792e628040a137714fcf62f9ff8989578e2429a038e59661'
f, f0 = np.load(fields_path), np.load(foundation_path)
report_path = intake / 'report.json'
report = json.loads(report_path.read_text())
rest_path = intake / report['rest']['path']
assert sha(rest_path) == report['rest']['sha256']
rest = json.loads(gzip.decompress(rest_path.read_bytes()))
names = rest['jointOrder']
assert names == f['boneNames'].tolist() == f0['boneNames'].tolist()
part = rest['parts']['head']
xyz = np.array(part['xyz'], np.float64)
tri = np.array(part['faces'], np.int64)
raw = np.array(part['fullRawWeights'], np.float32)
assert np.array_equal(xyz, f['headRestXYZ'].astype(np.float64))
assert np.array_equal(tri, f['headTriangles'])
assert np.array_equal(raw, f['headFullWeights'])
assert np.array_equal(raw, f['headFourWeights'])
assert np.array_equal(raw, np.array(part['fourRawWeights'], np.float32))
original = len(f0['headXYZ'])
assert original == 43707 and np.array_equal(xyz[:original], f0['headXYZ'])
assert np.array_equal(raw[:original], f0['headWeights'])
inner = np.sort(f['headInnerCutNativeIDs'].astype(np.int64))
assert len(inner) == len(np.unique(inner)) == 303 and inner.min() >= original
keys = {tuple(xyz[v]): int(v) for v in inner}
assert len(keys) == 303
# Search EVERY point, not only the constructor's declared cut rows.
aliases = np.array([v for v in range(len(xyz)) if v not in set(inner) and tuple(xyz[v]) in keys], np.int64)
representatives = np.array([keys[tuple(xyz[v])] for v in aliases], np.int64)
assert len(aliases) == 17 and aliases.min() >= original
expanded = np.union1d(inner, aliases)
ancestry = f['headAttributeEdgeSources']
endpoints = np.unique(ancestry[expanded, :2].astype(np.int64))
assert np.all(ancestry[expanded, :2] >= 0)
assert set(endpoints) <= set(f0['headEditableIDs'])
assert not np.intersect1d(endpoints, f0['headProtectedIDs']).size
assert not np.intersect1d(expanded, f['headOuterCutNativeIDs']).size
mask303, mask320 = np.isin(tri, inner), np.isin(tri, expanded)
cap = np.flatnonzero(mask303.all(axis=1))
assert np.array_equal(cap, np.arange(68704, 69005))
assert np.array_equal(cap, np.flatnonzero(mask320.all(axis=1)))
lining303 = np.flatnonzero(mask303.any(axis=1) & ~mask303.all(axis=1))
lining320 = np.flatnonzero(mask320.any(axis=1) & ~mask320.all(axis=1))
alias_incident = np.flatnonzero(np.isin(tri, aliases).any(axis=1))
assert len(lining303) == 455 and len(lining320) == 459
assert np.all(f['headTriangleSourcePolygonIDs'][cap] == -1)
assert np.all(f['headTriangleSourcePolygonIDs'][lining320] >= 0)
assert not np.intersect1d(f['headTriangleSourcePolygonIDs'][lining320], f0['headUpperIncidentTriangles']).size
head = names.index('head')
proposals = {}
changed = {}
for label, ids in [('literal303', inner), ('expanded320', expanded)]:
    proposal = raw.copy()
    proposal[ids] = 0
    proposal[ids, head] = 1
    changes = np.flatnonzero(np.any(proposal != raw, axis=1))
    outside = np.setdiff1d(np.arange(len(xyz)), ids)
    assert np.array_equal(proposal[outside], raw[outside])
    assert np.array_equal(proposal[:original], raw[:original])
    proposals[label], changed[label] = proposal, changes
assert changed['literal303'].tolist() == [43732, 43827, 43828, 43837, 44240]
assert changed['expanded320'].tolist() == [43732, 43827, 43828, 43829, 43837, 43842, 44240]
assert np.array_equal(proposals['expanded320'][aliases], proposals['expanded320'][representatives])

# Independently reconstruct normalized weighted affine skinning from saved matrices.
rig = np.array(rest['rigWorldRows'])
object_world = np.array(part['objectWorld'])
to_rig = np.linalg.inv(rig) @ object_world
hp = np.c_[xyz, np.ones(len(xyz))] @ to_rig.T
rest_world = (np.c_[xyz, np.ones(len(xyz))] @ object_world.T)[:, :3]
def crosses(points, ids):
    p = points[tri[ids]]
    return np.cross(p[:, 1]-p[:, 0], p[:, 2]-p[:, 0])
rest_cross = crosses(rest_world, np.arange(len(tri)))
def stats(points, ids, reference):
    cross = crosses(points, ids)
    areas = np.linalg.norm(cross, axis=1)
    ref = reference[ids]
    dots = np.einsum('ij,ij->i', cross, ref) / (areas*np.linalg.norm(ref, axis=1))
    ratios = areas / np.linalg.norm(rest_cross[ids], axis=1)
    return {'minimumArea2M2': float(areas.min()), 'minimumAreaRatioToRest': float(ratios.min()),
            'maximumAreaRatioToRest': float(ratios.max()), 'minimumDotToExpectedHeadAffine': float(dots.min()),
            'opposedTriangleIDs': ids[dots < 0].tolist(), 'zeroAreaTriangleIDs': ids[areas == 0].tolist()}
pins = {str(p.relative_to(root)): sha(p) for p in [source, fields_path, foundation_path, report_path, rest_path]}
samples = []
for sample_pin in report['samples']:
    path = intake / sample_pin['path']
    assert sha(path) == sample_pin['sha256']
    pins[str(path.relative_to(root))] = sha(path)
    s = json.loads(gzip.decompress(path.read_bytes()))
    skin = np.array(s['skinNativeRows'])
    current = np.array(s['parts']['head']['full']['xyzWorld'])
    # Matrix blend first, then multiply each homogeneous point; separate from constructor einsum.
    def predict(weights):
        weights = weights.astype(np.float64)
        weights /= weights.sum(axis=1)[:, None]
        blends = (weights @ skin.reshape(51, 16)).reshape(-1, 4, 4)
        return (np.einsum('vab,vb->va', blends, hp) @ rig.T)[:, :3]
    control = predict(raw)
    error = float(np.linalg.norm(control-current, axis=1).max())
    assert error < 2e-6
    affine = rig @ skin[head] @ to_rig
    world_affine = affine @ np.linalg.inv(object_world)
    linear = world_affine[:3, :3]
    expected = rest_cross @ np.linalg.inv(linear) * np.linalg.det(linear)
    record = {'index': s['index'], 'case': s['case'], 'phase': s['phase'],
              'manualNativeWholeHeadMaximumM': error,
              'headAffineDeterminant': float(np.linalg.det(linear)),
              'headAffineOrthogonalityMaximumError': float(np.abs(linear.T@linear-np.eye(3)).max()),
              'actualNativeAliasMaximumGapM': float(np.linalg.norm(current[aliases]-current[representatives], axis=1).max()),
              'currentNativeCap': stats(current, cap, expected)}
    for label, proposal in proposals.items():
        p = predict(proposal)
        ids = inner if label == 'literal303' else expanded
        hybrid = current.copy()
        hybrid[ids] = p[ids]
        # This rounding proxy is explicitly not Blender evaluation: points are rounded LOCAL float32.
        local = (np.c_[p, np.ones(len(p))] @ np.linalg.inv(object_world).T)[:, :3].astype(np.float32)
        rounded_world = (np.c_[local.astype(np.float64), np.ones(len(p))] @ object_world.T)[:, :3]
        record[label] = {'idealAliasMaximumGapM': float(np.linalg.norm(p[aliases]-p[representatives], axis=1).max()),
                         'idealAliasGapsM': np.linalg.norm(p[aliases]-p[representatives], axis=1).tolist(),
                         'localFloat32RoundingProxyAliasMaximumGapM': float(np.linalg.norm(rounded_world[aliases]-rounded_world[representatives], axis=1).max()),
                         'idealCap': stats(p, cap, expected),
                         'localFloat32RoundingProxyCap': stats(rounded_world, cap, expected),
                         'idealLining': stats(p, lining303 if label == 'literal303' else lining320, expected),
                         'nativeOutsideMaskHybridAliasMaximumGapM': float(np.linalg.norm(hybrid[aliases]-hybrid[representatives], axis=1).max()),
                         'nativeOutsideMaskHybridLining': stats(hybrid, lining303 if label == 'literal303' else lining320, expected),
                         'changedRowsMaximumDisplacementFromCurrentM': float(np.linalg.norm(p[changed[label]]-current[changed[label]], axis=1).max())}
    assert record['expanded320']['idealAliasMaximumGapM'] == 0
    assert record['expanded320']['localFloat32RoundingProxyAliasMaximumGapM'] == 0
    samples.append(record)

constructor_checks = {}
for version in ['01', '02']:
    folder = evidence / ('construction/body05/inner-cap-field-preflight' + version + '/proposal')
    receipt_path, mask_path = folder / 'preflight.json', folder / 'exact-mask-and-reference.npz'
    if not receipt_path.exists():
        continue
    receipt, c = json.loads(receipt_path.read_text()), np.load(mask_path)
    assert np.array_equal(c['headInner303NativeIDs'], f['headInnerCutNativeIDs'])
    assert np.array_equal(c['additionalInnerNativeAliases'], aliases)
    # Representative order follows the source ring; compare pair identity by positions.
    assert np.array_equal(c['aliasRepresentativeNativeIDs'], representatives)
    independent_by_index = {r['index']: r for r in samples}
    label = 'literal303' if version == '01' else 'expanded320'
    declared_ids = c['headInner303NativeIDs'] if version == '01' else c['expanded320NativeIDs']
    assert np.array_equal(np.sort(declared_ids), inner if version == '01' else expanded)
    assert np.array_equal(c['originalRawFullRows'], raw[declared_ids])
    assert np.array_equal(c['originalRawFourRows'], raw[declared_ids])
    assert np.array_equal(c['proposedHeadOnlyRows'], proposals[label][declared_ids])
    assert np.array_equal(c['capTriangleIDs'], cap) and np.array_equal(c['capTriangles'], tri[cap])
    lining = lining303 if version == '01' else lining320
    assert np.array_equal(c['adjacentLiningTriangleIDs'], lining)
    assert np.array_equal(c['adjacentLiningTriangles'], tri[lining])
    assert np.array_equal(c['aliasIncidentTriangleIDs'], alias_incident)
    assert [r['index'] for r in receipt['samples']] == [r['index'] for r in samples]
    residual = max(abs(r['aliasProposedMaximumSeparationM']-independent_by_index[r['index']][label]['nativeOutsideMaskHybridAliasMaximumGapM']) for r in receipt['samples'])
    area_residual = max(abs(r['liningProposed']['minimumAreaRatioToRest']-independent_by_index[r['index']][label]['nativeOutsideMaskHybridLining']['minimumAreaRatioToRest']) for r in receipt['samples'])
    dot_residual = max(abs(r['liningProposed']['minimumNormalDotExpectedHeadRigid']-independent_by_index[r['index']][label]['nativeOutsideMaskHybridLining']['minimumDotToExpectedHeadAffine']) for r in receipt['samples'])
    constructor_checks[version] = {'receiptSHA256': sha(receipt_path), 'maskSHA256': sha(mask_path),
                                   'exactAliasPairsAnd303MaskMatch': True,
                                   'exactProposalRowsCapLiningAndAllTenSampleIdentitiesMatch': True,
                                   'aliasMaximumGapPredictionResidualM': residual,
                                   'hybridLiningMinimumAreaRatioResidual': area_residual,
                                   'hybridLiningMinimumNormalDotResidual': dot_residual}

np.savez_compressed(manifest, inner303NativeIDs=inner, aliasNativeIDs=aliases,
                    aliasRepresentativeNativeIDs=representatives, expanded320NativeIDs=expanded,
                    literal303ChangedNativeIDs=changed['literal303'], expanded320ChangedNativeIDs=changed['expanded320'],
                    expandedSourceEdgeAncestry=ancestry[expanded], originalFullFourRows=raw[expanded],
                    proposedHeadOnlyRows=proposals['expanded320'][expanded], capTriangleIDs=cap,
                    capTriangles=tri[cap], lining303TriangleIDs=lining303, lining320TriangleIDs=lining320,
                    aliasIncidentTriangleIDs=alias_incident)
result = {'status': 'UNACCEPTED_READ_ONLY303_AND320_AFFINE_FIELD_SCOPE_AUDIT',
          'recipeSHA256': sha(__file__), 'numpy': np.__version__, 'inputPins': pins,
          'manifestSHA256': sha(manifest), 'manifestBytes': manifest.stat().st_size,
          'boneOrder': names, 'mask': {'literalVertices': 303, 'expandedVertices': 320,
          'literalEffectiveChangedIDs': changed['literal303'].tolist(), 'expandedEffectiveChangedIDs': changed['expanded320'].tolist(),
          'all17PositionAliasesFoundBySearchingEveryHeadPoint': True,
          'nonrigidAdditionalAliasIDs': np.intersect1d(aliases, changed['expanded320']).tolist(),
          'capTriangles': len(cap), 'literalAdjacentLiningTriangles': len(lining303),
          'expandedAdjacentLiningTriangles': len(lining320), 'aliasIncidentTriangles': len(alias_incident),
          'expandedLiningSourcePolygons': len(np.unique(f['headTriangleSourcePolygonIDs'][lining320])),
          'allMaskIDsDerived': True, 'ancestryEndpointsWhollyF0EditableProtectedDisjoint': True,
          'upperSourceFaceIncidentPolygonsDisjoint': True, 'outer313MaskDisjoint': True,
          'original43707AndOutsideProposedMaskRowsExact': True},
          'constructorReadback': constructor_checks, 'samples': samples,
          'limits': ['No Blender job, native batch, new pose, source mutation, save/export or candidate master.',
          'Constant-field ideal affine predictions close all17 exact position aliases. Actual native trial must independently verify source guards, topology, contacts and evaluated normals.',
          'Native-outside-mask hybrid retains already measured Float32 geometry outside the scope, matching the constructor method; this is separate from ideal normalized affine prediction of every point.',
          'Float32 local rounding proxy is not Blender evaluated geometry or custom fan decoding. Ideal area/winding is distinct from native moving-normal parity.',
          'Adjacent lining winding versus transported head reference is a finite diagnostic; no complete contact, continuous-time, grounded-stream, GPU, art or physiological acceptance.',
          'No tolerance relaxation, corner exclusion or generalized explanation of wholemesh near2 normal errors.']}
assert all(sha(root/path) == digest for path, digest in pins.items())
out.write_text(json.dumps(result, separators=(',', ':'), allow_nan=False)+'\n')
print(json.dumps({'mask': result['mask'], 'constructorReadback': constructor_checks,
                  'samples': [{'index': r['index'], 'literalGapM': r['literal303']['idealAliasMaximumGapM'],
                               'expandedGapM': r['expanded320']['idealAliasMaximumGapM'],
                               'expandedCap': r['expanded320']['idealCap'],
                               'expandedLining': r['expanded320']['idealLining']} for r in samples]}, indent=2))
