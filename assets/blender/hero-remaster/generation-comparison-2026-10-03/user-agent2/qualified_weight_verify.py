"""Verify selected existing checkpoint bytes against public HF LFS metadata."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import time
import urllib.request

STORE = Path('/Users/raynos/projects/weights/manual')


def digest(path):
    result = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b''):
            result.update(block)
    return result.hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--inventory', required=True)
    parser.add_argument('--inventory-sha256', required=True)
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    assert os.environ.get('ROCKHOP_GENERATION_CONTROLLER_PID') == str(os.getppid())
    inventory, output = Path(args.inventory), Path(args.out)
    assert digest(inventory) == args.inventory_sha256 and not output.exists()
    inputs = json.loads(inventory.read_text())
    selected = []
    for model in ('trellis', 'pixal'):
        for item in inputs[model]['checkpoints']:
            selected.append(Path(item['weights']['path']))
            selected.append(Path(item['config']['path']))
    selected.extend(Path(item['path']) for item in inputs['hunyuanShapeWeights'])
    selected.append(STORE / 'tencent/Hunyuan3D-2.1/hunyuan3d-dit-v2-1/config.yaml')
    selected.append(STORE / 'valeoai/NAF/naf_release.pth')
    selected.extend(p for p in (STORE / 'facebook/dinov3-vitl16-pretrain-lvd1689m').glob('*.safetensors'))
    selected.append(STORE / 'Ruicheng/moge-2-vitl/model.pt')
    revisions = {'tencent/Hunyuan3D-2.1': '0b94677654c57bb9a6b6845cd7b704ccf551d327',
                 'TencentARC/Pixal3D': 'b0cb2e1b794cab9aa0ac38a95d794a4d9337437f'}
    metadata, seen, cache = {}, set(), {}
    output.mkdir(parents=True)
    started = time.monotonic()
    report = {'accepted': False, 'modelRuns': 0, 'recipeSHA256': digest(Path(__file__)),
              'inventorySHA256': digest(inventory), 'files': [], 'publicMetadata': [],
              'limits': ['Selected shape/flow/decoder/NAF/DINO/MoGe files only; paint, background and other dependencies are separate.',
                         'No weights downloaded or copied, no credentials read, no runtime/source edits.',
                         'Published bytes are not inference, backend parity or asset-quality proof.']}
    for path in selected:
        assert path.is_file()
        if str(path) in seen:
            continue
        seen.add(str(path))
        relative = path.relative_to(STORE)
        repo_id = '/'.join(relative.parts[:2])
        filename = '/'.join(relative.parts[2:])
        if repo_id == 'valeoai/NAF':
            url = 'https://api.github.com/repos/valeoai/NAF/releases/tags/model'
            raw = urllib.request.urlopen(url, timeout=30).read()
            data = json.loads(raw)
            asset = next(a for a in data['assets'] if a['name'] == filename)
            assert asset['digest'].startswith('sha256:')
            expected = asset['digest'].split(':', 1)[1]
            actual = digest(path)
            item = {'path': str(path), 'resolvedPath': str(path.resolve()),
                    'bytes': path.stat().st_size, 'model': repo_id, 'release': 'model',
                    'file': filename, 'actualSHA256': actual, 'expectedSHA256': expected,
                    'method': 'Published GitHub release asset SHA256 and length',
                    'sourceURL': asset['browser_download_url'],
                    'match': actual == expected and path.stat().st_size == asset['size']}
            report['files'].append(item)
            report['publicMetadata'].append({'model': repo_id, 'release': 'model', 'url': url,
                'snapshotSHA256': hashlib.sha256(raw).hexdigest()})
            (output / 'valeoai-NAF-release-metadata.json').write_bytes(raw)
            (output / 'receipt.json').write_text(json.dumps(report, indent=2) + '\n')
            print(json.dumps({'file': str(relative), 'bytes': item['bytes'], 'match': item['match']}), flush=True)
            assert item['match'], 'Stop before trust on release mismatch'
            continue
        if repo_id not in metadata:
            url = 'https://huggingface.co/api/models/' + repo_id + '/revision/' + revisions.get(repo_id, 'main') + '?blobs=true'
            raw = urllib.request.urlopen(url, timeout=30).read()
            data = json.loads(raw)
            metadata[repo_id] = data
            (output / (repo_id.replace('/', '-') + '-metadata.json')).write_bytes(raw)
            report['publicMetadata'].append({'model': repo_id, 'revision': data['sha'],
                'url': url, 'snapshotSHA256': hashlib.sha256(raw).hexdigest()})
        data = metadata[repo_id]
        published = next(s for s in data['siblings'] if s['rfilename'] == filename)
        resolved = str(path.resolve())
        if resolved not in cache:
            cache[resolved] = digest(path)
        actual = cache[resolved]
        lfs = published.get('lfs')
        if lfs:
            expected = lfs['sha256']
            match = actual == expected and path.stat().st_size == lfs['size']
            method = 'Published LFS SHA256 plus byte length'
        else:
            url = 'https://huggingface.co/' + repo_id + '/resolve/' + data['sha'] + '/' + filename
            public_bytes = urllib.request.urlopen(url, timeout=30).read()
            expected = hashlib.sha256(public_bytes).hexdigest()
            match = actual == expected
            method = 'SHA256 of fetched public small config; Git blob SHA1 not compared'
        item = {'path': str(path), 'resolvedPath': resolved, 'bytes': path.stat().st_size,
                'model': repo_id, 'revision': data['sha'], 'file': filename,
                'actualSHA256': actual, 'expectedSHA256': expected, 'method': method, 'match': match}
        report['files'].append(item)
        (output / 'receipt.json').write_text(json.dumps(report, indent=2) + '\n')
        print(json.dumps({'file': str(relative), 'bytes': item['bytes'], 'match': match}), flush=True)
        assert match, 'Preserve mismatch receipt and stop before trust'
    report['allSelectedFilesMatch'] = all(item['match'] for item in report['files'])
    report['elapsedSeconds'] = time.monotonic() - started
    report['uniqueResolvedFilesHashed'] = len(cache)
    (output / 'receipt.json').write_text(json.dumps(report, indent=2) + '\n')


if __name__ == '__main__':
    main()
