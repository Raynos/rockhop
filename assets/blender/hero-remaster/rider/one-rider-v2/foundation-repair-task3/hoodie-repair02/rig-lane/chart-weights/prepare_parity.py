from pathlib import Path
import numpy as np,json,hashlib
HERE=Path(__file__).resolve().parent
rows=json.loads((HERE/'finite-gates.json').read_text())['rows']
for variant in ['chart-ownership','chart-anatomical']:
 folder=HERE/('runtime-'+variant);folder.mkdir(exist_ok=True);wanted=[]
 for row in rows:
  if row['variant']!=variant:continue
  if not(row['holdout']or row['probe']=='neutral'or(row['probe']=='forward'and row['fraction']==1)or(row['probe']=='neutral_elbow'and row['fraction']==90)or(row['probe']=='actual_source34'and row['fraction']==304)):continue
  data=np.load(row['path']);refs=[]
  for i in range(5):
   path=folder/f'{len(wanted):03d}-{i}.f64';data[f'p{i}'].astype('<f8').tofile(path);refs.append(str(path))
  wanted.append({'id':Path(row['path']).stem,'matrices':data['matrices'].tolist(),'references':refs,'poseSHA256':hashlib.sha256(Path(row['path']).read_bytes()).hexdigest()})
 glb=HERE/'exports'/(variant+'.glb');(folder/'manifest.json').write_text(json.dumps({'glb':str(glb),'frozenGLBSHA256':hashlib.sha256(glb.read_bytes()).hexdigest(),'poses':wanted,'morphWeightsAllZero':True,'toleranceM':.00002},indent=2))
 print(variant,len(wanted))
