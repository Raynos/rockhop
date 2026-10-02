/** CPU-only real loader/constructor contract; rejected diagnostic art stays private. */
/* oxlint-disable typescript/no-explicit-any -- private runtime and frozen receipts. */
import fs from 'node:fs';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import { pathToFileURL } from 'node:url';
import * as THREE from 'three';
import { build } from 'vite';
import { clone } from 'three/examples/jsm/utils/SkeletonUtils.js';
import { loadRigAt } from '../../src/render/hero/gltfTestUtils';
import { prepareHero } from '../../src/render/hero/lod';
import { FrameBuilder } from '../../src/render/frame';
import { patchFreshC19Source } from './new-rider-fresh-c19-adapter.mjs';

const repo=process.cwd(), root='/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2';
const source=root+'/candidate-handoff170/task3-tube10-four-diagnostic01/rider.glb';
const receipts=repo+'/assets/blender/hero-remaster/rider/one-rider-v2/foundation-repair-task3/hoodie-repair02/qa-lane/uv-lower01/tube10-export';
const evidence=repo+'/docs/evidence/hero-remaster/one-rider-v2/conditioning174';
const out=root+'/conditioning174/run03';
const sha=(b:Buffer)=>crypto.createHash('sha256').update(b).digest('hex');
assert(!fs.existsSync(out+'/report.json'),'Keep prior outputs'); fs.mkdirSync(out,{recursive:true});fs.mkdirSync(evidence,{recursive:true});
const hashes=Object.fromEntries([source,receipts+'/manifest.json',receipts+'/stock-three-conditioning.json',repo+'/src/render/hero/gltfRider.ts',repo+'/src/render/hero/sleeveSkin.ts',repo+'/src/render/hero/lod.ts',repo+'/harness/hero-remaster/new-rider-private-adapter.mts',repo+'/harness/hero-remaster/new-rider-fresh-c19-adapter.mts'].map(p=>[p,sha(fs.readFileSync(p))]));
assert.equal(hashes[source],'b077a27ceba5040e4c0388a3501b3815984ee21a13da58640d2d03b319fb4dee');
assert.equal(hashes[receipts+'/stock-three-conditioning.json'],'faf426a53b9f5edb5b4be7a2a77a4d4c9049bb0fbf69096e11ba5a5dbe2fdc38');
const manifest=JSON.parse(fs.readFileSync(receipts+'/manifest.json','utf8'));
const playedPath=repo+'/docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/body-bind34/played/candidate/side/textured/report.json';
hashes[playedPath]=sha(fs.readFileSync(playedPath));
const sample=JSON.parse(fs.readFileSync(playedPath,'utf8')).samples.find((s:any)=>s.i===304);assert(sample);
const lib:any={complete(){}};
const meshes=(s:THREE.Object3D)=>{const a:THREE.SkinnedMesh[]=[];s.traverse(o=>{if((o as THREE.SkinnedMesh).isSkinnedMesh)a.push(o as THREE.SkinnedMesh);});return a;};
const attr=(a:THREE.BufferAttribute|THREE.InterleavedBufferAttribute)=>({count:a.count,itemSize:a.itemSize,normalized:a.normalized,values:sha(Buffer.from(new Float64Array(Array.from({length:a.count*a.itemSize},(_,k)=>a.getComponent(Math.floor(k/a.itemSize),k%a.itemSize))).buffer))});
const geometry=(g:THREE.BufferGeometry)=>({attributes:Object.fromEntries(Object.entries(g.attributes).map(([k,a])=>[k,attr(a)])),morphAttributes:Object.fromEntries(Object.entries(g.morphAttributes).map(([k,a])=>[k,a!.map(attr)])),morphTargetsRelative:g.morphTargetsRelative,index:g.index?attr(g.index):null});
const rowsChanged=(a:THREE.BufferGeometry,b:THREE.BufferGeometry)=>{let n=0;const x=a.getAttribute('skinWeight'),y=b.getAttribute('skinWeight');for(let i=0;i<x.count;i++)if(Array.from({length:4},(_,j)=>x.getComponent(i,j)!==y.getComponent(i,j)).some(Boolean))n++;return n;};
const points=(ms:THREE.SkinnedMesh[])=>ms.map(m=>{const p=m.geometry.getAttribute('position');return Array.from({length:p.count},(_,i)=>m.localToWorld(m.getVertexPosition(i,new THREE.Vector3())));});
const seams=(ms:THREE.SkinnedMesh[])=>{const ps=points(ms),groups=new Map<number,[number,number][]>();ms.forEach((m,p)=>{assert.equal(manifest.physicalWeld[p].length,m.geometry.getAttribute('position').count);const referenced=new Set(m.geometry.index?Array.from(m.geometry.index.array):Array.from({length:ps[p]!.length},(_,i)=>i));for(const v of referenced){const id=manifest.physicalWeld[p][v];const a=groups.get(id)??[];a.push([p,v]);groups.set(id,a);}});let count=0,max=0,over=0;for(const a of groups.values()){if(a.length<2)continue;count++;let gap=0;for(let i=0;i<a.length;i++)for(let j=i+1;j<a.length;j++)gap=Math.max(gap,ps[a[i]![0]]![a[i]![1]]!.distanceTo(ps[a[j]![0]]![a[j]![1]]!));max=Math.max(max,gap);if(gap>1e-6)over++;}return{referencedAliasGroups:count,maximumGapM:max,groupsOver1um:over};};
const maxDistance=(a:THREE.Vector3[][],b:THREE.Vector3[][])=>{let max=0;for(let p=0;p<a.length;p++)for(let i=0;i<a[p]!.length;i++)max=Math.max(max,a[p]![i]!.distanceTo(b[p]![i]!));return max;};
const results:any[]=[];
for(const path of ['ordinary','private'] as const){
 const bundle=repo+'/harness/out/hero-remaster/conditioning174-run03-'+path;
 await build({configFile:false,publicDir:false,logLevel:'error',build:{ssr:'src/render/hero/gltfRider.ts',outDir:bundle,emptyOutDir:true,minify:false,rollupOptions:{external:['three',/^three\//],output:{entryFileNames:'rider.mjs'}}},plugins:path==='private'?[{name:'private-fresh-adapter',enforce:'pre',transform(code,id){return id.toLowerCase().endsWith('/src/render/hero/gltfrider.ts')?{code:patchFreshC19Source(code),map:null}:null;}}]:[]});
 hashes[bundle+'/rider.mjs']=sha(fs.readFileSync(bundle+'/rider.mjs'));
 const {GltfRider}=await import(pathToFileURL(bundle+'/rider.mjs').href);
 for(const flag of ['authored','absent'] as const){
  const gltf=await loadRigAt(pathToFileURL(source),true);const before=meshes(gltf.scene).map(m=>geometry(m.geometry));assert.equal(before.length,5);
  if(flag==='absent')gltf.scene.traverse(o=>{delete o.userData.rockhopRiderSkinConditioned;});
  await prepareHero(gltf);assert.deepEqual(meshes(gltf.scene).map(m=>geometry(m.geometry)),before,'prepareHero must preserve five morph/material primitives');
  const rider=new GltfRider(gltf,lib);const runtime=meshes(rider.scene);assert.equal(runtime.length,5);const changed=runtime.map((m,i)=>rowsChanged(meshes(gltf.scene)[i]!.geometry,m.geometry));
  if(flag==='authored')assert.deepEqual(runtime.map(m=>geometry(m.geometry)),before,'all runtime attributes/indices/morphs remain exact');
  else assert.deepEqual(changed,[5990,0,1138,0,0]);
  const inherited=runtime.map(m=>{let owner:THREE.Object3D|null=m;while(owner&&!Object.hasOwn(owner.userData,'rockhopRiderSkinConditioned'))owner=owner.parent;return{mesh:m.name,meshHasFlag:Object.hasOwn(m.userData,'rockhopRiderSkinConditioned'),owner:owner?.name??null,value:owner?.userData.rockhopRiderSkinConditioned??null};});
  if(flag==='authored')assert(inherited.every(v=>!v.meshHasFlag&&v.value===1));
  const frameRoot=new THREE.Group();rider.attach({frame:frameRoot} as any);frameRoot.updateMatrixWorld(true);
  const restSeams=seams(runtime);if(flag==='authored'){assert.equal(restSeams.maximumGapM,0);assert.equal(restSeams.referencedAliasGroups,15764);}
  const frozen=runtime.map(m=>m.geometry);const stage:any[]=[];
  for(const on of [true,false,true,false]){rider.setStage(on);frameRoot.updateMatrixWorld(true);stage.push({on,sourceWeightsExact:runtime.map((m,i)=>rowsChanged(meshes(gltf.scene)[i]!.geometry,m.geometry)===0),geometrySameAsInitial:runtime.map((m,i)=>m.geometry===frozen[i])});}
  if(flag==='authored')assert(stage.every(s=>s.geometrySameAsInitial.every(Boolean)));
  // Actual frozen physical input enters the constructor path; ordinary and private
  // adapters deliberately have different posing, so no cross-path pose parity is claimed.
  const stateBefore=JSON.stringify(sample.state);const frame=new FrameBuilder().build(sample.state,1);rider.update(frame);frameRoot.updateMatrixWorld(true);rider.scene.updateWorldMatrix(true,true);assert.equal(JSON.stringify(sample.state),stateBefore);
  const seam=seams(runtime);if(flag==='authored'){assert.equal(seam.referencedAliasGroups,15764);assert.equal(seam.groupsOver1um,0);assert(seam.maximumGapM<1e-12);}
  // Independent unconditioned clone adopts exactly this runtime's bone and mesh
  // transforms and morph influences; all vertices must agree, not a sparse sample.
  const control=clone(gltf.scene);control.position.copy(rider.scene.position);control.quaternion.copy(rider.scene.quaternion);control.scale.copy(rider.scene.scale);const cm=meshes(control);control.traverse(o=>{const r=rider.scene.getObjectByName(o.name);if(r){o.position.copy(r.position);o.quaternion.copy(r.quaternion);o.scale.copy(r.scale);}});cm.forEach((m,i)=>{if(m.morphTargetInfluences)m.morphTargetInfluences=runtime[i]!.morphTargetInfluences?.slice();});frameRoot.add(control);frameRoot.updateMatrixWorld(true);
  const delta=maxDistance(points(runtime),points(cm));if(flag==='authored')assert(delta<1e-12);else assert(delta>.001);
  // Separately assign the archived nineteen affine transforms, preserving this
  // actual constructor's geometry. This is finite matrix parity, not a replay.
  const body=runtime[0]!,prefix=body.matrixWorld.clone().multiply(body.bindMatrixInverse);
  for(const [j,bone] of body.skeleton.bones.entries()){
   const target=prefix.clone().invert().multiply(new THREE.Matrix4().fromArray(manifest.D304ColumnMajor[j])).multiply(body.bindMatrix.clone().invert()).multiply(body.skeleton.boneInverses[j]!.clone().invert());
   const local=bone.parent!.matrixWorld.clone().invert().multiply(target);local.decompose(bone.position,bone.quaternion,bone.scale);rider.scene.updateWorldMatrix(true,true);
  }
  runtime.forEach(m=>{if(m.morphTargetInfluences)m.morphTargetInfluences.fill(1);});rider.scene.updateWorldMatrix(true,true);
  const archivedPoints=points(runtime);let archivedReferenceMaxM=0;
  for(let p=0;p<runtime.length;p++){const file=receipts+'/mapped-D304-closed-p'+p+'-ref.f64',bytes=fs.readFileSync(file);hashes[file]=sha(bytes);const ref=new Float64Array(bytes.buffer,bytes.byteOffset,bytes.byteLength/8);assert.equal(ref.length,archivedPoints[p]!.length*3);for(let v=0;v<archivedPoints[p]!.length;v++)archivedReferenceMaxM=Math.max(archivedReferenceMaxM,archivedPoints[p]![v]!.distanceTo(new THREE.Vector3().fromArray(ref,v*3)));}
  const archivedSeams=seams(runtime);if(flag==='authored'){assert(archivedReferenceMaxM<1e-7);assert.equal(archivedSeams.maximumGapM,0);}else assert(archivedReferenceMaxM>.001);
  const sourceDisposals:number[]=[];meshes(gltf.scene).forEach((m,i)=>m.geometry.addEventListener('dispose',()=>sourceDisposals.push(i)));
  const ownedDisposals:number[]=[];runtime.forEach((m,i)=>{if(m.geometry!==meshes(gltf.scene)[i]!.geometry)m.geometry.addEventListener('dispose',()=>ownedDisposals.push(i));});rider.dispose();rider.dispose();assert.deepEqual(sourceDisposals,[]);if(flag==='authored')assert.deepEqual(ownedDisposals,[]);else assert.deepEqual(ownedDisposals,[0,2]);
  assert.deepEqual(meshes(gltf.scene).map(m=>geometry(m.geometry)),before,'shared source geometry remains immutable after use/disposal');
  results.push({path,flag,vertices:runtime.reduce((s,m)=>s+m.geometry.getAttribute('position').count,0),changedWeightRows:changed,inheritedOwners:inherited,restSeams,stage,recordedInputFrame:304,recordedInputScope:'Single frozen D304 physical input, first update; no 305-frame lead/stage history reconstruction.',physicalPose:rider.debug.physicalPose,seams:seam,allVertexUnconditionedControlDeltaM:delta,archivedD304:{referenceMaximumErrorM:archivedReferenceMaxM,seams:archivedSeams,scope:'Explicit archived19 affine transforms applied after real constructor; every vertex versus independent task3 authored reference.'},sourceGeometryDisposals:sourceDisposals,ownedGeometryDisposals:ownedDisposals});
 }
}
assert.equal(sha(fs.readFileSync(source)),hashes[source]);
for(const [file,hash] of Object.entries(hashes))assert.equal(sha(fs.readFileSync(file)),hash,'Frozen source changed during audit: '+file);
const report={status:'REAL_CONSTRUCTOR_ASSET_CONDITIONING_CONTRACT_PASS',hashes,results,limits:['CPU finite recorded D304 input; no continuous motion, GPU shader, rendered anatomy or art acceptance.','Ordinary constructor has no new-anatomy pose adapter; its skin-preservation check does not qualify its bone aiming.','Ordinary and private constructors both call the shared ancestor-scoped conditioner guard; no private scene-wide conditioning skip.','Four-weight stock LBS and original grip targets only; nonlinear responding sleeve/cap driver absent.','Textures omitted only in memory by production test decoder; source meshes and GLB untouched.','Stage checks exercise setStage geometry selection, not Garage rendered/clip acceptance.']};
fs.writeFileSync(out+'/report.json',JSON.stringify(report,null,2)+'\n');fs.writeFileSync(evidence+'/report.json',JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({status:report.status,results:results.map(r=>({path:r.path,flag:r.flag,changed:r.changedWeightRows,seams:r.seams,delta:r.allVertexUnconditionedControlDeltaM}))}));
