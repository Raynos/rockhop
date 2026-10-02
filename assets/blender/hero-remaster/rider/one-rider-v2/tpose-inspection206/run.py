"""Bounded CPU-only renderer launcher; source must exist before invocation."""
import argparse
import hashlib
import json
import os
import re
import signal
import subprocess
import time
from pathlib import Path

ROOT = Path('/Users/raynos/projects/games/rockhop')
PRIVATE = Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/tpose-inspection206')
EVIDENCE = ROOT / 'docs/evidence/hero-remaster/one-rider-v2/tpose-inspection206'
RECIPE = Path(__file__).parent
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()


def anonymous_bytes():
    output = subprocess.check_output(['vm_stat'], text=True)
    page_size = int(re.search(r'page size of (\d+) bytes', output).group(1))
    pages = int(re.search(r'Anonymous pages:\s+(\d+)', output).group(1))
    return pages * page_size


parser = argparse.ArgumentParser()
parser.add_argument('--mode', choices=['probe', 'render'], required=True)
parser.add_argument('--source', type=Path, required=True)
parser.add_argument('--source-kind', choices=['native', 'finite-subset'], required=True)
parser.add_argument('--orientation', type=Path)
parser.add_argument('--label', required=True)
a = parser.parse_args()
assert a.source.is_file() and a.source.name == 'native-display.glb'
assert re.fullmatch(r'[a-zA-Z0-9_-]+', a.label)
if a.mode == 'render':
    assert a.orientation is not None and a.orientation.is_file()
destination = PRIVATE / a.label
assert not destination.exists(), 'Use a new immutable output label'
PRIVATE.mkdir(parents=True, exist_ok=True)
EVIDENCE.mkdir(parents=True, exist_ok=True)
source_sha = sha(a.source)
command = ['/Applications/Blender.app/Contents/MacOS/Blender', '-b', '-t', '2', '--python-exit-code', '1', '--python', str(RECIPE / 'render.py'), '--', '--mode', a.mode, '--source', str(a.source), '--source-sha', source_sha, '--source-kind', a.source_kind, '--out', str(destination), '--seconds', '1650']
if a.orientation:
    command += ['--orientation', str(a.orientation)]
start = time.monotonic()
maximum_memory = anonymous_bytes()
assert maximum_memory < 70_000_000_000
with (PRIVATE / f'{a.label}-process.log').open('wb') as log:
    process = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT, start_new_session=True, env={**os.environ, 'OPENBLAS_NUM_THREADS': '2', 'OMP_NUM_THREADS': '2', 'PYTHONDONTWRITEBYTECODE': '1'})
    reason = None
    while process.poll() is None:
        memory = anonymous_bytes()
        maximum_memory = max(memory, maximum_memory)
        if memory >= 70_000_000_000 or time.monotonic() - start > 1710:
            reason = 'anonymous_memory_ceiling' if memory >= 70_000_000_000 else 'bounded_1710_second_cpu_render'
            os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
            break
        time.sleep(2)
    code = process.wait()
movie = None
if code == 0:
    render_report = json.loads((destination / 'report.json').read_text())
    assert render_report['status'] == 'COMPLETE_UNACCEPTED_RAW_STRUCTURAL_INSPECTION'
    assert len(render_report['views']) == (6 if a.mode == 'probe' else 11)
    assert len(render_report['frames']) == (0 if a.mode == 'probe' else 72)
if code == 0 and a.mode == 'render':
    movie = destination / 'gray-turntable.mp4'
    video_command = ['/opt/homebrew/bin/ffmpeg', '-v', 'error', '-nostdin', '-framerate', '12', '-i', str(destination / 'frames/%04d.png'), '-c:v', 'libx264', '-threads', '2', '-crf', '18', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', '-an', '-y', str(movie)]
    subprocess.run(video_command, check=True, timeout=max(1, 1790 - (time.monotonic() - start)), stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
receipt = {'mode': a.mode, 'command': command, 'source': str(a.source), 'sourceSHA256': source_sha, 'sourceSHA256After': sha(a.source), 'sourceKind': a.source_kind, 'finiteSubset': a.source_kind == 'finite-subset', 'exitCode': code, 'stopReason': reason, 'seconds': time.monotonic() - start, 'peakAnonymousMemoryBytes': maximum_memory, 'device': 'CPU', 'threads': 2, 'GPUJob': False, 'output': str(destination), 'movie': str(movie) if movie else None, 'movieSHA256': sha(movie) if movie else None, 'limits': 'Raw stationary mesh inspection only. A finite-subset diagnostic is not a valid native generation. No rig, weights, game export, pose/deformation pass or art score.'}
assert receipt['sourceSHA256After'] == source_sha
(EVIDENCE / f'{a.label}-run.json').write_text(json.dumps(receipt, indent=2) + '\n')
if code == 0:
    frozen = {'status': 'UNACCEPTED_INSPECTION_EVIDENCE', 'inputPins': {str(a.source): source_sha}, 'recipePins': {str(p): sha(p) for p in RECIPE.glob('*.py')}, 'outputPins': {str(p): sha(p) for p in destination.rglob('*') if p.is_file()}, 'receiptPin': {str(EVIDENCE / f'{a.label}-run.json'): sha(EVIDENCE / f'{a.label}-run.json')}}
    if a.orientation:
        frozen['inputPins'][str(a.orientation)] = sha(a.orientation)
    (EVIDENCE / f'{a.label}-freeze.json').write_text(json.dumps(frozen, indent=2) + '\n')
print(json.dumps({'exitCode': code, 'report': str(destination / 'report.json'), 'movie': receipt['movie'], 'stopReason': reason}))
raise SystemExit(code or (1 if reason else 0))
