"""Prepare independent raw glTF expectations and rest/bind gate for stock Three CPU test."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
ROOT=Path(__file__).resolve().parents[3];Q=ROOT/'hoodie-repair02/qa-lane'
# Reuse established independently implemented accessor/TRS/SLERP/LBS evaluator read-only;
# omit its original workflow and output mutations.
source=(ROOT/'runtime/prepare_references.py').read_text();func=source[source.index('def decode('):source.index("manifest={'tolerance_m'")];ns={};exec('import struct,json,copy,hashlib\nfrom pathlib import Path\nimport numpy as np\n'+func,ns)
for k in ['decode','array','pose','vertices']:globals()[k]=ns[k]
input_path=Path(sys.argv[1]).resolve()if len(sys.argv)>1 else Q/'C19-source.glb';label=sys.argv[2]if len(sys.argv)>2 else input_path.stem
out=Q/'runtime'/label;out.mkdir(parents=True,exist_ok=True);refsdir=out/'references';refsdir.mkdir(exist_ok=True)
doc,bin,sha=decode(input_path);empty={'samplers':[],'channels':[]};nodes,world=pose(doc,bin,empty,0);bones=[]
for sk in doc['skins']:
 inv=array(doc,bin,sk['inverseBindMatrices']).reshape(-1,4,4).transpose(0,2,1)
 for j,i in enumerate(sk['joints']):
  m=world[i];bones.append({'name':nodes[i].get('name'),'node':i,'world_position_m':m[:3,3].tolist(),'determinant':float(np.linalg.det(m[:3,:3])),'axis_lengths':np.linalg.norm(m[:3,:3],axis=0).tolist(),'orthogonality_max_error':float(abs(m[:3,:3].T@m[:3,:3]-np.eye(3)).max()),'inverse_bind_identity_max_error':float(abs(m@inv[j]-np.eye(4)).max())})
rest_drift=[]
for mi,pi,p in vertices(doc,bin,nodes,world):
 src=array(doc,bin,doc['meshes'][mi]['primitives'][pi]['attributes']['POSITION']);rest_drift.append({'mesh':mi,'primitive':pi,'max_distance_m':float(np.linalg.norm(p-src,axis=1).max())})
refs=[];clips=[];authored=[]
for clip in doc.get('animations',[]):
 times=sorted(set(float(x)for s in clip['samplers']for x in array(doc,bin,s['input']).ravel()));duration=times[-1]
 probes=sorted(set([times[0],duration]+[duration*x for x in [.137,.371,.613,.887]]+[times[i]for i in np.linspace(0,len(times)-1,min(9,len(times))).astype(int)]))
 if clip['name']in ['foundation_stand_to_sit','hoodie_compression_stand_to_sit']:probes=sorted(set(probes+times+[(a+b)*.5 for a,b in zip(times[:-1],times[1:])]))
 clips.append({'name':clip['name'],'times':probes})
 for k,t in enumerate(probes):
  for mi,pi,p in vertices(doc,bin,*pose(doc,bin,clip,t)):
   origin='independent raw glTF accessor+TRS/SLERP+morph-before-matrix-LBS evaluator'
   if clip['name']in ['foundation_stand_to_sit','hoodie_compression_stand_to_sit']:
    key=int(round(t*24));fp=ROOT/'hoodie-repair02/poses'/f'{label}-movie-candidate-{key:03d}.npz'
    if label=='v7'and not fp.exists():fp=ROOT/'hoodie-repair02/poses'/f'v6-movie-candidate-{key:03d}.npz'
    if fp.exists()and abs(t-key/24)<1e-7:
     global_primitive=sum(len(m['primitives'])for m in doc['meshes'][:mi])+pi;authored_position=np.load(fp)[f'p{global_primitive}'];delta=np.linalg.norm(p-authored_position,axis=1);authored.append({'time_s':t,'key':key,'mesh':mi,'primitive':pi,'max_m':float(delta.max()),'rms_m':float(np.sqrt(np.mean(delta*delta)))});p=authored_position;origin='root independently authored dense-field all-primitive pose NPZ; verifies export implementation in addition to raw decoder agreement'
   name=f'{clip["name"]}-{k:03d}-{mi}-{pi}.f32';p.astype('<f4').tofile(refsdir/name);refs.append({'clip':clip['name'],'time':t,'mesh_index':mi,'primitive_index':pi,'path':'references/'+name,'format':'float32le','reference_origin':origin})
manifest={'tolerance_m':.00002,'variants':[{'id':label,'path':str(input_path),'sha256_reference_source':sha,'clips':clips,'expected':refs}]}
(out/'authored-export-crosscheck.json').write_text(json.dumps({'comparisons':authored,'max_m':max([x['max_m']for x in authored],default=None),'pass':max([x['max_m']for x in authored],default=0)<.00002,'limits':'Authored key agreement measured only for foundation_stand_to_sit; inherited clips evaluated with fresh geometry and weights rather than using old source vertex expectations.'},indent=2))
(out/'manifest.json').write_text(json.dumps(manifest,indent=2));(out/'rest-bind.json').write_text(json.dumps({'source':str(input_path),'sha256':sha,'bone_count':len(bones),'bones':bones,'rest_skin_drift':rest_drift,'gates':{'inverse_bind':max(b['inverse_bind_identity_max_error']for b in bones)<2e-6,'unit_orthogonal_bases':max(b['orthogonality_max_error']for b in bones)<2e-6,'rest_skin_drift':max(r['max_distance_m']for r in rest_drift)<2e-6},'limits':'Algebraic bind correctness does not prove anatomical pivot placement, envelope shape, weights or collision.'},indent=2))
print(str(out/'manifest.json'))
