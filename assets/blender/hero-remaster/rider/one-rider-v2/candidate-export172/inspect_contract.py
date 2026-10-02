"""Read-only frozen tube06 export preflight; emit no GLB without full semantics."""
import os
os.environ.setdefault('OPENBLAS_NUM_THREADS', '2')
os.environ.setdefault('OMP_NUM_THREADS', '2')
import hashlib
import importlib.util
import json
from pathlib import Path
import numpy as np

REPO = Path('/Users/raynos/projects/games/rockhop')
OWN = REPO / 'assets/blender/hero-remaster/rider/one-rider-v2/candidate-export172'
EVIDENCE = REPO / 'docs/evidence/hero-remaster/one-rider-v2/candidate-export172'
TASK3 = REPO / 'assets/blender/hero-remaster/rider/one-rider-v2/foundation-repair-task3'
PRIVATE = Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/candidate-export172')
NPZ = TASK3 / 'hoodie-repair03/tube03-four-bind/four-cap-carrier06-envelope.npz'
SOURCE = TASK3 / 'deliverables/C19.glb'
REFERENCE = Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/garment-rebuild01/physical-v5-control157/rider.glb')
MAPPER = REPO / 'assets/blender/hero-remaster/rider/one-rider-v2/candidate-handoff170/map_candidate.py'
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()

def pack_all(weights):
    """Keep each literal nonzero lane, refusing even a tiny fifth influence."""
    assert weights.ndim == 2 and weights.shape[1] == 19
    assert np.isfinite(weights).all() and (weights >= 0).all()
    assert np.max(abs(weights.sum(1) - 1)) < 1e-12
    assert (weights != 0).sum(1).max() <= 4
    joints = np.zeros((len(weights), 4), dtype=np.uint16)
    values = np.zeros((len(weights), 4), dtype=np.float64)
    for vertex in range(len(weights)):
        ids = np.flatnonzero(weights[vertex] != 0)
        joints[vertex, :len(ids)] = ids
        values[vertex, :len(ids)] = weights[vertex, ids]
    rebuilt = np.zeros_like(weights)
    np.add.at(rebuilt, (np.arange(len(weights))[:, None], joints), values)
    assert np.array_equal(rebuilt, weights)
    return joints, values

def main():
    spec = importlib.util.spec_from_file_location('handoff170', MAPPER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    inputs = [NPZ, SOURCE, REFERENCE, MAPPER, TASK3 / 'OWNERSHIP.json',
              TASK3 / 'hoodie-repair03/tube03-four-bind/four-cap-carrier06-envelope-report.json',
              TASK3 / 'hoodie-repair03/tube03-visual06/snapshot-rest.json']
    before = {str(p): sha(p) for p in inputs}
    assert before[str(NPZ)] == 'ece32f56441f144925d83344e544331463f20c6e9f39221111b003702df35406'
    z = np.load(NPZ, allow_pickle=False)
    source, reference = module.GLB(SOURCE), module.GLB(REFERENCE)
    rows, requirements, protected = [], [], []
    for ordinal, (_, _, primitive) in enumerate(module.inventory(source.j)):
        original_count = len(source.array(primitive['attributes']['POSITION']))
        count = len(z[f'p{ordinal}'])
        weights = z[f'W{ordinal}']
        assert weights.shape == (count, 19) and np.isfinite(weights).all()
        assert (weights >= 0).all() and np.max(abs(weights.sum(1) - 1)) < 1e-12
        influence_counts = (weights != 0).sum(1)
        assert influence_counts.max() <= 4  # Literal nonzero, no threshold/truncation.
        packed_joints, packed_weights = pack_all(weights)
        quantization = {}
        for field in ['p', 'n', 'uv', 'W']:
            a = z[f'{field}{ordinal}']
            quantization[field] = {'float64ExactlyRepresentableInFloat32': np.array_equal(a, a.astype(np.float32).astype(np.float64)),
                                   'maximumAbsoluteFloat32Rounding': float(abs(a - a.astype(np.float32)).max())}
        missing = []
        if count != original_count:
            for name in primitive['attributes']:
                if name not in ['POSITION', 'NORMAL', 'TEXCOORD_0', 'JOINTS_0', 'WEIGHTS_0']:
                    a = source.array(primitive['attributes'][name])
                    missing.append({'semantic': name, 'sourceDistinctRows': len(np.unique(a, axis=0)),
                                    'sourceAccessorSignature': source.signature(primitive['attributes'][name]),
                                    'npzPayloadAbsent': True})
            for target_i, target in enumerate(primitive.get('targets', [])):
                for semantic, accessor in target.items():
                    a = source.array(accessor)
                    missing.append({'morphTarget': target_i, 'semantic': semantic,
                                    'sourceNonzeroRows': int(np.any(a != 0, axis=1).sum()),
                                    'sourceMaximumAbsoluteDelta': float(abs(a).max()),
                                    'npzNewRowsPayloadAbsent': True})
        if missing:
            requirements.append({'primitive': ordinal, 'newRows': count - original_count,
                                 'requiredAuthoredOrExplicitlyApprovedExtensionPolicies': missing})
        if ordinal in [1, 3]:
            reference_primitive = module.inventory(reference.j)[ordinal][2]
            exact = all(source.signature(ai) == reference.signature(reference_primitive['attributes'][name])
                        and source.array(ai).tobytes() == reference.array(reference_primitive['attributes'][name]).tobytes()
                        for name, ai in primitive['attributes'].items())
            assert exact
            assert np.array_equal(z[f'p{ordinal}'], source.array(primitive['attributes']['POSITION']).astype(float))
            assert np.array_equal(z[f'n{ordinal}'], source.array(primitive['attributes']['NORMAL']).astype(float))
            assert np.array_equal(z[f'uv{ordinal}'], source.array(primitive['attributes']['TEXCOORD_0']).astype(float))
            protected.append({'primitive': ordinal, 'allSourceReferenceAttributeBytesAndFlagsExact': True,
                              'npzPositionNormalUVExactSource': True})
        rows.append({'primitive': ordinal, 'vertices': count, 'sourceVertices': original_count,
                     'triangles': len(z[f'tr{ordinal}']), 'maxLiteralNonzeroInfluences': int(influence_counts.max()),
                     'denseToFourLaneFloat64ReconstructionExact': True,
                     'maximumWeightSumError': float(abs(weights.sum(1) - 1).max()),
                     'float32Rounding': quantization})
    negative_controls = []
    for label, values in [('tiny_fifth_influence', [.25, .25, .25, .25, 1e-18]),
                          ('negative_influence', [1.0, -1e-18]),
                          ('nonfinite_influence', [float('nan')])]:
        corrupted = np.zeros((1, 19))
        corrupted[0, :len(values)] = values
        try:
            pack_all(corrupted)
        except AssertionError:
            negative_controls.append({'control': label, 'status': 'REJECTED_AS_EXPECTED'})
        else:
            raise AssertionError('Invalid influence control packed: ' + label)
    assert {str(p): sha(p) for p in inputs} == before
    report = {
        'status': 'EXPORT_REQUIREMENTS_IDENTIFIED_NO_SKINNED_ASSET_EMITTED',
        'sourceInputsSHA256': before, 'recipeSHA256': sha(__file__),
        'snapshotIsUnskinnedVisualOnly': True, 'protected': protected, 'primitives': rows,
        'missingExportSemantics': requirements,
        'packingNegativeControls': negative_controls,
        'requiredConstructionOwnerDecisions': [
            'Supply new fabric COLOR_2 or explicitly declare a bounded extension after auditing consumers: source garment has 647 distinct rows; median or zeros are newly defined data, not preserved source information.',
            'Declare auxiliary TEXCOORD_1/2 and COLOR_0/1/2 extension policies, retaining old rows and normalized flags exactly.',
            'Declare two original grip morph NORMAL extensions on changed topology: source POSITION deltas are zero for garment, but NORMAL deltas are not.',
            'Permit bounded float32 rounding explicitly: glTF standard floating attributes cannot losslessly store the authored float64 NPZ.',
            'Identify source C19 material/primitive ancestry explicitly; preserve original clips or declare why a diagnostic-only export omits them.',
            'Keep the separate responding_surface material adapter out of a stock-four-weight export unless explicitly integrated and independently tested.'
        ],
        'readyExportConstraints': [
            'Preserve all original C19 nodes, nineteen inverse binds and axes, protected head/glove attributes/morphs/images/PBR.',
            'Enumerate every literal nonzero dense influence; preserve it without thresholding, top-four ranking, or renormalization. Reject fifth influence.',
            'Copy existing old-row JOINTS_0/WEIGHTS_0 byte encodings when semantically unchanged; explicit cast error only on authored new rows.',
            'Export original grip targets at new vertex counts with an owner-declared extension; do not copy V7 topology-specific corrective morphs.',
            'Run handoff170 strict contract then continuous stock Three.js gate; runtime parity is not visual acceptance.'
        ],
        'limits': [
            'CPU attribute inspection and exact all-row float64 influence packing only; no new GLB, Three.js motion, render, garment, contact or mobile pass.',
            'Frozen06 is a protocol diagnostic; later UV07 remains separately owned and is not substituted.',
            'No source files changed, no GPU workload, no construction/weight repair and no normal player asset promotion.'
        ]}
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    (EVIDENCE / 'contract-report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'status': report['status'], 'vertices': sum(row['vertices'] for row in rows),
                      'missingPolicyPrimitives': len(requirements), 'maxInfluences': max(row['maxLiteralNonzeroInfluences'] for row in rows)}))

if __name__ == '__main__':
    main()
