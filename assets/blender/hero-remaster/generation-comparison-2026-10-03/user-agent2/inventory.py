"""Read-only installed-model and inherited-input audit; never imports a model."""
import argparse
import ast
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[5]
ML = Path('/Users/raynos/ml/img2mesh')
LOCALAI = Path('/Users/raynos/projects/localai')
WEIGHTS = Path('/Users/raynos/projects/weights/manual')
PREP = ROOT / 'docs/evidence/hero-remaster/generation-comparison-2026-10-03'
SESSION = '01a101fe-a358-7731-987d-4168614e9ece'


def command(args):
    result = subprocess.run(args, capture_output=True, text=True, timeout=20)
    return {'exitCode': result.returncode, 'stdout': result.stdout.strip(),
            'stderr': result.stderr.strip()}


def pin(path, digest=True):
    path = Path(path)
    item = {'path': str(path), 'exists': path.is_file()}
    if item['exists']:
        item.update(bytes=path.stat().st_size, resolved=str(path.resolve()))
        if digest:
            hasher = hashlib.sha256()
            with path.open('rb') as stream:
                for block in iter(lambda: stream.read(1024 * 1024), b''):
                    hasher.update(block)
            item['sha256'] = hasher.hexdigest()
    return item


def inherited():
    receipt = PREP / 'FINAL-R1-verification.json'
    previous = json.loads(receipt.read_text())
    rows = []
    for group in ('preparedSources', 'inputs', 'references', 'library'):
        for old in previous[group]:
            path = Path(old['path'])
            if not path.is_absolute():
                path = ROOT / path
            row = pin(path)
            row.update(group=group, expectedSHA256=old['sha256'],
                       matches=row.get('sha256') == old['sha256'])
            if group == 'preparedSources' and row['exists']:
                ast.parse(path.read_text(), filename=str(path))
                row['syntax'] = 'AST pass'
            rows.append(row)
    return {'receipt': pin(receipt), 'rows': rows,
            'allPinsMatch': all(row['matches'] for row in rows)}


def model(name, source, config, license_paths, weight_dir, runner):
    source = ML / source
    result = {'name': name, 'sourceHEAD': command(['git', '-C', str(source),
              'rev-parse', 'HEAD']), 'sourceStatus': command(['git', '-C',
              str(source), 'status', '--short']), 'config': pin(config),
              'licenses': [pin(p) for p in license_paths], 'runner': pin(runner)}
    diff = command(['git', '-C', str(source), 'diff', 'HEAD', '--'])
    result['trackedPatchNormalizedStdoutSHA256'] = hashlib.sha256(diff['stdout'].encode()).hexdigest()
    result['trackedPatchReadExitCode'] = diff['exitCode']
    python = source / '.venv/bin/python'
    result['python'] = pin(python, digest=False)
    # Metadata only: no torch/model import, MPS allocation or model loading.
    code = ('import importlib.metadata as m,json,sys; '
            'print(json.dumps({"python":sys.version,"packages":'
            '{k:m.version(k) for k in ["torch","numpy","Pillow"]}}))')
    result['runtimeMetadata'] = command([str(python), '-c', code])
    result['weightFiles'] = [pin(p, digest=False) for p in sorted(Path(weight_dir).rglob('*'))
                             if p.is_file() and p.suffix in ('.bin', '.pt', '.pth', '.safetensors')]
    result['weightsRehashed'] = False
    if Path(config).is_file() and str(config).endswith('pipeline.json'):
        args = json.loads(Path(config).read_text())['args']
        result['configuredModelFiles'] = {
            key: [pin(base + suffix, digest=False) for suffix in ('.json', '.safetensors')]
            for key, base in args['models'].items()}
        result['conditioner'] = args.get('image_cond_model')
        result['remover'] = args.get('rembg_model')
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    models = [
        model('Hunyuan3D 2.1', 'Hunyuan3D-2.1',
              WEIGHTS / 'tencent/Hunyuan3D-2.1/hunyuan3d-dit-v2-1/config.yaml',
              [ML / 'Hunyuan3D-2.1/LICENSE', ML / 'Hunyuan3D-2.1/Notice.txt',
               WEIGHTS / 'tencent/Hunyuan3D-2.1/LICENSE'],
              WEIGHTS / 'tencent/Hunyuan3D-2.1',
              ROOT / 'assets/blender/hero-remaster/generation-comparison-2026-10-03/hunyuan_shape.py'),
        model('TRELLIS.2', 'trellis-mac', ML / 'trellis-view/pipeline.json',
              [ML / 'trellis-mac/LICENSE'], WEIGHTS / 'microsoft/TRELLIS.2-4B',
              LOCALAI / 'bin/img2mesh/trellis_batch.py'),
        model('Pixal3D', 'Pixal3D-mac', ML / 'pixal-view/pipeline.json',
              [ML / 'Pixal3D-mac/LICENSE'], WEIGHTS / 'TencentARC/Pixal3D',
              ML / 'Pixal3D-mac/generate_mps.py'),
    ]
    process = command(['ps', '-axo', 'pid,ppid,etime,rss,comm'])
    process['stdout'] = '\n'.join(line for line in process['stdout'].splitlines()
                                  if any(word in line.lower() for word in
                                         ('lockf', 'blender', 'hunyuan', 'pixal', 'trellis')))
    record = {'schemaVersion': 1, 'session': SESSION,
              'verifiedAtUTC': datetime.now(timezone.utc).isoformat(),
              'accepted': False, 'inferenceExecuted': False, 'ownedHeavyJobs': [],
              'modelLeaseHeld': False, 'head': command(['git', 'rev-parse', 'HEAD']),
              'attribution': command(['node', '.githooks/resolve-attribution.mjs']),
              'effectiveSuppliedContext': {'filesystem': 'danger-full-access',
                                          'network': 'enabled', 'approval': 'never'},
              'inherited': inherited(), 'models': models,
              'resources': {'memory': command(['bash', str(LOCALAI / 'bin/mem-gb.sh')]),
                            'lockHolder': command(['lsof', str(LOCALAI / '.model.lock')]),
                            'processes': process},
              'limits': ['Inventory proves bytes/presence, not model execution or fit.',
                         'Large checkpoint content hashes not recomputed; sizes and symlink targets recorded.',
                         'No qualified new fitting contract received; historical inputs remain unaccepted.',
                         'Resource snapshot is not a future launch clearance.']}
    output = Path(args.out)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(record, indent=2) + '\n')
    print(json.dumps({'out': str(output), 'pins': len(record['inherited']['rows']),
                      'allPinsMatch': record['inherited']['allPinsMatch'],
                      'modelWeightFiles': {m['name']: len(m['weightFiles']) for m in models}}))
    return 0 if record['inherited']['allPinsMatch'] else 1


if __name__ == '__main__':
    sys.exit(main())
