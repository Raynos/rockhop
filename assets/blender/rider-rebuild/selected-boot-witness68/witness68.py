"""Whole saved-stage witness comparison; representation only, no excluded fields."""
import ast
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[4]
NATIVE68=Path(__file__).with_name('native-proof.py')
NATIVE67=ROOT/'assets/blender/rider-rebuild/selected-boot-surface67/native-proof.py'
NATIVE67_SHA='8bbfcc04fa62836224477785a55f272cd3e78d8f93ff662cb7230bb28758460a'
PROOF67=NATIVE67.with_name('proof.py')
PROOF67_SHA='46e22c6fe3d16d3f610a04ee2e5ba19b638f542798370149adcaddfd94acc4a2'
assert hashlib.sha256(PROOF67.read_bytes()).hexdigest()==PROOF67_SHA
assert hashlib.sha256(NATIVE67.read_bytes()).hexdigest()==NATIVE67_SHA
spec=importlib.util.spec_from_file_location('witness68_frozen_proof67',PROOF67)
frozen=importlib.util.module_from_spec(spec);spec.loader.exec_module(frozen)
# Explicit reuse of the frozen geometry/provenance inputs, without native launch.
for name in ['PRODUCTION','PRODUCTION_SHA','NATIVE63','NATIVE63_SHA','NATIVE34','NATIVE34_SHA',
             'ENGINE','ENGINE_SHA','WITNESS','WITNESS_SHA','ADMISSION63','ADMISSION63_SHA','TARGET','OWN','BEARING',
             'sha','pin','load']:
    globals()[name]=getattr(frozen,name)


def canonical(value):
    """Exactly the full JSON value persisted by production63; tuples become arrays."""
    return json.loads(json.dumps(value,sort_keys=True,allow_nan=False))


def differences(actual,expected,path='$',representation=False):
    rows=[]
    if isinstance(actual,dict) and isinstance(expected,dict):
        for key in sorted(actual.keys()|expected.keys()):
            child=path+'.'+str(key)
            if key not in actual:rows.append({'path':child,'kind':'missing','expected':expected[key]})
            elif key not in expected:rows.append({'path':child,'kind':'unexpected','actual':actual[key]})
            else:rows.extend(differences(actual[key],expected[key],child,representation))
    elif isinstance(actual,(tuple,list)) and isinstance(expected,(tuple,list)):
        if representation and type(actual) is not type(expected):
            rows.append({'path':path,'kind':'sequence-representation','actualType':type(actual).__name__,'expectedType':type(expected).__name__})
        if len(actual)!=len(expected):rows.append({'path':path,'kind':'length','actual':len(actual),'expected':len(expected)})
        for i,(left,right) in enumerate(zip(actual,expected)):rows.extend(differences(left,right,f'{path}[{i}]',representation))
    elif type(actual) is not type(expected) or actual!=expected:
        rows.append({'path':path,'kind':'value','actual':actual,'expected':expected,
                     'actualType':type(actual).__name__,'expectedType':type(expected).__name__})
    return rows


def comparison(actual,expected):
    actual_json=canonical(actual);expected_json=canonical(expected)
    changes=differences(actual_json,expected_json)
    return {'equal':not changes,'comparison':'Whole canonical JSON value; no field exclusions, numeric tolerance or order changes inside arrays',
            'livePythonEquality':actual==expected,'valueDifferenceCount':len(changes),'valueDifferences':changes,
            'representationDifferences':differences(actual,expected,representation=True)},actual_json,expected_json


def persist_comparison(out,actual,expected,stage):
    result,before,saved=comparison(actual,expected)
    files={}
    for label,value in [('actual',before),('expected',saved),('diff',result)]:
        file=Path(out)/f'{stage}-witness-{label}.json'
        file.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')
        files[label]=pin(file,sha(file))
    return {'equal':result['equal'],'livePythonEquality':result['livePythonEquality'],
            'valueDifferenceCount':result['valueDifferenceCount'],
            'representationDifferenceCount':len(result['representationDifferences']),'files':files,
            'expectedStage':'production63.sourceWitness captured before construction, rechecked equal immediately before raw63 save; raw63 saved before transfer'}


def validate_comparison(row):
    values={}
    for key in ['actual','expected','diff']:
        item=row['files'][key];file=ROOT/item['path'];pin(file,item['sha256']);values[key]=json.loads(file.read_text())
    recomputed,_,_=comparison(values['actual'],values['expected'])
    pin(PRODUCTION,PRODUCTION_SHA)
    expected_saved=json.loads(PRODUCTION.read_text())['sourceWitness']
    assert comparison(values['expected'],expected_saved)[0]['equal'], 'Expected witness is not the pinned raw63 stage'
    assert recomputed['equal'] and row['equal'] is True
    assert recomputed['valueDifferenceCount']==row['valueDifferenceCount']==0
    assert values['diff']['equal'] is True and values['diff']['valueDifferences']==[]
    assert values['diff']['livePythonEquality']==row['livePythonEquality']
    assert len(values['diff']['representationDifferences'])==row['representationDifferenceCount']


def validate(data):
    assert data['nativeProofAncestry67']==pin(NATIVE67,NATIVE67_SHA)
    assert data['proofValidatorAncestry67']==pin(PROOF67,PROOF67_SHA)
    validate_comparison(data['sourceWitnessReadback'])
    validate_comparison(data['sourceWitnessAfterReadback'])
    # Keep all frozen67 geometry, normal, material, raw-byte and witness assertions.
    raw=PROOF67.read_text();tree=ast.parse(raw)
    source=ast.get_source_segment(raw,next(node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name=='validate'))
    patches=[("sha(Path(__file__).with_name('native-proof.py'))","sha(NATIVE68)"),
             ("sha(__file__)","sha(WITNESS68)")]
    for old,new in patches:
        assert source.count(old)==1,('Frozen67 proof validator drift',old);source=source.replace(old,new)
    namespace=dict(vars(frozen),NATIVE68=NATIVE68,WITNESS68=Path(__file__).resolve())
    exec(compile(source,str(PROOF67)+'[witness68-provenance]','exec'),namespace)
    namespace['validate'](data)


def verify(path,reviewed_sha):
    path=Path(path).resolve();assert path.is_relative_to(ROOT/'harness/out/rider-rebuild/selected-boot-witness68')
    result=pin(path,reviewed_sha);validate(json.loads(path.read_text()));return result
