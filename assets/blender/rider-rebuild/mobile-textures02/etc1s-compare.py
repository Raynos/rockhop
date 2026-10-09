#!/usr/bin/env python3
"""One maximal configured ETC1S ORM trial; no material/resolution change."""
import argparse, hashlib, json, os, struct, subprocess
from pathlib import Path

assert os.environ.get('ROCKHOP_GENERATION_CONTROLLER_PID') == str(os.getppid()), 'Run under original guard'
parser = argparse.ArgumentParser()
parser.add_argument('--out', type=Path, default=Path('harness/out/rider-rebuild/mobile-textures02/etc1s01'))
args = parser.parse_args()
source = Path('harness/out/rider-rebuild/mobile-textures02/components01/boot-L/inventory.json')
inventory = json.loads(source.read_text())
row = next(r for r in inventory['images'] if r['image'] == 1)
png = Path(row['path']).read_bytes()
assert hashlib.sha256(png).hexdigest() == row['sha256'] and row['size'] == [2048, 2048] and not row['srgb']
target = args.out / 'etc1s-max'
target.mkdir(parents=True, exist_ok=True)
output = target / 'image-01.ktx2'
assert not output.exists(), 'Fresh trial required'
command = ['/opt/homebrew/bin/basisu', '-etc1s', '-file', row['path'], '-output_file', str(output),
           '-ktx2', '-max_endpoints', '16128', '-max_selectors', '16128', '-comp_level', '6',
           '-no_selector_rdo', '-no_endpoint_rdo', '-mipmap', '-mip_filter', 'box', '-linear', '-max_threads', '2']
with (target / 'encode.log').open('w') as log:
    subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, check=True)
payload = bytearray(output.read_bytes())
dfd = struct.unpack_from('<I', payload, 48)[0]
payload[dfd + 13] = 0
output.write_bytes(payload)
assert payload[dfd + 12] == 163 and payload[dfd + 14] == 1
assert struct.unpack_from('<I', payload, 44)[0] == 1
assert list(struct.unpack_from('<2I', payload, 20)) == row['size']
meta = {'image': 1, 'path': str(output), 'bytes': len(payload), 'sha256': hashlib.sha256(payload).hexdigest(),
        'size': row['size'], 'levels': struct.unpack_from('<I', payload, 40)[0], 'command': command,
        'sourcePNG_SHA256': row['sha256'], 'sourceOriginalMasterSHA256': inventory['sourceOriginalSelectedSHA256'],
        'dfd': {'model': 163, 'primaries': 0, 'transfer': 1}, 'accepted': False,
        'scope': 'Maximum configured endpoint/selector caps and effort, backend RDO disabled; ETC1S remains lossy, no appearance acceptance.'}
inventory['images'] = [row]
inventory['originalTextureBytes'] = row['bytes']
(args.out / 'inventory.json').write_text(json.dumps(inventory, indent=2) + '\n')
(args.out / 'etc1s-max-encode.json').write_text(json.dumps([meta], indent=2) + '\n')
print(json.dumps(meta))
