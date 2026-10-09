"""Native lifetime adapter: exact65 transport applied to the selected original47.

The pinned65 component's source checks, normals, raw save and independent
qualification are reused verbatim. Only target/solve/carry execution is replaced
by intake of complete, sealed72 transport of committed69 maps. No geometry is refit.
"""
import runpy
import shutil
from pathlib import Path

_HERE72 = Path(__file__).resolve().parent
_W = runpy.run_path(str(_HERE72/'worker.py'))
FROZEN = _HERE72.parent/'selected-anatomical-hoodie-fit65'


def transformed_component():
    source = _W['checked'](_W['PINS']['component65']).read_text()
    source = source[:source.index("\nif __name__ == '__main__':")]
    replacements = {
        "ROOT/'harness/out/rider-rebuild/selected-anatomical-hoodie-fit65'":
            "ROOT/'harness/out/rider-rebuild/selected-anatomical-hoodie-fit72'",
        'UNACCEPTED_ANATOMICAL65_': 'UNACCEPTED_ANATOMICAL72_',
        'UNACCEPTED-selected-anatomical-hoodie-fit65.blend': 'UNACCEPTED-selected-anatomical-hoodie-fit72.blend',
        "assert config['pins']['component65'] == pin(__file__)":
            "assert config['pins']['component65'] == pin(FROZEN/'component.py')",
        "pin(HERE/'multiscale.py')": "pin(FROZEN/'multiscale.py')",
        'pin(HERE/v)': 'pin(FROZEN/v)',
        'def freeze(output):': 'def _unused_frozen65_freeze(output):',
        "    target_helper = module(config['pins']['targets65'], 'anatomical65_targets')\n": '',
        "    broad = np.load(checked(config['pins']['broad50Arrays']))\n": '',
        "    assert np.array_equal(faces, broad['faces']) and len(original) == len(c['source'])":
            "    assert len(original) == len(c['source'])",
        '    del transformed, normals, arrays, maps, inverse, vector, differential':
            '    del transformed, normals, inverse, vector, differential',
        "'sourceInput47': SOURCE47, 'sourceIntake47': config['pins']['gloveReceipt'],":
            "'sourceInput47': SOURCE47, 'sourceIntake47': config['pins']['gloveReceipt'], 'execution72': config['execution72'],",
        "c['progress']('SAVE selected anatomical65 before full contact/strain qualification')":
            "c['progress']('SAVE selected anatomical72 exact65 transport before full contact/strain qualification')"}
    expected = [2, 3, 1, 1, 2, 2, 1, 1, 1, 1, 1, 1, 1]
    for (old, new), count in zip(replacements.items(), expected):
        assert source.count(old) == count, ('Changed frozen65 adapter boundary', old, source.count(old))
        source = source.replace(old, new)
    start = source.index("    STAGE['name'] = 'ACTUAL_SOURCE_MERIDIANS_AND_BODY_TARGETS'\n")
    end = source.index('    retained = np.ones(len(faces), bool); removed = {}\n', start)
    source = source[:start]+"    out = c['out']; out.mkdir(parents=True)\n    STAGE['name'] = 'APPLY_COMPLETE_EXACT65_CPU_TRANSPORT'\n    moved, differential, report = ingest72(config, out, original, np)\n"+source[end:]
    return source


# __file__ remains this72 source, so all receipts and native authority name72.
exec(compile(transformed_component(), str(_W['checked'](_W['PINS']['component65'])), 'exec'), globals())
_source_gate65 = source_gate
_qualify_receipt65 = qualify_receipt


def source_gate(config):
    receipt = _source_gate65(config)
    assert {k: v for k, v in config.items() if k != 'execution72'} == read(_W['PINS']['input65'])
    execution = config['execution72']
    assert set(execution) == {'componentRecipe', 'workerRecipe', 'transportReceipt'}
    assert execution['componentRecipe'] == pin(__file__)
    assert execution['workerRecipe'] == pin(HERE/'worker.py')
    _W['transport_gate'](checked(execution['transportReceipt']))
    return receipt


def ingest72(config, out, original, np):
    carried, solved = _W['transport_gate'](checked(config['execution72']['transportReceipt']))
    assert len(original) == carried['sourceVertexCount']
    assert np.array_equal(np.vstack((original.min(0), original.max(0))), np.asarray(solved['originalBounds']))
    positions = np.load(checked(carried['positions']), mmap_mode='r')
    differential = np.load(checked(carried['jacobians']), mmap_mode='r')
    assert positions.shape == original.shape and positions.dtype == np.float64
    assert differential.shape == (len(original), 3, 3) and differential.dtype == np.float64
    for row, filename in ((solved['registrationMaps'], 'anatomical-cage.npz'),
                          (_W['PINS']['fixedMaterialTargets'], 'fixed-material-targets.npz'),
                          (_W['PINS']['materialTargets'], 'material-targets.json')):
        target = out/filename; assert not target.exists(); shutil.copyfile(checked(row), target)
        assert pin(target)['sha256'] == row['sha256']
    return positions, differential, solved['anatomicalRegistration']


def freeze(carried_path, output):
    output = Path(output).resolve(); assert output.is_relative_to(HERE) and not output.exists()
    _W['transport_gate'](carried_path)
    config = read(_W['PINS']['input65'])
    config['execution72'] = {'componentRecipe': pin(__file__), 'workerRecipe': pin(HERE/'worker.py'),
                             'transportReceipt': pin(carried_path)}
    source_gate(config); write(output, config)
    print(json.dumps({'input': pin(output), 'nativeRunExecuted': False}))


def qualify_receipt(path):
    report = _qualify_receipt65(path)
    assert report['execution72'] == read(report['input'])['execution72']
    return report


if __name__ == '__main__':
    args = sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else sys.argv[1:]
    if args[0] == 'freeze':
        assert len(args) == 3; freeze(args[1], args[2])
    elif args[0] == 'qualify':
        assert len(args) == 2
        import bpy
        qualify(args[1], bpy)
    else:
        assert len(args) == 2; construct()
