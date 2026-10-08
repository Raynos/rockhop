"""Copy and pin the exact selected glove/actual wearer artist sources; no model job.

python THIS -- FRESH_harness/out/rider-rebuild/production-gloves03/artist-handoff01
ZIP_STORED avoids an unnecessary compression job on existing binary masters.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import time
import zipfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('out')
    args = parser.parse_args()
    out = Path(args.out).resolve()
    assert not out.exists() and out.is_relative_to(ROOT/'harness/out/rider-rebuild/production-gloves03')
    manifest_path = HERE/'artist-sources.json'
    manifest = json.loads(manifest_path.read_text())
    started = time.monotonic()
    for row in manifest['files']:
        source = ROOT/row['source']
        assert source.is_file() and sha(source) == row['sha256']
        assert source.stat().st_size == row['bytes']
        assert not Path(row['packagePath']).is_absolute() and '..' not in Path(row['packagePath']).parts
    out.mkdir(parents=True)
    copied = out/'sources'
    copied.mkdir()
    for row in manifest['files']:
        destination = copied/row['packagePath']
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT/row['source'], destination)
        assert sha(destination) == row['sha256']
    shutil.copyfile(manifest_path, copied/'artist-sources.json')
    archive = out/'rockhop-selected-glove-character-artist-sources.zip'
    with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_STORED) as package:
        for path in sorted(copied.rglob('*')):
            if path.is_file():
                package.write(path, path.relative_to(copied))
    with zipfile.ZipFile(archive) as package:
        for row in manifest['files']:
            assert hashlib.sha256(package.read(row['packagePath'])).hexdigest() == row['sha256']
        assert package.read('artist-sources.json') == manifest_path.read_bytes()
    assert all(sha(ROOT/row['source']) == row['sha256'] for row in manifest['files'])
    receipt = {'accepted': False, 'status': 'EXACT_CHARACTER_ARTIST_PACKAGE_NO_NEW_AUTHORING',
               'copiedFiles': len(manifest['files']), 'allCopiedAndZipMembersMatchPins': True,
               'allOriginalInputsUnchanged': True, 'elapsedSeconds': round(time.monotonic()-started, 3),
               'manifestSHA256': sha(manifest_path), 'recipeSHA256': sha(__file__),
               'archive': {'path': str(archive.relative_to(ROOT)), 'sha256': sha(archive),
                           'bytes': archive.stat().st_size},
               'blenderRun': False, 'geometryRepair': False, 'bakeRun': False,
               'artistContacted': False, 'acceptedGates': 0}
    (out/'artist-package.json').write_text(json.dumps(receipt, indent=2)+'\n')
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    main()
