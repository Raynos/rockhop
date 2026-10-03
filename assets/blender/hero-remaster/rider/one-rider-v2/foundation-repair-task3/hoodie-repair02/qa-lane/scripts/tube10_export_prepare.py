from pathlib import Path
import numpy as np,json,hashlib,sys
ROOT=Path('/Users/raynos/projects/games/rockhop/assets/blender/hero-remaster/rider/one-rider-v2/foundation-repair-task3');Q=ROOT/'hoodie-repair02/qa-lane';OUT=Q/'uv-lower01/tube10-export';OUT.mkdir(exist_ok=True)
code=(ROOT/'runtime/prepare_references.py').read_text();ns={};exec('import struct,json,copy,hashlib\nfrom pathlib import Path\nimport numpy as np\n'+code[code.index('def decode('):code.index("manifest={'tolerance_m'")],ns);decode,array,pose,vertices=[ns[k] for k in ['decode','array','pose','vertices']]
def read(p):
 with np.load(p) as z:return {k:z[k] for k in z.files}
npzpath=ROOT/'hoodie-repair03/tube03-four-bind/four-cap-carrier10-rmf.npz';z=read(npzpath);dpath=ROOT/'hoodie-repair03/inputs/source34-authoritative168-matrices.npz';archive=read(dpath);D=archive['D'][int(np.flatnonzero(archive['sampleIndices']==304)[0])];prior=read(ROOT/'hoodie-repair03/poses/game304-source.npz')['matrices'];assert abs(D-prior).max()<1e-11
src,sbin,ssha=decode(Q/'C19-source.glb');sp=[p for m in src['meshes'] for p in m['primitives']]
paths=[('local','/Users/raynos/Documents/Codex/2026-10-01/task-3/deliverables/tube10-four-diagnostic.glb'),('mapped','/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/candidate-handoff170/task3-tube10-four-diagnostic01/rider.glb')];config={'D304ColumnMajor':[m.T.ravel().tolist() for m in D],'D_source_sha256':hashlib.sha256(dpath.read_bytes()).hexdigest(),'D304_sha256':hashlib.sha256(D.tobytes()).hexdigest(),'D304_prior_reference_max_error':float(abs(D-prior).max()),'physicalWeld':[z[f'physicalWeld{i}'].tolist() for i in range(5)],'variants':[]};contract=[]
for name,path in paths:
 doc,bin,sha=decode(path);pr=[p for m in doc['meshes'] for p in m['primitives']];nodes,world=pose(doc,bin,{'channels':[],'samplers':[]},0);rest=vertices(doc,bin,nodes,world);checks={'original_BIN_prefix_exact':bin[:len(sbin)]==sbin,'no_animations':not doc.get('animations'),'19joint_order_and_inversebind_preserved':doc['skins']==src['skins']};morph=[];refs={}
 for case,closed in [('rest-open',False),('rest-closed',True),('D304-closed',True)]:
  refs[case]=[]
  for i,(mi,pi,restp) in enumerate(rest):
   p=pr[i];P=array(doc,bin,p['attributes']['POSITION']).copy();j=array(doc,bin,p['attributes']['JOINTS_0']).astype(int);w=array(doc,bin,p['attributes']['WEIGHTS_0']);dense=np.zeros((len(P),19));np.put_along_axis(dense,j,w,axis=1)
   checks[f'p{i}_W_quantized_NPZ_max_le_1e-7']=bool(abs(dense-z[f'W{i}']).max()<1e-7);checks[f'p{i}_P_quantized_NPZ_exact']=np.array_equal(P,z[f'p{i}'].astype('f4').astype(float));checks[f'p{i}_max4_exact_nonzero']=bool((dense!=0).sum(1).max()<=4)
   if closed:
    for target in p.get('targets',[]):
     if 'POSITION' in target:P+=array(doc,bin,target['POSITION'])
   if case.startswith('rest'):
    sk=doc['skins'][next(n['skin'] for n in nodes if n.get('mesh')==mi and 'skin' in n)];ib=array(doc,bin,sk['inverseBindMatrices']).reshape(-1,4,4).transpose(0,2,1);M=np.array([world[jj] for jj in sk['joints']])@ib
   else:M=D
   expected=np.zeros_like(P);hom=np.c_[P,np.ones(len(P))]
   for k in range(4):expected+=w[:,k,None]*np.einsum('vab,vb->va',M[j[:,k],:3,:],hom,optimize=False)
   fp=OUT/f'{name}-{case}-p{i}-ref.f64';expected.astype('<f8').tofile(fp);refs[case].append(str(fp))
 for i,p in enumerate(pr):
  if i in [1,3]:checks[f'p{i}_protected_attributes_indices_targets_json_exact']=p==sp[i]
  for sem,ai in p['attributes'].items():
   checks[f'p{i}_{sem}_normalized_flag_preserved']=doc['accessors'][ai].get('normalized',False)==src['accessors'][sp[i]['attributes'][sem]].get('normalized',False)
  count=len(array(src,sbin,sp[i]['attributes']['POSITION']));parents=z[f'sourceVertexParents{i}'];bary=z[f'sourceVertexBarycentric{i}'];old=z[f'oldVertex{i}'];valid=old>=0
  for ti,tar in enumerate(p.get('targets',[])):
   for sem,ai in tar.items():
    orig=array(src,sbin,sp[i]['targets'][ti][sem]);ex=np.zeros((len(old),orig.shape[1]));ex[valid]=orig[old[valid]];ids=np.flatnonzero((parents>=0).all(1));ex[ids]=(orig[parents[ids]]*bary[ids,:,None]).sum(1);actual=array(doc,bin,ai);err=float(abs(actual-ex).max());morph.append({'primitive':i,'target':ti,'semantic':sem,'max_error':err});checks[f'p{i}_target{ti}_{sem}_source_parent_expansion']=err<1e-7
 config['variants'].append({'id':name,'path':path,'sha256':sha,'references':refs});contract.append({'variant':name,'sha256':sha,'checks':{k:bool(v) for k,v in checks.items()},'morph_source_parent_checks':morph})
(OUT/'manifest.json').write_text(json.dumps(config));r={'status':'EXPORT_ATTRIBUTES_BIND_SOURCE_PARENT_PASS' if all(all(v['checks'].values()) for v in contract) else 'FAIL','npz_sha256':hashlib.sha256(npzpath.read_bytes()).hexdigest(),'variants':contract,'limits':'No stock loader,conditioning,nonlinear driver or appearance acceptance in this raw accessor contract.'};(OUT/'raw-contract.json').write_text(json.dumps(r,indent=2));print(r['status'],[(v['variant'],[k for k,b in v['checks'].items() if not b]) for v in contract])
