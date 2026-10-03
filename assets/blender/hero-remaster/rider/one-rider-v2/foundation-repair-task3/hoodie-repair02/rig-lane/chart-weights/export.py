"""Isolated chart-weight GLB exports; only skin index/weight BIN rows change."""
from pathlib import Path
import sys,json,hashlib,numpy as np
CHART=Path(__file__).resolve().parent;sys.path.insert(0,str(CHART.parents[2]/'scripts'));from glb import GLB
original=CHART.parent/'mechanical-suite/input/v7.glb';out=CHART/'exports';out.mkdir(exist_ok=True)
for variant in ['chart-ownership','chart-anatomical']:
 g=GLB(original);pr=[p for m in g.j['meshes']for p in m['primitives']];w=np.load(CHART/(variant+'.npz'))
 for i,p in enumerate(pr):
  weights=w[f'W{i}'];slots=np.argsort(weights,axis=1)[:,-4:];values=np.take_along_axis(weights,slots,axis=1);g.array(p['attributes']['JOINTS_0'])[:]=slots;g.array(p['attributes']['WEIGHTS_0'])[:]=values
 path=out/(variant+'.glb');g.write(path)
 source=GLB(original);candidate=GLB(path);assert source.j==candidate.j
 unchanged=[]
 for i,a in enumerate(source.j['accessors']):
  changed=any(i in[p['attributes']['JOINTS_0'],p['attributes']['WEIGHTS_0']]for p in pr)
  if not changed and 'bufferView'in a:assert np.array_equal(source.array(i),candidate.array(i));unchanged.append(i)
 record={'variant':variant,'originalGLBSHA256':hashlib.sha256(original.read_bytes()).hexdigest(),'weightsNPZSHA256':hashlib.sha256((CHART/(variant+'.npz')).read_bytes()).hexdigest(),'exportGLBSHA256':hashlib.sha256(path.read_bytes()).hexdigest(),'allGLTFJSONExact':True,'allNonSkinAccessorsExact':True,'unchangedAccessorCount':len(unchanged),'onlySkinIndexWeightBINRowsChanged':True,'limits':['Diagnostic unaccepted export; no production integration or gameplayclip change.','Exact frozen textures/UVs/normals/geometry/bind/metadata/animations retained; inherited morphs/clips are not newly qualified.','Frozen unadapted freshC19 contract retained. Explicit body34/name/contact mapping and baked-conditioning opt-out are required before gameplay integration; never recondition these weights silently.']};(out/(variant+'-provenance.json')).write_text(json.dumps(record,indent=2));print(json.dumps(record))
