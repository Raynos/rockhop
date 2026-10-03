/** Read-only actual body34 replay; CPU bone matrices only. */
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import * as THREE from 'three';
import {pathToFileURL} from 'node:url';
import {loadRigAt} from '/Users/raynos/projects/games/rockhop/src/render/hero/gltfTestUtils';
import {prepareHero} from '/Users/raynos/projects/games/rockhop/src/render/hero/lod';
import {GltfBike} from '/Users/raynos/projects/games/rockhop/src/render/hero/gltfBike';
import {FrameBuilder} from '/Users/raynos/projects/games/rockhop/src/render/frame';
const root='/Users/raynos/projects/games/rockhop',out=path.dirname(new URL(import.meta.url).pathname);
const bundle=root+'/harness/out/hero-remaster/body34-fresh-rig-cpu/rider.mjs';
const source='/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/rig-adapter01/body-bind34/rider.glb';
const report=root+'/docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/body-bind34/played/candidate/side/textured/report.json';
const rawdir='/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/rig-adapter01/body-bind34/candidate-cpu';
const sha=(p:string)=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
const captured=JSON.parse(fs.readFileSync(report,'utf8'));assert.equal(sha(source),captured.sourceSHA256);assert.equal(captured.samples.length,480);
const {GltfRider}=await import(pathToFileURL(bundle).href);
(globalThis as any).document={createElement:()=>({width:128,height:64,getContext:()=>({createRadialGradient:()=>({addColorStop(){}}),scale(){},fillRect(){}})})};
const lib:any={complete(){}};
const bg=await loadRigAt(pathToFileURL(root+'/public/models/bike-rookie.glb'),true);await prepareHero(bg);const bike=new GltfBike(bg,lib);
const g=await loadRigAt(pathToFileURL(source),true);await prepareHero(g);const rider=new GltfRider(g,lib);rider.attach(bike);bike.root.updateMatrixWorld(true);
const meshes:THREE.SkinnedMesh[]=[];rider.scene.traverse((o:THREE.Object3D)=>{const m=o as THREE.SkinnedMesh;if(m.isSkinnedMesh&&m.name.startsWith('Protected')&&!m.name.endsWith('_1'))meshes.push(m);});assert.equal(meshes.length,2);
const all:number[]=[];const rows:any[]=[];let maxMeshDifference=0,maxOldControlDifference=0,maxBonePointDifference=0;
for(const sample of captured.samples){
 const before=JSON.stringify(sample.state),f=new FrameBuilder().build(sample.state,1);bike.update(f);rider.update(f);bike.root.updateMatrixWorld(true);rider.scene.updateWorldMatrix(true,true);const inverse=bike.frame.matrixWorld.clone().invert();
 const perMesh=meshes.map(m=>{const prefix=new THREE.Matrix4().multiplyMatrices(inverse,m.matrixWorld).multiply(m.bindMatrixInverse);return m.skeleton.bones.flatMap((b,j)=>new THREE.Matrix4().multiplyMatrices(prefix,new THREE.Matrix4().multiplyMatrices(b.matrixWorld,m.skeleton.boneInverses[j]!)).multiply(m.bindMatrix).elements);});
 for(let k=0;k<perMesh[0]!.length;k++)maxMeshDifference=Math.max(maxMeshDifference,Math.abs(perMesh[1]![k]!-perMesh[0]![k]!));
 if([114,186,304,426].includes(sample.i)){const raw=fs.readFileSync(path.join(rawdir,`sample${sample.i}-mesh0-joint-transforms.f64`));for(let k=0;k<perMesh[0]!.length;k++)maxOldControlDifference=Math.max(maxOldControlDifference,Math.abs(raw.readDoubleLE(k*8)-perMesh[0]![k]!));}
 for(const b of meshes[0]!.skeleton.bones){const point=b.getWorldPosition(new THREE.Vector3()).applyMatrix4(inverse),ref=sample.bonesInBikeFrame[b.name];if(ref)maxBonePointDifference=Math.max(maxBonePointDifference,point.distanceTo(new THREE.Vector3(...ref)));}
 all.push(...perMesh[0]!);rows.push({i:sample.i,tick:sample.tick,phase:sample.phase,debug:structuredClone(rider.debug)});assert.equal(JSON.stringify(sample.state),before);
}
const data=new Float64Array(all);fs.writeFileSync(path.join(out,'source34-480.f64'),Buffer.from(data.buffer));
const result={source,sourceSHA256:sha(source),report,reportSHA256:sha(report),driver:bundle,driverSHA256:sha(bundle),boneNames:meshes[0]!.skeleton.bones.map(b=>b.name),shape:[480,19,4,4],layout:'float64 little endian, each matrix column major; bike-frame deformation matrices',maxMeshDifference,maxOldControlDifference,maxBonePointDifference,pass:maxOldControlDifference<1e-9&&maxMeshDifference<1e-12&&maxBonePointDifference<1e-8,rows,limits:['CPU replay of existing captured states using preserved compiled body34 driver, no new GPU work.','Recorded riding/lean/landing recovery only; stand/Garage coverage not invented.','Bone matrices alone do not certify new geometry contact or material shading.']};fs.writeFileSync(path.join(out,'source34-480-replay.json'),JSON.stringify(result,null,2));console.log(JSON.stringify({...result,rows:undefined}));
