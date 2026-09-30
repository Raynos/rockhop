"""One approved Pixal bust; shared lock covers sampling and native export.

Queue time is outside the 30-minute batch. Sources stay untouched. The saved
NPZ is written by the installed worker before asset_to_glb processes the mesh.
"""
import argparse
import hashlib
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[5]
LOCALAI = Path('/Users/raynos/projects/localai')
PORT = Path('/Users/raynos/ml/img2mesh/Pixal3D-mac')
PYTHON = PORT / '.venv/bin/python'
WEIGHTS = Path('/Users/raynos/projects/weights')
OUT = LOCALAI / 'runtime/rockhop-rider-search-v1/one-rider-v2/buzz-bust-01'
REFERENCE = REPO / 'assets/design/hero-remaster/one-rider-v2/head/buzz-bust-reference.png'
SOURCES = [PORT / 'generate_mps.py', PORT / 'pixal3d/pipelines/rembg/BiRefNet.py',
           PORT / 'pixal3d/trainers/flow_matching/mixins/image_conditioned_proj.py',
           Path('/Users/raynos/ml/img2mesh/pixal-view/pipeline.json'), REFERENCE,
           Path(__file__), Path(__file__).with_name('pixal_cache_worker.py')]


def hashes():
    return {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in SOURCES}


def memory():
    values = subprocess.check_output(['bash', str(LOCALAI / 'bin/mem-gb.sh')], text=True)
    return dict(zip(['anonymousGiB', 'wiredGiB', 'freeGiB'], map(float, values.split())))


def stop(process):
    os.killpg(process.pid, signal.SIGTERM)
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        os.killpg(process.pid, signal.SIGKILL)
        process.wait()


def worker(attempt):
    global OUT
    if attempt == 2:
        OUT = OUT.with_name('buzz-bust-02')
    OUT.mkdir(parents=True, exist_ok=True)
    assert not (OUT / 'generation.json').exists(), 'Use a fresh numbered experiment'
    before = hashes()
    env = os.environ.copy()
    env.update({
        'PIXAL3D_MPS_ROOT': str(PORT),
        'PIXAL3D_DINO_PATH': str(WEIGHTS / 'manual/facebook/dinov3-vitl16-pretrain-lvd1689m'),
        'PIXAL3D_MOGE_PATH': str(WEIGHTS / 'manual/Ruicheng/moge-2-vitl/model.pt'),
        'PIXAL3D_NAF_ROOT': '/Users/raynos/ml/img2mesh/NAF',
        'PIXAL3D_NAF_WEIGHTS': str(WEIGHTS / 'manual/valeoai/NAF/naf_release.pth'),
        'O_VOXEL_PYTHON': str(PYTHON),
        'TORCH_HOME': str(WEIGHTS / 'store/pixal3d-torch'),
        'HF_HUB_OFFLINE': '1', 'TRANSFORMERS_OFFLINE': '1',
        'PYTORCH_ENABLE_MPS_FALLBACK': '1', 'SPARSE_ATTN_BACKEND': 'naive',
    })
    entry = str(Path(__file__).with_name('pixal_cache_worker.py')) if attempt == 2 else 'generate_mps.py'
    command = [str(PYTHON), '-u', entry, str(REFERENCE),
               '--device', 'mps', '--model-path', '/Users/raynos/ml/img2mesh/pixal-view',
               '--pipeline-type', '1024_cascade', '--steps', '24', '--seed', '42',
               '--texture-size', '1024' if attempt == 2 else '2048', '--native-decimation-target', '100000',
               '--save-mesh', str(OUT / 'raw.npz'), '--output', str(OUT / 'bust.glb')]
    record = {'status': 'started', 'accepted': False, 'command': command,
              'lock': str(LOCALAI / '.model.lock'), 'lockMethod': 'lockf -k',
              'batchLimitSeconds': 1800, 'anonymousLimitGiB': 70,
              'stopAtAnonymousGiB': 65 if attempt == 2 else 70,
              'memoryPollSeconds': 1 if attempt == 2 else 10, 'attempt': attempt,
              'adaptation': 'installed stage cache hooks + predecode latent/shape checkpoints; export atlas1024' if attempt == 2 else 'installed CLI unchanged',
              'sourceHashesBefore': before, 'memorySamples': [],
              'sourceHEAD': subprocess.check_output(['git', '-C', str(PORT), 'rev-parse', 'HEAD'], text=True).strip(),
              'sourceDirty': subprocess.check_output(['git', '-C', str(PORT), 'status', '--short'], text=True),
              'decodedShape': 'raw.npz before installed asset_to_glb cleanup/remesh/decimation'}
    report = OUT / 'generation.json'
    started = time.monotonic()
    first = memory()
    record['memorySamples'].append({'seconds': 0, **first})
    report.write_text(json.dumps(record, indent=2) + '\n')
    if first['anonymousGiB'] >= 70:
        record['status'] = 'memory gate refused; no sampling or eviction'
        report.write_text(json.dumps(record, indent=2) + '\n')
        return 75
    with (OUT / 'generation.log').open('w') as log:
        process = subprocess.Popen(command, cwd=PORT, env=env, stdout=log,
                                   stderr=subprocess.STDOUT, start_new_session=True)
        deadline = started + 1790  # Reserve termination time inside 30 minutes.
        while process.poll() is None:
            sample = {'seconds': round(time.monotonic() - started, 2), **memory()}
            record['memorySamples'].append(sample)
            if sample['anonymousGiB'] >= record['stopAtAnonymousGiB'] or time.monotonic() >= deadline:
                record['status'] = 'stopped at memory/time bound; retained partial evidence'
                stop(process)
                break
            report.write_text(json.dumps(record, indent=2) + '\n')
            try:
                process.wait(timeout=record['memoryPollSeconds'])
            except subprocess.TimeoutExpired:
                pass
        record['exitCode'] = process.returncode
    record['elapsedSeconds'] = round(time.monotonic() - started, 3)
    record['sourceHashesAfter'] = hashes()
    record['sourceUnchanged'] = before == record['sourceHashesAfter']
    record['outputs'] = {p.name: {'bytes': p.stat().st_size,
                         'sha256': hashlib.file_digest(p.open('rb'), 'sha256').hexdigest()}
                         for p in [OUT / 'raw.npz', OUT / 'bust.glb', OUT / 'sampled-latents.pt',
                                   OUT / 'decoded-shape-0.npz'] if p.exists()}
    if record['status'] == 'started':
        record['status'] = 'generated; visual/geometry review pending' if process.returncode == 0 else 'worker failed'
    report.write_text(json.dumps(record, indent=2) + '\n')
    print(json.dumps({k: record[k] for k in ['status', 'elapsedSeconds', 'exitCode', 'sourceUnchanged']}), flush=True)
    return process.returncode or (0 if record['sourceUnchanged'] else 1)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--worker', action='store_true')
    parser.add_argument('--preflight', action='store_true')
    parser.add_argument('--attempt', type=int, choices=[1, 2], default=1)
    args = parser.parse_args()
    if args.preflight:
        assert PYTHON.exists() and all(p.exists() for p in SOURCES)
        print(json.dumps({'sourceHashes': hashes(), 'output': str(OUT), 'memory': memory()}, indent=2))
    elif args.worker:
        sys.exit(worker(args.attempt))
    else:
        os.execvp('lockf', ['lockf', '-k', str(LOCALAI / '.model.lock'),
                            str(PYTHON), '-u', str(Path(__file__).resolve()), '--worker',
                            '--attempt', str(args.attempt)])
