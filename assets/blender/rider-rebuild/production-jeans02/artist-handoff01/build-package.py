"""Explicit-file artist handoff packager; no Blender, fitting or model jobs."""
import hashlib
import json
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
LEAF = Path(__file__).resolve().parent
EVIDENCE = ROOT / 'docs/evidence/rider-rebuild/production-jeans02/artist-handoff01'


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def main():
    assert len(sys.argv) == 1
    archive_path = LEAF / 'selected-denim-artist01.zip'
    assert not archive_path.exists(), 'Fresh handoff archive required'
    groups = {}
    def add(category, *paths):
        for value in paths:
            path = Path(value)
            if path.is_absolute(): path = path.relative_to(ROOT)
            assert path not in groups, ('Repeated payload', str(path))
            assert (ROOT / path).is_file(), ('Missing payload', str(path))
            groups[path] = category
    dense_intake = json.loads((ROOT / 'assets/blender/rider-rebuild/production-jeans02/dense-fit01/intake.json').read_text())
    for row in [dense_intake[k] for k in ('native', 'nativeFields', 'dense', 'bodyArrays', 'negativeInspection')] + list(dense_intake['helpers'].values()) + list(dense_intake['maps'].values()):
        assert sha(ROOT / row['path']) == row['sha256'], ('Frozen source pin changed', row)
    jeans = 'assets/blender/hero-remaster/rider/finish-2026-10-05/wardrobe/data/prep02/jeans/'
    raw = json.loads((ROOT / 'docs/evidence/hero-remaster/finish-2026-10-05/wardrobe/jeans-source.json').read_text())
    assert sha(raw['source']['path']) == raw['source']['sha256']
    add('original-selected-denim', raw['source']['path'], jeans + 'cleaned-donor.npz',
        jeans + 'baseColorTexture.png', jeans + 'metallicRoughnessTexture.png',
        'assets/blender/hero-remaster/generation-comparison-2026-10-03/user-agent2/items01/references/jeans-reference01.png',
        'docs/evidence/hero-remaster/finish-2026-10-05/wardrobe/jeans-source.json')
    current = 'harness/out/rider-rebuild/production-jeans02/authored01/'
    add('current-compact-native-and-gusset-lineage', current + 'production-jeans.blend',
        current + 'production-jeans-fields.npz', current + 'local-gusset-delta.npz', current + 'report.json',
        'harness/out/rider-rebuild/production-jeans01/authored04/production-jeans.blend',
        'docs/evidence/rider-rebuild/production-jeans01/author04-report.json')
    body = 'harness/out/rider-rebuild/native-hand-repair01/native02/'
    add('unchanged-wearer-shared75-full-four-authority', *[body + name for name in
        ['anatomical-hand-rig.blend', 'native-body.npz', 'weights-full.json', 'weights-four.json',
         'report.json', 'independent-verification.json', 'digit-controls.json', 'rider-contract.json']])
    failed = 'harness/out/rider-rebuild/production-jeans02/dense-fit01/authored01/'
    add('failed-outside-operation-exact-control', *[failed + name for name in
        ['evaluated-before-fit.blend', 'selected-dense-fitted.blend', 'dense-fit-lineage.npz', 'report.json']])
    evidence = 'docs/evidence/rider-rebuild/production-jeans02/'
    add('failed-outside-operation-exact-control', evidence + 'dense-fit01/actual01/FINDING.md',
        evidence + 'dense-fit01/actual01/report.json', evidence + 'dense-fit01/guard01/guard.json',
        evidence + 'dense-fit01/guard01/worker.txt', evidence + 'dense-fit01/guard01/worker.log')
    gallery = json.loads((ROOT / (evidence + 'donor-review01/report.json')).read_text())
    assert len(gallery['photos']) == 6
    for photo in gallery['photos']:
        assert sha(ROOT / photo['path']) == photo['sha256']
        add('six-actual-negative-matched-view-originals', photo['path'])
        # Parent-retained evidence copies must be byte-identical to actual output.
        retained = evidence + 'donor-review01/' + Path(photo['path']).name
        assert sha(ROOT / retained) == photo['sha256']
        add('six-actual-negative-matched-views', retained)
    add('six-actual-negative-matched-views', evidence + 'donor-review01/report.json',
        evidence + 'donor-review01/FINDING.md', evidence + 'donor-review-guard01/guard.json',
        evidence + 'donor-review-guard01/worker.txt')
    add('six-actual-negative-matched-view-originals', 'harness/out/rider-rebuild/production-jeans02/donor-review01/report.json')
    for prefix, names in [
        ('assets/blender/rider-rebuild/production-jeans01/', ['author-jeans.py', 'recipe.json']),
        ('assets/blender/rider-rebuild/production-jeans02/', ['author.py', 'controls.json', 'bake.py', 'intake.json', 'dense-fit01/author.py', 'dense-fit01/intake.json']),
        (evidence, ['source-checkpoint.json', 'RECONSTRUCTION-SOURCE.md', 'author01-report.json', 'author01-result.json',
                    'bake-source-checkpoint.json', 'PBR-INTAKE-SOURCE.md', 'dense-fit01/source-checkpoint.json', 'dense-fit01/SOURCE.md'])]:
        add('source-controls-and-intake-provenance', *[prefix + name for name in names])
    add('required-dressed-motion-and-engine-gates',
        'docs/plans/sol-6.1-2026-10-07-RIDER_REBUILD_FROM_FIRST_PRINCIPLES.md',
        'docs/mission.md', 'docs/design/CONTRACT.md', 'harness/README.md',
        'assets/blender/rider-rebuild/production-assembly01/compose.py',
        'harness/rider-rebuild/private-rider.mjs', 'harness/rider-rebuild/build-private-engine.mjs',
        'harness/rider-rebuild/private-engine-plugin.mjs')
    add('handoff-instructions-and-packager', str((LEAF / 'HANDOFF.md').relative_to(ROOT)), str(Path(__file__).resolve().relative_to(ROOT)))
    records = [{'path': str(path), 'category': groups[path], 'bytes': (ROOT / path).stat().st_size,
                'sha256': sha(ROOT / path)} for path in sorted(groups)]
    pinned = {row['path']: row['sha256'] for row in records}
    assert pinned[current + 'production-jeans.blend'] == '956548765454fe683952801f5ba401ed82f481489a256cf48039c459850e5c95'
    assert pinned[failed + 'selected-dense-fitted.blend'] == '5115aec7b0579bb164816c837eeccdea7b1e529f9a08d302ea97ea3236a7a3a5'
    assert pinned[failed + 'dense-fit-lineage.npz'] == '1c644d3993648b4f25d88e86303cfb4643a76f8b6ac1e50b19b7fcf172605478'
    manifest = {'schema': 'rockhop-selected-denim-expert-tailoring-package-v1', 'accepted': False,
                'purpose': 'Direct expert tailoring of the original selected denim around unchanged body/shared75; automated outside mechanism stopped',
                'files': records, 'payloadBytes': sum(r['bytes'] for r in records),
                'archiveLayout': 'Repository-relative paths; root HANDOFF.md and manifest.json are convenience copies',
                'limits': ['No fit/PBR/movement/player acceptance.', 'No artist contact.', 'Do not relax guards or retry projection.',
                           'Fully dressed native/private-engine review and existing parity/device/release gates remain required.']}
    manifest_path = LEAF / 'manifest.json'
    manifest_path.write_text(json.dumps(manifest, indent=2) + '\n')
    with zipfile.ZipFile(archive_path, 'w', compression=zipfile.ZIP_STORED, allowZip64=True) as archive:
        for record in records: archive.write(ROOT / record['path'], record['path'])
        archive.write(LEAF / 'HANDOFF.md', 'HANDOFF.md')
        archive.write(manifest_path, 'manifest.json')
    # Verify every archived payload against its exact original manifest digest.
    with zipfile.ZipFile(archive_path) as archive:
        for record in records:
            h = hashlib.sha256()
            with archive.open(record['path']) as stream:
                for chunk in iter(lambda: stream.read(1024 * 1024), b''): h.update(chunk)
            assert h.hexdigest() == record['sha256'], ('Archive mismatch', record['path'])
            assert sha(ROOT / record['path']) == record['sha256'], ('Input changed during packaging', record['path'])
        assert archive.read('manifest.json') == manifest_path.read_bytes()
        assert archive.read('HANDOFF.md') == (LEAF / 'HANDOFF.md').read_bytes()
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    (EVIDENCE / 'manifest.json').write_bytes(manifest_path.read_bytes())
    receipt = {'accepted': False, 'kind': 'EXACT_SELECTED_DENIM_ARTIST_HANDOFF_NO_CONTACT',
               'archive': {'path': str(archive_path.relative_to(ROOT)), 'sha256': sha(archive_path), 'bytes': archive_path.stat().st_size},
               'manifestSHA256': sha(manifest_path), 'payloadFiles': len(records), 'payloadBytes': manifest['payloadBytes'],
               'allArchivePayloadHashesVerified': True, 'allSourcePinsStableAfterPackaging': True,
               'zipCompression': 'STORED: cheap file packaging only', 'modelOrFitJobsRun': False,
               'outsideMechanismStoppedGuardsUnchanged': True}
    (EVIDENCE / 'package-receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__': main()
