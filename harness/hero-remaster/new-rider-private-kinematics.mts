/** CPU actual GltfRider overlay evaluation; synthetic targets, not played acceptance. */
import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import { pathToFileURL } from 'node:url';
import * as THREE from 'three';
import { build } from 'vite';
import { patchNewRiderSource } from './new-rider-private-adapter.mjs';
import { loadRigAt } from '../../src/render/hero/gltfTestUtils';
import { prepareHero } from '../../src/render/hero/lod';
import type { MaterialLibrary } from '../../src/render/materials/library';
import type { HeroBike } from '../../src/render/bike/bikeModel';
import { FrameBuilder } from '../../src/render/frame';
import { BIKE_GEOMETRY_V2 } from '../../src/render/hero/assetFrame';
import { makeRiderRigPose, riderPoseAtLean, RIDER_TORSO_REST } from '../../src/core/riderGeometry';
const out=path.resolve(process.argv.find(a=>a.startsWith('--out='))?.slice(6) ?? 'docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/body-bind05'),bundle=path.resolve('harness/out/hero-remaster/new-rider-adapter-cpu');
fs.mkdirSync(out,{recursive:true});
await build({configFile:false,publicDir:false,logLevel:'error',build:{ssr:'src/render/hero/gltfRider.ts',outDir:bundle,emptyOutDir:true,minify:false,rollupOptions:{external:['three',/^three\//],output:{entryFileNames:'adapted-rider.mjs'}}},plugins:[{name:'private-new-rider',enforce:'pre',transform(code,id){if(id.toLowerCase().endsWith('/src/render/hero/gltfrider.ts'))return{code:patchNewRiderSource(code,true,process.argv.includes('--seam=1')),map:null};return null;}}]});
const {GltfRider}=await import(pathToFileURL(bundle+'/adapted-rider.mjs').href);
const g=await loadRigAt(pathToFileURL(process.argv.find(a=>a.startsWith('--source='))?.slice(9) ?? '/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/rig-adapter01/body-bind05/rider.glb'),true);await prepareHero(g);const rider=new GltfRider(g,{complete(){}} as unknown as MaterialLibrary);const frame=new THREE.Group();rider.attach({frame} as HeroBike);frame.updateMatrixWorld(true);const rows=[];
for(let i=0;i<=100;i++){
 const lean=-1+i/50,p=riderPoseAtLean(lean,makeRiderRigPose()),f=new FrameBuilder().frame;
 f.riderBody.present=true;f.riderBody.relX=p.com.x+BIKE_GEOMETRY_V2.chassisToAxle.x;f.riderBody.relY=p.com.y+BIKE_GEOMETRY_V2.chassisToAxle.y;f.riderBody.relAngle=p.torsoAngle-RIDER_TORSO_REST;f.tSim=4;f.dt=1/60;f.cut=true;f.speed=0;const before=JSON.stringify(f.riderBody);
 for(let n=0;n<20;n++){rider.update(f);frame.updateMatrixWorld(true);}assert.equal(before,JSON.stringify(f.riderBody),'Physical frame mutated');let finite=true;const morphs:unknown[]=[];
 frame.traverse(o=>{const m=o as THREE.SkinnedMesh;if(m.isSkinnedMesh){m.skeleton.update();const p=m.geometry.getAttribute('position');for(let k=0;k<p.count;k+=Math.max(1,Math.floor(p.count/128))){const v=m.getVertexPosition(k,new THREE.Vector3());m.localToWorld(v);finite=finite&&v.toArray().every(Number.isFinite);}if(m.morphTargetDictionary)morphs.push({mesh:m.name,dictionary:m.morphTargetDictionary,influences:m.morphTargetInfluences});}});assert(finite);rows.push({lean,finite,physicalFrameUnchanged:true,debug:structuredClone(rider.debug),morphs});
}
const summary={gripErrM:Math.max(...rows.flatMap(r=>r.debug.gripErr)),soleErrM:Math.max(...rows.flatMap(r=>r.debug.soleErr)),gripAngleErrRad:Math.max(...rows.flatMap(r=>r.debug.gripAngleErr)),allHandContacts:rows.every(r=>r.debug.handOnGrip.every(Boolean)),allFootContacts:rows.every(r=>r.debug.footOnPeg.every(Boolean)),maxArmStretch:Math.max(...rows.flatMap(r=>r.debug.armStretch)),maxLegStretch:Math.max(...rows.flatMap(r=>r.debug.legStretch))};
// The overlay is opt-in perasset. Verify the historicalasset remains exactly
// identical under both codepaths; it is comparison-only, never a donor.
const Original = (await import('../../src/render/hero/gltfRider')).GltfRider;
const legacySnapshots:string[]=[];
for(const Class of [Original,GltfRider]){
 const old=await loadRigAt(pathToFileURL(path.resolve('public/models/rider-street-mustard.glb')),true);await prepareHero(old);const r=new Class(old,{complete(){}} as unknown as MaterialLibrary),root=new THREE.Group();r.attach({frame:root} as HeroBike);const frames=[];
 for(const lean of [-1,0,1]){const p=riderPoseAtLean(lean,makeRiderRigPose()),f=new FrameBuilder().frame;f.riderBody.present=true;f.riderBody.relX=p.com.x+BIKE_GEOMETRY_V2.chassisToAxle.x;f.riderBody.relY=p.com.y+BIKE_GEOMETRY_V2.chassisToAxle.y;f.riderBody.relAngle=p.torsoAngle-RIDER_TORSO_REST;f.tSim=4;f.dt=1/60;f.cut=true;for(let n=0;n<20;n++){r.update(f);root.updateMatrixWorld(true);}const bones:unknown[]=[];root.traverse(o=>{if((o as THREE.Bone).isBone)bones.push({name:o.name,position:o.position.toArray(),quaternion:o.quaternion.toArray(),world:o.matrixWorld.toArray()});});frames.push({lean,bones,debug:r.debug});}
 legacySnapshots.push(JSON.stringify(frames));
}
assert.equal(legacySnapshots[0],legacySnapshots[1],'Legacy comparison changed without adaptermetadata');
fs.writeFileSync(out+'/private-kinematics.json',JSON.stringify({summary,rows,legacyWithoutMetadataByteExact:true,scope:'RealpatchedGltfRider/prepareHero/skeleton/morphskin CPU evaluated across101syntheticlean targets. Physicalinputread unchanged; not recorded gameplay/visible surface/Garage/LOD acceptance'},null,2)+'\n');console.log(JSON.stringify(summary));
