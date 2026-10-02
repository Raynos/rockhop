"""CPU-only readiness capture. Never imports Torch or dispatches model work."""
import ast
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import time

R = Path('/Users/raynos/projects/games/rockhop')
A = R / 'assets/blender/hero-remaster/rider/one-rider-v2/tpose-readiness203'
E = R / 'docs/evidence/hero-remaster/one-rider-v2/tpose-readiness203'
S = Path('/Users/raynos/ml/img2mesh/Hunyuan3D-2.1')
OLD = Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/hunyuan21/04')
TEAM = Path('/Users/raynos/Documents/Codex/2026-10-01/task-3/hoodie-repair02')


def pin(path):
    h = hashlib.sha256()
    with path.open('rb') as handle:
        for chunk in iter(lambda: handle.read(4 * 1024 * 1024), b''):
            h.update(chunk)
    return {'bytes': path.stat().st_size, 'sha256': h.hexdigest()}


def main():
    started = time.monotonic()
    assert not (E / 'freeze.json').exists(), 'Preserve frozen readiness'
    installed = Path('/Users/raynos/projects/localai/bin/img2mesh/rockhop_hunyuan21_runner.py')
    tree = ast.parse(installed.read_text())
    flags = [argument.value for node in ast.walk(tree)
             if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
             and node.func.attr == 'add_argument' for argument in node.args
             if isinstance(argument, ast.Constant) and isinstance(argument.value, str)]
    assert '--shape-only' not in flags and '--shape_only' not in flags
    old = json.loads((OLD / 'generation.json').read_text())
    assert old['version'] == 'Hunyuan3D-2.1' and old['shape_steps'] == 30 and old['octree'] == 380
    qa_path = TEAM / 'qa-lane/results/v7-export-motion-manifest-gate.json'
    qa = json.loads(qa_path.read_text())
    actual = [row for row in qa['rows'] if row['probe'] == 'actual_export_stand_to_sit']
    computational = sorted((S / 'hy3dshape/hy3dshape').rglob('*.py'))
    weights = Path('/Users/raynos/projects/weights/manual/tencent/Hunyuan3D-2.1')
    computational.extend(sorted((weights / 'hunyuan3d-dit-v2-1').glob('*')))
    computational.extend(sorted((weights / 'hunyuan3d-vae-v2-1').glob('*')))
    computational.append(S / '.venv/pyvenv.cfg')
    site = S / '.venv/lib/python3.11/site-packages'
    metadata = []
    for package in ('torch', 'numpy', 'trimesh', 'pillow', 'torchvision'):
        paths = sorted(site.glob(f'{package}-*.dist-info/METADATA'))
        assert len(paths) == 1
        computational.extend(paths)
        version = next(line.split(': ', 1)[1] for line in paths[0].read_text().splitlines() if line.startswith('Version: '))
        metadata.append({'package': package, 'version': version})
    inputs = [installed, Path('/Users/raynos/projects/localai/bin/img2mesh/rockhop-hunyuan21.sh'),
              OLD / 'generation.json', OLD / 'start-settings.json', OLD / 'raw-shape.npz',
              TEAM / 'v7-export.json', TEAM / 'qa-lane/README.md', qa_path,
              R / 'docs/evidence/hero-remaster/one-rider-v2/independent-pipeline-learnings-2026-10-01/README.md']
    report = {'status': 'CPU_READINESS_ONLY_UNEXECUTED_MODEL_WORKER',
              'modelWorkloadsRun': 0, 'GPUUsed': False, 'accepted': False,
              'installedRunnerFlags': flags, 'installedShapeOnlySupported': False,
              'newWorkerNeeded': True,
              'python': str(S / '.venv/bin/python'), 'sourceRoot': str(S),
              'sourceHEAD': subprocess.check_output(['git', '-C', str(S), 'rev-parse', 'HEAD'], text=True).strip(),
              'sourceDirty': subprocess.check_output(['git', '-C', str(S), 'status', '--short'], text=True),
              'packagesMetadataOnly': metadata,
              'retained04': {key: old[key] for key in ['version', 'runnerSHA256', 'source_commit', 'weights_revision', 'seed', 'shape_steps', 'octree', 'shape_seconds', 'raw_faces', 'nativeSHA256', 'wall_seconds', 'peak_rss_gb']},
              'nativeDefinitionDifference': 'Source04 raw is before explicit cleanup/reducer but after official Trimesh default processing. Proposed worker saves Latent2MeshOutput first.',
              'structuralHypothesis': 'Horizontal T-pose exposes separate sleeves/underarms to image-conditioned reconstruction; no guarantee of topology or anatomy.',
              'preserveLikedHead': 'A newly reconstructed body must keep the approved existing new head; generated reference head is not a silent replacement.',
              'teamInspection': {'qaRows': len(qa['rows']), 'actualTransitionRows': len(actual),
                                 'actualTransitionUpperCrossingsMaximum': max(row['regions']['shoulder_underarm']['strict_transverse_crossings'] for row in actual),
                                 'actualTransitionHipCrossingsRange': [min(row['regions']['hip']['strict_transverse_crossings'] for row in actual), max(row['regions']['hip']['strict_transverse_crossings'] for row in actual)],
                                 'actualTransitionMinimumSaddleVertexGapMM': min(row['seat']['projected_skin_vertex_min_vertical_gap_mm'] for row in actual),
                                 'broaderUpperFailureRows': sum(row['regions']['shoulder_underarm']['gate'] == 'FAIL' for row in qa['rows'] if row['probe'] != 'actual_export_stand_to_sit'),
                                 'conclusion': 'V7 is finite baked motion evidence, not a qualified general armhole or rig. New T-pose source does not duplicate their repair job.'},
              'bounds': {'lock': '/Users/raynos/projects/localai/.model.lock', 'lockMethod': 'lockf -k',
                         'anonymousLimitBytes': 70_000_000_000, 'memoryPollSeconds': 1,
                         'terminateAtSeconds': 1790, 'batchLimitSeconds': 1800,
                         'includesSamplingAndNativeExports': True, 'queueOutsideBatch': True,
                         'eviction': False, 'killOnlyOwnedWorkerProcessGroup': True},
              'limits': ['Model worker, MPS adaptation and new native-output route have not been run.',
                         'One-second anonymous-memory sampling is an observed stop rule, not a hard OS memory cap.',
                         'Package metadata pins are not complete environment file hashes.',
                         'No new T-pose reference exists in this readiness capture; parent freezes its exact SHA before generation.',
                         'No appearance, clothing, rig, continuous pose, contact, game or mobile acceptance.']}
    for script in A.glob('*.py'):
        compile(script.read_text(), str(script), 'exec')
    report['syntaxChecks'] = {'pythonFilesCompiledWithoutExecution': len(list(A.glob('*.py'))), 'passed': True}
    report['elapsedSeconds'] = time.monotonic() - started
    (E / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    computational_pins = {str(p): pin(p) for p in computational if p.is_file()}
    input_pins = {str(p): pin(p) for p in inputs}
    owned = [p for p in A.iterdir() if p.is_file()] + [p for p in E.iterdir() if p.is_file()]
    frozen = {'status': 'READINESS_NOT_GENERATION', 'computationalInputs': computational_pins,
              'inputPins': input_pins, 'ownedFiles': {str(p): pin(p) for p in owned},
              'GPUUsed': False, 'modelWorkloadsRun': 0, 'workerExecuted': False}
    (E / 'freeze.json').write_text(json.dumps(frozen, indent=2) + '\n')
    print(json.dumps({'report': str(E / 'report.json'), 'computationalPins': len(computational_pins),
                      'inputPins': len(input_pins), 'ownedPins': len(owned), 'GPUUsed': False}))


if __name__ == '__main__':
    main()
