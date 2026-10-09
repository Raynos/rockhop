"""Compact77 receipt admission; no spatial-map fiction or boolean fallback.

The artist's actual CPU qualifier must exist before native relation intake.
Merge admission additionally requires the actual independently qualified bake.
Until those receipts exist this file deliberately refuses, with the missing key.
"""
import json
import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
BASE51 = {'path':'assets/blender/rider-rebuild/selected-distal-wardrobe51/component.py',
          'sha256':'cea65de4c22dc7f0250ea7038e2c8328c25115a62db3a1c9559595c9192c1f27'}
import hashlib
assert hashlib.sha256((ROOT/BASE51['path']).read_bytes()).hexdigest() == BASE51['sha256']
base = runpy.run_path(str(ROOT/BASE51['path']))
pin,checked,write = (base[k] for k in ('pin','checked','write'))
GLOVES,REFERENCE = base['GLOVES'],base['REFERENCE']
DENSE_DONOR = 'RiderHoodie__SelectedDenseBakeSource77'
OBJECTS = base['OBJECTS']|{DENSE_DONOR}
PROTECTED = base['PROTECTED']
SOURCE47 = {'path':'harness/out/rider-rebuild/selected-sleeve-component47/intake01/intake-qualified.json',
            'sha256':'55adfeb1c0a6ff43d640338af1062d05c2893b56695cc94fa79a46144fd532c5'}
INPUT47 = ROOT/'assets/blender/rider-rebuild/selected-sleeve-component47/input01.json'


def read(row): return json.loads(checked(row).read_text())


def required(row,key,meaning):
    assert key in row, 'Missing actual '+meaning+' evidence: '+key
    return row[key]


def authority(row,key,receipt_key):
    recipe = required(row,key,'artist77 independent qualifier')
    path = checked(recipe)
    assert path in (ROOT/'assets/blender/rider-rebuild/selected-hoodie-joints77/native.py',HERE/'bake.py')
    helper = runpy.run_path(str(path))
    assert callable(helper.get('qualify_receipt')), 'Actual artist77 CPU qualify_receipt required'
    receipt = required(row,receipt_key,'artist77 independently reopened receipt')
    actual = read(receipt)
    assert actual['recipe']==recipe
    assert helper['qualify_receipt'](checked(receipt)) == actual
    return actual


def native_gate(row,config):
    assert row['acceptedArt'] is False
    actual = authority(row,'qualificationRecipe','artistReceipt')
    assert actual['native'] == row['native']
    if actual['recipe']['path']==str((HERE/'bake.py').relative_to(ROOT)):
        assert actual['status']=='BAKED79_NATIVE_INDEPENDENTLY_REOPENED_UNACCEPTED'
        assert actual['detailBakePassed'] is actual['bakeReopened'] is True
    else:assert actual['status'] == 'AUTHORED77_NATIVE_INDEPENDENTLY_REOPENED_UNACCEPTED'
    assert actual['independentReopenPassed'] is True
    assert actual['source47Receipt'] == SOURCE47
    assert actual['denseBakeSourceObject'] == DENSE_DONOR and actual['targetObject'] == 'RiderHoodie'
    assert actual['nativeStorage'] == {'compressed':False,'reopenVerified':True}
    source = read(SOURCE47); base['legacy']['intake_gate'](source)
    glove = read(source['componentReceipt'])
    expected = read(actual['expectedWitness'])
    assert expected['rest'] == source['expectedRest']
    # The pinned geometry helper hashes object.name. The independently reopened
    # renamed donor keeps its own donorGeometry; only the read-only original-name
    # witness compares to original47. Artist77 verifies both against one mesh.
    assert expected['donorOriginalNamedGeometry'] == source['expectedHoodieGeometry']
    assert expected['donorMetadata'] == source['expectedHoodieMetadata']
    assert set(expected['objectNames']) == OBJECTS
    assert expected['visibleRenderMeshes'] == sorted(['RiderHoodie',*GLOVES])
    assert expected['protectedGeometry'][REFERENCE] == glove['protectedBefore']['fullReference']
    for name in GLOVES:
        assert expected['protectedGeometry'][name] == glove['expectedConstructedGeometry'][name]
    assert row['input'] == pin(checked(row['input'])) and row['sourcePins'] == config['pins']
    assert row['sourcePins']['cuffInput'] == json.loads(INPUT47.read_text())['pins']['cuffInput']
    assert row['sourcePins']['sourceIntake47'] == SOURCE47
    for entry in row['sourcePins'].values(): checked(entry)
    for key in ('native','input','artistReceipt','qualificationRecipe'): checked(row[key])
    return actual


def donor_gate(row,config):
    actual = native_gate(row,config)
    baked = authority(row,'bakeQualificationRecipe','bakeReceipt')
    assert baked['native'] == actual['native'] == row['native']
    assert baked['sourceReceipt'] == SOURCE47
    assert baked['detailBakePassed'] is True
    assert baked['bakeReopened'] is True
    # Native and bake gates bind the same actual saved receiver/material.
    # The baked79 receipt can supply both gates after one independent reopen.
    assert baked['receiverReceipt'] == actual['receiverReceipt']
    expected = read(actual['expectedWitness'])
    assert baked['receiverGeometry'] == expected['receiverGeometry']
    assert baked['receiverMetadata'] == expected['receiverMetadata']
    return actual


def freeze(artist_path,output,bake_path=None,bake_recipe=None):
    """Wrap actual native77 for measurements; no absent future bake pin emitted."""
    artist_path,output = Path(artist_path).resolve(),Path(output).resolve()
    assert output.is_relative_to(ROOT/'harness/out/rider-rebuild/selected-engine-receiver79')
    assert not output.exists()
    row = json.loads(artist_path.read_text())
    qualification = row['recipe']; checked(qualification)
    assert qualification['path'] in ('assets/blender/rider-rebuild/selected-hoodie-joints77/native.py',
                                     str((HERE/'bake.py').relative_to(ROOT)))
    pins = {'sourceIntake47':SOURCE47,'artistReceipt':pin(artist_path),'qualificationRecipe':qualification,
            'cuffInput':json.loads(INPUT47.read_text())['pins']['cuffInput']}
    config = {'acceptedArt':False,'pins':pins}
    report = {'acceptedArt':False,'native':row['native'],'artistReceipt':pins['artistReceipt'],
              'qualificationRecipe':qualification,'sourcePins':pins,
              'status':'UNACCEPTED_RECEIVER79_COMPONENT_DENSE_BAKE_MOTION_PENDING'}
    if bake_path is not None:
        assert bake_recipe is not None
        report.update(bakeReceipt=pin(bake_path),bakeQualificationRecipe=pin(bake_recipe))
    elif qualification['path']==str((HERE/'bake.py').relative_to(ROOT)):
        report.update(bakeReceipt=pin(artist_path),bakeQualificationRecipe=qualification)
    output.mkdir(parents=True)
    write(output/'input.json',config)
    report['input'] = pin(output/'input.json')
    native_gate(report,config)
    write(output/'construction.json',report)


if __name__ == '__main__':
    import sys
    assert sys.argv[1] == 'freeze'
    freeze(*sys.argv[2:])
