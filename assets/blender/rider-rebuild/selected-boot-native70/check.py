"""CPU actual admission, exact-face routing and frozen-gate mutation fixtures."""
import ast
import copy
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import numpy as np
import intake
import author
import surface


def reject(fn,message=''):
    try:fn()
    except AssertionError as error:assert message in str(error),(message,str(error))
    else:raise AssertionError('Mutation accepted: '+message)


out=intake.OUTPUT_BASE/'cpu-fixture-no-native-output'
result=intake.admit(intake.RECEIPT,intake.RECEIPT_SHA,out);assert not out.exists()
proof=json.loads(intake.PROOF68.read_text())
assert proof['ownSourceCentroidDistanceM']==0 and proof['ownSourceNormalDot']>=.25
assert proof['ownFaceBVHNearest']['distanceM']>proof['fullBVHNearest']['distanceM']
checks=['Actual five-round67 candidate and full68 native proof admitted; the measured single-face BVH error remains explicit']
receipt=json.loads(intake.RECEIPT.read_text())
for keys,value in [(('candidateAttempts',),4),(('fixedPoint','complete'),False),(('sceneBudgetPassed',),True),
                   (('policy','minimumNormalDot'),.1),(('policy','targetErrorM'),.002),
                   (('nativeFaceAncestryProofRequired',),False),(('vertexNormalCensus','passed'),False),
                   (('faceCentroidCensus','minimumNormalDotRequired'),.1),(('faceCentroidCensus','passed'),False)]:
    mutated=copy.deepcopy(receipt);row=mutated
    for key in keys[:-1]:row=row[key]
    row[keys[-1]]=value
    reject(lambda:intake.metadata(mutated))
reject(lambda:intake.admit(intake.RECEIPT,'0'*64,out),'Exact actual67 receipt required')
reject(lambda:intake.admit(intake.RECEIPT,intake.RECEIPT_SHA,intake.OUTPUT_BASE),'Fresh native70 output required')
checks.append('Changed receipt SHA, incomplete joint pass, normal/distance policy, proof requirement and budget mutations reject')

source=intake.arrays(receipt['sourceArrayPackage']);candidate=intake.arrays(receipt['candidate'])
sp=source['positions'].reshape(-1,3).astype(float);sf=source['triangles'].reshape(-1,3)
tp=candidate['positions'].reshape(-1,3).astype(float);tf=candidate['triangles'].reshape(-1,3);original=candidate['originalVertexIds']
sm=source['faceMaterialIds'];tm=candidate['faceMaterialIds']
maps=surface.exact_maps(sp,sf,tp,tf,original,sm,tm)
matched=np.flatnonzero(maps['targetToSource']>=0)
assert len(matched)==receipt['faceCentroidCensus']['exactInheritedFaces']==5522
assert np.count_nonzero(maps['sourceToTarget']>=0)==5522
assert len(tf)-len(matched)==24934
source_id=278671;target_id=int(maps['sourceToTarget'][source_id]);assert target_id>=0
assert np.array_equal(original[tf[target_id]],sf[source_id])
assert np.array_equal(tp[tf[target_id]].mean(0),sp[sf[source_id]].mean(0))
mutated=tp.copy();mutated[0,0]+=.00001
reject(lambda:surface.exact_maps(sp,sf,mutated,tf,original,sm,tm),'moved original positions')
mutated=tm.copy();mutated[target_id]+=1
reject(lambda:surface.exact_maps(sp,sf,tp,tf,original,sm,mutated),'material differs')
changed=tf.copy();changed[target_id]=changed[target_id][::-1]
reversed_maps=surface.exact_maps(sp,sf,tp,changed,original,sm,tm)
assert reversed_maps['targetToSource'][target_id]==-1 and reversed_maps['sourceToTarget'][source_id]==-1
cyclic=tf.copy();cyclic[target_id]=np.roll(cyclic[target_id],1)
assert np.array_equal(surface.exact_maps(sp,sf,tp,cyclic,original,sm,tm)['targetToSource'],maps['targetToSource'])
fields=dict(candidate);fields['namedWeights']=candidate['namedWeights'].copy();fields['namedWeights'][0]+=.01
reject(lambda:intake.frozen.verify_arrays(source,fields,intake.arrays(receipt['returnedOriginalIndices']),intake.arrays(receipt['finalFanProtection']),receipt),'Original named fields')
checks.append('All5522 exact inherited faces map forward and reverse;24934 new faces remain unmatched; moved positions/materials/fields reject and reversed winding receives no ancestry bypass')

# Execute the adapted frozen37 surface function with counted BVH calls. This
# checks routing and real frozen assertions, without Blender or a substitute gate.
p=np.array([[0.,0.,0.],[1.,0.,0.],[0.,1.,0.],[1.,1.,0.]])
sfaces=np.array([[0,1,2],[1,3,2]],np.int32);tfaces=np.array([[0,1,2],[0,3,2]],np.int32)
class Tree:
    def __init__(self,distance):self.calls=0;self.distance=distance
    def find_nearest(self,point):
        self.calls+=1;return np.asarray(point),None,0,self.distance
class Engine:
    def __init__(self,target_faces,distance=0):self.target_faces=target_faces;self.distance=distance;self.trees=[]
    def points(self,obj):return p
    def triangles(self,obj):return sfaces if obj=='source' else self.target_faces
    def tree(self,points,faces):
        distance=self.distance[len(self.trees)] if isinstance(self.distance,tuple) else self.distance
        tree=Tree(distance);self.trees.append(tree);return tree

def fixture_maps(engine,source,target,sp,sf,tp,tf):
    return surface.exact_maps(sp,sf,tp,tf,np.arange(4),np.zeros(len(sf),int),np.zeros(len(tf),int))

with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as temporary:
    directory=Path(temporary);namespace={'np':np,'Vector':lambda value:value,'ROOT':intake.ROOT,'sha':intake.sha,
        'exact_face_maps70':fixture_maps,'PROOF68_PIN':result['actualProof68']}
    exec(compile(surface.adapted_source(),'surface70-fixture','exec'),namespace)
    engine=Engine(tfaces);rows=namespace['surface_checks'](engine,'source','target',.001,.25,directory,lambda row:None)
    assert rows['target-face-centroids']['exactInheritedAncestryBearings']==1
    assert rows['source-face-centroids']['exactInheritedAncestryBearings']==1
    assert rows['target-edge-midpoints']['exactInheritedAncestryBearings']==0
    assert engine.trees[0].calls==1+rows['target-edge-midpoints']['samples']
    assert engine.trees[1].calls==1
    altered=tfaces.copy();altered[1]=altered[1][::-1]
    reject(lambda:namespace['surface_checks'](Engine(altered),'source','target',.001,.25,directory,lambda row:None),'Original source surface/orientation bound failed')
    reject(lambda:namespace['surface_checks'](Engine(tfaces,.00101),'source','target',.001,.25,directory,lambda row:None),'Original source surface/orientation bound failed')
    reject(lambda:namespace['surface_checks'](Engine(tfaces,(0,.00101)),'source','target',.001,.25,directory,lambda row:None),'source-face-centroids')
    reject(lambda:namespace['surface_checks'](Engine(sfaces,.00101),'source','target',.001,.25,directory,lambda row:None),'target-edge-midpoints')
checks.append('Executed frozen surface routing: exact forward/reverse centroids use ancestry, every new face and every edge uses global BVH; new-face reversal and distance>1mm still fail')

expanded,*_=author.adapted_source();ast.parse(expanded);ast.parse(surface.adapted_source())
for file in Path(__file__).parent.glob('*.py'):ast.parse(file.read_text())
for token in ["spec['full'] == 8000 and spec['maximumSurfaceErrorM'] == 0.001",
              "'minimumNormalDot': 0.25, 'maximumSkinWeightL1': 0.3",
              "'maximumInfluences': 4, 'maximumRemovedMass': 0.001",
              "'maximumAdditionalAdjacentWeightL1': 0.002, 'supportEpsilon': 1e-05",
              'ORIENTATION57.install(engine, out, PROOF57)',
              "assert before == witness.retained(sources, rig)",
              "'bakeEligibility': 'LEFT_BOOT_ONLY_NOT_A_BILATERAL_FAMILY32_INPUT'",
              "'sourceIdentityAfterProduction': True",'assert np.array_equal(engine.triangles(target), f)']:
    assert token in expanded,token
assert expanded.index('bpy.ops.wm.save_as_mainfile')<expanded.index("report['objects'][name]['transfer'] = engine.transfer")
assert expanded.index('surface_checks(engine, source, target, spec')<expanded.index('engine.unwrap_family([target])')
assert 'ADMITTED63' not in expanded and 'ADMISSION63' not in expanded
assert "near = tree.find_nearest(Vector(point))" in surface.adapted_source()
checks.append('Raw-save precedes unchanged56/57 transfer; all37 skin/shape/surface/FOUR/source gates and left-boot-only bake exclusion remain')

evidence=intake.ROOT/'docs/evidence/rider-rebuild/selected-boot-native70';evidence.mkdir(parents=True,exist_ok=True)
(evidence/'cpu-admission.json').write_text(json.dumps(result,indent=2)+'\n')
(evidence/'fixtures.json').write_text(json.dumps({'status':'CPU_NATIVE70_ADMISSION_AND_SURFACE_FIXTURES_PASSED_NATIVE_PENDING',
    'constructor':result['constructor'],'proof68':result['actualProof68'],'checks':checks,
    'exactFaceAncestry':{'targetToSource':5522,'sourceToTarget':5522,'newTargetFacesUsingNativeBVH':24934,
        'proofSource278671CurrentTargetFaceId':target_id},
    'limits':'CPU admission and routing checks only. No Blender/native/atlas job, scene allocation, bilateral bake or art acceptance.'},indent=2)+'\n')
print('\n'.join('PASS: '+check for check in checks))
