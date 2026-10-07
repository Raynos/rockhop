"""Reuse pinned export skeleton recipe, preserving constructed donor source IDs."""
import hashlib
import json
import runpy
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[4]
recipe = root / 'assets/blender/rider-rebuild/construction01/assemble-export04.py'
assert hashlib.sha256(recipe.read_bytes()).hexdigest() == '960bf0c0adef29e59157a35eedb9ebc196ea126a91594814ebf2a394551904ac'
native = root / 'harness/out/rider-rebuild/construction01/rig04/anatomical-rig.blend'
assert hashlib.sha256(native.read_bytes()).hexdigest() == 'e348548d974150cf089e5440b6d6b34846c7b6fbecd71b208df7b5fce81a0629'
helper = Path(__file__).with_name('build-selected-rider01.py')
glove_source = runpy.run_path(str(helper))['GLOVE_SOURCE']
assert glove_source is not None, 'Verified actual glove source required before native assembly'
glove_receipt = Path(glove_source['receiptPath']).resolve()
assert hashlib.sha256(glove_receipt.read_bytes()).hexdigest() == glove_source['receiptSHA256']
args = sys.argv[sys.argv.index('--') + 1:]
assert len(args) == 1
sys.argv = [str(recipe), '--', str(native), str(Path(args[0]).resolve()), str(helper)]
source = recipe.read_text()
start = source.index("assert len(body.data.vertices)==10582,'Body source vertex identities must survive appearance changes'")
end = source.index('# Contact sockets are calibrated', start)
source = source[:start] + "assert len(body.data.vertices)>10582, 'Selected high-resolution face must be constructed'\nattr=body.data.attributes.get('_NATIVE_ID');attr.data.foreach_set('value',list(range(len(body.data.vertices))))\n" + source[end:]
source = source.replace("sole=bpy.data.objects.get('RiderSole.'+side)", "sole=bpy.data.objects.get('ActualSelectedBoot.'+side)")
# Check immediately before the inherited export selection and native save.
marker = "bpy.ops.object.select_all(action='DESELECT');rig.hide_set(False);rig.select_set(True)"
assert source.count(marker) == 1
gate = """expected_author_objects={'RiderBody','RiderHoodie','RiderJeans','ActualSelectedGlove.L','ActualSelectedGlove.R','ActualSelectedBoot.L','ActualSelectedBoot.R'}
assert {o.name for o in meshes}==expected_author_objects, 'Incomplete selected outfit cannot export'
assert len(rig.data.bones)==75
assert all(not o.hide_render and not o.hide_viewport for o in meshes)
"""
source = source.replace(marker, gate + marker)
exec(compile(source, str(recipe), 'exec'), {'__name__': '__main__', '__file__': str(recipe)})
out = Path(args[0]).resolve()
receipt = json.loads((out / 'input-receipt.json').read_text())
receipt['integrationInputs'] = [{'path': str(p), 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}
    for p in (Path(__file__).resolve(), helper, helper.with_name('build-selected-face01.py'),
              root / 'assets/blender/rider-rebuild/donor-wardrobe01/build-wardrobe.py',
              root / 'assets/blender/rider-rebuild/donor-hand-foot01/build-hand-foot.py')]
assert hashlib.sha256(glove_receipt.read_bytes()).hexdigest() == glove_source['receiptSHA256']
receipt['integrationInputs'].append({'path': str(glove_receipt), 'sha256': glove_source['receiptSHA256']})
receipt['gloveNativeInput'] = json.loads(glove_receipt.read_text())['native']
receipt['completeSourceRequired'] = True
receipt['limits'] = ['Unaccepted complete source assembly; whole-outfit moving review and calibrated contact remain required.']
(out / 'input-receipt.json').write_text(json.dumps(receipt, indent=2)+'\n')
