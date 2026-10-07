"""Read-only five-day Git/source audit; writes only beside this script."""
from pathlib import Path
from collections import Counter
import hashlib
import json
import struct
import subprocess

ROOT = Path('/Users/raynos/projects/games/rockhop')
OUT = Path(__file__).resolve().parent
HEAD = 'b48ac6d756199f013705d953929b8d9fe40c972f'
SINCE = '2026-10-02T00:00:00-05:00'


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT)


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def pin(path, expected=None):
    p = Path(path)
    if not p.is_absolute():
        p = ROOT / p
    rel = str(p.relative_to(ROOT))
    result = {'path': rel, 'exists': p.is_file()}
    if not result['exists']:
        return result
    result.update(bytes=p.stat().st_size, sha256=digest(p))
    if expected:
        result.update(expectedSHA256=expected, expectedMatch=result['sha256'] == expected)
    oid = git('ls-tree', HEAD, '--', rel).decode().strip()
    result['committedAtAuditHead'] = bool(oid)
    if oid:
        committed = git('show', f'{HEAD}:{rel}')
        result['workingBytesEqualAuditHead'] = hashlib.sha256(committed).hexdigest() == result['sha256']
    else:
        result['ignored'] = subprocess.run(['git', 'check-ignore', '-q', rel], cwd=ROOT).returncode == 0
    return result


log = git('log', HEAD, f'--since={SINCE}', '--format=%H\t%aI\t%cI\t%s').decode()
(OUT / 'git-window.tsv').write_text(log)
commits = [x.split('\t', 3) for x in log.splitlines()]
paths = sorted(set(x for x in git('log', HEAD, f'--since={SINCE}', '--format=', '--name-only').decode().splitlines() if x))
(OUT / 'changed-paths.txt').write_text('\n'.join(paths) + '\n')
player_prefixes = ('src/', 'public/models/')
summary = {
    'auditHead': HEAD, 'sinceInclusive': SINCE, 'scope': 'All main-reachable commits, selected by Git committer-date traversal; dates below are author dates. Historical five-day work plus current October7 handoff.',
    'commitCount': len(commits), 'distinctChangedPaths': len(paths),
    'authorDates': dict(Counter(x[1][:10] for x in commits)),
    'types': dict(Counter(x[3].split('(')[0].split(':')[0] for x in commits)),
    'playerSourceOrModelChangedPaths': [x for x in paths if x.startswith(player_prefixes)],
    'finishPlanCreationCommit': 'c83490ccbca708735ab8bf323859a5a91dff9151',
    'commitsAfterFinishPlanCreation': int(git('rev-list', '--count', 'c83490cc..' + HEAD)),
    'limits': ['Commit counts include preservation/documentation and are not accepted progress.', 'No model execution, Blender, gameplay, contact recomputation, movie playback or visual acceptance performed by this auditor. Parent judges.', 'Pinned HEAD prevents concurrent new commits from changing this audit scope.'],
}

sources = json.loads((ROOT / 'docs/evidence/hero-remaster/audit-2026-10-05/source-verification.json').read_text())['sources']
source_receipts = []
for source in sources:
    result = pin(source['path'], source['expectedSHA256'])
    with Path(source['path']).open('rb') as f:
        magic, version, length = struct.unpack('<III', f.read(12))
        json_length, json_type = struct.unpack('<II', f.read(8))
        glb = json.loads(f.read(json_length))
    tris = sum((glb['accessors'][p['indices']]['count'] if 'indices' in p else glb['accessors'][p['attributes']['POSITION']]['count']) // 3 for m in glb['meshes'] for p in m['primitives'] if p.get('mode', 4) == 4)
    result.update(name=source['name'], glbVersion=version, declaredBytes=length, triangles=tris, skins=len(glb.get('skins', [])), animations=len(glb.get('animations', [])))
    source_receipts.append(result)

capture_path = 'docs/evidence/hero-remaster/finish-2026-10-05/runtime/savedpose-capture01/capture50-execution.json'
capture = json.loads((ROOT / capture_path).read_text())
capture_pins = [pin(capture_path)]
for key in ('command', 'manifest', 'recipe', 'guardRecipe', 'nativeCandidate', 'fields', 'native49ScopeReceipt'):
    x = capture[key]
    capture_pins.append(pin(x['path'], x['sha256']))
for x in [capture['rest'], *capture['samples']]:
    capture_pins.append(pin(str(Path(capture['nativeOutputDirectory']) / x['path']), x['sha256']))

primary = [
    'docs/evidence/hero-remaster/independent-audit-2026-10-03/README.md',
    'docs/evidence/hero-remaster/user-agent3-qa-2026-10-03/body53/finding.json',
    'docs/evidence/hero-remaster/anatomical-foundation-2026-10-03/user-agent1/selected-hoodie26/native92/FINDING.md',
    'docs/evidence/hero-remaster/anatomical-foundation-2026-10-03/user-agent1/selected-hoodie26/rest-head94/FINDING.md',
    'docs/evidence/hero-remaster/user-agent3-qa-2026-10-03/hand83/FINDING.md',
    'docs/evidence/hero-remaster/finish-2026-10-05/runtime/played-review01/parent-review.json',
    'docs/evidence/hero-remaster/finish-2026-10-05/runtime/played-review01/playback.json',
    'docs/evidence/hero-remaster/finish-2026-10-05/construction/body07/parent-preflight45.json',
    'docs/evidence/hero-remaster/finish-2026-10-05/runtime/body06-qa-summary01.json',
    'docs/evidence/hero-remaster/finish-2026-10-05/runtime/body06-parent-readback01.json',
    'docs/evidence/hero-remaster/finish-2026-10-05/runtime/body06-loft-fan-parent01.json',
    'docs/evidence/hero-remaster/finish-2026-10-05/runtime/savedpose-capture01/parent-readback50.json',
    'docs/evidence/hero-remaster/finish-2026-10-05/unimate/decode02/parent-verdict.json',
    'docs/evidence/hero-remaster/handoff-2026-10-07/HANDOFF.md',
    'docs/plans/sol-6.1-2026-10-05-FINISH_RIDER_CLOTHES_AND_ANIMATIONS.md',
    'docs/plans/sol-6.1-2026-10-03-RIDER_BASELINE_TO_SHIP.md',
    'docs/evidence/hero-remaster/finish-2026-10-05/construction/body07/hip-underwear-next-proposal.json',
    'assets/blender/hero-remaster/rider/finish-2026-10-05/wardrobe/glove-enclosure12/inventory-target.py',
]
summary['sourceVerification'] = source_receipts
summary['capture50PinVerification'] = capture_pins
summary['primaryReceiptPins'] = [pin(x) for x in primary]
summary['allDeclaredSourceAndCaptureHashesMatch'] = all(x.get('expectedMatch', True) for x in source_receipts + capture_pins)
summary['contacts51ReceiptExists'] = (ROOT / 'docs/evidence/hero-remaster/finish-2026-10-05/runtime/body07-whole-contacts51.json').exists()
(OUT / 'receipt.json').write_text(json.dumps(summary, indent=2) + '\n')
print(json.dumps({k: summary[k] for k in ('auditHead', 'commitCount', 'distinctChangedPaths', 'commitsAfterFinishPlanCreation', 'playerSourceOrModelChangedPaths', 'allDeclaredSourceAndCaptureHashesMatch', 'contacts51ReceiptExists')}, indent=2))
