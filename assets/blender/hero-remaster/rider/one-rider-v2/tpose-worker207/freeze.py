"""Freeze the diagnostic-only correction without executing the model worker."""
import ast
import difflib
import hashlib
import json
from pathlib import Path
import subprocess

R = Path('/Users/raynos/projects/games/rockhop')
A = R / 'assets/blender/hero-remaster/rider/one-rider-v2/tpose-worker207'
E = R / 'docs/evidence/hero-remaster/one-rider-v2/tpose-worker207'
OLD_A = A.with_name('tpose-readiness203')
OLD_E = E.with_name('tpose-readiness203')
PRIVATE = Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2')
REFERENCE = R / 'assets/design/hero-remaster/one-rider-v2/tpose-construction-target204/reference.png'
REFERENCE_SHA = 'ee2c96a4f70bc6aa7c360a5c563479ce15bbfb381ff6001955d9d5c633dab024'
CPU = '/Users/raynos/projects/localai/runtime/unimate/.venv/bin/python'


def pin(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as handle:
        for chunk in iter(lambda: handle.read(4194304), b''):
            h.update(chunk)
    return {'bytes': Path(path).stat().st_size, 'sha256': h.hexdigest()}


def generation_ast(path):
    tree = ast.parse(path.read_text())
    main = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'main')
    nodes = [node for node in main.body if isinstance(node, ast.Assign)
             and any(isinstance(target, ast.Name) and target.id in ('pipeline', 'decoded') for target in node.targets)]
    nodes += [node for node in main.body if isinstance(node, ast.Expr)
              and isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Attribute)
              and node.value.func.attr == 'enable_flashvdm']
    assert len(nodes) == 3
    return ast.dump(ast.Module(body=nodes, type_ignores=[]), include_attributes=False)


def main():
    assert not (E / 'freeze.json').exists(), 'Preserve frozen207'
    old = json.loads((OLD_E / 'freeze.json').read_text())
    for group in ('computationalInputs', 'inputPins', 'ownedFiles'):
        for path, expected in old[group].items():
            assert pin(path) == expected, f'Frozen203 changed: {path}'
    assert pin(REFERENCE)['sha256'] == REFERENCE_SHA
    assert (OLD_A / 'run_bounded.py').read_bytes() == (A / 'run_bounded.py').read_bytes()
    original_ast = generation_ast(OLD_A / 'shape_only_worker.py')
    assert original_ast == generation_ast(A / 'shape_only_worker.py')
    diff = ''.join(difflib.unified_diff((OLD_A / 'shape_only_worker.py').read_text().splitlines(True),
                                      (A / 'shape_only_worker.py').read_text().splitlines(True),
                                      fromfile=str(OLD_A / 'shape_only_worker.py'),
                                      tofile=str(A / 'shape_only_worker.py')))
    (E / 'preservation-only.diff').write_text(diff)
    fixtures = json.loads((E / 'cpu-fixtures.json').read_text())
    assert len(fixtures['fixtures']) == 7 and not fixtures['GPUUsed']
    output = PRIVATE / 'tpose-shape207-01'
    assert not output.exists()
    command = [CPU, '-u', str(A / 'run_bounded.py'), '--image', str(REFERENCE),
               '--image-sha256', REFERENCE_SHA, '--out', str(output), '--seed', '42']
    preflight = subprocess.run([*command, '--preflight'], capture_output=True, text=True)
    assert preflight.returncode == 0, preflight.stderr
    preflight_receipt = json.loads(preflight.stdout)
    assert preflight_receipt['command'][2] == str(A / 'shape_only_worker.py')
    assert not output.exists()
    (E / 'preflight.json').write_text(json.dumps(preflight_receipt, indent=2) + '\n')
    source206 = [PRIVATE / 'tpose-shape206-01/start-settings.json',
                 PRIVATE / 'tpose-shape206-01-process.json', PRIVATE / 'tpose-shape206-01-process.log']
    report = {'status': 'DIAGNOSTIC_PRESERVATION_CORRECTION_READY_UNEXECUTED',
              'GPUUsed': False, 'modelWorkloadsRun': 0, 'accepted': False,
              'reference': str(REFERENCE), 'referenceSHA256': REFERENCE_SHA,
              'output': str(output), 'command': command,
              'source206': {str(p): pin(p) for p in source206},
              'unchangedInferenceAST': True, 'inferenceASTSHA256': hashlib.sha256(original_ast.encode()).hexdigest(),
              'controllerByteIdenticalTo203': True,
              'controllerWorkerResolution': 'Path(__file__).with_name(shape_only_worker.py) resolves the207 sibling',
              'parameters': {'version': 'Hunyuan3D-2.1', 'seed': 42, 'shapeSteps': 30,
                             'octree': 380, 'numChunks': 200000, 'guidanceScale': 5.0,
                             'device': 'mps', 'flashVDM': 'mc', 'outputType': 'mesh'},
              'changes': ['New207 freeze/recipe paths', 'Save untouched numeric native NPZ before finite/index/shape validation',
                          'Record all invalid element/row IDs and values before refusing display export',
                          'Retain a generation receipt on validation rejection'],
              'fixtures': {'count': 7, 'preservedExactDtypeValues': True, 'GPUUsed': False},
              'limits': ['Not a geometry repair or model-setting change', 'Same-settings actual diagnostic rerun not executed here',
                         'Non-real/object decoder values refuse as unsupported API arrays; no silent coercion',
                         'No reference, liked head, production rider, current comparisons or installed environment changed']}
    (E / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    inputs = dict(old['inputPins'])
    for path in [OLD_E / 'freeze.json', OLD_A / 'shape_only_worker.py', OLD_A / 'run_bounded.py', REFERENCE, *source206]:
        inputs[str(path)] = pin(path)
    owned = [p for p in A.rglob('*') if p.is_file()] + [p for p in E.rglob('*') if p.is_file()
             and not p.name.startswith('parent-') and p.name not in ('freeze.json', 'initial-freeze-including-parent-receipt.json')]
    frozen = {'status': 'DIAGNOSTIC_RECIPE_FROZEN_NO_MODEL_RUN', 'computationalInputs': old['computationalInputs'],
              'inputPins': inputs, 'ownedFiles': {str(p): pin(p) for p in owned},
              'GPUUsed': False, 'modelWorkloadsRun': 0, 'referenceSHA256': REFERENCE_SHA,
              'samplingChanges': False, 'preservationDiagnosticsOnly': True}
    (E / 'freeze.json').write_text(json.dumps(frozen, indent=2) + '\n')
    print(json.dumps({'status': report['status'], 'freezeSHA256': pin(E / 'freeze.json')['sha256'],
                      'computationalPins': len(frozen['computationalInputs']), 'inputPins': len(inputs),
                      'ownedPins': len(owned), 'unchangedInferenceAST': True, 'controllerByteIdentical': True}))


if __name__ == '__main__':
    main()
