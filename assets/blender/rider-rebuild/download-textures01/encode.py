#!/usr/bin/env python3
"""Preserved-size UASTC LDR4x4, no RDO; encode sequentially with two CPUs."""
import argparse, hashlib, json, re, shutil, struct, subprocess, time
from pathlib import Path

DEFAULT = Path('harness/out/rider-rebuild/download-opt01/textures01')

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, default=DEFAULT)
    parser.add_argument('--basisu', default='/opt/homebrew/bin/basisu')
    parser.add_argument('--variant', default='uastc')
    parser.add_argument('--rdo', type=float)
    parser.add_argument('--reuse-dir', type=Path)
    parser.add_argument('--reuse-inventory', type=Path)
    args = parser.parse_args()
    inventory = json.loads((args.out / 'inventory.json').read_text())
    if bool(args.reuse_dir) != bool(args.reuse_inventory):
        parser.error('Reuse requires both directory and source inventory')
    previous = {row['image']:row for row in json.loads(args.reuse_inventory.read_text())['images']} if args.reuse_inventory else {}
    previous_encoded = {row['image']:row for row in json.loads((args.reuse_dir.parent / f'{args.reuse_dir.name}-encode.json').read_text())} if args.reuse_dir else {}
    target = args.out / args.variant
    target.mkdir(exist_ok=True)
    results = []
    for row in inventory['images']:
        output = target / f"image-{row['image']:02d}.ktx2"
        command = [args.basisu, '-file', row['path'], '-output_file', str(output),
                   '-uastc', '-uastc_level', '3', '-ktx2', '-ktx2_zstandard_level', '18',
                   '-mipmap', '-mip_filter', 'box', '-max_threads', '2',
                   '-srgb' if row['srgb'] else '-linear']
        if args.rdo is not None:
            command += ['-uastc_rdo_l', str(args.rdo), '-uastc_rdo_d', '4096']
        # No renorm/swizzle/y_flip/source resize/alpha removal: level0 source semantics retained.
        start = time.monotonic()
        log = target / f"image-{row['image']:02d}-encode.log"
        old = previous.get(row['image'])
        old_encoded = previous_encoded.get(row['image'])
        reusable = old and old_encoded and all(old[k] == row[k] for k in ['sha256','size','srgb']) and old_encoded['command'][5:] == command[5:]
        if reusable and not output.exists():
            old_file = args.reuse_dir / output.name
            old_log = args.reuse_dir / log.name
            assert hashlib.sha256(old_file.read_bytes()).hexdigest() == old_encoded['sha256']
            shutil.copy2(old_file, output)
            shutil.copy2(old_log, log)
        if not output.exists():
            with log.open('w') as handle:
                subprocess.run(command, stdout=handle, stderr=subprocess.STDOUT, check=True)
        payload = output.read_bytes()
        # KHR_texture_basisu requires unspecified primaries for non-color data.
        dfd_offset = struct.unpack_from('<I', payload, 48)[0]
        if not row['srgb'] and payload[dfd_offset + 13] != 0:
            patched = bytearray(payload)
            patched[dfd_offset + 13] = 0
            output.write_bytes(patched)
            payload = bytes(patched)
        width, height = struct.unpack_from('<II', payload, 20)
        assert [width, height] == row['size']
        assert payload[dfd_offset + 14] == (2 if row['srgb'] else 1)
        assert payload[dfd_offset + 12] == 166  # KHR_DF_MODEL_UASTC
        assert struct.unpack_from('<I', payload, 44)[0] == 2  # Zstandard
        results.append({'image':row['image'], 'path':str(output), 'bytes':len(payload),
                        'sha256':hashlib.sha256(payload).hexdigest(), 'command':command,
                        'reusedSourcePNGAndKTX':bool(reusable),
                        'encodeSeconds':time.monotonic()-start, 'nativeEncodeSeconds':
                        float(re.search(r'size \d+ bytes in ([0-9.]+) secs',log.read_text()).group(1)),
                        'size':[width,height],
                        'levels':struct.unpack_from('<I',payload,40)[0],
                        'dfd':{'model':payload[dfd_offset+12], 'primaries':payload[dfd_offset+13],
                               'transfer':payload[dfd_offset+14], 'flags':payload[dfd_offset+15]}})
        (args.out / f'{args.variant}-encode.json').write_text(json.dumps(results, indent=2)+'\n')
        print(json.dumps(results[-1]), flush=True)

if __name__ == '__main__':
    main()
