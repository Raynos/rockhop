// Independent decoded stream proof of final delivery pruning/remapping.
import fs from 'node:fs';
import assert from 'node:assert/strict';
import {openGlb,viewBytes,fileSha,sha} from '../download-opt01/geometry01/glb.mjs';
const [candidatePath,compositionPath,reportPath]=process.argv.slice(2);
assert(candidatePath && compositionPath && reportPath);
const receipt=JSON.parse(fs.readFileSync(compositionPath));
assert.equal(fileSha(candidatePath),receipt.candidate.sha256);
assert.equal(fileSha(receipt.sourceGraft.path),receipt.sourceGraft.sha256);
const graft=openGlb(receipt.sourceGraft.path),candidate=openGlb(candidatePath);
const a=graft.json,b=candidate.json,streams=[];
const selectedPath='harness/out/rider-rebuild/download-opt01/textures01/composition01/rider.glb';
assert.equal(fileSha(selectedPath),receipt.selectedSourceSHA256);
const selected=openGlb(selectedPath),protectedStreams=[];
for(const key of ['nodes','skins','animations','scenes','scene','cameras'])assert.deepEqual(selected.json[key],b[key]);
const protectedAccessors=new Set(selected.json.skins.map(s=>s.inverseBindMatrices));
for(const clip of selected.json.animations)for(const sampler of clip.samplers){protectedAccessors.add(sampler.input);protectedAccessors.add(sampler.output);}
for(let mi=4;mi<selected.json.meshes.length;mi++)for(const primitive of selected.json.meshes[mi].primitives)for(const index of [...Object.values(primitive.attributes),primitive.indices])protectedAccessors.add(index);
for(const index of protectedAccessors){
 const left=await viewBytes(selected,selected.json.accessors[index].bufferView),right=await viewBytes(candidate,b.accessors[index].bufferView);
 assert(left.equals(right),`Protected selected stream ${index}`);
 const x=structuredClone(selected.json.accessors[index]),y=structuredClone(b.accessors[index]);delete x.bufferView;delete y.bufferView;assert.deepEqual(x,y);
 protectedStreams.push({accessor:index,decodedBytes:right.length,sha256:sha(right),exact:true});
}
assert.equal(a.accessors.length,b.accessors.length);
for(let index=0;index<a.accessors.length;index++){
 const x=structuredClone(a.accessors[index]),y=structuredClone(b.accessors[index]);
 const av=x.bufferView,bv=y.bufferView;delete x.bufferView;delete y.bufferView;
 assert.deepEqual(x,y,`Accessor metadata ${index}`);
 const left=await viewBytes(graft,av),right=await viewBytes(candidate,bv);
 assert(left.equals(right),`Decoded accessor view ${index}`);
 streams.push({accessor:index,sourceView:av,candidateView:bv,decodedBytes:right.length,sha256:sha(right),exact:true});
}
for(const key of ['nodes','skins','animations','scenes','scene','cameras','samplers'])assert.deepEqual(a[key],b[key]);
const geometryViews=new Set(),meshes=[];
for(let mi=0;mi<b.meshes.length;mi++)for(const [pi,p] of b.meshes[mi].primitives.entries()){
 const fields={};
 for(const [key,index] of Object.entries({...p.attributes,indices:p.indices})){
  const ac=b.accessors[index],v=b.bufferViews[ac.bufferView];geometryViews.add(ac.bufferView);
  fields[key]={accessor:index,count:ac.count,type:ac.type,componentType:ac.componentType,normalized:ac.normalized??false,decodedViewBytes:v.byteLength};
 }
 assert(!('_NATIVE_ID' in fields));
 meshes.push({mesh:mi,primitive:pi,name:b.meshes[mi].name,vertices:fields.POSITION.count,triangles:fields.indices.count/3,fields});
}
const geometryBytes=[...geometryViews].reduce((total,v)=>total+b.bufferViews[v].byteLength,0);
const liveMaterials=new Set(b.meshes.flatMap(m=>m.primitives.map(p=>p.material))),liveTextures=new Set();
function textures(o){for(const [key,value] of Object.entries(o??{}))if(key.endsWith('Texture')&&typeof value==='object'&&value?.index!==undefined)liveTextures.add(value.index);else if(value&&typeof value==='object')textures(value);}
for(const mi of liveMaterials)textures(b.materials[mi]);
const liveImages=new Set([...liveTextures].map(t=>b.textures[t].extensions.KHR_texture_basisu.source));
assert.equal(liveMaterials.size,b.materials.length);assert.equal(liveTextures.size,b.textures.length);assert.equal(liveImages.size,b.images.length);
assert(b.images.every(i=>i.mimeType==='image/ktx2'));
const imageProof=[];
for(const row of receipt.maps){
 const bytes=await viewBytes(candidate,b.images[row.image].bufferView);
 assert.equal(sha(bytes),row.sha256);assert.equal(bytes.length,row.bytes);
 assert(bytes.equals(fs.readFileSync(row.path)));
 imageProof.push({image:row.image,sourceImages:row.sourceImageAliases,bytes:bytes.length,sha256:sha(bytes),exactToPinnedKTX:true});
}
assert.equal(b.skins.reduce((total,s)=>total+s.joints.length,0),75);
assert.equal(b.animations.reduce((total,clip)=>total+clip.channels.length,0),225);
const result={accepted:false,pass:true,candidate:receipt.candidate,sourceGraft:receipt.sourceGraft,
 selectedCheckpointReference:{path:selectedPath,sha256:receipt.selectedSourceSHA256},protectedSelectedAccessorStreamsExact:protectedStreams,
 nativeJSONAndAllDecodedAccessorViewsExactToGraft:true,nativeJoints:75,nativeAnimationChannels:225,
 accessorStreams:streams,imagePayloadProof:imageProof,allMaterialTextureImageRecordsReferenced:true,
 geometry:{meshes,vertices:meshes.reduce((n,m)=>n+m.vertices,0),triangles:meshes.reduce((n,m)=>n+m.triangles,0),uniqueViews:geometryViews.size,decodedBytes:geometryBytes},
 scope:'Independent delivery-to-graft decoded storage proof; graft-to-selected source/component motion proofs remain separate. Raw metadata hashes are not compiled native-rest hashes. No moving, GPU filtering or phone-performance judgment.'};
fs.writeFileSync(reportPath,JSON.stringify(result,null,2)+'\n');fs.closeSync(graft.fd);fs.closeSync(candidate.fd);fs.closeSync(selected.fd);
console.log(JSON.stringify({pass:true,geometry:result.geometry.decodedBytes,vertices:result.geometry.vertices,triangles:result.geometry.triangles}));
