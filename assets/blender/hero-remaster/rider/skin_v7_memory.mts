/** CPU loaded-array accounting; actual GPU/frame/texture checks remain in engine. */
import fs from 'node:fs';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
import * as THREE from 'three';
import {loadRigAt} from '../../../../src/render/hero/gltfTestUtils';
import {GltfRider} from '../../../../src/render/hero/gltfRider';
import {prepareHero} from '../../../../src/render/hero/lod';
import type {MaterialLibrary} from '../../../../src/render/materials/library';
import type {HeroBike} from '../../../../src/render/bike/bikeModel';
const out=process.argv[2]??'docs/evidence/hero-remaster/rider-generation/skin-v7-runtime-memory.json';
function arrays(root:THREE.Object3D){
 const buffers=new Set<ArrayBufferLike>();let meshCount=0,vertexAttributeViews=0;
 root.traverse(o=>{if(!(o as THREE.SkinnedMesh).isSkinnedMesh)return;meshCount++;const g=(o as THREE.SkinnedMesh).geometry;
  for(const a of [...Object.values(g.attributes),g.index].filter(Boolean)){
   const attr=a as THREE.BufferAttribute|THREE.InterleavedBufferAttribute;
   const array=(attr as THREE.InterleavedBufferAttribute).isInterleavedBufferAttribute?(attr as THREE.InterleavedBufferAttribute).data.array:(attr as THREE.BufferAttribute).array;
   buffers.add(array.buffer);vertexAttributeViews++;
  }
 });
 return {meshCount,attributeAndIndexViews:vertexAttributeViews,uniqueArrayBuffers:buffers.size,uniqueArrayBufferBytes:[...buffers].reduce((n,b)=>n+b.byteLength,0)};
}
const reports=[];
for(const lod of [false,true])for(const version of ['v6','v7','v7b']){
 const v7=version!=='v6';
 let file=`assets/blender/hero-remaster/rider/${v7?'candidate-skin-'+version:'candidate-v6'}${lod?'-lod':''}-packed.glb`;
 if(version==='v6'&&!fs.existsSync(file))file=`assets/blender/hero-remaster/rider/work/skin-v7-v6${lod?'-lod':''}.glb`;
 if(version==='v7'&&!fs.existsSync(file)){reports.push({lod,version,file,omitted:'Rejected first V7 local master unavailable; not required for compact V7b rebuild.'});continue;}
 const gltf=await loadRigAt(pathToFileURL(path.resolve(file)),true),source=arrays(gltf.scene);
 const body=gltf.scene.getObjectByName('Street_remaster_neural_full_body') as THREE.SkinnedMesh;
 const skin=gltf.scene.getObjectByName('Street_forearm_skin') as THREE.SkinnedMesh|undefined;
 const sourceBodySkinAttributesShared=skin?Object.keys(body.geometry.attributes).every(k=>body.geometry.getAttribute(k)===skin.geometry.getAttribute(k)):null;
 await prepareHero(gltf);const rider=new GltfRider(gltf,{complete(){}} as unknown as MaterialLibrary),frame=new THREE.Group();rider.attach({frame} as HeroBike);const riding=arrays(frame);rider.setStage(true);const garage=arrays(frame);
 let conditionedSkinWeightDeltaMax:number|null=null;
 if(version==='v7b'){
  const map=JSON.parse(fs.readFileSync(file+'.json','utf8')).compactForearm.compactVertexToOriginal as number[];
  rider.setStage(false);
  const liveBody=frame.getObjectByName('Street_remaster_neural_full_body') as THREE.SkinnedMesh,liveSkin=frame.getObjectByName('Street_forearm_skin') as THREE.SkinnedMesh;
  const vector=(mesh:THREE.SkinnedMesh,i:number)=>{const out=Array(mesh.skeleton.bones.length).fill(0),js=mesh.geometry.getAttribute('skinIndex'),ws=mesh.geometry.getAttribute('skinWeight');for(let j=0;j<4;j++)out[js.getComponent(i,j)]+=ws.getComponent(i,j);return out as number[];};
  conditionedSkinWeightDeltaMax=0;
  map.forEach((old,i)=>{const a=vector(liveBody,old),b=vector(liveSkin,i);conditionedSkinWeightDeltaMax=Math.max(conditionedSkinWeightDeltaMax!,...a.map((w,j)=>Math.abs(w-b[j]!)));});
 }
 reports.push({lod,version,file,source,sourceBodySkinAttributesShared,riding,garage,conditionedSkinWeightDeltaMax});rider.dispose();
}
const report={method:'Production GLTFLoader+MeshoptDecoder loaded geometry arrays and GltfRider sleeve-conditioned runtime geometry; unique ArrayBuffer byte counts include attributes and indices. Images omitted by CPU fixture. This is not actual GPU allocation, render timing or texture-memory evidence.',reports};
fs.writeFileSync(out,JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify(report,null,2));
