"""Exact explicit-file source packaging only; no Blender or geometry job.

python THIS check   validates pins and writes cheap source verification.
python THIS build   only after parent inventory/brief review; fresh ZIP_STORED.
"""
import argparse
import hashlib
import json
from pathlib import Path
import time
import zipfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
EVIDENCE = ROOT / 'docs/evidence/rider-rebuild/production-face01/artist-handoff01'


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=('check', 'build'))
    args = parser.parse_args()
    manifest_path = HERE / 'artist-sources.json'
    manifest = json.loads(manifest_path.read_text())
    names = set(); started = time.monotonic()
    for row in manifest['files']:
        source = ROOT / row['source']; destination = Path(row['packagePath'])
        assert source.is_file() and sha(source) == row['sha256'], ('Changed source', row['source'])
        assert source.stat().st_size == row['bytes']
        assert not destination.is_absolute() and '..' not in destination.parts
        assert str(destination) not in names and str(destination) != 'artist-sources.json'
        names.add(str(destination))
    assert manifest['joiningMechanism'] == 'STOPPED_GROSS_ANATOMY_REJECTION'
    assert manifest['normalDiagnostic'] == 'PARKED_UNEXECUTED_HYPOTHESIS_ONLY'
    assert manifest['acceptedGates'] == 0
    receipt = {'accepted': False, 'status': 'SOURCE_PINS_VERIFIED_ZIP_NOT_BUILT',
               'manifestSHA256': sha(manifest_path), 'recipeSHA256': sha(__file__),
               'payloadFiles': len(manifest['files']), 'payloadBytes': sum(r['bytes'] for r in manifest['files']),
               'allOriginalSourcePinsMatch': True, 'blenderRun': False, 'geometryRepair': False,
               'normalDiagnosticRun': False, 'artistContacted': False, 'acceptedGates': 0}
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    (EVIDENCE / 'source-verification.json').write_text(json.dumps(receipt, indent=2) + '\n')
    (EVIDENCE / 'artist-sources.json').write_bytes(manifest_path.read_bytes())
    if args.mode == 'build':
        archive = HERE / 'rockhop-selected-face-character-artist-sources.zip'
        assert not archive.exists(), 'Never overwrite an existing archive'
        with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_STORED, allowZip64=True) as package:
            for row in manifest['files']:
                package.write(ROOT / row['source'], row['packagePath'])
            package.write(manifest_path, 'artist-sources.json')
        with zipfile.ZipFile(archive) as package:
            assert set(package.namelist()) == names | {'artist-sources.json'}
            for row in manifest['files']:
                h = hashlib.sha256()
                with package.open(row['packagePath']) as stream:
                    for chunk in iter(lambda: stream.read(1024 * 1024), b''):
                        h.update(chunk)
                assert h.hexdigest() == row['sha256'], ('Archive mismatch', row['packagePath'])
                assert sha(ROOT / row['source']) == row['sha256'], ('Source changed while packaging', row['source'])
            assert package.read('artist-sources.json') == manifest_path.read_bytes()
        receipt.update({'status': 'EXACT_CHARACTER_ARTIST_PACKAGE_NO_NEW_AUTHORING',
                        'archive': {'path': str(archive.relative_to(ROOT)), 'sha256': sha(archive),
                                    'bytes': archive.stat().st_size},
                        'allZipMembersMatchPins': True, 'allOriginalInputsUnchanged': True,
                        'elapsedSeconds': round(time.monotonic() - started, 3), 'compression': 'STORED'})
        (EVIDENCE / 'artist-package.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    main()
