import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import * as THREE from 'three';
import { loadRigAt } from '../../../../../../src/render/hero/gltfTestUtils';
import { boneName } from '../../../../../../src/render/hero/gltfRider';
const output=path.dirname(new URL(import.meta.url).pathname);
const repo=process.cwd();
const selectedPath='/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/parent-assembly/donor-fit05/rider.glb';
const sha=(file:string)=>crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');
const inputFiles=['src/render/hero/gltfRider.ts','src/core/riderGeometry.ts','src/render/hero/clipAliases.ts','src/render/hero/lod.ts','src/render/hero/gltf.ts','src/render/hero/sleeveSkin.ts','src/render/rider/pose.ts','src/render/hero/assetFrame.ts','src/render/hero/gltfTestUtils.ts','docs/evidence/hero-art/delivery/RIG_CONTRACT.md','docs/evidence/hero-art/delivery/rig-contract.json'];
const assets=[];
for(const name of ['rider-street-mustard.glb','rider-street-mustard-lod.glb','bike-rookie.glb','bike-pro.glb']){
 const file=path.join(repo,'public/models',name),g=await loadRigAt(new URL('file://'+file),true);
 g.scene.updateMatrixWorld(true);
 const bones:any[]=[],sockets:any[]=[],meshes:any[]=[];
 g.scene.traverse(o=>{
  const record=()=>({name:o.name,canonicalName:boneName(o.name),parent:o.parent?.name,local:{position:o.position.toArray(),quaternion:o.quaternion.toArray(),scale:o.scale.toArray()},worldPosition:o.getWorldPosition(new THREE.Vector3()).toArray(),worldQuaternion:o.getWorldQuaternion(new THREE.Quaternion()).toArray(),worldMatrix:o.matrixWorld.toArray()});
  if((o as THREE.Bone).isBone) bones.push(record());
  if(/Socket|attach_(grip|peg|frame_origin|rear_axle_rest|front_axle_rest)/.test(o.name)) sockets.push(record());
  if((o as THREE.Mesh).isMesh){const m=o as THREE.SkinnedMesh;meshes.push({name:m.name,skinned:m.isSkinnedMesh===true,materials:(Array.isArray(m.material)?m.material:[m.material]).map(x=>({name:x.name,type:x.type})),attributes:Object.fromEntries(Object.entries(m.geometry.attributes).map(([k,v])=>[k,{itemSize:v.itemSize,count:v.count,type:v.array.constructor.name,normalized:v.normalized}])),vertices:m.geometry.getAttribute('position').count,triangles:(m.geometry.index?.count??m.geometry.getAttribute('position').count)/3,...(m.isSkinnedMesh?{joints:m.skeleton.bones.map(b=>({name:b.name,parent:b.parent?.name})),inverseBindMatrices:m.skeleton.boneInverses.map(x=>x.toArray()),bindMatrix:m.bindMatrix.toArray(),bindMatrixInverse:m.bindMatrixInverse.toArray()}: {})});}
 });
 const find=(name:string)=>g.scene.getObjectByName(name)??g.scene.getObjectByName(name.replace('.',''));
 const lengths=(bones.length?['L','R']:[]).map(side=>{const p=(name:string)=>find(name+'.'+side)!.getWorldPosition(new THREE.Vector3());return {side,upperArm:p('upperArm').distanceTo(p('forearm')),forearm:p('forearm').distanceTo(p('hand')),thigh:p('thigh').distanceTo(p('shin')),shin:p('shin').distanceTo(p('foot')),gripOffset:find('gripSocket.'+side)!.getWorldPosition(new THREE.Vector3()).sub(p('hand')).toArray(),soleOffset:find('soleSocket.'+side)!.getWorldPosition(new THREE.Vector3()).sub(p('foot')).toArray()};});
 assets.push({path:file,sha256:sha(file),bytes:fs.statSync(file).size,bones,sockets,meshes,lengths,clips:g.animations.map(c=>({name:c.name,duration:c.duration,tracks:c.tracks.map(t=>({name:t.name,type:t.ValueTypeName,keys:t.times.length,firstTime:t.times[0],lastTime:t.times.at(-1)}))}))});
}
const selectedBytes=fs.readFileSync(selectedPath);
const selectedJSON=JSON.parse(selectedBytes.subarray(20,20+selectedBytes.readUInt32LE(12)).toString());
const selectedNewAppearance={path:selectedPath,sha256:sha(selectedPath),skins:selectedJSON.skins?.length??0,animations:selectedJSON.animations?.length??0,geometryDonorPolicy:'New appearance only; production geometry comparison-only, never donor'};
fs.writeFileSync(path.join(output,'production-runtime-contract.json'),JSON.stringify({selectedNewAppearance,createdAt:new Date().toISOString(),method:'Actual current production GLBs decoded CPU-only with production GLTFLoader/MeshoptDecoder; texture references removed in memory; no disk assets altered; old geometry is comparison-only. No prepareHero mutation was applied in this transform extraction.',sources:inputFiles.map(p=>({path:path.join(repo,p),sha256:sha(p)})),assets},null,2)+'\n');
console.log(JSON.stringify(assets.map(a=>({path:a.path,sha256:a.sha256,bones:a.bones.length,meshes:a.meshes.length,lengths:a.lengths,clips:a.clips.map(c=>({name:c.name,duration:c.duration}))})),null,2));
