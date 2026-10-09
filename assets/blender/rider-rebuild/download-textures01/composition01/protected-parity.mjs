// Prove protected geometry04 checkpoint parts stayed exact through composition.
import fs from 'node:fs';
import assert from 'node:assert/strict';
import {openGlb,accessorBytes,viewBytes,fileSha,sha} from '../../download-opt01/geometry01/glb.mjs';
const [acceptedPath,candidatePath,reportPath]=process.argv.slice(2);
const accepted=openGlb(acceptedPath),candidate=openGlb(candidatePath),a=accepted.json,b=candidate.json;
const expected='c5a857a19a81b4b21f594c945cab206b9814bdaacd1b26b64acc986291e0b9dc';
assert.equal(fileSha(acceptedPath),expected);
for(const key of ['nodes','scenes','scene','cameras'])assert.deepEqual(a[key],b[key]);
assert.equal(a.skins.length,b.skins.length);
let joints=0,channels=0;
for(let i=0;i<a.skins.length;i++){
 const x=structuredClone(a.skins[i]),y=structuredClone(b.skins[i]);
 assert.deepEqual(await accessorBytes(accepted,x.inverseBindMatrices),await accessorBytes(candidate,y.inverseBindMatrices));
 delete x.inverseBindMatrices;delete y.inverseBindMatrices;assert.deepEqual(x,y);joints+=x.joints.length;
}
assert.equal(a.animations.length,b.animations.length);
for(let i=0;i<a.animations.length;i++){
 const x=a.animations[i],y=b.animations[i];assert.deepEqual(x.channels,y.channels);channels+=x.channels.length;
 assert.equal(x.samplers.length,y.samplers.length);
 for(let k=0;k<x.samplers.length;k++){
  assert.equal(x.samplers[k].interpolation,y.samplers[k].interpolation);
  for(const field of ['input','output'])assert.deepEqual(await accessorBytes(accepted,x.samplers[k][field]),await accessorBytes(candidate,y.samplers[k][field]));
 }
}
const parts=[];
for(let mi=0;mi<a.meshes.length;mi++){
 if(mi===5)continue;
 assert.equal(a.meshes[mi].name,b.meshes[mi].name);assert.equal(a.meshes[mi].primitives.length,b.meshes[mi].primitives.length);
 for(let pi=0;pi<a.meshes[mi].primitives.length;pi++){
  const x=a.meshes[mi].primitives[pi],y=b.meshes[mi].primitives[pi];
  assert.deepEqual(Object.keys(x.attributes).sort(),Object.keys(y.attributes).sort());
  assert.equal(x.material,y.material);assert.equal(x.mode,y.mode);
  const fields=[];
  for(const key of ['indices',...Object.keys(x.attributes)]){
   const ai=key==='indices'?x.indices:x.attributes[key],bi=key==='indices'?y.indices:y.attributes[key];
   const ac=structuredClone(a.accessors[ai]),bc=structuredClone(b.accessors[bi]);
   delete ac.bufferView;delete bc.bufferView;assert.deepEqual(ac,bc);
   const av=await viewBytes(accepted,a.accessors[ai].bufferView),bv=await viewBytes(candidate,b.accessors[bi].bufferView);assert(av.equals(bv),`Protected stream changed ${mi}/${pi}/${key}`);
   fields.push({semantic:key,bytes:av.length,sha256:sha(av),exact:true});
  }
  parts.push({mesh:mi,primitive:pi,name:a.meshes[mi].name,fields});
 }
}
for(let i=0;i<a.materials.length;i++)if(i!==6)assert.deepEqual(a.materials[i],b.materials[i]);
const images=[];
for(const i of [0,1,2,3,4,5,6,9,10,11]){
 const x=await viewBytes(accepted,a.images[i].bufferView),y=await viewBytes(candidate,b.images[i].bufferView);assert(x.equals(y));images.push({image:i,sha256:sha(x),bytes:x.length,exact:true});
}
assert.equal(joints,75);assert.equal(channels,225);
const result={pass:true,checkpointReference:{path:acceptedPath,sha256:expected},candidate:{path:candidatePath,sha256:fileSha(candidatePath)},
 protectedNonHoodiePartsExact:parts,nativeJoints:joints,nativeAnimationChannelsExact:channels,nativeAnimationAndInverseBindBytesExact:true,
 nodesScenesCamerasExact:true,protectedMaterialAndPNGImagesExact:images,hoodieExcludedFromCheckpointPartParity:true,accepted:false};
fs.writeFileSync(reportPath,JSON.stringify(result,null,2)+'\n');fs.closeSync(accepted.fd);fs.closeSync(candidate.fd);console.log(JSON.stringify({pass:true,joints,channels,parts:parts.length}));
