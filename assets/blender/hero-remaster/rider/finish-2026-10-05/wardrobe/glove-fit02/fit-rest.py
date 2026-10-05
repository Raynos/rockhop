"""One ambient Gaussian flow; anatomical distal controls, no skin or bone edits."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def unit(vector):
    return vector / np.linalg.norm(vector)


def frame(radial, distal):
    y = unit(distal)
    x = unit(radial - y * (radial * y).sum())
    return np.stack([x, y, np.cross(x, y)], axis=1)


def kernel(points, centers, sigma):
    delta = points[:, None, :] - centers[None, :, :]
    return np.exp(-(delta * delta).sum(2) / (2 * sigma * sigma))


def main():
    parser = argparse.ArgumentParser()
    for key in ['source', 'classification', 'semantics', 'foundation', 'out', 'evidence']:
        parser.add_argument('--' + key, required=True)
    args = parser.parse_args()
    out = Path(args.out)
    assert not out.exists()
    out.mkdir(parents=True)
    evidence = Path(args.evidence)
    evidence.mkdir(parents=True, exist_ok=True)
    source = np.load(args.source)
    classification = json.loads(Path(args.classification).read_text())
    assert sha(args.source) == classification['output']['sha256']
    semantics = json.loads(Path(args.semantics).read_text())['gloves']
    foundation = np.load(args.foundation)
    names = foundation['boneNames'].tolist()
    rest = foundation['boneRest'].astype(float)
    digits = ['pinky', 'ring', 'middle', 'index', 'thumb']
    source_controls = np.concatenate([np.array(classification['digits'][name]['sectionCenters']) for name in digits])
    target_controls = np.concatenate([np.array(semantics['targetNamedChains']['R'][name]['canonicalKnotsMeters']) for name in digits])
    # Same right-side own-rest chains; source controls remain geometric hypotheses.
    for index, name in enumerate(digits):
        for joint in range(3):
            assert np.array_equal(target_controls[index * 4 + joint].astype(np.float32), rest[names.index(f'{name}_{joint + 1:02}.R'), :3, 3].astype(np.float32))
        target_controls[index * 4 + 3] += .002 * unit(target_controls[index * 4 + 3] - target_controls[index * 4 + 2])
    source_wrist = np.array(semantics['coarsePalmRegistration']['R']['sourceWristCentre'])
    target_wrist = rest[names.index('hand.R'), :3, 3]
    source_frame = frame(source_controls[12] - source_controls[0], source_controls[8] - source_wrist)
    target_frame = frame(target_controls[12] - target_controls[0], target_controls[8] - target_wrist)
    width = np.linalg.norm(target_controls[12] - target_controls[0]) / np.linalg.norm(source_controls[12] - source_controls[0]) * 1.1
    length = np.linalg.norm(target_controls[8] - target_wrist) / np.linalg.norm(source_controls[8] - source_wrist)
    scales = np.array([width, length, width])
    matrix = (target_frame * scales[None, :]) @ source_frame.T
    initial = (source['vertices'] - source_wrist) @ matrix.T + target_wrist
    current = np.vstack([initial, (source_controls - source_wrist) @ matrix.T + target_wrist, target_wrist[None, :]])
    start = len(initial)
    target = np.vstack([target_controls, target_wrist])
    sigma = .022
    frames = [initial.copy()]
    step_rows = []
    # Refit one continuous ambient field, never per-vertex/digit blends.
    for iteration in range(600):
        controls = current[start:]
        error = target - controls
        maximum_error = float(np.linalg.norm(error, axis=1).max())
        if maximum_error < .00015:
            break
        coefficients = np.linalg.solve(kernel(controls, controls, sigma) + np.eye(len(controls)) * 1e-7, error)
        # ||grad v||_2 <= sum_i ||c_i|| exp(-1/2)/sigma globally.
        # Euler F(x)=x+h*v(x) is injective when h*L<1.
        bound = float(np.linalg.norm(coefficients, axis=1).sum() * np.exp(-.5) / sigma)
        h = min(.30, .18 / max(bound, 1e-12))
        velocity = kernel(current, controls, sigma) @ coefficients
        current += h * velocity
        assert np.isfinite(current).all() and h * bound <= .180000001
        step_rows.append({'iteration': iteration, 'maxControlErrorM': maximum_error, 'globalVelocityLipschitzBound': bound, 'step': h, 'stepLipschitzProduct': h * bound})
        if iteration % 16 == 0:
            frames.append(current[:start].copy())
    frames.append(current[:start].copy())
    fitted = current[:start]
    remainder = float(np.linalg.norm(target - current[start:], axis=1).max())
    mirror = fitted.copy()
    mirror[:, 1] *= -1
    for side, vertices, faces in [('R', fitted, source['faces']), ('L', mirror, source['faces'][:, ::-1])]:
        np.savez_compressed(out / f'glove-{side}.npz', vertices=vertices, faces=faces, uv=source['uv'], sourceXYZ=source['vertices'], sourceFaces=source['faces'], branchLabels=source['branchLabels'], originalTriangleRows=source['originalTriangleRows'], barycentric=source['barycentric'], boneNames=foundation['boneNames'], boneRest=foundation['boneRest'])
    np.savez_compressed(out / 'flow.npz', positions=np.array(frames, np.float32), faces=source['faces'], branchLabels=source['branchLabels'], sourceXYZ=source['vertices'], times=np.linspace(0, 3, len(frames)))
    report = {'accepted': False, 'status': 'CONNECTED_AMBIENT_REST_FLOW_CHECKPOINT_UNACCEPTED', 'recipeSHA256': sha(__file__),
              'source': {'path': args.source, 'sha256': sha(args.source)}, 'foundation': {'path': args.foundation, 'sha256': sha(args.foundation)},
              'properInitialMatrix': matrix.tolist(), 'initialDeterminant': float(np.linalg.det(matrix)), 'sourceGeometricFrame': source_frame.tolist(), 'targetGeometricFrame': target_frame.tolist(),
              'scales': scales.tolist(), 'gaussianSigmaM': sigma, 'steps': step_rows, 'maxControlResidualM': remainder,
              'sourceControls': source_controls.tolist(), 'targetControls': target.tolist(), 'finalControls': current[start:].tolist(),
              'mirrorPolicy': 'Exact native Y reflection of fitted R; reverse triangle winding; no L bone-roll warp.',
              'candidates': {side: {'path': str(out / f'glove-{side}.npz'), 'sha256': sha(out / f'glove-{side}.npz')} for side in ['R', 'L']},
              'flow': {'path': str(out / 'flow.npz'), 'sha256': sha(out / 'flow.npz'), 'frames': len(frames)},
              'limits': ['Ambient Euler-step Lipschitz bound certifies injectivity of the smooth maps, not of linearly retessellated triangles or source solid occupancy.',
                         'Finite triangle self/body checks and parent played geometry review required before skin.',
                         'Source distal stations and palm geometry remain hypotheses; no cavity clearance, skin, native/engine, source handedness, PBR bake, device or art approval.']}
    (evidence / 'fit.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'steps': len(step_rows), 'frames': len(frames), 'maxControlResidualM': remainder, 'maxStepLipschitzProduct': max(row['stepLipschitzProduct'] for row in step_rows)}))


if __name__ == '__main__':
    main()
