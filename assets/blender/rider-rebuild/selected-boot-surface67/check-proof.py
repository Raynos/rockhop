"""Synthetic schema mutations only; never claims an actual native67 proof."""
import ast
import copy
import json
from pathlib import Path
import numpy as np
import proof as p

for file in Path(__file__).parent.glob('*.py'):ast.parse(file.read_text())
a=p.load(p.ADMISSION63,'check67_admission63');receipt=json.loads(a.RECEIPT.read_text());source=a.array_package(receipt['sourceArrayPackage'])
sp=source['positions'].reshape(-1,3).astype(float);sf=source['triangles'].reshape(-1,3)
tri=sp[sf[p.OWN]];bearing=sp[sf[p.BEARING]];centroid=tri.mean(0);query=centroid.astype(np.float32).astype(float)
normal=np.cross(tri[1]-tri[0],tri[2]-tri[0]);normal/=np.linalg.norm(normal)
bn=np.cross(bearing[1]-bearing[0],bearing[2]-bearing[0]);bn/=np.linalg.norm(bn)
# This deliberately synthetic in-memory record exercises the verifier schema.
# No diagnostic.json is written and no future native closest point is claimed.
fixture={'status':'CONFIRMED_EXACT_INHERITED_FACE_NATIVE_BEARING_UNACCEPTED',
    'recipeSHA256':p.sha(Path(__file__).with_name('native-proof.py')),'proofRecipeSHA256':p.sha(p.__file__),
    'production':p.pin(p.PRODUCTION,p.PRODUCTION_SHA),'native63':{'sha256':p.NATIVE63_SHA},'source34':{'sha256':p.NATIVE34_SHA},
    'targetFaceId':p.TARGET,'ownSourceFaceId':p.OWN,'targetOriginalVertexIds':sf[p.OWN].tolist(),'ownSourceOriginalVertexIds':sf[p.OWN].tolist(),
    'targetPositions':tri.tolist(),'ownSourcePositions':tri.tolist(),'materialsExact':True,'materialIndex':int(source['faceMaterialIds'][p.OWN]),
    'sourceWitnessExact':True,'sourceWitnessUnchangedAfterProbe':True,'raw63BytesUnchanged':True,'source34BytesUnchanged':True,
    'centroidFloat64':centroid.tolist(),'queryFloat32':query.tolist(),'targetGeometricNormal':normal.tolist(),
    'ownSourceGeometricNormal':normal.tolist(),'ownSourceNormalDot':float(normal@normal),'ownSourceCentroidDistanceM':0,
    'fullBVHNearest':{'sourceFaceId':p.BEARING,'point':query.tolist(),'distanceM':6.51925802230835e-09,
        'normalDot':float(normal@bn),'originalVertexIds':sf[p.BEARING].tolist(),'positions':bearing.tolist(),'geometricNormal':bn.tolist()},
    'ownFaceBVHNearest':{'sourceFaceId':p.OWN,'point':query.tolist(),'distanceM':0}}
p.validate(fixture)
mutations=[(('sourceWitnessExact',),False),(('raw63BytesUnchanged',),False),(('source34BytesUnchanged',),False),
    (('ownSourceFaceId',),p.BEARING),(('targetOriginalVertexIds',0),0),(('targetPositions',0,0),0),
    (('fullBVHNearest','sourceFaceId'),p.OWN),(('fullBVHNearest','normalDot'),1),
    (('ownSourceNormalDot',),.2),(('materialsExact',),False),(('materialIndex',),3),
    (('queryFloat32',0),float(query[0])+1e-12),(('fullBVHNearest','positions',0,0),0)]
for keys,value in mutations:
    altered=copy.deepcopy(fixture);row=altered
    for key in keys[:-1]:row=row[key]
    row[keys[-1]]=value
    try:p.validate(altered)
    except AssertionError:pass
    else:raise AssertionError('Invalid proof mutation accepted: '+repr(keys))
script=Path(__file__).with_name('native-proof.py').read_text()
assert 'save_as_mainfile' not in script and 'from_pydata' not in script
assert script.index("report['fullBVHNearest']")<script.index("own_tree=engine.tree")
assert script.index("report['sourceWitnessUnchangedAfterProbe']")<script.index('p.validate(report)')
out=p.ROOT/'docs/evidence/rider-rebuild/selected-boot-surface67'
(out/'proof-fixtures.json').write_text(json.dumps({'status':'SYNTHETIC_PROOF_SCHEMA_FIXTURES_PASSED_ACTUAL_NATIVE_PROOF_PENDING',
    'mutationCases':len(mutations),'sourceASTParsed':True,'partialBearingSavedBeforeOwnFaceProbe':True,
    'limits':'Synthetic verifier fixtures only. No Blender call, actual native proof, nearest point or native policy change.'},indent=2)+'\n')
print('PASS: synthetic proof schema and13 ancestry/geometry/material/witness/normal/query mutations; actual native proof remains pending')
