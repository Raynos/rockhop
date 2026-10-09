#!/usr/bin/env python3
"""Bounded admission waiting around the unchanged original encoding guard."""
import argparse, hashlib, importlib.util, json, subprocess, sys, time
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument('directory', type=Path)
p.add_argument('--wait-seconds', type=int, default=600)
p.add_argument('--receipt', type=Path, required=True)
args = p.parse_args()
assert 0 < args.wait_seconds <= 900
assert not args.receipt.exists(), 'Fresh queue receipt required'
guard = Path('assets/blender/hero-remaster/generation-comparison-2026-10-03/user-agent2/run_bounded96.py')
expected = 'cf8acd15d8b7484480bee74d23892be815d955ffd87115d3da8ed228ffb3d916'
assert hashlib.sha256(guard.read_bytes()).hexdigest() == expected
spec = importlib.util.spec_from_file_location('original_guard', guard)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
command = [sys.executable, 'assets/blender/rider-rebuild/download-textures01/encode.py', '--out', str(args.directory), '--variant', 'uastc-rdo05', '--rdo', '0.5']
record = {'accepted':False, 'directory':str(args.directory), 'originalGuardSHA256':expected,
          'maximumAdmissionWaitSeconds':args.wait_seconds, 'guardOwnedChildLimitSeconds':300,
          'samples':[], 'attempts':[], 'status':'waiting for original admission',
          'scope':'One active fixed-family job; original shared lock/admission/stop limits unchanged. No foreign process or global guard mutation.'}
args.receipt.parent.mkdir(parents=True, exist_ok=True)
start = time.monotonic()
def save():
    args.receipt.write_text(json.dumps(record, indent=2) + '\n')
while time.monotonic() - start < args.wait_seconds:
    memory = module.memory()
    record['samples'].append({'seconds':round(time.monotonic()-start,3), **memory})
    save()
    if memory['anonymousGiB'] < 55 and memory['anonymousGiB'] + memory['wiredGiB'] < 68:
        index = 1
        while (args.directory / f'encode-guard{index:02d}').exists():
            index += 1
        out = args.directory / f'encode-guard{index:02d}'
        print(json.dumps({'status':'original guard attempt','out':str(out),'memory':memory}),flush=True)
        # Original guard takes its own shared lock and rechecks admission after it.
        result = subprocess.run([sys.executable,str(guard),'--out',str(out),'--limit-seconds','300','--',*command])
        record['attempts'].append({'guardReceipt':str(out/'guard.json'),'exitCode':result.returncode})
        if result.returncode != 75:
            record['status'] = 'guarded family returned' if result.returncode == 0 else 'guarded family stopped or failed'
            record['exitCode'] = result.returncode
            save()
            sys.exit(result.returncode)
    time.sleep(min(10, max(0, args.wait_seconds - (time.monotonic() - start))))
record['status'] = 'bounded admission window expired; no pending child'
record['exitCode'] = 75
save()
print(json.dumps({'status':record['status'],'receipt':str(args.receipt)}),flush=True)
sys.exit(75)
