"""Complete CPU vertex-normal census and one conservative exact-fan policy.

Protect every donor fan spanning the existing 0.25 normal criterion, plus
every retained source fan whose current candidate vertex normal fails it.
No triangle removal, changed threshold, simplification or native execution.
"""
import hashlib
import json
from pathlib import Path

import numpy as np

import diagnose as diagnosis

ROOT = diagnosis.ROOT
OUT = ROOT/'docs/evidence/rider-rebuild/selected-boot-fan59'
NORMAL_MINIMUM = .25


def geometric_vertex_normals(p, f):
    triangle = p[f]
    cross = np.cross(triangle[:, 1]-triangle[:, 0], triangle[:, 2]-triangle[:, 0])
    length = np.linalg.norm(cross, axis=1)
    assert np.isfinite(length).all() and np.all(length > 0), 'Degenerate geometric face'
    normal = cross/length[:, None]
    sums = np.zeros_like(p); total = np.zeros(len(p))
    for corner in range(3):
        a = triangle[:, (corner+1) % 3]-triangle[:, corner]
        b = triangle[:, (corner+2) % 3]-triangle[:, corner]
        angle = np.arctan2(np.linalg.norm(np.cross(a, b), axis=1), np.einsum('ij,ij->i', a, b))
        np.add.at(sums, f[:, corner], angle[:, None]*normal)
        np.add.at(total, f[:, corner], angle)
    length = np.linalg.norm(sums, axis=1)
    assert np.isfinite(length).all() and np.all(length > 0), 'Undefined vertex normal'
    return sums/length[:, None], normal, length/total


def protection(sp, sf, source_normals, tp, tf, original):
    sn, face_normals, source_coherence = geometric_vertex_normals(sp, sf)
    tn, _, target_coherence = geometric_vertex_normals(tp, tf)
    source_reproduction = np.einsum('ij,ij->i', sn, source_normals)
    # Every target vertex is compared with its exact native donor ancestor.
    assert np.array_equal(tp, sp[original])
    dots = np.einsum('ij,ij->i', tn, source_normals[original])
    failed = np.flatnonzero(dots < NORMAL_MINIMUM)
    minimum_incident_dot = np.ones(len(sp))
    for corner in range(3):
        value = np.einsum('ij,ij->i', face_normals, source_normals[sf[:, corner]])
        np.minimum.at(minimum_incident_dot, sf[:, corner], value)
    mixed = np.flatnonzero(minimum_incident_dot < NORMAL_MINIMUM)
    centers = np.union1d(mixed, original[failed]).astype(np.uint32)
    center_mask = np.zeros(len(sp), bool); center_mask[centers] = True
    face_ids = np.flatnonzero(center_mask[sf].any(axis=1)).astype(np.uint32)
    locked = np.unique(sf[face_ids]).astype(np.uint32)
    required_edges = np.asarray(diagnosis.edges(sf[face_ids]), dtype=np.uint32)
    arrays = {'centerOriginalVertexIds': centers, 'lockedOriginalVertexIds': locked,
              'requiredSourceFaceIds': face_ids, 'requiredEdgesOriginal': required_edges}
    summary = {'sourceVerticesExamined': len(sp), 'sourceTrianglesExamined': len(sf),
        'candidateVerticesExamined': len(tp), 'candidateTrianglesExamined': len(tf),
        'minimumSourceNormalReproductionDot': float(source_reproduction.min()),
        'sourceNormalReproductionBelowPoint25': int(np.count_nonzero(source_reproduction < NORMAL_MINIMUM)),
        'minimumCandidateVertexNormalDot': float(dots.min()),
        'minimumCandidateDotDistanceFromPoint25': float(np.min(np.abs(dots-NORMAL_MINIMUM))),
        'candidateFailingVertices': len(failed), 'mixedDonorFanCenters': len(mixed),
        'additionalFailedCandidateFanCenters': len(centers)-len(mixed),
        'protectedCenters': len(centers), 'protectedOriginalVertices': len(locked),
        'requiredSourceFaces': len(face_ids), 'requiredEdges': len(required_edges),
        'failures': [{'targetVertexId': int(v), 'originalVertexId': int(original[v]),
            'normalDot': float(dots[v]), 'minimumDonorIncidentFaceDot': float(minimum_incident_dot[original[v]]),
            'sourceFanMixedUnderExistingCriterion': bool(minimum_incident_dot[original[v]] < NORMAL_MINIMUM),
            'sourceFanCoherence': float(source_coherence[original[v]]), 'targetFanCoherence': float(target_coherence[v])}
            for v in failed]}
    return summary, arrays


def main():
    constructor_pin = diagnosis.fan.pin(diagnosis.fan.CANDIDATE, diagnosis.fan.CANDIDATE_SHA)
    receipt = json.loads(diagnosis.fan.CANDIDATE.read_text())
    s = diagnosis.fan.arrays(receipt['sourceArrayPackage']); c = diagnosis.fan.arrays(receipt['candidate'])
    sp = s['positions'].reshape(-1, 3).astype(float); sf = s['triangles'].reshape(-1, 3)
    tp = c['positions'].reshape(-1, 3).astype(float); tf = c['triangles'].reshape(-1, 3)
    summary, arrays = protection(sp, sf, s['vertexNormals'].reshape(-1, 3).astype(float), tp, tf, c['originalVertexIds'])
    assert summary['sourceNormalReproductionBelowPoint25'] == 0
    assert diagnosis.ORIGINAL_ID in arrays['centerOriginalVertexIds']
    bounded = json.loads((OUT/'source-fan-constraint.json').read_text())
    assert set(bounded['lockedOriginalVertexIds']).issubset(set(arrays['lockedOriginalVertexIds'].tolist()))
    assert set(bounded['sourceFaceIds']).issubset(set(arrays['requiredSourceFaceIds'].tolist()))
    layout = {}; blocks = []; offset = 0
    for name, array in arrays.items():
        array = np.asarray(array, dtype='<u4'); block = array.tobytes()
        layout[name] = {'byteOffset': offset, 'byteLength': len(block), 'dtype': '<u4', 'count': array.size}
        blocks.append(block); offset += len(block)
    binary = b''.join(blocks); binary_path = OUT/'fan-protection.bin'
    OUT.mkdir(parents=True, exist_ok=True); binary_path.write_bytes(binary)
    report = {'status': 'COMPLETE_CPU_FAN_PROTECTION_CENSUS_UNACCEPTED', 'acceptedArt': False,
        'recipeSHA256': diagnosis.fan.sha(__file__),
        'boundedFindingRecipeSHA256': diagnosis.fan.sha(Path(diagnosis.__file__)),
        'constructor46': constructor_pin, 'census35': receipt['census'],
        'sourceArrayPackage': {'path': receipt['sourceArrayPackage']['path'], 'sha256': receipt['sourceArrayPackage']['sha256']},
        'minimumNormalDot': NORMAL_MINIMUM,
        'criterion': 'Protect the complete original incident fan of every source vertex with any incident geometric face dot native donor vertex normal below 0.25, union every original ancestor whose candidate geometric vertex normal dot native donor vertex normal is below 0.25. This is conservative topology protection, not rejection/filtering of donor faces.',
        'summary': summary,
        'protection': {'path': str(binary_path.relative_to(ROOT)), 'sha256': hashlib.sha256(binary).hexdigest(), 'layout': layout},
        'sourceInputBytesUnchanged': True, 'candidateAttempts': 0,
        'limits': 'CPU angle-weighted normals approximate Blender arithmetic. Full coverage and all failures are recorded; native 0.25 gate remains authoritative. All exact protected source fans must survive one separately guarded construction. No new candidate or scene allocation claim.'}
    (OUT/'fan-census.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__': main()
