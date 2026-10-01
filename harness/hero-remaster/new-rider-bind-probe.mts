/** CPU production-decoder check for a private source and its NEW bound export. */
import fs from 'node:fs';
import assert from 'node:assert/strict';
import * as THREE from 'three';
import { loadRigAt } from '../../src/render/hero/gltfTestUtils';
const stage=process.argv.find(x=>x.startsWith('--stage='))?.slice(8)??'body-bind01'; assert(/^body-bind[0-9]+$/.test(stage));
const base='/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2';
const g=await loadRigAt(new URL('file://'+base+`/rig-adapter01/${stage}/rider.glb`));
const source=await loadRigAt(new URL('file://'+base+'/parent-assembly/donor-fit05/rider.glb'));
g.scene.updateMatrixWorld(true);source.scene.updateMatrixWorld(true);
const collect=(root:THREE.Object3D)=>{const out:THREE.Mesh[]=[];root.traverse(o=>{if((o as THREE.Mesh).isMesh)out.push(o as THREE.Mesh);});return out;};
const actual=collect(g.scene),original=collect(source.scene);assert.equal(actual.length,original.length);
const rigBones:string[]=[];g.scene.traverse(o=>{if((o as THREE.Bone).isBone)rigBones.push(o.name);});assert.equal(rigBones.length,19);
const rows=[];
for(let i=0;i<actual.length;i++){
 const a=actual[i] as THREE.SkinnedMesh,s=original[i]!;assert(a.isSkinnedMesh);a.skeleton.update();
 const ap=a.geometry.getAttribute('position'),sp=s.geometry.getAttribute('position');const expectedPoints=new Map<string,THREE.Vector3[]>(); const grid=1e-5; const key=(v:THREE.Vector3)=>[v.x,v.y,v.z].map(x=>Math.round(x/grid)).join(','); for(let k=0;k<sp.count;k++){const v=new THREE.Vector3().fromBufferAttribute(sp,k);s.localToWorld(v);const q=new THREE.Vector3(v.z+.65,v.y,-v.x);const kk=key(q);const arr=expectedPoints.get(kk)??[];arr.push(q);expectedPoints.set(kk,arr);} assert.equal(a.geometry.index?.count,s.geometry.index?.count,'Triangle topology count changed');
 let error=0;
 for(let k=0;k<ap.count;k++){
  const v=new THREE.Vector3().fromBufferAttribute(ap,k);a.applyBoneTransform(k,v);a.localToWorld(v);
  const ix=Math.round(v.x/grid),iy=Math.round(v.y/grid),iz=Math.round(v.z/grid);let closest=Infinity;
  for(let x=-1;x<=1;x++)for(let y=-1;y<=1;y++)for(let z=-1;z<=1;z++)for(const q of expectedPoints.get([ix+x,iy+y,iz+z].join(','))??[])closest=Math.min(closest,v.distanceTo(q));
  error=Math.max(error,closest);
 }
 rows.push({mesh:a.name,source:s.name,vertices:ap.count,restShapeMaxErrorM:error});assert(error<1e-5,'Rest shape exceeds documented10micron numerical gate');
}
const clip=g.animations.find(c=>c.name==='stand_to_sit_probe');assert(clip);const mixer=new THREE.AnimationMixer(g.scene);mixer.clipAction(clip).setLoop(THREE.LoopOnce,1).play();const samples=[];
for(let i=0;i<24;i++){
 mixer.setTime(Math.min(clip.duration,(i/23)*clip.duration));g.scene.updateMatrixWorld(true);let finite=true;
 for(const mesh of actual){const a=mesh as THREE.SkinnedMesh;a.skeleton.update();const p=a.geometry.getAttribute('position');for(let k=0;k<p.count;k+=Math.max(1,Math.floor(p.count/128))){const v=new THREE.Vector3().fromBufferAttribute(p,k);a.applyBoneTransform(k,v);a.localToWorld(v);finite=finite&&v.toArray().every(Number.isFinite);}}
 assert(finite);samples.push({sample:i,timeSeconds:(i/23)*clip.duration,finite});
}
fs.writeFileSync(`docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/${stage}/production-decoder-validation.json`,JSON.stringify({bones:rigBones,rows,clip:{name:clip.name,duration:clip.duration,tracks:clip.tracks.length},samples,limits:'CPU decoder/skin integrity only, textures omitted; no render or ridingcontact acceptance'},null,2)+'\n');
console.log(JSON.stringify({restErrorM:Math.max(...rows.map(r=>r.restShapeMaxErrorM)),bones:rigBones.length,samples:samples.length}));
