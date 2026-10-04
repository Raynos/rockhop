"""Read existing glTF bindings and archived captures; no new pose capture."""
import gzip,hashlib,json,struct
from pathlib import Path
import numpy as np
root=Path.cwd();out=Path(__file__).resolve().parent;qa=out.parent
base=root/'assets/blender/hero-remaster/rider/anatomical-foundation-2026-10-03/user-agent1'
normalize=lambda s:s.replace('.','').replace('_','')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def read(path):
    b=path.read_bytes();length=struct.unpack_from('<I',b,12)[0];g=json.loads(b[20:20+length]);binary=b[28+length:]
    def acc(i):
        a=g['accessors'][i];v=g['bufferViews'][a['bufferView']];d=np.dtype({5126:'<f4',5125:'<u4',5123:'<u2',5121:'<u1'}[a['componentType']]);cols={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}[a['type']]
        return np.ndarray((a['count'],cols),dtype=d,buffer=binary,offset=v.get('byteOffset',0)+a.get('byteOffset',0),strides=(v.get('byteStride',cols*d.itemsize),d.itemsize)).copy()
    skin=g['skins'][0];names=[g['nodes'][i]['name'] for i in skin['joints']];ib=acc(skin['inverseBindMatrices']).reshape(-1,4,4).transpose(0,2,1).astype(float)
    body=next(m for m in g['meshes'] if m['name']=='base.002')['primitives'][0]
    return names,ib,{k:acc(i) for k,i in body['attributes'].items()},acc(body['indices'])
p09=base/'appearance09/rider-source-normals.glb';p10=base/'appearance10/rider-source-normals.glb'
n09,ib09,a09,t09=read(p09);n10,ib10,a10,t10=read(p10)
assert n09==n10 and np.array_equal(ib09,ib10)
fields={k:np.array_equal(a09[k],a10[k]) for k in ['POSITION','JOINTS_0','WEIGHTS_0','_SOURCE_ID']};assert all(fields.values()) and np.array_equal(t09,t10)
finding=json.loads((qa/'garment47/finding.json').read_text());runtime_names=finding['engineContract']['jointOrder'];assert list(map(normalize,runtime_names))==list(map(normalize,n10))
first=qa/'garment47/first.weights.ndjson.gz';repeat=qa/'garment47/repeat.weights.ndjson.gz';assert first.read_bytes()==repeat.read_bytes()
with gzip.open(first,'rt') as f:rows=[json.loads(line) for line in f]
assert len(rows)==703 and max(row['manual4ResidualM'] for row in rows)==0
K=np.array([row['matrices'] for row in rows]).reshape(703,51,4,4).transpose(0,1,3,2);W=K@np.linalg.inv(ib10)
film_path=qa/'presentation50/report.json.gz';film=json.loads(gzip.decompress(film_path.read_bytes()));samples=film['cases'][0]['samples'][:176]
worst=(0,None);per_joint=np.zeros(51)
for sample in samples:
    tick=int(sample['label'].split('input ')[1].split('/')[0]);by_name={normalize(x[0]):np.array(x[1:]).reshape(4,4).T for x in sample['matrices']}
    for j,name in enumerate(n10):
        gap=float(np.abs(W[tick-1,j]-by_name[normalize(name)]).max());per_joint[j]=max(per_joint[j],gap)
        if gap>worst[0]:worst=(gap,{'inputTick':tick,'joint':name})
report={'status':'EXACT_BIND_AND_BODY_FIELDS_DISTINCT_EXISTING_POSE_STREAMS','creationDate':'2026-10-04','pins':{str(p.relative_to(root)):sha(p) for p in [p09,p10,first,repeat,film_path,qa/'garment47/finding.json',root/'harness/hero-remaster/user-agent3-2026-10-03/garment-engine-capture.mjs',root/'harness/hero-remaster/user-agent3-2026-10-03/garment-engine-runtime.mjs',root/'harness/hero-remaster/user-agent3-2026-10-03/wide-bike-presentation.mjs']},'recipeSHA256':sha(Path(__file__)),'bodyAttributesByteExact09Vs10':fields,'bodyTriangleIndicesByteExact09Vs10':True,'inverseBindsByteExact09Vs10':True,'runtimeJointOrderMatchesSemanticExportOrder':True,'actual47All703NumericalRowsRepeatByteExact':True,'actual47ManualFourResidualM':0,'actual47VsActual50BoneWorldComparison':{'samples':176,'maximumAbsMatrixDifference':worst[0],'witness':worst[1],'maximumPerJoint':dict(zip(n10,per_joint.tolist()))},'conclusion':'Actual47 and actual50 have different existing bone-world poses. Shared bind/body identity disproves an export-bind explanation for this discrepancy. Do not synchronize film50 with numeric47. Cause not established; capture recipes differ in render cadence and wrapper presence. Native stream remains separately proven against current body fields.'}
(out/'bind-and-stream-proof.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='pins' and k!='actual47VsActual50BoneWorldComparison'}))
