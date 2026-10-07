"""Assemble one loose-cloth checkpoint on pinned rig04; frozen fields unchanged."""
import hashlib
import json
import runpy
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[4]
recipe = root / 'assets/blender/rider-rebuild/construction01/assemble-export04.py'
wardrobe = root / 'assets/blender/rider-rebuild/wardrobe04/build-wardrobe.py'
proposal = wardrobe.parent / 'construction-proposal.py'
base = wardrobe.parent.parent / 'wardrobe01/build-wardrobe03.py'
native = root / 'harness/out/rider-rebuild/construction01/rig04/anatomical-rig.blend'
pins = {
    recipe: '960bf0c0adef29e59157a35eedb9ebc196ea126a91594814ebf2a394551904ac',
    wardrobe: '676b463da026961d3851f7e8f2b0ea4b14d0467b178afb8228d258279026d163',
    proposal: '516855e020df38872a24f1447af5f5d625692fd54aefab1c8f3025da5d02cc6a',
    base: '3f8599336daaeeabc7b9307b07bf3d40ccb3f35b6433ac719aaa774827320098',
    native: 'e348548d974150cf089e5440b6d6b34846c7b6fbecd71b208df7b5fce81a0629',
}
for path, expected in pins.items():
    assert hashlib.sha256(path.read_bytes()).hexdigest() == expected, str(path)
args = sys.argv[sys.argv.index('--') + 1:]
assert len(args) == 1, 'Provide one fresh output leaf only'
out = Path(args[0]).resolve()
sys.argv = [str(recipe), '--', str(native), str(out), str(wardrobe)]
runpy.run_path(str(recipe), run_name='__main__')
receipt = json.loads((out / 'input-receipt.json').read_text())
receipt['integrationInputs'] = [{'path': str(path), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
                                for path in [Path(__file__).resolve(), proposal, base]]
receipt['limits'] = ['One loose-cloth checkpoint, frozen rig04 and body FOUR unchanged.',
                     'Generic action is a separate derivative; no tiny-weight cleanup bundled.']
(out / 'input-receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
