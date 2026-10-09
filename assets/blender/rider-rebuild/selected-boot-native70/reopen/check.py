"""CPU fixtures for the pinned saved-native qualifier; no Blender import/run."""
import ast
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace as NS
import numpy as np
import qualify as q


def reject(fn,message=''):
    try:fn()
    except AssertionError as error:assert message in str(error),(message,str(error))
    else:raise AssertionError('Mutation accepted: '+message)


orientation,whole=q.dependencies();raw=q.readonly_transfer_source(orientation);ast.parse(raw)
production=json.loads(q.PRODUCTION.read_text());q.metadata(production,q.PRODUCTION_SHA)
q.intake.pin(q.NATIVE,q.NATIVE_SHA)
reject(lambda:q.metadata(production,'0'*64),'Exact actual70')
for key,value in [('acceptedArt',True),('restGeometryPassed',False),('sourceInputBytesUnchanged',False),('bakeEligibility','BILATERAL')]:
    mutated=copy.deepcopy(production);mutated[key]=value;reject(lambda:q.metadata(mutated,q.PRODUCTION_SHA))
checks=['Actual saved production70 and final native hashes pass admission; stale SHA, missing rest/source proof and broadened acceptance reject']

witness=production['sourceWitness'];assert len(witness['rig']['bones'])==75
assert whole.comparison(witness,witness)[0]['equal']
tuple_form=copy.deepcopy(witness)
for source in tuple_form['sources'].values():source['groups']=[tuple(group) for group in source['groups']]
assert whole.comparison(tuple_form,witness)[0]['equal']
for path in [('sources','ActualSelectedBoot.L','weightSHA256'),('materials','graphSHA256'),('rig','bones',0,'matrixLocal',0,0)]:
    changed=copy.deepcopy(witness);row=changed
    for key in path[:-1]:row=row[key]
    row[path[-1]]=row[path[-1]]+1 if isinstance(row[path[-1]],(int,float)) else 'changed'
    assert not whole.comparison(changed,witness)[0]['equal']
checks.append('Whole saved witness accepts tuple/list JSON representation only; full named fields, selected PBR and 75-rest matrix changes reject')

transfer=production['objects']['ActualSelectedBoot.L']['transfer']
def package(pin):
    q.intake.pin(q.ROOT/pin['path'],pin['sha256'])
    with np.load(q.ROOT/pin['path']) as archive:return dict(archive)
reference=package(transfer['sourceTransfer']);fields=package(transfer['fourFieldDiagnostics']['arrays'])
constructor=json.loads(q.intake.RECEIPT.read_text());source=q.intake.arrays(constructor['sourceArrayPackage']);candidate=q.intake.arrays(constructor['candidate'])
assert np.array_equal(reference['targetRestLocal'],candidate['positions'].reshape(-1,3))
assert np.array_equal(reference['sourceVertexIds'],source['triangles'].reshape(-1,3)[reference['sourceFaceIds']])
assert np.array_equal(reference['sourceReferenceTrianglesLocal'],source['positions'].reshape(-1,3)[reference['sourceVertexIds']])
assert np.array_equal(fields['finalFourFields'],candidate['namedWeights'].reshape(-1,3))
for pin in [transfer['sourceTransfer'],transfer['fourFieldDiagnostics']['arrays']]+[row['arrays'] for row in production['sourceSurfaceSamples'].values()]:
    values=package(pin);assert q.array_diff(values,values)==[]
    key=next(key for key,value in values.items() if value.dtype.kind in 'fiu')
    changed={key:value.copy() for key,value in values.items()};changed[key].flat[0]=123
    assert q.array_diff(changed,values)
    changed=dict(values);changed[key]=changed[key].astype(np.float64);assert q.array_diff(changed,values)
checks.append('Actual source-reference/target-rest arrays and original named FOUR fields match; all five saved measurement packages reject value and dtype drift, preserving intentional distance-only NaNs')

for required in ['Wrong-facing source correspondence','Anatomical field correspondence escaped its source',
                 'Selected source detail exceeds geometry bound','Target face chord leaves selected source',
                 'FOUR projection changes source support beyond declared bounds','correspondence56.evaluate','ancestry57']:
    assert required in raw,required
for forbidden in ['vertex_groups.clear','vertex_groups.new','shape_key_add','modifiers.new','matrix_world=','save_as_mainfile']:
    assert forbidden not in raw,forbidden

class Groups(list):
    def clear(self):raise AssertionError('Unexpected scene group mutation')
    def new(self,**kwargs):raise AssertionError('Unexpected scene group mutation')

class Tree:
    def __init__(self,distance,index,bad_stage):self.distance=distance;self.index=index;self.bad_stage=bad_stage;self.calls=0
    def find_nearest(self,point,limit):
        self.calls+=1
        missing=(self.bad_stage=='reverse' and self.index==1) or (self.bad_stage=='chord' and self.index==0 and self.calls>3)
        return (np.asarray(point) if self.distance<=limit and not missing else None,None,0,self.distance)

def run_fixture(directory,normal=1.,weight=1.,distance=0.,count=1,bad_stage=None):
    p=np.array([[0.,0.,0.],[1.,0.,0.],[0.,1.,0.]]);f=np.array([[0,1,2]],np.int32)
    names=['group'+str(i) for i in range(count)];groups=Groups(NS(name=name) for name in names)
    source=NS(name='source',vertex_groups=groups)
    target=NS(name='target',vertex_groups=groups,data=NS(vertices=[NS(normal=np.array([0.,0.,normal])) for _ in range(3)]))
    trees=[]
    def tree(p,f):
        item=Tree(distance,len(trees),bad_stage);trees.append(item);return item
    engine={'np':np,'hashlib':hashlib,'json':json,'ROOT':q.ROOT,'sha':q.intake.sha,'Vector':lambda p:p,
        'points':lambda obj:p,'triangles':lambda obj:f,'tree':tree,
        'skin_rows':lambda obj,names:np.full((3,count),(1. if obj is source else weight)/count),
        'ancestry57':lambda *args:(np.tile([0.,0.,1.],(3,1)),np.arange(3)),
        'correspondence56':orientation.kernel.Audit()}
    config=json.loads((q.intake.BASE/'selected-rider-production25/input.json').read_text())
    exec(compile(raw,'readonly-reopen70-fixture','exec'),engine)
    return engine['transfer'](source,target,NS(data=NS(bones=names)),{'maximumSurfaceErrorM':.001},'full',config,directory)

with tempfile.TemporaryDirectory(dir=q.HERE) as tmp:
    out=Path(tmp);passed=run_fixture(out)
    assert passed['maximumTargetVertexDistanceM']==passed['maximumSourceSkinL1']==0 and passed['minimumSourceNormalDot']==1
    reject(lambda:run_fixture(out,normal=-1),'Wrong-facing source correspondence')
    reject(lambda:run_fixture(out,weight=.5),'Anatomical field correspondence escaped its source')
    reject(lambda:run_fixture(out,distance=.00101),'Target vertex escapes selected source')
    reject(lambda:run_fixture(out,bad_stage='reverse'),'Selected source detail exceeds geometry bound')
    reject(lambda:run_fixture(out,bad_stage='chord'),'Target face chord leaves selected source')
    reject(lambda:run_fixture(out,count=6),'FOUR projection changes source support beyond declared bounds')
checks.append('Executed unchanged frozen transfer prefix without mutation: valid case passes; reversed vertex normal, skin L1>.3, target/reverse/chord distance failures and removed mass>.001 reject')

for path in q.HERE.glob('*.py'):ast.parse(path.read_text())
native_source=Path(q.__file__).read_text()
assert 'save_as_mainfile' not in native_source and 'unwrap_family' not in native_source
assert native_source.index("compare('source-before'")<native_source.index("namespace['transfer']")
assert "compare('target-after'" in native_source and "surface.install(namespace" in native_source
assert 'bpy' not in sys.modules
checks.append('Native recipe parses without Blender; persists whole witness before assertions, uses existing surface70 and compares target/source after read-only checks; no native save or unwrap')

evidence=q.ROOT/'docs/evidence/rider-rebuild/selected-boot-native70/reopen-source';evidence.mkdir(parents=True,exist_ok=True)
(evidence/'fixtures.json').write_text(json.dumps({'status':'CPU_SAVED_NATIVE70_REOPEN_FIXTURES_PASS_NATIVE_NOT_RUN',
    'production':q.intake.pin(q.PRODUCTION,q.PRODUCTION_SHA),'native':q.intake.pin(q.NATIVE,q.NATIVE_SHA),
    'checks':checks,'acceptedArt':False,'limits':'Source and CPU fixtures only. Parent guarded saved-native reopen remains pending.'},indent=2)+'\n')
print('\n'.join('PASS: '+check for check in checks))
