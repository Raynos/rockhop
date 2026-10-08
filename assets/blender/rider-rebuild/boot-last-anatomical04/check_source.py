"""Only AST/pins: this must run in ordinary Python without bpy/NumPy."""
import ast
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as handle:
        while block := handle.read(1024 * 1024):
            digest.update(block)
    return digest.hexdigest()


manifest = json.loads((HERE / 'inputs.json').read_text())
rows = [*manifest['inputs'].values(), manifest['workingOutfit']]
for row in rows:
    assert sha(ROOT / row['path']) == row['sha256'], ('Changed source', row['path'])
source = HERE / 'extract_region.py'
tree = ast.parse(source.read_text(), filename=str(source))
calls = [ast.unparse(node.func) for node in ast.walk(tree) if isinstance(node, ast.Call)]
assert not any(token in call for call in calls for token in
               ('save_as_mainfile', 'save_mainfile', 'render', 'bake', 'modifier_apply',
                'frame_set', 'export_scene', 'bmesh.ops'))
assert manifest['accepted'] is False
assert manifest['inputs']['anatomical-hand-rig.blend']['sha256'] == '42fca617ea8d246a6c3e3ca68a90cd3cb5f3ce8b9bb78130e0e2bbd65f605fac'
report = {'accepted': False, 'stage': 'READ_ONLY_REGION_EXTRACTION_SOURCE_READY',
          'pythonASTPassed': True, 'explicitInputPinsPassed': len(rows),
          'noBlenderModelBakeRenderOrDenseArrayJobExecuted': True,
          'recipeSHA256': sha(source), 'manifestSHA256': sha(HERE / 'inputs.json'),
          'command': ['/Applications/Blender.app/Contents/MacOS/Blender', '-b', '-t', '2',
                      '--python-exit-code', '1', '--python', str(source.relative_to(ROOT)),
                      '--', 'docs/evidence/rider-rebuild/boot-last-anatomical04/extraction01'],
          'runtimeIntakePending': ['Actual source mesh triangle/UV/packed-map/rest state.',
                                  'Exact displayed-foot source ID match with canonical42f.',
                                  'Actual closed/branched cut loops, disconnected source features and cavity topology.'],
          'limits': manifest['limits']}
path = ROOT / 'docs/evidence/rider-rebuild/boot-last-anatomical04/source-checkpoint.json'
path.write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
