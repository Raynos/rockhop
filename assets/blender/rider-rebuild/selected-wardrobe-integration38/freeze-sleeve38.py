"""Freeze actual qualified04 glove and original full-reference witnesses."""
import json
import runpy
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
helper = runpy.run_path(str(HERE/'sleeve_checkpoint.py'))
root = helper['ROOT']
original = {'path': 'assets/blender/rider-rebuild/selected-sleeve-rebuild28/freeze_inputs.py',
            'sha256': '1011883f199d77b820495920aff4210da5256a4d60dfcea54714f6c774bd0058'}
assert len(sys.argv) == 4, 'freeze-sleeve38.py QUALIFIED_GLOVE_JSON ORIGINAL_FULL_REFERENCE_NPZ NEW_INPUT_JSON'
glove = json.loads(Path(sys.argv[1]).read_text())
assert glove['protectedValidationPassed'] is True
assert glove['protectedValidationStage'] == 'SEPARATE_REOPENED_NATIVE'
assert glove['nativeStorage']['reopenVerified'] is True
source = helper['checked'](original).read_text()
old = 'assert not output.exists() and output.is_relative_to(HERE)'
assert source.count(old) == 1
source = source.replace(old, 'assert not output.exists() and output.is_relative_to(NEW_HERE)')
namespace = {'__name__': 'freeze_original28_input38', '__file__': str(helper['checked'](original)), 'NEW_HERE': HERE}
exec(compile(source, namespace['__file__'], 'exec'), namespace)
namespace['main']()
path = Path(sys.argv[3]).resolve()
config = json.loads(path.read_text())
for name, filename in [('checkpointHelper38', 'sleeve_checkpoint.py'), ('constructor38', 'sleeve38.py')]:
    config['pins'][name] = helper['pin'](HERE/filename)
path.write_text(json.dumps(config, indent=2)+'\n')
print(json.dumps({'acceptedArt': False, 'input': helper['pin'](path), 'nativeRunExecuted': False}))
