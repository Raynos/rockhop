"""Unmodified170 mapping, complete matched baseline guard and exact row subset."""
from pathlib import Path
import json,hashlib,subprocess,importlib.util,copy
import numpy as np
R=Path('/Users/raynos/projects/games/rockhop');B=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2');A=R/'assets/blender/hero-remaster/rider/one-rider-v2/source-preserving-garment187';E=R/'docs/evidence/hero-remaster/one-rider-v2/source-preserving-garment187';S=B/'source-preserving-garment187';M=R/'assets/blender/hero-remaster/rider/one-rider-v2/candidate-handoff170/map_candidate.py';mapped=B/'candidate-handoff170/hood-fixed185-187';sha=lambda b:hashlib.sha256(b).hexdigest();pins={}
def pin(p,h=None):
 b=p.read_bytes();d=sha(b)
 if h:assert d==h,(str(p),d,h)
 pins[str(p)]={'sha256':d,'bytes':len(b)};return b
def save(p,x):p.write_text(json.dumps(x,indent=2)+'\n')
attempt=json.loads((E/'attempt.json').read_text())
try:
 S.mkdir(parents=True,exist_ok=True);assert not mapped.exists()and not(S/'fixture-three-families.json').exists(),'Preserve every frozen output'
 source=B/'source-preserving-garment185/operator/rider.glb';base=B/'rig-adapter01/body-bind34/rider.glb';ref=B/'garment-rebuild01/physical-v5-control157/rider.glb';fixture=B/'basic-pose-gate158/fixture-v4-asymmetric-halfsteps.json'
 pin(source,'ffb9ec5acaca7c5e60b732d88e9313b7c337f3058a32dec2fda0170f634281c5');pin(base,'adbac6f2949cec0f32a8e0cfa4cfabd02cce61e58dab4022209e23a605f31df7');pin(ref,'2100384b8f2183e98e6e0c78d8b717718b1cc57dd8298e76fab53c1d491c77e9');pin(fixture,'78732965343f6eba40ae68ca99ffa949f6718910eb7b930b67d4a48d0083afab');pin(M,'d90018cc9c94706f564b8440349267fd4b47a1e2bffacb7b087ed01af6f7fd90')
 for n,h in [('capture.mts','9f47ee7e015cc03b8e85aa9570ee30f309d7f3170b89b6db35bf1f04c119b5c5'),('protocol.ts','031ec5faf7abb90d13749bcb0a40b64c857588fedbb551705ed0109e01eb1c9d'),('studio.ts','d14447b716a8f368308a3e2b90a1e827f5f25629aa687f1082186f0780452acc')]:pin(R/'harness/hero-remaster/basic-pose-gate'/n,h)
 cmd=['/Users/raynos/projects/localai/runtime/unimate/.venv/bin/python',str(M),'--source',str(source),'--reference',str(ref),'--output-dir',str(mapped),'--fixture',str(fixture)];subprocess.run(cmd,check=True);mapperReceipt=mapped/'mapping-report.json';pin(mapperReceipt);pin(mapped/'rider.glb');(E/'mapping-report.json').write_bytes(mapperReceipt.read_bytes())
 spec=importlib.util.spec_from_file_location('unchanged_mapper170',M);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);C=mod.GLB(mapped/'rider.glb');D=mod.GLB(base);X=mod.GLB(source);assert C.bin==X.bin;arrays=[];indexdiff=[]
 for mi,mesh in enumerate(C.j['meshes']):
  for pi,p in enumerate(mesh['primitives']):
   q=D.j['meshes'][mi]['primitives'][pi];assert set(p['attributes'])==set(q['attributes']);assert len(p.get('targets',[]))==len(q.get('targets',[]));assert mesh.get('extras',{}).get('targetNames')==D.j['meshes'][mi].get('extras',{}).get('targetNames')
   for name,ai in p['attributes'].items():
    ca,da=C.array(ai),D.array(q['attributes'][name]);assert C.signature(ai)==D.signature(q['attributes'][name])and ca.tobytes()==da.tobytes();arrays.append({'mesh':mi,'primitive':pi,'field':name,'sha256':sha(ca.tobytes()),'exact':True})
   for ti,t in enumerate(p.get('targets',[])):
    for name,ai in t.items():
     bi=q['targets'][ti][name];assert C.signature(ai)==D.signature(bi)and C.array(ai).tobytes()==D.array(bi).tobytes();arrays.append({'mesh':mi,'primitive':pi,'target':ti,'field':name,'sha256':sha(C.array(ai).tobytes()),'exact':True})
   cf,df=C.array(p['indices']).reshape(-1,3),D.array(q['indices']).reshape(-1,3);assert cf.shape==df.shape;changed=np.flatnonzero(np.any(cf!=df,axis=1)).tolist();indexdiff.append({'mesh':mi,'primitive':pi,'changedFaceSlots':changed});assert changed==([28,29,3813,3829,3847,3848,4105,4106]if(mi,pi)==(0,2)else[])
 assert mod.resolved_materials(C)==mod.resolved_materials(D);cs,ds=C.j['skins'][0],D.j['skins'][0];assert len(cs['joints'])==len(ds['joints'])==19;assert C.array(cs['inverseBindMatrices']).tobytes()==D.array(ds['inverseBindMatrices']).tobytes();cw,dw=mod.worlds(C.j),mod.worlds(D.j);errors=[]
 for i,j in zip(cs['joints'],ds['joints']):
  assert C.j['nodes'][i]['name']==D.j['nodes'][j]['name']and mod.local(C.j['nodes'][i])==mod.local(D.j['nodes'][j]);errors.append(float(abs(cw[i]-dw[j]).max()))
 assert max(errors)==0;ce=next(n['extras']for n in C.j['nodes']if 'rockhopRiderContactAdapter'in n.get('extras',{}));de=next(n['extras']for n in D.j['nodes']if 'rockhopRiderContactAdapter'in n.get('extras',{}));keys=['rockhopRiderContactAdapter','rockhopFreshC19RestAxes','rockhopRiderSkinConditioned','privateFreshC19AdapterUnaccepted'];assert all(ce[k]==de[k]for k in keys);sockets=[]
 for name in ['gripSocket.L','soleSocket.L','gripSocket.R','soleSocket.R']:
  ci=next(i for i,n in enumerate(C.j['nodes'])if n.get('name')==name);di=next(i for i,n in enumerate(D.j['nodes'])if n.get('name')==name);err=float(abs(cw[ci]-dw[di]).max());assert err<1e-12;sockets.append({'name':name,'maxRestWorldDifference':err,'exactLocalJSON':C.j['nodes'][ci]==D.j['nodes'][di]})
 original=json.loads(fixture.read_text());subset=copy.deepcopy(original);families=['overhead.L','forward','sit'];subset['families']=families;subset['frames']=[copy.deepcopy(row)for family in families for row in original['frames']if row['family']==family];assert len(subset['frames'])==579
 for family in families:
  old=[x for x in original['frames']if x['family']==family];new=[x for x in subset['frames']if x['family']==family];assert old==new and len(new)==193 and [r['frame']for r in new]==list(range(193))
 subsetPath=S/'fixture-three-families.json';subsetPath.write_text(json.dumps(subset,separators=(',',':'))+'\n');pin(subsetPath)
 report={'status':'ONE_UNMODIFIED_MAPPING_AND_MATCHED_BASELINE_VERIFIED','mapperCommand':cmd,'inputs':pins,'sourceBINExact':True,'allGeometryAttributesMorphUVNormalWeightsExactBaseline':True,'resolvedPBRSamplerImagesExactBaseline':True,'actualArrays':arrays,'indexDifferences':indexdiff,'baselineJointRestMaximumDifference':max(errors),'inverseBindsExact':True,'adapterMetadataFieldsExact':keys,'socketWorldComparison':sockets,'declaredMetadataDifferences':['candidateHandoffUnaccepted:true on candidate rig container','JSON source name/metadata provenance may differ; four adapter fields exact','Socket local matrix JSON may differ by floating-point reconstruction; world error<1e-12'],'fixtureSubset':str(subsetPath),'families':families,'framesPerFamily':193,'framesPerAsset':579,'fps':48,'fixtureRowsExactlyCopied':True,'sourceClipsPreservedExact185':C.j.get('animations')==X.j.get('animations'),'sourceBaselineClipsUsed':False,'referenceUsedForGeometryOrWeights':False,'recipeSHA256':sha(Path(__file__).read_bytes()),'limits':['Matched authored fixtures via stockThree; no native source animation playback or Garage contact acceptance','Mapping metadata is compatibility; conditioning flag is not a new weight improvement','V7 compression/shape/weights not reused']};save(E/'preparation.json',report)
 for p,d in pins.items():assert sha(Path(p).read_bytes())==d['sha256']
 attempt['status']='MAPPING_AND_BASELINE_VERIFIED_CAPTURE_NOT_STARTED';save(E/'attempt.json',attempt);print(json.dumps({'status':report['status'],'candidateSHA256':sha(C.raw),'subsetFrames':579,'jointRestDifference':max(errors)}))
except Exception as e:
 attempt['status']='FROZEN_PREPARATION_FAILURE';attempt['failures'].append({'stage':'mapping/baseline/subset preparation','type':type(e).__name__,'error':str(e)});save(E/'attempt.json',attempt);raise
