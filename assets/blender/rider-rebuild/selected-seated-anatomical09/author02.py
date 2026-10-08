"""Parent CPU2 only: stable named supports, unchanged selection and brush.

Reuses author01's source protection, saved native actions and reopen checks.
No posed sculpt, old corrective, GLB export, or normal-player promotion.
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import author as base
from support_brush02 import COALESCE, smooth_rows

PROOF = 'docs/evidence/rider-rebuild/selected-seated-anatomical09/support-equivalence02.json'
PROOF_SHA = 'a185ab8fdc04c5a67e9f10b659be552a6d8428513996631204a5133011cc449b'


def pruning_proof(out, report):
    np, bpy = base.np, base.bpy
    rig = bpy.data.objects['RiderSkeleton']; obj = bpy.data.objects['RiderJeans']
    positions = base.xyz(obj.data.vertices)
    edits = {r['nativeID']: r for r in json.loads((out/'authored-weight-rows.json').read_text())}
    selected = sorted(edits); final = base.named_weights(obj, rig)
    full = [edits[i]['fullAuthored'] if i in edits else row for i, row in enumerate(final)]
    edges = [tuple(e.vertices) for e in obj.data.edges if set(e.vertices) & edits.keys()]
    edge_a, edge_b = np.asarray(edges, dtype=np.int32).T
    inverse = {b.name: b.matrix_local.inverted() for b in rig.data.bones}
    names = sorted({n for row in full for n in row})
    required = sorted(set(selected) | set(edge_a) | set(edge_b))

    def deform(rows):
        points = positions.astype(np.float64).copy()
        matrices = {n: np.asarray(rig.pose.bones[n].matrix @ inverse[n], dtype=np.float64) for n in names}
        for i in required:
            p = np.append(positions[i], 1.)
            points[i] = sum((matrices[n] @ p)[:3]*w for n, w in rows[i].items())
        return points

    samples = []
    for bike, pin in report['diagnosticPoses'].items():
        receipt = json.loads((base.ROOT/pin['path']).read_text()); targets = base.pose_targets(receipt, rig)
        for kind in ['rejected-key', 'diagnostic-L-thigh-subtree-rest', 'diagnostic-R-thigh-subtree-rest']:
            base.reset_pose(rig); base.set_target_pose(rig, targets)
            if 'subtree' in kind:
                side = kind.split('-')[1]; root = rig.pose.bones['DEF-thigh.'+side]
                for bone in [root, *root.children_recursive]: bone.matrix_basis = base.Matrix.Identity(4)
                bpy.context.view_layer.update()
            a, b = deform(full), deform(final); displacement = b-a
            distance = np.linalg.norm(displacement, axis=1)
            jumps = np.linalg.norm(displacement[edge_a]-displacement[edge_b], axis=1)
            native = base.evaluated_positions(obj)
            native_residual = float(np.max(np.linalg.norm(native[required]-b[required], axis=1)))
            assert native_residual < .000002, ('FOUR CPU/native mismatch', bike, kind, native_residual)
            maximum = float(np.max(distance[selected])); assert maximum <= .0001, ('Final cutoff destabilizes deformation', maximum)
            samples.append({'bike': bike, 'pose': kind, 'artPose': False,
                'maximumDisplacementM': maximum, 'p95DisplacementM': float(np.percentile(distance[selected], 95)),
                'maximumNeighborJumpM': float(np.max(jumps)), 'p95NeighborJumpM': float(np.percentile(jumps, 95)),
                'savedFourNativeResidualM': native_residual,
                'worstVertices': [{'nativeID': i, 'displacementM': float(distance[i]),
                    'fullAuthored': full[i], 'savedFour': final[i]} for i in sorted(selected, key=lambda i: -distance[i])[:12]],
                'worstEdges': [{'nativeIDs': list(edges[j]), 'displacementJumpM': float(jumps[j]),
                    'fullEdgeM': float(np.linalg.norm(a[edges[j][0]]-a[edges[j][1]])),
                    'fourEdgeM': float(np.linalg.norm(b[edges[j][0]]-b[edges[j][1]])),
                    'fullSupportAtEndpoints': [sorted(full[i]) for i in edges[j]],
                    'savedSupportAtEndpoints': [sorted(final[i]) for i in edges[j]],
                    'cutoffRemovedAtEndpoints': [sorted(set(full[i])-set(final[i])) for i in edges[j]]}
                    for j in np.argsort(-jumps)[:12]]})
    base.reset_pose(rig)
    return {'scope': 'Actual reopened native matrices; both rejected bike keys and each unilateral thigh-rest diagnostic. Native polygon edges, not exporter diagonals.',
        'editedVertexCount': len(selected), 'incidentNativeEdgeCount': len(edges), 'rankRemovedMass': 0,
        'maximumPreCutoffSupportCount': max(map(len, (full[i] for i in selected))),
        'positiveSupportPalettes': sorted({tuple(sorted(full[i])) for i in selected}),
        'toleranceM': .0001, 'samples': samples}


def main():
    assert base.sha(HERE/'author.py') == 'a862eab5ecc2cd0065fa2d9ca98b7a6d80e2cd94a11800b17364ae3749cca585'
    assert base.sha(base.ROOT/PROOF) == PROOF_SHA
    proof = json.loads((base.ROOT/PROOF).read_text())
    assert proof['status'] == 'FINITE_SUPPORT_EQUIVALENCE_PASS' and proof['coalesce'] == COALESCE
    for filename, digest in proof['sourcePins'].items(): assert base.sha(base.ROOT/filename) == digest
    base.smooth_rows = smooth_rows
    base.main()
    out = Path(sys.argv[sys.argv.index('--')+1]).resolve()
    report = json.loads((out/'receipt.json').read_text())
    native_proof = pruning_proof(out, report)
    (out/'four-pruning-native.json').write_text(json.dumps(native_proof, indent=2)+'\n')
    report['baseRecipeSHA256'] = report['recipeSHA256']; report['recipeSHA256'] = base.sha(__file__)
    report['weightBrushSHA256'] = base.sha(HERE/'support_brush02.py')
    report['supportCorrection'] = {'kind': 'named-motion-equivalent-anatomical-supports', 'coalesce': COALESCE,
        'supportEquivalence': {'path': PROOF, 'sha256': PROOF_SHA},
        'maximumMeasuredOperatorDifferenceM': proof['maximumM'],
        'rankPruning': False, 'cutoffOnly': .0001, 'brushAndSelectionUnchanged': True,
        'preservedContext': ['DEF-spine.001 at waistband', 'ipsilateral shin at lower boundary', 'bilateral thighs through crotch'],
        'futureMotion': proof['requiredFutureEnvelope'],
        'nativePruningProof': {'path': str((out/'four-pruning-native.json').relative_to(base.ROOT)), 'sha256': base.sha(out/'four-pruning-native.json')}}
    report['limits'].append('Named support equivalence covers the declared finite samples only. Motion11 qualification and posed anatomy remain pending.')
    (out/'receipt.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({'supportCorrection': report['supportCorrection'], 'nativePruning': [
        {k: v for k, v in s.items() if not k.startswith('worst')} for s in native_proof['samples']]}), flush=True)


if __name__ == '__main__': main()
