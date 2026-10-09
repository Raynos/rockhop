"""CPU-only identity and unchanged-construction checks for cached73 lifetime."""
import ast
import copy
import json
import runpy
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
L = runpy.run_path(str(HERE/'lifetime.py'))


def segment(source, start, end):
    return source[source.index(start):source.index(end)]


def main(input_path, output):
    value, execution = L['stage'](input_path)
    _, prepared = L['prepared_function'](value, execution)
    _, applied = L['applied_function'](value, execution)
    old_prepare = L['function_source'](L['JOB']['worker'], 'prepare')
    old_apply = L['function_source'](L['JOB']['native'], 'apply')
    start = '    unique, first, inverse = np.unique'; end = "    write(out/'prepared.json'"
    assert segment(prepared, start, end) == segment(old_prepare, start, end)
    start = "    moved = np.load(checked(solved['positions'])"; end = "    report = {'acceptedArt'"
    assert segment(applied, start, end) == segment(old_apply, start, end)
    assert 'open_mainfile' not in prepared and 'open_original' not in prepared
    assert 'cached_intake(np)' in prepared and 'not bpy.data.filepath' in prepared
    assert "assert witness(rig, hoodie, config, bpy, np) == expected" in L['function_source'](L['JOB']['native'], 'qualify')
    assert 'cornerNormals' not in value['sourceWitness']
    assert value['originalNormalsBoundByNativeFileSHA'] == L['JOB']['native47']
    assert "'actualOriginalCornerNormals': before['cornerNormals']" in applied
    for source in (prepared, applied): ast.parse(source)
    rejected = []
    base = L['ROOT']/'harness/out/rider-rebuild/selected-anatomical-hoodie-fit73'
    with tempfile.TemporaryDirectory(prefix='lifetime-fixture-', dir=base) as temporary:
        for name, key, mutate in (
            ('wrongOriginalNativeBinding', 'original54', lambda row: row['native'].update(sha256='0'*64)),
            ('wrongBodyBasisBinding', 'reference05', lambda row: row['arraySHA256'].update(RiderBody__FullAnatomyReference_basis='0'*64))):
            evidence = copy.deepcopy(value['evidence']); row = L['read'](evidence[key]); mutate(row)
            path = Path(temporary)/(name+'.json'); path.write_text(json.dumps(row))
            evidence[key] = L['pin'](path)
            try: L['authority'](evidence)
            except AssertionError: rejected.append(name)
            else: raise AssertionError('Incorrect cached identity was admitted: '+name)
    report = {'acceptedArt': False, 'actualNativeExecuted': False,
        'input': L['pin'](input_path), 'recipe': L['pin'](__file__),
        'frozenOriginalInput': L['FROZEN'], 'originalSourcePinsVerifiedUnchanged': True,
        'completeWallGuideAndPreparedArraysStatementsByteExact': True,
        'positionNormalTransportSaveAndExpectedWitnessStatementsByteExact': True,
        'originalIndependentNormalReopenUnchanged': True,
        'emptyBlenderPreparationContainsNoNativeOpen': True,
        'normalHashNotInvented': True, 'negativeIdentityChecksRejected': rejected,
        'sourceWitnessFields': sorted(value['sourceWitness']),
        'limits': ['Cached identity/lifetime checks only; no wall preparation, solve, native apply, contact or art result.',
                   'Actual73 source point/body/matrix checks and full native normal readback remain at apply/reopen.']}
    L['durable_json'](output, report); print(json.dumps(report), flush=True)


if __name__ == '__main__': main(*sys.argv[1:])
