"""Fresh digests of the existing Hunyuan PBR/DINO/ESRGAN route, no downloads."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import time
import urllib.request

STORE = Path('/Users/raynos/projects/weights/manual')
VIEW = Path('/Users/raynos/ml/img2mesh/hunyuan21-view')


def digest(path):
    value = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b''):
            value.update(block)
    return value.hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    assert os.environ.get('ROCKHOP_GENERATION_CONTROLLER_PID') == str(os.getppid())
    out = Path(args.out)
    assert not out.exists()
    out.mkdir(parents=True)
    started = time.monotonic()
    report = {'accepted': False, 'modelRuns': 0, 'recipeSHA256': digest(__file__), 'files': [],
              'runtimeView': [], 'metadata': [],
              'limits': ['No weight downloads, installs, credentials or shared runtime edits.',
                         'Digests do not prove inference, attention parity, mesh preservation or texture quality.',
                         'Legacy ESRGAN fallback is a recorded installation pin if release digest is absent.']}
    def save():
        (out / 'receipt.json').write_text(json.dumps(report, indent=2) + '\n')
    for repo, revision, folder in [
        ('tencent/Hunyuan3D-2.1', '0b94677654c57bb9a6b6845cd7b704ccf551d327', 'hunyuan3d-paintpbr-v2-1'),
        ('facebook/dinov2-giant', '611a9d42f2335e0f921f1e313ad3c1b7178d206d', '')]:
        url = f'https://huggingface.co/api/models/{repo}/revision/{revision}?blobs=true'
        raw = urllib.request.urlopen(url, timeout=30).read()
        metadata = json.loads(raw)
        assert metadata['sha'] == revision
        (out / (repo.replace('/', '-') + '-metadata.json')).write_bytes(raw)
        report['metadata'].append({'URL': url, 'SHA256': hashlib.sha256(raw).hexdigest(), 'revision': revision})
        selected = sorted(p for p in (STORE / repo / folder).rglob('*') if p.is_file())
        assert selected
        for path in selected:
            filename = str(path.relative_to(STORE / repo))
            sibling = next(s for s in metadata['siblings'] if s['rfilename'] == filename)
            actual = digest(path)
            lfs = sibling.get('lfs')
            if lfs:
                expected, method = lfs['sha256'], 'Published LFS SHA256 plus length'
                assert path.stat().st_size == lfs['size']
            else:
                published = urllib.request.urlopen(f'https://huggingface.co/{repo}/resolve/{revision}/{filename}', timeout=30).read()
                expected, method = hashlib.sha256(published).hexdigest(), 'Fetched published small-file SHA256, not Git blob SHA1'
            item = {'path': str(path), 'resolvedPath': str(path.resolve()), 'bytes': path.stat().st_size,
                    'actualSHA256': actual, 'expectedSHA256': expected, 'method': method,
                    'publishedDigestVerified': True, 'match': actual == expected}
            report['files'].append(item)
            save()
            assert item['match']
            if folder:
                view_path = VIEW / filename
                assert view_path.is_file()
                view_sha = digest(view_path)
                canonical_equal = view_sha == actual
                if not canonical_equal:
                    assert filename == folder + '/unet/attn_processor.py'
                    original = path.read_text()
                    adapted = original.replace('.to("cuda:0")', '.to(hidden_states.device)')
                    assert view_path.read_text() == adapted, 'Unrecorded runtime-view code change'
                report['runtimeView'].append({'path': str(view_path), 'SHA256': view_sha,
                                              'canonicalBytesIdentical': canonical_equal,
                                              'adaptation': None if canonical_equal else 'Existing exact CUDA:0 to hidden_states.device substitution'})
            print(json.dumps({'file': filename, 'match': True}), flush=True)
    path = STORE / 'xinntao/Real-ESRGAN/RealESRGAN_x4plus.pth'
    url = 'https://api.github.com/repos/xinntao/Real-ESRGAN/releases/tags/v0.1.0'
    raw = urllib.request.urlopen(url, timeout=30).read()
    metadata = json.loads(raw)
    asset = next(a for a in metadata['assets'] if a['name'] == path.name)
    (out / 'Real-ESRGAN-release-metadata.json').write_bytes(raw)
    public_digest = asset.get('digest')
    if public_digest:
        assert public_digest.startswith('sha256:')
        expected, method = public_digest.split(':', 1)[1], 'Published GitHub release digest'
    else:
        expected = '4fa0d38905f75ac06eb49a7951b426670021be3018265fd191d2125df9d682f1'
        method = 'Existing canonical install SHA256 pin; release publishes no digest'
    actual = digest(path)
    report['files'].append({'path': str(path), 'bytes': path.stat().st_size, 'actualSHA256': actual,
                            'expectedSHA256': expected, 'method': method,
                            'publishedDigestVerified': bool(public_digest),
                            'match': actual == expected and path.stat().st_size == asset['size']})
    report['metadata'].append({'URL': url, 'SHA256': hashlib.sha256(raw).hexdigest()})
    report['allSelectedPinsMatch'] = all(f['match'] for f in report['files'])
    report['publishedDigestVerifiedFiles'] = sum(f['publishedDigestVerified'] for f in report['files'])
    report['elapsedSeconds'] = time.monotonic() - started
    save()
    assert report['allSelectedPinsMatch']
    print(json.dumps({'files': len(report['files']), 'publicDigests': report['publishedDigestVerifiedFiles'],
                      'allMatch': True, 'elapsedSeconds': report['elapsedSeconds']}), flush=True)


if __name__ == '__main__':
    main()
