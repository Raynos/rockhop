"""Strict JSON-only C19 handoff. Private diagnostic output; no art acceptance."""
import os
os.environ.setdefault('OPENBLAS_NUM_THREADS', '2')
os.environ.setdefault('OMP_NUM_THREADS', '2')
import argparse, copy, hashlib, json, struct, subprocess
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation
NAMES=['pelvis','spine','chest','neck','head','shoulder.L','upperArm.L','forearm.L','hand.L','shoulder.R','upperArm.R','forearm.R','hand.R','thigh.L','shin.L','foot.L','thigh.R','shin.R','foot.R']
FLAG='WORLD_ALIGNED_EXPLICIT_CHILD_DIRECTIONS'
PRIVATE=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/candidate-handoff170')
class Rejected(ValueError):pass
def require(value,reason):
 if not value:raise Rejected(reason)
def digest(b):return hashlib.sha256(b).hexdigest()
class GLB:
 def __init__(self,path):
  self.path=Path(path);self.raw=self.path.read_bytes();require(len(self.raw)>=28,'truncated GLB');magic,version,size=struct.unpack_from('<III',self.raw);require(magic==0x46546c67 and version==2 and size==len(self.raw),'GLB header/size invalid');at=12;chunks=[]
  while at<len(self.raw):
   n,kind=struct.unpack_from('<II',self.raw,at);at+=8;require(at+n<=len(self.raw),'truncated chunk');chunks.append((kind,self.raw[at:at+n]));at+=n
  require([k for k,b in chunks]==[0x4e4f534a,0x004e4942],'require exactly JSON and BIN chunks');self.j=json.loads(chunks[0][1]);self.bin=chunks[1][1];require(len(self.j.get('buffers',[]))==1 and 'uri'not in self.j['buffers'][0],'embedded single BIN required')
 def array(self,ai):
  a=self.j['accessors'][ai];dt=np.dtype({5120:'i1',5121:'u1',5122:'<i2',5123:'<u2',5125:'<u4',5126:'<f4'}[a['componentType']]);w={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}[a['type']]
  def read(vi,offset,count,width,dtype):
   v=self.j['bufferViews'][vi];require(v.get('buffer',0)==0 and not v.get('extensions'),'compressed/external accessor not supported');d=np.dtype(dtype);return np.ndarray((count,width),dtype=d,buffer=self.bin,offset=v.get('byteOffset',0)+offset,strides=(v.get('byteStride',d.itemsize*width),d.itemsize)).copy()
  x=read(a['bufferView'],a.get('byteOffset',0),a['count'],w,dt)if 'bufferView'in a else np.zeros((a['count'],w),dtype=dt)
  if 'sparse'in a:
   sp=a['sparse'];i=sp['indices'];v=sp['values'];ids=read(i['bufferView'],i.get('byteOffset',0),sp['count'],1,{5121:'u1',5123:'<u2',5125:'<u4'}[i['componentType']]).reshape(-1);x[ids]=read(v['bufferView'],v.get('byteOffset',0),sp['count'],w,dt)
  require(np.isfinite(x).all(),'nonfinite accessor');return x
 def signature(self,i):
  a=self.j['accessors'][i];return {k:a.get(k)for k in ['componentType','type','count','normalized']}|{'normalizedPresent':'normalized'in a}
 def image(self,i):
  a=self.j['images'][i];require('uri'not in a and 'bufferView'in a,'protected embedded images required');v=self.j['bufferViews'][a['bufferView']];return self.bin[v.get('byteOffset',0):v.get('byteOffset',0)+v['byteLength']]
 def encode(self):
  encoded=json.dumps(self.j,separators=(',',':')).encode();encoded+=b' '*((-len(encoded))%4);return struct.pack('<III',0x46546c67,2,28+len(encoded)+len(self.bin))+struct.pack('<II',len(encoded),0x4e4f534a)+encoded+struct.pack('<II',len(self.bin),0x004e4942)+self.bin

def parents(doc):
 out={}
 for i,n in enumerate(doc['nodes']):
  for child in n.get('children',[]):require(child not in out,'node has multiple parents');out[child]=i
 return out
def local(n):return {k:n[k]for k in ['translation','rotation','scale','matrix']if k in n}
def worlds(doc):
 p=parents(doc);cache={};visiting=set()
 def world(i):
  if i in cache:return cache[i]
  require(i not in visiting,'cyclic node hierarchy');visiting.add(i);n=doc['nodes'][i]
  if 'matrix'in n:require(not any(k in n for k in ['translation','rotation','scale']),'mixed matrix/TRS');m=np.array(n['matrix'],float).reshape(4,4).T
  else:m=np.eye(4);m[:3,:3]=Rotation.from_quat(n.get('rotation',[0,0,0,1])).as_matrix()@np.diag(n.get('scale',[1,1,1]));m[:3,3]=n.get('translation',[0,0,0])
  require(np.isfinite(m).all()and abs(np.linalg.det(m))>1e-12,'invalid node transform');cache[i]=world(p[i])@m if i in p else m;visiting.remove(i);return cache[i]
 return [world(i)for i in range(len(doc['nodes']))]
def inventory(doc):return [(mi,pi,p)for mi,m in enumerate(doc['meshes'])for pi,p in enumerate(m['primitives'])]
def equal_accessor(source,si,reference,ri,label,records,allow_index_width=False):
 same_signature=source.signature(si)==reference.signature(ri);a,b=source.array(si),reference.array(ri);lossless_index=allow_index_width and source.signature(si)['componentType']in[5121,5123,5125]and reference.signature(ri)['componentType']in[5121,5123,5125]and all(source.signature(si)[k]==reference.signature(ri)[k]for k in ['type','count','normalized','normalizedPresent'])and source.signature(si)['type']=='SCALAR'and a.shape==b.shape and np.array_equal(a,b);equal=(same_signature and a.shape==b.shape and a.tobytes()==b.tobytes())or lossless_index;record={'label':label,'sourceAccessor':si,'referenceAccessor':ri,'sourceSignature':source.signature(si),'referenceSignature':reference.signature(ri),'shape':list(a.shape),'exact':equal,'losslessIndexEncodingDifference':bool(lossless_index and not same_signature),'sourceDenseSHA256':digest(a.tobytes()),'referenceDenseSHA256':digest(b.tobytes())};records.append(record);require(equal,'protected/rig accessor mismatch: '+label)

def resolved_materials(g):
 """Resolve image bytes, sampler values and texture bindings, ignoring embedding IDs."""
 j=g.j;images=[{k:v for k,v in image.items()if k!='bufferView'}|{'embeddedSHA256':digest(g.image(i))}for i,image in enumerate(j.get('images',[]))]
 def texture(i):
  t=copy.deepcopy(j['textures'][i]);source=t.pop('source',None);sampler=t.pop('sampler',None)
  if source is not None:t['resolvedImage']=images[source]
  t['resolvedSampler']=j.get('samplers',[])[sampler]if sampler is not None else{}
  for ext in t.get('extensions',{}).values():
   if isinstance(ext,dict)and 'source'in ext:ext['resolvedImage']=images[ext.pop('source')]
  return t
 def resolve(value,key=''):
  if isinstance(value,list):return [resolve(v)for v in value]
  if isinstance(value,dict):
   out={k:resolve(v,k)for k,v in value.items()if not(key.endswith('Texture')and k=='index')}
   if key.endswith('Texture')and 'index'in value:out['resolvedTexture']=texture(value['index'])
   return out
  return value
 return [resolve(m)for m in j.get('materials',[])],images

def map_candidate(source_path,reference_path,output_dir,fixture_path=None):
 output=Path(output_dir).resolve();require(output.is_relative_to(PRIVATE)and output!=PRIVATE,'output must be a fresh child of private candidate-handoff170');require(not output.exists(),'fresh output directory required');s=GLB(source_path);r=GLB(reference_path);original=copy.deepcopy(s.j);report={'status':'PREFLIGHT','source':str(s.path.resolve()),'sourceSHA256':digest(s.raw),'reference':str(r.path.resolve()),'referenceSHA256':digest(r.raw),'recipeSHA256':digest(Path(__file__).read_bytes()),'outputDirectory':str(output),'checks':[]}
 try:
  sj,rj=s.j,r.j;require(len(sj.get('skins',[]))==len(rj.get('skins',[]))==1,'exactly one skin required');ss,rs=sj['skins'][0],rj['skins'][0];require(len(ss['joints'])==len(rs['joints'])==19,'exact19 joint contract required');sn=[sj['nodes'][i].get('name')for i in ss['joints']];rn=[rj['nodes'][i].get('name')for i in rs['joints']];require(rn==NAMES,'reference canonical19names not current contract');require(sn in [NAMES,['fresh.'+n for n in NAMES]],'source ordered C19 names not explicitly recognized');sp,rp=parents(sj),parents(rj);sw,rw=worlds(sj),worlds(rj);sm={i:k for k,i in enumerate(ss['joints'])};rm={i:k for k,i in enumerate(rs['joints'])}
  def ancestry(j,p,m,i):
   chain=[]
   while True:
    chain.append({'jointOrdinal':m.get(i),'transform':local(j['nodes'][i])})
    if i not in p:break
    i=p[i]
   return chain
  rig=[]
  for k,(a,b)in enumerate(zip(ss['joints'],rs['joints'])):
   require(ancestry(sj,sp,sm,a)==ancestry(rj,rp,rm,b),'changed rest hierarchy/local transform: '+NAMES[k]);require(np.array_equal(sw[a],rw[b]),'changed rest world transform: '+NAMES[k]);rig.append({'name':NAMES[k],'sourceNode':a,'referenceNode':b,'exactRestWorld':True})
  require(sm.get(ss.get('skeleton'))==rm.get(rs.get('skeleton')),'different skeleton root');equal_accessor(s,ss['inverseBindMatrices'],r,rs['inverseBindMatrices'],'19 inverseBindMatrices',report['checks']);report['restHierarchy']=rig
  # The mapped V5 is the sole metadata donor. Historical scale stays metadata only.
  refs=[i for i,n in enumerate(rj['nodes'])if 'rockhopRiderContactAdapter'in n.get('extras',{})];require(len(refs)==1,'unique reference contact metadata node required');ri=refs[0];extras=rj['nodes'][ri]['extras'];require(extras.get('rockhopFreshC19RestAxes')==FLAG,'reference explicit child-axis flag missing');require(extras.get('rockhopRiderSkinConditioned')==1,'reference sleeve conditioning bypass missing');require(extras.get('privateFreshC19AdapterUnaccepted')is True,'reference diagnostic unaccepted flag missing');metadata=extras['rockhopRiderContactAdapter'];require(isinstance(metadata,str)and json.loads(metadata).get('version')==1,'unsupported contact metadata');report['currentContactMetadataSHA256']=digest(metadata.encode());report['declaredUniformScaleMetadataOnly']=json.loads(metadata).get('declaredUniformScale');report['appliedScale']=1.0
  source_nodes=[i for i,n in enumerate(sj['nodes'])if n.get('extras',{}).get('freshRigComparison')];require(len(source_nodes)==1,'unique source C19 rig container required');rig_node=source_nodes[0];require(np.array_equal(sw[rig_node],rw[ri]),'changed rig container world transform')
  si,rv=inventory(sj),inventory(rj);require(len(si)==len(rv)==5,'current exact5 primitive inventory required');require([(mi,pi)for mi,pi,p in si]==[(mi,pi)for mi,pi,p in rv],'primitive namespaces changed')
  for mi in range(len(sj['meshes'])):
   source_mesh_nodes=[i for i,n in enumerate(sj['nodes'])if n.get('mesh')==mi];ref_mesh_nodes=[i for i,n in enumerate(rj['nodes'])if n.get('mesh')==mi];require(len(source_mesh_nodes)==len(ref_mesh_nodes)==1,'ambiguous mesh instance');a,b=source_mesh_nodes[0],ref_mesh_nodes[0];require(sj['nodes'][a].get('skin')==rj['nodes'][b].get('skin')==0 and local(sj['nodes'][a])==local(rj['nodes'][b])and np.array_equal(sw[a],rw[b]),'changed mesh bind transform')
  source_materials,source_images=resolved_materials(s);reference_materials,reference_images=resolved_materials(r)
  canonical=lambda value:json.dumps(value,sort_keys=True,separators=(',',':'))
  require(sorted(map(canonical,source_images))==sorted(map(canonical,reference_images)),'embedded texture content/metadata changed')
  require(sorted(map(canonical,source_materials))==sorted(map(canonical,reference_materials)),'resolved PBR/material/texture bindings changed')
  report['textureComparison']={'resolvedEmbeddedImageBytesAndSemanticPBRBindingsExact':True,'rawImageEncodingReferencesEqual':sj.get('images')==rj.get('images'),'rawTextureEncodingReferencesEqual':sj.get('textures')==rj.get('textures'),'imageRelocations':[{'sourceImage':i,'sourceBufferView':sj['images'][i]['bufferView'],'referenceImageMatches':[k for k,image in enumerate(reference_images)if image==source_images[i]]}for i in range(len(source_images))],'sourceBINPreservedRegardlessOfEmbeddingIDs':True}

  primitive_bindings=[]
  for ordinal,((mi,pi,a),(rmi,rpi,b))in enumerate(zip(si,rv)):
   source_binding=source_materials[a['material']]if 'material'in a else None;reference_binding=reference_materials[b['material']]if 'material'in b else None
   require(source_binding==reference_binding,'per-primitive resolved PBR binding changed: primitive'+str(ordinal))
   primitive_bindings.append({'ordinal':ordinal,'mesh':mi,'primitive':pi,'sourceMaterialIndex':a.get('material'),'referenceMaterialIndex':b.get('material'),'resolvedBindingSHA256':digest(canonical(source_binding).encode()),'exactSemanticBinding':True})
  report['allFivePrimitiveResolvedPBRBindings']=primitive_bindings
  for protected in [1,3]:
   mi,pi,a=si[protected];_,_,b=rv[protected];require(set(a['attributes'])==set(b['attributes']),'protected attribute semantics changed');require(source_materials[a['material']]==reference_materials[b['material']]and a.get('mode',4)==b.get('mode',4),'protected resolved material/primitive mode changed');equal_accessor(s,a['indices'],r,b['indices'],f'primitive{protected}/indices',report['checks'],allow_index_width=True)
   for semantic in a['attributes']:equal_accessor(s,a['attributes'][semantic],r,b['attributes'][semantic],f'primitive{protected}/{semantic}',report['checks'])
   require(len(a.get('targets',[]))==len(b.get('targets',[])),'protected morph count changed')
   for ti,(at,bt)in enumerate(zip(a.get('targets',[]),b.get('targets',[]))):
    require(set(at)==set(bt),'protected morph semantics changed')
    for semantic in at:equal_accessor(s,at[semantic],r,bt[semantic],f'primitive{protected}/morph{ti}/{semantic}',report['checks'])
   require(sj['meshes'][mi].get('extras',{}).get('targetNames')==rj['meshes'][mi].get('extras',{}).get('targetNames'),'protected mesh morph names changed')
  report['protectedPrimitiveOrdinals']={'1':'gloves (mesh0 primitive1)','3':'main head (mesh1 primitive0)'}
  for a,name in zip(ss['joints'],NAMES):sj['nodes'][a]['name']=name
  sockets=[]
  for side in ['L','R']:
   for prefix,parentname in [('gripSocket.','hand.'),('soleSocket.','foot.')]:
    name=prefix+side;refids=[i for i,n in enumerate(rj['nodes'])if n.get('name')==name];require(len(refids)==1,'missing/ambiguous reference socket '+name);require(not any(n.get('name')==name for n in sj['nodes']),'source already has socket '+name);p=ss['joints'][NAMES.index(parentname+side)];q=rs['joints'][NAMES.index(parentname+side)];require(rp.get(refids[0])==q,'reference socket parent not current contract');target=rw[refids[0]];matrix=np.linalg.inv(sw[p])@target;error=float(abs(sw[p]@matrix-target).max());require(error<1e-12,'socket world reconstruction failed');new=len(sj['nodes']);sj['nodes'].append({'name':name,'matrix':matrix.T.reshape(-1).tolist()});sj['nodes'][p].setdefault('children',[]).append(new);sockets.append({'name':name,'sourceParent':p,'referenceParent':q,'referenceRestWorldColumnMajor':target.T.reshape(-1).tolist(),'newLocalColumnMajor':matrix.T.reshape(-1).tolist(),'reconstructionMaxError':error})
  se=sj['nodes'][rig_node].setdefault('extras',{});se.update({k:copy.deepcopy(extras[k])for k in ['rockhopRiderContactAdapter','rockhopFreshC19RestAxes','rockhopRiderSkinConditioned','privateFreshC19AdapterUnaccepted']});se['candidateHandoffUnaccepted']=True
  report['sockets']=sockets
  # All non-node JSON, including source clips/material/morph records, remains exact.
  require({k:v for k,v in sj.items()if k!='nodes'}=={k:v for k,v in original.items()if k!='nodes'},'non-node JSON changed')
  for i,n in enumerate(original['nodes']):
   changed=copy.deepcopy(sj['nodes'][i]);baseline=copy.deepcopy(n)
   if i in ss['joints']:changed.pop('name',None);baseline.pop('name',None);changed['children']=[x for x in changed.get('children',[])if x<len(original['nodes'])];baseline.setdefault('children',[])
   if i==rig_node:changed.pop('extras',None);baseline.pop('extras',None)
   require(changed==baseline,'unexpected source node mutation '+str(i))
  report['sourceBINExact']=True;report['sourceAllGeometryUVNormalSkinMorphMaterialAnimationJSONExact']=True
  if fixture_path:
   fr=Path(fixture_path).read_bytes();fixture=json.loads(fr);require(fixture.get('schemaVersion')==1 and fixture['jointNames']==NAMES,'unsupported fixture contract');centre=np.array(fixture['referenceCentresWorld']);actual=np.array([sw[i][:3,3]for i in ss['joints']]);error=float(np.linalg.norm(actual-centre,axis=1).max());require(error<=1e-5,'basic fixture rest mismatch requires new adapter');report['basicFixtureRestCompatibility']={'fixture':str(Path(fixture_path).resolve()),'sha256':digest(fr),'maximumCentreDifferenceM':error,'protocolRestToleranceM':1e-5,'status':'REST_NAMES_AND_CENTRES_COMPATIBLE_ONLY','all5404motionSamples':'NOT_RUN'}
  result=s.encode();mapped=GLB.__new__(GLB);n=struct.unpack_from('<I',result,12)[0];require(result[28+n:]==s.bin,'BIN changed');require(s.path.read_bytes()==s.raw and r.path.read_bytes()==r.raw,'input changed during run');report.update(status='DIAGNOSTIC_HANDOFF_VALIDATED_UNACCEPTED',candidate=str(output/'rider.glb'),candidateSHA256=digest(result),candidateBytes=len(result),sourceBIN_SHA256=digest(s.bin),referenceBIN_SHA256=digest(r.bin),limits=['C19-compatible rest only; any hierarchy/rest/bind/anatomy change needs a new explicit adapter.','Protected arrays/morphs/textures are exact donor guardrails; garment anatomy, intersections, normals appearance and deformation are not accepted.','Contact/socket and rest-axis metadata copied from explicitly supplied mapped reference, not regenerated from ancestry. Historical declaredUniformScale is inert provenance; no1.015 scaling applied.','Static/fixture rest compatibility is not5404-frame, gameplay, Garage blend, grip/sole surface or appearance acceptance.'])
  output.mkdir(parents=True);(output/'rider.glb').write_bytes(result);(output/'mapping-report.json').write_text(json.dumps(report,indent=2)+'\n');return report
 except (Rejected,ValueError,KeyError,IndexError,np.linalg.LinAlgError)as error:
  report.update(status='REJECTED_NO_MAPPED_ASSET',failure=str(error));output.mkdir(parents=True);(output/'mapping-report.json').write_text(json.dumps(report,indent=2)+'\n');raise Rejected(str(error))from error

CPU_SMOKE_SOURCE = r"""import fs from 'node:fs';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import { pathToFileURL } from 'node:url';
import * as THREE from '/Users/raynos/projects/games/rockhop/node_modules/three/build/three.module.js';
import { loadRigAt } from '/Users/raynos/projects/games/rockhop/src/render/hero/gltfTestUtils.ts';
import { createFixturePlayer } from '/Users/raynos/projects/games/rockhop/harness/hero-remaster/basic-pose-gate/protocol.ts';
const [source,fixturePath,out]=process.argv.slice(2);
assert(source && fixturePath && out);
const hash=(path:string)=>crypto.createHash('sha256').update(fs.readFileSync(path)).digest('hex');
const before=hash(source),fixture=JSON.parse(fs.readFileSync(fixturePath,'utf8'));
const gltf=await loadRigAt(pathToFileURL(source),true);
const player=createFixturePlayer(gltf.scene,fixture),rows=[];
for(const family of ['neutral','sit','lean','overhead.L','grip.R']) {
 const frames=fixture.frames.filter((f:any)=>f.family===family);assert(frames.length);
 const frame=family==='neutral'?frames[0]:frames[Math.floor(frames.length/2)];
 const parity=player.apply(frame);let vertices=0;
 for(const mesh of player.meshes) {
  const count=mesh.geometry.getAttribute('position').count;
  for(const i of [...new Set([0,Math.floor(count/2),count-1])]) {
   const p=mesh.localToWorld(mesh.getVertexPosition(i,new THREE.Vector3()));
   assert(p.toArray().every(Number.isFinite));vertices++;
  }
 }
 rows.push({family,frame:frame.frame,timeSeconds:frame.timeSeconds,closedGrip:frame.closedGrip,gripSide:frame.gripSide??null,maximumWorldMatrixError:parity.maximumWorldMatrixError,finiteStockThreeSurfaceVertices:vertices});
}
assert.equal(hash(source),before);
const result={status:'FIVE_CPU_PROTOCOL_FRAMES_ONLY_NO_ART_ACCEPTANCE',source,sourceSHA256:before,fixture:fixturePath,fixtureSHA256:hash(fixturePath),scriptSHA256:hash(new URL(import.meta.url).pathname),protocolSHA256:hash('/Users/raynos/projects/games/rockhop/harness/hero-remaster/basic-pose-gate/protocol.ts'),loaderHelperSHA256:hash('/Users/raynos/projects/games/rockhop/src/render/hero/gltfTestUtils.ts'),bones:player.bones.size,meshes:player.meshes.length,rows,limits:['Images omitted in memory by existing CPU loader; no disk asset changed.','Only five named fixture frames and15 surface vertices/frame; not all5404 samples, garment deformation quality, intersections, actual gameplay, grip/sole contact, or rendered acceptance.']};
fs.writeFileSync(out,JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify(result,null,2));
"""

def verify_controls(source_path,reference_path,output_dir,fixture_path,report_path,smoke=False):
 """Private corrupted copies exercise fail-closed guardrails; never repaired sources."""
 directory=Path(output_dir).resolve();require(directory.is_relative_to(PRIVATE)and directory!=PRIVATE and not directory.exists(),'fresh private verification directory required');directory.mkdir(parents=True);source=GLB(source_path);reference=GLB(reference_path);results=[]
 positive=map_candidate(source.path,reference.path,directory/'positive',fixture_path)
 mapped=GLB(positive['candidate']);require(mapped.bin==source.bin,'positive BIN mismatch');require({k:v for k,v in mapped.j.items()if k!='nodes'}=={k:v for k,v in source.j.items()if k!='nodes'},'positive non-node JSON mismatch')
 report_copy=copy.deepcopy(positive);Path(report_path).parent.mkdir(parents=True,exist_ok=True)
 # Only source/reference corruption controls are written, under this private root.
 cases=['garment_primitive_material','rest_translation','rest_hierarchy','inverse_bind','protected_head_position','protected_glove_uv','protected_glove_weight','protected_normalized_flag','protected_morph','embedded_texture','reference_axis_flag','reference_conditioning_flag','reference_contact_version','reference_name_contract']
 for case in cases:
  a=copy.deepcopy(source);b=copy.deepcopy(reference);pr=inventory(a.j)
  def mutate_accessor(ai):
   ac=a.j['accessors'][ai];require('bufferView'in ac and ac['componentType']==5126,'control expects direct float32 accessor');v=a.j['bufferViews'][ac['bufferView']];offset=v.get('byteOffset',0)+ac.get('byteOffset',0);blob=bytearray(a.bin);value=struct.unpack_from('<f',blob,offset)[0];struct.pack_into('<f',blob,offset,value+.001);a.bin=bytes(blob)
  if case=='garment_primitive_material':
   materials,_=resolved_materials(a);first=pr[0][2]['material'];different=next((i for i,m in enumerate(materials)if m!=materials[first]),None)
   require(different is not None,'negative material binding control needs distinguishable retained materials');pr[0][2]['material']=different
  elif case=='rest_translation':a.j['nodes'][a.j['skins'][0]['joints'][0]]['translation'][0]+=.001
  elif case=='rest_hierarchy':
   joint=a.j['skins'][0]['joints'][13];parent=parents(a.j)[joint];a.j['nodes'][parent]['children'].remove(joint);a.j['nodes'][a.j['skins'][0]['joints'][1]].setdefault('children',[]).append(joint)
  elif case=='inverse_bind':mutate_accessor(a.j['skins'][0]['inverseBindMatrices'])
  elif case=='protected_head_position':mutate_accessor(pr[3][2]['attributes']['POSITION'])
  elif case=='protected_glove_uv':mutate_accessor(pr[1][2]['attributes']['TEXCOORD_0'])
  elif case=='protected_glove_weight':mutate_accessor(pr[1][2]['attributes']['WEIGHTS_0'])
  elif case=='protected_normalized_flag':a.j['accessors'][pr[1][2]['attributes']['COLOR_0']]['normalized']=False
  elif case=='protected_morph':
   ai=pr[1][2]['targets'][0]['POSITION'];ac=a.j['accessors'][ai]
   if 'bufferView'in ac:mutate_accessor(ai)
   else:
    sparse=ac['sparse'];v=a.j['bufferViews'][sparse['values']['bufferView']];offset=v.get('byteOffset',0)+sparse['values'].get('byteOffset',0);blob=bytearray(a.bin);struct.pack_into('<f',blob,offset,struct.unpack_from('<f',blob,offset)[0]+.001);a.bin=bytes(blob)
  elif case=='embedded_texture':
   v=a.j['bufferViews'][a.j['images'][0]['bufferView']];blob=bytearray(a.bin);blob[v.get('byteOffset',0)+20]^=1;a.bin=bytes(blob)
  else:
   node=next(n for n in b.j['nodes']if 'rockhopRiderContactAdapter'in n.get('extras',{}));extras=node['extras']
   if case=='reference_axis_flag':extras.pop('rockhopFreshC19RestAxes')
   elif case=='reference_conditioning_flag':extras.pop('rockhopRiderSkinConditioned')
   elif case=='reference_contact_version':metadata=json.loads(extras['rockhopRiderContactAdapter']);metadata['version']=2;extras['rockhopRiderContactAdapter']=json.dumps(metadata)
   elif case=='reference_name_contract':b.j['nodes'][b.j['skins'][0]['joints'][0]]['name']='differentPelvis'
  case_dir=directory/case;case_dir.mkdir();ap=case_dir/'source.glb';bp=case_dir/'reference.glb';ap.write_bytes(a.encode());bp.write_bytes(b.encode());target=case_dir/'mapped'
  try:map_candidate(ap,bp,target,fixture_path)
  except Rejected as error:results.append({'control':case,'status':'REJECTED_AS_EXPECTED','reason':str(error),'mappedAssetAbsent':not(target/'rider.glb').exists()})
  else:raise Rejected('negative control unexpectedly mapped: '+case)
  require(not(target/'rider.glb').exists(),'rejected control emitted rider')
 relocated=copy.deepcopy(source);image=relocated.j['images'][0];view=copy.deepcopy(relocated.j['bufferViews'][image['bufferView']]);image['bufferView']=len(relocated.j['bufferViews']);relocated.j['bufferViews'].append(view);relocated_path=directory/'image-relocated.glb';relocated_path.write_bytes(relocated.encode());relocation=map_candidate(relocated_path,reference.path,directory/'relocation-positive',fixture_path);require(GLB(relocation['candidate']).bin==relocated.bin,'relocated positive BIN changed');require(relocation['textureComparison']['rawImageEncodingReferencesEqual']is False,'relocation control not exercised')
 before=(directory/'positive/rider.glb').read_bytes()
 try:map_candidate(source.path,reference.path,directory/'positive',fixture_path)
 except Rejected as error:results.append({'control':'reuse_output_directory','status':'REJECTED_AS_EXPECTED','reason':str(error),'existingOutputUnchanged':before==(directory/'positive/rider.glb').read_bytes()})
 else:raise Rejected('existing output directory was overwritten')
 require(source.path.read_bytes()==source.raw and reference.path.read_bytes()==reference.raw,'verification touched source')
 output={'status':'DIAGNOSTIC_ADAPTER_CONTROLS_PASS_NO_ART_ACCEPTANCE','source':str(source.path.resolve()),'sourceSHA256':digest(source.raw),'reference':str(reference.path.resolve()),'referenceSHA256':digest(reference.raw),'recipeSHA256':digest(Path(__file__).read_bytes()),'positiveCandidate':positive['candidate'],'positiveCandidateSHA256':positive['candidateSHA256'],'positiveBINExact':True,'positiveNonNodeJSONExact':True,'currentContactMetadataCopiedExact':mapped.j['nodes'][next(i for i,n in enumerate(mapped.j['nodes'])if 'rockhopRiderContactAdapter'in n.get('extras',{}))]['extras']['rockhopRiderContactAdapter']==next(n['extras']['rockhopRiderContactAdapter']for n in reference.j['nodes']if 'rockhopRiderContactAdapter'in n.get('extras',{})),'negativeControls':results,'losslessImageRelocationPositive':{'status':relocation['status'],'candidate':relocation['candidate'],'sourceBINExact':True,'resolvedTextureGraphExact':True,'rawImageEncodingReferencesEqual':False},'fixtureRestCompatibility':positive.get('basicFixtureRestCompatibility'),'sourceInputsUnchanged':True,'setupErrorsPreserved':['outward-diagnostic01 was initially rejected because protected indices had uint32 encoding versus uint16 reference. Values were exact; final guard explicitly permits only lossless unsigned index encoding differences and reports them. Vertex attributes retain strict component/normalized/dense-byte equality.'],'limits':positive['limits']}
 if smoke:
  require(fixture_path is not None,'CPU protocol smoke requires explicit --fixture');script=directory/'cpu-fixture-smoke.mts';script.write_text(CPU_SMOKE_SOURCE);smoke_result=directory/'cpu-smoke.json';command=['/Users/raynos/projects/games/rockhop/node_modules/.bin/tsx',str(script),positive['candidate'],str(fixture_path),str(smoke_result)];process=subprocess.run(command,capture_output=True,text=True,timeout=120);require(process.returncode==0,'CPU fixture smoke failed: '+process.stderr);output['fiveFrameCPUProtocolSmoke']=json.loads(smoke_result.read_text());output['fiveFrameCPUProtocolSmoke']['command']=command
 Path(report_path).write_text(json.dumps(output,indent=2)+'\n');return output,report_copy

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True);p.add_argument('--reference',type=Path,required=True);p.add_argument('--output-dir',type=Path,required=True);p.add_argument('--fixture',type=Path);p.add_argument('--verify-controls',action='store_true');p.add_argument('--cpu-fixture-smoke',action='store_true');p.add_argument('--verification-report',type=Path);a=p.parse_args()
 if a.cpu_fixture_smoke and not a.verify_controls:p.error('--cpu-fixture-smoke requires --verify-controls')
 if a.verify_controls:
  p.error('--verification-report required')if a.verification_report is None else None
  r,_=verify_controls(a.source,a.reference,a.output_dir,a.fixture,a.verification_report,a.cpu_fixture_smoke);print(json.dumps({'status':r['status'],'negativeControls':len(r['negativeControls'])}));return
 try:r=map_candidate(a.source,a.reference,a.output_dir,a.fixture)
 except (Rejected,OSError,ValueError)as e:p.exit(2,'REJECTED: '+str(e)+'\n')
 print(json.dumps({k:r[k]for k in ['status','candidate','candidateSHA256','sourceBINExact']},indent=2))
if __name__=='__main__':main()
