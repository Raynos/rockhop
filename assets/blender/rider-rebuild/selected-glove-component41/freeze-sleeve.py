"""New narrow component41 intake; unchanged sleeve28 math and sleeve38 lifetime."""
import json
import runpy
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
assembly = runpy.run_path(str(HERE/'assemble.py'))
component = assembly['component']; checked, pin, ROOT = (assembly[name] for name in ('checked', 'pin', 'ROOT'))
FREEZE28 = {'path': 'assets/blender/rider-rebuild/selected-sleeve-rebuild28/freeze_inputs.py',
            'sha256': '1011883f199d77b820495920aff4210da5256a4d60dfcea54714f6c774bd0058'}


def main():
    assert len(sys.argv) == 4, 'freeze-sleeve.py QUALIFIED_ATTACHED_GLOVE_JSON ORIGINAL_FULL_REFERENCE_NPZ NEW_INPUT_JSON'
    glove = json.loads(Path(sys.argv[1]).read_text())
    assert glove['sourceRecipe'] == pin(HERE/'assemble.py')
    assert glove['methodAncestry'] == component['FROZEN04']
    assert glove['protectedValidationPassed'] is True and glove['exact75RestUnchanged'] is True
    assert glove['protectedValidationStage'] == 'SEPARATE_REOPENED_NATIVE'
    assert glove['nativeStorage'] == {'compressed': False, 'reopenVerified': True}
    receipt = component['read'](glove['componentReceipt']); assembly['component_gate'](receipt)
    assembly['intake'](checked(glove['assemblyInput']))
    assert glove['componentRecipe'] == receipt['sourceRecipe']
    source = checked(FREEZE28).read_text()
    old = 'assert not output.exists() and output.is_relative_to(HERE)'
    assert source.count(old) == 1
    source = source.replace(old, 'assert not output.exists() and output.is_relative_to(NEW_HERE)')
    namespace = {'__name__': 'component41_freeze_exact28', '__file__': str(checked(FREEZE28)), 'NEW_HERE': HERE}
    exec(compile(source, namespace['__file__'], 'exec'), namespace)
    namespace['main']()
    path = Path(sys.argv[3]).resolve(); config = json.loads(path.read_text())
    prior = ROOT/'assets/blender/rider-rebuild/selected-wardrobe-integration38'
    config['pins']['checkpointHelper38'] = pin(prior/'sleeve_checkpoint.py')
    config['pins']['constructor38'] = pin(prior/'sleeve38.py')
    path.write_text(json.dumps(config, indent=2)+'\n')
    print(json.dumps({'input': pin(path), 'acceptedArt': False, 'nativeRunExecuted': False}))


if __name__ == '__main__': main()
