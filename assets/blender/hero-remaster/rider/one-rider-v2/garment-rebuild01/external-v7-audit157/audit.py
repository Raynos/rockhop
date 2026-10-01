"""Read-only frozen C19/V5/V6/V7 activeGLB field and finite receipt audit.
CPU only, no export/geometry edits. Original prefix bytes are not activefield proof.
"""
from pathlib import Path
import hashlib,json,struct,shutil
import numpy as np
from scipy.spatial.transform import Rotation
REPO=Path('/Users/raynos/projects/games/rockhop');ROOT=Path('/Users/raynos/Documents/Codex/2026-10-01/task-3');EXT=ROOT/'hoodie-repair02';OUT=REPO/'docs/evidence/hero-remaster/one-rider-v2/garment-rebuild01/external-v7-audit157';RUN=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/garment-rebuild01/external-v7-audit157');OUT.mkdir(parents=True,exist_ok=True);RUN.mkdir(parents=True,exist_ok=True);sha=lambda b:hashlib.sha256(b).hexdigest()
paths={'C19':ROOT/'deliverables/C19.glb','V5':EXT/'deliverables/rider-foundation-v5.glb','V6':EXT/'deliverables/rider-compression-v6.glb','V7':EXT/'deliverables/rider-compression-v7.glb'}
class GLB:
 def __init__(self,path):
  self.raw=path.read_bytes();n=struct.unpack_from('<I',self.raw,12)[0];self.j=json.loads(self.raw[20:20+n]);self.b=self.raw[28+n:];self.cache={}
 def read(self,vi,offset,count,width,dtype):
  view=self.j['bufferViews'][vi];start=view.get('byteOffset',0)+offset;d=np.dtype(dtype);stride=view.get('byteStride',d.itemsize*width)
  return np.ndarray((count,width),dtype=d,buffer=self.b,offset=start,strides=(stride,d.itemsize)).copy()
 def acc(self,index):
  if index in self.cache:return self.cache[index]
  a=self.j['accessors'][index];dtype={5120:'i1',5121:'u1',5122:'<i2',5123:'<u2',5125:'<u4',5126:'<f4'}[a['componentType']];width={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT2':4,'MAT3':9,'MAT4':16}[a['type']];x=self.read(a['bufferView'],a.get('byteOffset',0),a['count'],width,dtype) if 'bufferView' in a else np.zeros((a['count'],width),dtype=dtype)
  if 'sparse' in a:
   s=a['sparse'];i=s['indices'];v=s['values'];ids=self.read(i['bufferView'],i.get('byteOffset',0),s['count'],1,{5121:'u1',5123:'<u2',5125:'<u4'}[i['componentType']]).reshape(-1);vals=self.read(v['bufferView'],v.get('byteOffset',0),s['count'],width,dtype);assert len(np.unique(ids))==len(ids) and np.all(ids<a['count']);x[ids]=vals
  self.cache[index]=x;return x
 def info(self,index):
  a=self.j['accessors'][index];x=self.acc(index);r={'count':len(x),'shape':list(x.shape),'dtype':str(x.dtype),'normalized':bool(a.get('normalized',False)),'sparseCount':a.get('sparse',{}).get('count',0),'expandedSHA256':sha(x.tobytes()),'nonfinite':int((~np.isfinite(x)).sum()),'declaredMin':a.get('min'),'declaredMax':a.get('max')}
  if x.size:r['actualMin']=x.min(0).tolist();r['actualMax']=x.max(0).tolist()
  return r
 def primitives(self):return [(mi,pi,m,p) for mi,m in enumerate(self.j['meshes']) for pi,p in enumerate(m['primitives'])]
 def image(self,i):
  im=self.j['images'][i];assert 'bufferView'in im;v=self.j['bufferViews'][im['bufferView']];return self.b[v.get('byteOffset',0):v.get('byteOffset',0)+v['byteLength']]
 def world(self):
  parents={child:i for i,n in enumerate(self.j['nodes']) for child in n.get('children',[])};cache={}
  def calc(i):
   if i in cache:return cache[i]
   n=self.j['nodes'][i]
   if 'matrix'in n:m=np.array(n['matrix']).reshape(4,4).T
   else:
    m=np.eye(4);m[:3,:3]=Rotation.from_quat(n.get('rotation',[0,0,0,1])).as_matrix()@np.diag(n.get('scale',[1,1,1]));m[:3,3]=n.get('translation',[0,0,0])
   cache[i]=calc(parents[i])@m if i in parents else m;return cache[i]
  return [calc(i) for i in range(len(self.j['nodes']))]
inputs={};g={}
for name,path in paths.items():
 glb=GLB(path);frozen=RUN/(name+'.glb')
 if frozen.exists():assert frozen.read_bytes()==glb.raw
 else:frozen.write_bytes(glb.raw)
 inputs[name]={'source':str(path),'frozen':str(frozen),'sha256':sha(glb.raw),'bytes':len(glb.raw)};g[name]=glb
inventory={}
for name,s in g.items():
 world=s.world();skins=[]
 for sk in s.j['skins']:
  binds=s.acc(sk['inverseBindMatrices']).reshape(-1,4,4).transpose(0,2,1);skins.append({'bones':[s.j['nodes'][i]['name'] for i in sk['joints']],'jointNodeIDs':sk['joints'],'inverseBindAccessor':s.info(sk['inverseBindMatrices']),'jointRestWorldMatrices':[world[i].tolist() for i in sk['joints']],'maximumRestBindIdentityError':float(max(abs(world[i]@inv-np.eye(4)).max() for i,inv in zip(sk['joints'],binds)))})
 prim=[]
 for mi,pi,m,p in s.primitives():prim.append({'mesh':mi,'primitive':pi,'name':m.get('name'),'attributes':{k:s.info(v) for k,v in p['attributes'].items()},'indices':s.info(p['indices']),'targets':[{k:s.info(v) for k,v in t.items()} for t in p.get('targets',[])],'morphDefaultWeights':m.get('weights',[]),'morphNames':m.get('extras',{}).get('targetNames',[]),'material':p.get('material')})
 clips=[]
 for a in s.j.get('animations',[]):
  samplers=[]
  for sp in a['samplers']:
   tt=s.acc(sp['input']).reshape(-1);samplers.append({'interpolation':sp.get('interpolation','LINEAR'),'times':tt.tolist(),'duration':float(tt.max()),'input':s.info(sp['input']),'output':s.info(sp['output'])})
  clips.append({'name':a.get('name'),'samplers':samplers,'channels':[{'sampler':c['sampler'],'path':c['target']['path'],'targetNode':c['target']['node'],'targetName':s.j['nodes'][c['target']['node']].get('name')} for c in a['channels']]})
 inventory[name]={'skins':skins,'primitives':prim,'animations':clips,'materialsJSON':s.j.get('materials',[]),'images':[{'index':i,'mimeType':im.get('mimeType'),'bytes':len(s.image(i)),'sha256':sha(s.image(i))} for i,im in enumerate(s.j.get('images',[]))]}
comparisons={}
for older,newer in [('C19','V5'),('V5','V6'),('V6','V7'),('V5','V7')]:
 a,b=g[older],g[newer];rows=[]
 for ai,bi in zip(a.primitives(),b.primitives()):
  mi,pi,am,ap=ai;_,_,bm,bp=bi;r={'mesh':mi,'primitive':pi,'name':am.get('name'),'attributes':{},'targetsComparedCommon':[]}
  for key in sorted(set(ap['attributes'])|set(bp['attributes'])):
   x=a.acc(ap['attributes'][key]) if key in ap['attributes'] else None;y=b.acc(bp['attributes'][key]) if key in bp['attributes'] else None;equal=x is not None and y is not None and x.dtype==y.dtype and x.shape==y.shape and x.tobytes()==y.tobytes();d={'exactExpandedBytes':equal,'oldSHA256':sha(x.tobytes()) if x is not None else None,'newSHA256':sha(y.tobytes()) if y is not None else None}
   if x is not None and y is not None and x.shape==y.shape:d['changedRows']=np.flatnonzero(np.any(x!=y,axis=1)).tolist();d['maximumAbsoluteComponentDifference']=float(np.abs(x.astype(float)-y.astype(float)).max())
   r['attributes'][key]=d
  x=a.acc(ap['indices']);y=b.acc(bp['indices']);r['indicesExact']=x.shape==y.shape and x.tobytes()==y.tobytes();r['changedTriangleIDs']=np.flatnonzero(np.any(x.reshape(-1,3)!=y.reshape(-1,3),axis=1)).tolist() if x.shape==y.shape else None
  at=ap.get('targets',[]);bt=bp.get('targets',[]);r['oldTargets']=len(at);r['newTargets']=len(bt)
  for ti,(t,u) in enumerate(zip(at,bt)):
   r['targetsComparedCommon'].append({'target':ti,'fields':{key:{'exactExpandedBytes':a.acc(t[key]).shape==b.acc(u[key]).shape and a.acc(t[key]).tobytes()==b.acc(u[key]).tobytes(),'oldSHA256':sha(a.acc(t[key]).tobytes()),'newSHA256':sha(b.acc(u[key]).tobytes())} for key in set(t)&set(u)}})
  rows.append(r)
 comparisons[older+'_'+newer]={'primitives':rows,'skinInverseBindExact':[a.acc(x['inverseBindMatrices']).tobytes()==b.acc(y['inverseBindMatrices']).tobytes() for x,y in zip(a.j['skins'],b.j['skins'])],'skinsJSONExact':a.j['skins']==b.j['skins'],'jointRestWorldMaximumComponentDelta':float(max(abs(x-y).max() for x,y in zip(a.world(),b.world()))),'materialsJSONExact':a.j.get('materials')==b.j.get('materials'),'allImageBytesExact':len(a.j.get('images',[]))==len(b.j.get('images',[])) and all(a.image(i)==b.image(i) for i in range(len(a.j.get('images',[])))),'clipsJSONExact':a.j.get('animations')==b.j.get('animations')}
(OUT/'glb-fields.json').write_text(json.dumps({'kind':'Frozen active GLB field comparison; no export or physics claim','inputs':inputs,'inventory':inventory,'comparisons':comparisons},separators=(',',':'))+'\n')
print(json.dumps({k:{'imagesExact':v['allImageBytesExact'],'inverseBindExact':v['skinInverseBindExact'],'restMatrixDelta':v['jointRestWorldMaximumComponentDelta'],'primitives':[{'mesh':r['mesh'],'p':r['primitive'],'changedAttrs':{k:len(a.get('changedRows',[])) for k,a in r['attributes'].items() if not a['exactExpandedBytes']},'changedTri':len(r['changedTriangleIDs'] or []),'targets':[r['oldTargets'],r['newTargets']]} for r in v['primitives']]} for k,v in comparisons.items()},indent=2))
def weights19(s,p):
 if not hasattr(s,'weightCache'):s.weightCache={}
 token=p['attributes']['JOINTS_0'],p['attributes']['WEIGHTS_0']
 if token in s.weightCache:return s.weightCache[token]
 attrs=p['attributes'];ids=s.acc(attrs['JOINTS_0']);weights=s.acc(attrs['WEIGHTS_0']);W=np.zeros((len(ids),19))
 for lane in range(4):np.add.at(W,(np.arange(len(ids)),ids[:,lane]),weights[:,lane])
 s.weightCache[token]=W;return W
src=g['C19'];b0=src.j['meshes'][0]['primitives'][0];h0=src.j['meshes'][0]['primitives'][2];gp=src.j['meshes'][0]['primitives'][1]
def aliases(s,p):
 P=s.acc(p['attributes']['POSITION']);d={}
 for i,point in enumerate(P):d.setdefault(tuple(point),[]).append(i)
 return d
bodyAliases=aliases(src,b0);hoodAliases=aliases(src,h0);gloveAliases=aliases(src,gp);seamKeys=sorted(set(bodyAliases)&set(hoodAliases));gripKeys=sorted(set(bodyAliases)&set(gloveAliases));assert len(seamKeys)==307 and len(gripKeys)==127
seamReport={'sourceC19ExactBodyHoodPhysicalGroups':307,'sourceC19ExactBodyGlovePhysicalGroups':127,'variants':{},'literalBodyHoodGroups':[{'sourcePosition':[float(v) for v in key],'bodyVertexIDs':bodyAliases[key],'hoodVertexIDs':hoodAliases[key]} for key in seamKeys]}
for name,s in g.items():
 body=s.j['meshes'][0]['primitives'][0];hood=s.j['meshes'][0]['primitives'][2];glove=s.j['meshes'][0]['primitives'][1];BP=s.acc(body['attributes']['POSITION']);HP=s.acc(hood['attributes']['POSITION']);GP=s.acc(glove['attributes']['POSITION']);BW=weights19(s,body);HW=weights19(s,hood);GW=weights19(s,glove);BN=s.acc(body['attributes']['NORMAL']);HN=s.acc(hood['attributes']['NORMAL']);r=[]
 for i,key in enumerate(seamKeys):
  bi=bodyAliases[key];hi=hoodAliases[key];ps=np.r_[BP[bi],HP[hi]];ws=np.r_[BW[bi],HW[hi]];normal=np.r_[BN[bi],HN[hi]];sourceBPos=src.acc(b0['attributes']['POSITION'])[bi];sourceHPos=src.acc(h0['attributes']['POSITION'])[hi];sourceBW=weights19(src,b0)[bi];sourceHW=weights19(src,h0)[hi]
  r.append({'group':i,'bodyVertexIDs':bi,'hoodVertexIDs':hi,'maximumSharedPositionComponentGapM':float(np.ptp(ps,axis=0).max()),'maximumSharedWeightComponentGap':float(np.ptp(ws,axis=0).max()),'bodyPositionSourceExact':BP[bi].tobytes()==sourceBPos.tobytes(),'hoodPositionSourceExact':HP[hi].tobytes()==sourceHPos.tobytes(),'maximumRestSourceShiftM':float(np.linalg.norm(ps-np.array(key),axis=1).max()),'bodyWeights19SourceExact':BW[bi].tobytes()==sourceBW.tobytes(),'hoodWeights19SourceExact':HW[hi].tobytes()==sourceHW.tobytes(),'bodyNormalsSourceExact':BN[bi].tobytes()==src.acc(b0['attributes']['NORMAL'])[bi].tobytes(),'hoodNormalsSourceExact':HN[hi].tobytes()==src.acc(h0['attributes']['NORMAL'])[hi].tobytes(),'maximumSharedNormalComponentGap':float(np.ptp(normal,axis=0).max())})
 gloveRows=[]
 for i,key in enumerate(gripKeys):
  bi=bodyAliases[key];gi=gloveAliases[key];gloveRows.append({'group':i,'bodyVertexIDs':bi,'gloveVertexIDs':gi,'maximumPositionComponentGapM':float(np.ptp(np.r_[BP[bi],GP[gi]],axis=0).max()),'maximumWeightComponentGap':float(np.ptp(np.r_[BW[bi],GW[gi]],axis=0).max()),'glovePositionSourceExact':GP[gi].tobytes()==src.acc(gp['attributes']['POSITION'])[gi].tobytes(),'bodyPositionSourceExact':BP[bi].tobytes()==src.acc(b0['attributes']['POSITION'])[bi].tobytes()})
 seamReport['variants'][name]={'hoodBodyRows':r,'hoodBodySummary':{'groups':len(r),'maximumPositionComponentGapM':max(x['maximumSharedPositionComponentGapM'] for x in r),'maximumWeightComponentGap':max(x['maximumSharedWeightComponentGap'] for x in r),'sourceChangedPositionGroups':sum(not x['bodyPositionSourceExact'] or not x['hoodPositionSourceExact'] for x in r),'sourceChangedWeightGroups':sum(not x['bodyWeights19SourceExact'] or not x['hoodWeights19SourceExact'] for x in r),'sourceChangedNormalGroups':sum(not x['bodyNormalsSourceExact'] or not x['hoodNormalsSourceExact'] for x in r),'maximumSourceRestShiftM':max(x['maximumRestSourceShiftM'] for x in r)},'bodyGloveRows':gloveRows,'bodyGloveSummary':{'groups':len(gloveRows),'maximumPositionComponentGapM':max(x['maximumPositionComponentGapM'] for x in gloveRows),'maximumWeightComponentGap':max(x['maximumWeightComponentGap'] for x in gloveRows)}}
# Exact current retained hand/sole ROIs under original primitive index contract.
roiPath=REPO/'docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/played-surfaces11/framed04/source-roi.json';roi=json.loads(roiPath.read_bytes());contactRows=[]
for name,s in g.items():
 for kind in ['hands','feet']:
  for e in roi[kind]:
   pi=1 if kind=='hands' else 0;p=s.j['meshes'][0]['primitives'][pi];sp=src.j['meshes'][0]['primitives'][pi];ids=e['sourceVertices'];fields={}
   for key in ['POSITION','NORMAL','TEXCOORD_0','JOINTS_0','WEIGHTS_0']:
    x=s.acc(p['attributes'][key])[ids];y=src.acc(sp['attributes'][key])[ids];fields[key]={'sourceC19Exact':x.dtype==y.dtype and x.tobytes()==y.tobytes(),'sha256':sha(x.tobytes()),'changedRows':int(np.any(x!=y,axis=1).sum())}
   targets=[]
   for i,(t,u) in enumerate(zip(p.get('targets',[]),sp.get('targets',[]))):targets.append({'target':i,'fields':{key:{'sourceExactOnROI':s.acc(t[key])[ids].tobytes()==src.acc(u[key])[ids].tobytes(),'sha256':sha(s.acc(t[key])[ids].tobytes())} for key in set(t)&set(u)}})
   contactRows.append({'variant':name,'kind':kind,'side':e['side'],'primitive':pi,'vertices':len(ids),'fields':fields,'originalClosedGripTargets':targets})
seamReport['contactROI_SHA256']=sha(roiPath.read_bytes());seamReport['contactRows']=contactRows;seamReport['limits']=['307source physicalgroups preserve provenance even when restshape intentionally changes; exact position equality alone does not certify face/neck seam normals or motion.','Source joints/binds equal does not imply identical dynamic contacts if nativeweights/shape change or optional author morph is activated.']
(OUT/'protected-seam-contacts.json').write_text(json.dumps(seamReport,separators=(',',':'))+'\n')
print(json.dumps({k:{'hood':v['hoodBodySummary'],'glove':v['bodyGloveSummary']} for k,v in seamReport['variants'].items()},indent=2))
# Freeze finite QA receipts; verify referenced samples/topology hashes, retain scope.
receiptNames=['v7-provenance.json','v7-export.json','v7-film-provenance.json','qa-lane/v7-export-motion-manifest.json','qa-lane/results/v7-export-motion-manifest-gate.json','qa-lane/runtime/v7/validation.json','qa-lane/runtime/v7/rest-bind.json','qa-lane/runtime/v7/bounds-integrity.json','qa-lane/runtime/v7/authored-export-crosscheck.json','qa-lane/runtime/v7/mixer-restore.json','rig-lane/mechanical-suite/frozen-provenance.json']
receipts={};frozenReceipts=RUN/'receipts';frozenReceipts.mkdir(exist_ok=True)
for relative in receiptNames:
 path=EXT/relative;raw_=path.read_bytes();destination=frozenReceipts/relative;destination.parent.mkdir(parents=True,exist_ok=True)
 if destination.exists():assert destination.read_bytes()==raw_
 else:destination.write_bytes(raw_)
 receipts[relative]={'source':str(path),'frozen':str(destination),'sha256':sha(raw_),'bytes':len(raw_),'parsed':json.loads(raw_)}
manifest=receipts['qa-lane/v7-export-motion-manifest.json']['parsed'];gate=receipts['qa-lane/results/v7-export-motion-manifest-gate.json']['parsed'];assert manifest['source_sha256']==inputs['V7']['sha256'] and len(manifest['rows'])==len(gate['rows'])==111
sampleRows=[]
for i,(a,b) in enumerate(zip(manifest['rows'],gate['rows'])):
 path=Path(a['path']);assert a['path']==b['path'];raw_=path.read_bytes();expected=[x['sha256'] for x in [a,b] if 'sha256'in x];assert all(x==sha(raw_) for x in expected)
 destination=RUN/'qa-samples'/f'{i:03d}.npz';destination.parent.mkdir(exist_ok=True)
 if destination.exists():assert destination.read_bytes()==raw_
 else:destination.write_bytes(raw_)
 sampleRows.append({'sample':i,'kind':a['sample_kind'],'time_s':a['time_s'],'path':str(path),'frozen':str(destination),'sha256':sha(raw_),'expectedHashCount':len(expected),'bytes':len(raw_)})
topologyPath=Path(gate['topology_path']);topologyBytes=topologyPath.read_bytes();assert sha(topologyBytes)==gate['topology_sha256'];topFrozen=RUN/'actual-topology.npz'
if topFrozen.exists():assert topFrozen.read_bytes()==topologyBytes
else:topFrozen.write_bytes(topologyBytes)
from collections import Counter
summaries={}
for scope in ['shoulder_underarm','hip','cuff_elbow']:
 v=[r['regions'][scope] for r in gate['rows']];summaries[scope]={'gateCounts':dict(Counter(x['gate'] for x in v)),'maximumStrictTransverseCrossings':max(x['strict_transverse_crossings'] for x in v),'maximumOneSharedVertexCrossings':max(x['one_shared_source_vertex_strict_transverse_crossings'] for x in v),'maximumAreaBelowQuarter':max(x['area_below_quarter'] for x in v),'maximumEdge_ge_2mm':max(x['edge_ge_2mm_max'] for x in v)}
for scope in ['cuff','collar_head','seams','seat']:summaries[scope]={'gateCounts':dict(Counter(r[scope]['gate'] for r in gate['rows']))}
summaries['seams'].update(maximumExactAliasGapMM=max(r['seams']['all_alias_bbox_diagonal_max_mm'] for r in gate['rows']),maximumCrossPrimitiveAliasGapMM=max(r['seams']['cross_primitive_alias_bbox_diagonal_max_mm'] for r in gate['rows']))
summaries['seat'].update(maximumStrictHipSaddleCrossings=max(r['seat']['strict_hip_saddle_triangle_crossings'] for r in gate['rows']),minimumProjectedVertexGapMM=min(r['seat']['projected_skin_vertex_min_vertical_gap_mm'] for r in gate['rows']),lastAuthoredKey=next(r['seat'] for r in gate['rows'] if r['sample_kind']=='key' and r['time_s']==2))
validation=receipts['qa-lane/runtime/v7/validation.json']['parsed'];variant=validation['variants'][0];assert variant['sha256']==inputs['V7']['sha256'];qa={'kind':'Frozen finite authored export QA receipts; no arbitrary physics claim','receipts':{k:{key:value for key,value in v.items() if key!='parsed'} for k,v in receipts.items()},'samples':sampleRows,'sampleKinds':dict(Counter(r['sample_kind'] for r in manifest['rows'])),'topology':{'source':str(topologyPath),'frozen':str(topFrozen),'sha256':sha(topologyBytes)},'summary':summaries,'actualInstalledRuntime':{'method':validation['method'],'status':validation['status'],'failures':validation['failures'],'parity':variant['parity_summary'],'clips':[{'name':a['name'],'duration_s':a['duration_s'],'sample_count':a['sample_count']} for a in variant['clips']]},'receiptLimitations':gate['limits']+manifest['limitations'],'interpretation':['49authoredkeys+48halfkeys+10offgrid positions from exported stand_to_sit clip;4independently solved V6holdouts use samepositions with V7topology, not extra gameplay samples.','NUMERIC_ONLY_CLEAR applies to shoulder_underarm, not hip or fullcharacter.','GLTFLoader/AnimationMixer CPU parity verifies this authored clip/morph playback. It does not validate the game physics-driven IK/COM/lean articulation.','Static V5active basefields match V7 excepttwohoodtriangles; V7adds49clip-specific POSITION/NORMALmorph targets, not a generic physics correction.','Preserved sourceBINprefix is archival preservation, not proof that activebody/hood POSITION/skin fields stayed sourceexact.']}
(OUT/'finite-qa-receipts.json').write_text(json.dumps(qa,separators=(',',':'))+'\n')
for name,path in paths.items():assert path.read_bytes()==g[name].raw
print(json.dumps({'sampleKinds':qa['sampleKinds'],'summary':summaries,'runtime':qa['actualInstalledRuntime']},indent=2))
# Independent remaining head join, POSITIONbounds and animation semantic checks.
sourceHeadAliases={}
for mi,pi,m,p in src.primitives():
 if mi!=1:continue
 for key,ids in aliases(src,p).items():sourceHeadAliases.setdefault(key,[]).extend((mi,pi,i) for i in ids)
headKeys=sorted(set(bodyAliases)&set(sourceHeadAliases));headRows={}
for name,s in g.items():
 BP=s.acc(s.j['meshes'][0]['primitives'][0]['attributes']['POSITION']);BW=weights19(s,s.j['meshes'][0]['primitives'][0]);maximumGap=maximumWeightGap=0.;changedBodyPositions=0
 for key in headKeys:
  points=[*BP[bodyAliases[key]]];weights=[*BW[bodyAliases[key]]]
  for mi,pi,i in sourceHeadAliases[key]:
   p=s.j['meshes'][mi]['primitives'][pi];points.append(s.acc(p['attributes']['POSITION'])[i]);weights.append(weights19(s,p)[i])
  maximumGap=max(maximumGap,float(np.ptp(points,axis=0).max()));maximumWeightGap=max(maximumWeightGap,float(np.ptp(weights,axis=0).max()));changedBodyPositions+=not np.array_equal(BP[bodyAliases[key]],src.acc(b0['attributes']['POSITION'])[bodyAliases[key]])
 headRows[name]={'sourceBodyHeadPhysicalGroups':len(headKeys),'maximumSharedPositionComponentGapM':maximumGap,'maximumSharedWeightComponentGap':maximumWeightGap,'sourceChangedBodyPositionGroups':changedBodyPositions}
positionBounds=[]
for mi,pi,m,p in g['V7'].primitives():
 for label,index in [('base',p['attributes']['POSITION'])]+[(f'target{i}',t['POSITION']) for i,t in enumerate(p.get('targets',[])) if 'POSITION'in t]:
  x=g['V7'].acc(index);a=g['V7'].j['accessors'][index];lo=np.array(a.get('min',[]));hi=np.array(a.get('max',[]));assert lo.shape==hi.shape==(3,);err=max(float(np.maximum(lo-x.min(0),0).max()),float(np.maximum(x.max(0)-hi,0).max()));assert err<1e-7;positionBounds.append({'mesh':mi,'primitive':pi,'field':label,'maximumUnderboundError':err})
a,b=g['V6'],g['V7'];semanticClips=[]
for ca,cb in zip(a.j['animations'],b.j['animations']):
 channels=[];assert ca['name']==cb['name'] and len(ca['channels'])==len(cb['channels'])
 for ia,ib in zip(ca['channels'],cb['channels']):
  sa=ca['samplers'][ia['sampler']];sb=cb['samplers'][ib['sampler']];channels.append({'targetPath':ia['target']['path'],'targetNode':ia['target']['node'],'sameTarget':ia['target']==ib['target'],'interpolationExact':sa.get('interpolation','LINEAR')==sb.get('interpolation','LINEAR'),'inputTimesExpandedExact':a.acc(sa['input']).tobytes()==b.acc(sb['input']).tobytes(),'outputValuesExpandedExact':a.acc(sa['output']).tobytes()==b.acc(sb['output']).tobytes()})
 semanticClips.append({'name':ca['name'],'channels':channels,'semanticExact':all(x['sameTarget'] and x['interpolationExact'] and x['inputTimesExpandedExact'] and x['outputValuesExpandedExact'] for x in channels)})
extra={'sourceBodyHeadJoin':headRows,'sourceBodyHeadJoinInterpretation':'No exact raw-local body/head aliases; empty-group zero differences are not seam clearance. Head/cheek activeattrs and restnodes/binds are sourceexact; rendered worldspace join remains parentowned.','independentV7POSITIONBounds':{'count':len(positionBounds),'allBoundsPass':True,'rows':positionBounds},'V6V7AuthoredClipsSemantic':semanticClips,'recommendedReusableSource':{'variant':'V5 frozen static foundation','source':inputs['V5'],'reason':'Exactly same activebase shape/weights/19bind/rest/materials/head/grips asV7; excludes49authored compression morphs. Parent may map canonicalnames into currentphysics driver and measure actual480motion.','alternativeV7StaticDelta':'Only hood triangleIDs78/79 differ fromV5; optional topology control, not a new universal deformer.','requiredPhysicsAdaptation':'19fresh.*names need existing explicit C19anatomical rest-axis/contact/socket adapter. Keep sourcehead/glove/solefields and307matchedhoodbody aliases together. Authored neck/head20percent posture is an animation choice, not static base or proof of game behavior.','acceptance':'NOT accepted; finite authored morphology and visual potential do not prove rider appearance, grip/sole support, Garage or arbitrary physics motion.'},'setupFailure':'First seam JSON serialization received numpyfloat32 source coordinates; corrected to nativefloat before complete seam receipt. No model or export retry.'}
(OUT/'reuse-recommendation.json').write_text(json.dumps(extra,indent=2)+'\n');print(json.dumps({'headJoin':headRows,'positionBoundsCount':len(positionBounds),'semanticClips':[(a['name'],a['semanticExact']) for a in semanticClips],'recommended':'V5staticfoundation'},indent=2))
