from motion import *
import hashlib
folder=HERE/'runtime';folder.mkdir(exist_ok=True)
manifest=json.loads((HERE/'manifest.json').read_text());wanted=[]
for row in manifest['rows']:
 k,t,v=row['kind'],row['fraction'],row['variant']
 if (k=='neutral'and v=='legacy')or(k in ['horizontal','overhead','functional_overhead','forward','elbow','legacy_elbow']and t==1 and v in ['fixed_ik','girdle'])or(k=='functional_overhead'and t in [.5,.625]and v=='girdle')or(k in ['forward','elbow']and t in [.375,.625]and v=='girdle')or(k in ['wrist_flex','wrist_deviation','forearm_twist']and abs(t)==1 and v=='girdle'):
  data=np.load(row['path']);refs=[]
  for i in range(5):
   path=folder/f'{len(wanted):03d}-{i}.f64';data[f'p{i}'].astype('<f8').tofile(path);refs.append(str(path))
  wanted.append({'id':f'{v}-{k}-{t:g}','matrices':data['matrices'].tolist(),'references':refs,'poseSHA256':hashlib.sha256(Path(row['path']).read_bytes()).hexdigest()})
# Include actual game D and clean elbow-only probes in the same stock skin test.
for filename in ['source34-manifest.json','neutral-elbow-manifest.json']:
 doc=json.loads((HERE/filename).read_text())
 for row in doc['rows']:
  if filename=='neutral-elbow-manifest.json'and not(row['side']=='both'and row['degrees']in[0,30,60,90,120]):continue
  data=np.load(row['path']);refs=[]
  for i in range(5):
   path=folder/f'{len(wanted):03d}-{i}.f64';data[f'p{i}'].astype('<f8').tofile(path);refs.append(str(path))
  wanted.append({'id':row['id'],'matrices':data['matrices'].tolist(),'references':refs,'poseSHA256':hashlib.sha256(Path(row['path']).read_bytes()).hexdigest()})
(folder/'manifest.json').write_text(json.dumps({'glb':str(HERE/'input/v7.glb'),'frozenGLBSHA256':hashlib.sha256((HERE/'input/v7.glb').read_bytes()).hexdigest(),'poses':wanted,'morphWeightsAllZero':True,'toleranceM':.00002},indent=2))
print(len(wanted))
