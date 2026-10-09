"""CPU representation/lifecycle and protected-field mutations; no native read."""
import ast
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import witness68 as w

file=Path(__file__).with_name('native-proof.py');spec=importlib.util.spec_from_file_location('native68_check',file)
adapter=importlib.util.module_from_spec(spec);spec.loader.exec_module(adapter)
for path in Path(__file__).parent.glob('*.py'):ast.parse(path.read_text())
expanded=adapter.adapted_source();ast.parse(expanded)
w.pin(w.WITNESS,w.WITNESS_SHA);w.pin(w.PRODUCTION,w.PRODUCTION_SHA)
source=w.WITNESS.read_text();tree=ast.parse(source)
fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='source')
returned=next(n.value for n in ast.walk(fn) if isinstance(n,ast.Return))
groups=next(value for key,value in zip(returned.keys,returned.values) if isinstance(key,ast.Constant) and key.value=='groups')
assert isinstance(groups,ast.ListComp) and isinstance(groups.elt,ast.Tuple)
production=json.loads(w.PRODUCTION.read_text());expected=production['sourceWitness']
live=copy.deepcopy(expected)
for row in live['sources'].values():row['groups']=[tuple(group) for group in row['groups']]
result,actual_json,expected_json=w.comparison(live,expected)
assert live!=expected and result['equal'] and actual_json==expected_json
assert result['valueDifferenceCount']==0 and len(result['representationDifferences'])==6
assert all(row['kind']=='sequence-representation' and '.groups[' in row['path'] for row in result['representationDifferences'])
checks=['Witness31 AST and actual63 JSON prove six tuple/list group-row mismatches; full JSON values remain equal in this CPU reproduction']

frozen37=w.ROOT/'assets/blender/rider-rebuild/selected-production-constructor37/author.py'
w.pin(frozen37,'b5ec57c735a1e2e4c030f14d90597097b043fbe59f945793de42bd134e7556cc')
recipe=frozen37.read_text()
assert recipe.index('before = witness.retained(sources, rig)')<recipe.index("assert before == witness.retained(sources, rig), 'Selected source changed during construction'")
assert recipe.index("'sourceWitness': before")<recipe.index('bpy.ops.wm.save_as_mainfile')<recipe.index('engine.transfer(source, target')
assert production['native']['sha256']==w.NATIVE63_SHA and production['sourceMaster']['sha256']==w.NATIVE34_SHA
assert production['native']['path'].endswith('UNACCEPTED-constructor62-before-transfer.blend')
checks.append('Frozen37/63 lifecycle binds production63.sourceWitness to the exact pre-transfer raw save, after source equality was rechecked')

left='ActualSelectedBoot.L';uv=next(iter(expected['sources'][left]['uv']));image=next(iter(expected['materials']['images']))
mutations=[(('sources',left,'positionSHA256'),'changed'),(('sources',left,'edgeSHA256'),'changed'),
    (('sources',left,'weightSHA256'),'changed'),(('sources',left,'materialIndexSHA256'),'changed'),
    (('sources',left,'uv',uv,'sha256'),'changed'),(('sources',left,'groups',0,1),'changed'),
    (('sources',left,'matrixWorld',0,3),.1),(('sources',left,'modifiers',0,'objectReferences','object'),'changed'),
    (('materials','graphSHA256'),'changed'),(('materials','images',image,'packedSHA256'),'changed'),
    (('rig','bones',0,'head',0),.1),(('rig','bones',0,'useDeform'),False)]
for keys,value in mutations:
    mutated=copy.deepcopy(actual_json);row=mutated
    for key in keys[:-1]:row=row[key]
    row[keys[-1]]=value
    difference,_,_=w.comparison(mutated,expected)
    assert not difference['equal'] and difference['valueDifferenceCount']>=1,keys
mutated=copy.deepcopy(actual_json);del mutated['sources'][left]['uv'];assert not w.comparison(mutated,expected)[0]['equal']
mutated=copy.deepcopy(actual_json);mutated['unexpected']=True;assert not w.comparison(mutated,expected)[0]['equal']
mutated=copy.deepcopy(actual_json);mutated['sources'][left]['groups'].reverse();assert not w.comparison(mutated,expected)[0]['equal']
try:w.comparison({'value':float('nan')},{'value':0})
except ValueError:pass
else:raise AssertionError('Nonfinite JSON witness accepted')
checks.append('Geometry, topology, UV, fields, bind, modifier, material/PBR, rig, missing/unexpected fields and group order mutations all reject; no tolerance or field exclusion')

with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as temporary:
    row=w.persist_comparison(Path(temporary),live,expected,'fixture')
    assert row['equal'] is True and row['livePythonEquality'] is False
    assert set(row['files'])=={'actual','expected','diff'}
    w.validate_comparison(row)
    bad=copy.deepcopy(live);bad['sources'][left]['positionSHA256']='changed'
    failure=w.persist_comparison(Path(temporary),bad,expected,'failure')
    assert failure['equal'] is False and all((w.ROOT/item['path']).exists() for item in failure['files'].values())
    try:w.validate_comparison(failure)
    except AssertionError:pass
    else:raise AssertionError('Real source mutation accepted')
    # Equal forged witnesses cannot replace the pinned saved-stage expectation.
    forged=w.persist_comparison(Path(temporary),bad,bad,'forged')
    try:w.validate_comparison(forged)
    except AssertionError:pass
    else:raise AssertionError('Wrong saved-stage witness accepted')
assert expanded.index("p.persist_comparison(out,before,expected")<expanded.index("assert report['sourceWitnessReadback']['equal']")
assert "before==json.loads(p.PRODUCTION.read_text())['sourceWitness']" not in expanded
for token in ['before==after','tree=engine.tree(sp,sf);near=tree.find_nearest(query)',
              'assert np.array_equal(sp.ravel(),dense[\'positions\'])',
              'assert np.array_equal(original[tf[p.TARGET]],sf[p.OWN])',
              "report['raw63BytesUnchanged']=p.sha(p.NATIVE63)==p.NATIVE63_SHA",'p.validate(report)']:
    assert token in expanded,token
assert 'save_as_mainfile' not in expanded
checks.append('Whole actual/expected/diff files persist before mismatch assertion; wrong saved-stage substitution rejects; all frozen67 geometry/raw-byte checks and live before/after guard remain')

out=w.ROOT/'docs/evidence/rider-rebuild/selected-boot-witness68';out.mkdir(parents=True,exist_ok=True)
(out/'finding.json').write_text(json.dumps({'status':'CPU_SERIALIZATION_CAUSE_PROVEN_ACTUAL_READBACK_PENDING','acceptedArt':False,
    'production':w.pin(w.PRODUCTION,w.PRODUCTION_SHA),'witnessRecipe':w.pin(w.WITNESS,w.WITNESS_SHA),
    'frozenNativeProof':w.pin(w.NATIVE67,w.NATIVE67_SHA),
    'knownSufficientFailure':'Live source.groups rows are Python tuples; production63 JSON rows are lists. Direct live-dict equality to JSON-dict is false even when all values match.',
    'cpuReproduction':result,'savedStage':'Capture before construction; exact witness check immediately before raw63 save; raw63 save precedes transfer. The original expected sourceWitness is correct.',
    'correction':'Compare full canonical JSON values, persist actual/expected/diff before asserting, preserve live-before==live-after and every frozen67 geometric/raw guard.',
    'limits':'Native67 did not persist its actual live witness. Other reopen differences are unknown until68 runs; no actual source unchanged claim, native proof or qualification is made.'},indent=2)+'\n')
(out/'fixtures.json').write_text(json.dumps({'status':'CPU_WITNESS68_FIXTURES_PASSED_NATIVE_PENDING','checks':checks,
    'limits':'CPU schema reproduction only; no Blender launch or actual readback.'},indent=2)+'\n')
print('\n'.join('PASS: '+check for check in checks))
