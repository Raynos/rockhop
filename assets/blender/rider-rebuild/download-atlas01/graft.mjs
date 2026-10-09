// Replace only the exact selected hoodie payload; preserve native rig and clips.
import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import {openGlb,accessorBytes,viewBytes,fileSha,sha} from '../download-opt01/geometry01/glb.mjs';
const [input,atlas,out,reportPath]=process.argv.slice(2);
assert.equal(fileSha(input),'127e316a8ff7910a4918b63f83e086e4e658062f102c73f17d0ee2f956750649');
const g=openGlb(input),j=structuredClone(g.json),p=j.meshes[5].primitives[0];
const b=JSON.parse(fs.readFileSync(path.join(atlas,'bake.json'))),replacements=new Map();
for(const [name,index] of Object.entries(p.attributes)) {
 const a=j.accessors[index],m=b.attributes[name],data=fs.readFileSync(path.join(atlas,name+'.bin'));
 replacements.set(a.bufferView,data);a.count=m.count;
 if(name==='POSITION') {a.min=m.min;a.max=m.max;}
}
const ia=j.accessors[p.indices];ia.count=b.indicesCount;replacements.set(ia.bufferView,fs.readFileSync(path.join(atlas,'indices.bin')));
for(const [kind,tex] of [['albedo',7],['orm',8]]) {
 const image=j.images[j.textures[tex].source];replacements.set(image.bufferView,fs.readFileSync(path.join(atlas,kind+'.png')));
 image.name='ExactSelectedHoodieNewAtlas_'+kind;
}
const tangentView=j.bufferViews.length;
j.bufferViews.push({buffer:0,byteLength:0});replacements.set(tangentView,fs.readFileSync(path.join(atlas,'TANGENT.bin')));
p.attributes.TANGENT=j.accessors.length;j.accessors.push({bufferView:tangentView,componentType:5126,count:b.attributes.TANGENT.count,type:'VEC4'});
const normalView=j.bufferViews.length;
j.bufferViews.push({buffer:0,byteLength:0});replacements.set(normalView,fs.readFileSync(path.join(atlas,'normal.png')));
const imageIndex=j.images.length;j.images.push({bufferView:normalView,mimeType:'image/png',name:'ExactSelectedHoodieNewAtlas_normal'});
const textureIndex=j.textures.length;j.textures.push({sampler:0,source:imageIndex});j.materials[6].normalTexture={index:textureIndex};
let offset=0;const parts=[];
for(let i=0;i<j.bufferViews.length;i++) {
 const data=replacements.has(i)?replacements.get(i):await viewBytes(g,i);
 const pad=(4-offset%4)%4;if(pad){parts.push(Buffer.alloc(pad));offset+=pad;}
 j.bufferViews[i]={...j.bufferViews[i],buffer:0,byteOffset:offset,byteLength:data.length};
 parts.push(data);offset+=data.length;
}
const tail=(4-offset%4)%4;if(tail){parts.push(Buffer.alloc(tail));offset+=tail;}
j.buffers=[{byteLength:offset}];
const js=Buffer.from(JSON.stringify(j));const jp=Buffer.alloc((js.length+3)&~3,0x20);js.copy(jp);
const header=Buffer.alloc(20);header.writeUInt32LE(0x46546c67,0);header.writeUInt32LE(2,4);header.writeUInt32LE(28+jp.length+offset,8);header.writeUInt32LE(jp.length,12);header.writeUInt32LE(0x4e4f534a,16);
const bh=Buffer.alloc(8);bh.writeUInt32LE(offset,0);bh.writeUInt32LE(0x004e4942,4);
fs.mkdirSync(path.dirname(out),{recursive:true});const fd=fs.openSync(out,'wx');for(const data of [header,jp,bh,...parts])fs.writeSync(fd,data);fs.closeSync(fd);
const candidate=openGlb(out);const protectedKeys=['nodes','skins','animations','scenes','scene','cameras'];
for(const key of protectedKeys)assert.deepEqual(candidate.json[key],g.json[key]);
const protectedAccessors=new Set();let channels=0;
for(const s of g.json.skins)protectedAccessors.add(s.inverseBindMatrices);
for(const a of g.json.animations){channels+=a.channels.length;for(const s of a.samplers){protectedAccessors.add(s.input);protectedAccessors.add(s.output);}}
for(const index of protectedAccessors)assert.deepEqual(await accessorBytes(g,index),await accessorBytes(candidate,index));
for(let mi=0;mi<g.json.meshes.length;mi++)if(mi!==5) {
 assert.deepEqual(candidate.json.meshes[mi],g.json.meshes[mi]);
 for(const pr of g.json.meshes[mi].primitives)for(const index of [...Object.values(pr.attributes),pr.indices])assert.deepEqual(await accessorBytes(g,index),await accessorBytes(candidate,index));
}
for(let mi=0;mi<g.json.materials.length;mi++)if(mi!==6)assert.deepEqual(candidate.json.materials[mi],g.json.materials[mi]);
for(let ti=0;ti<g.json.textures.length;ti++)if(ti!==7&&ti!==8){const source=g.json.textures[ti].source;assert.deepEqual(await viewBytes(g,g.json.images[source].bufferView),await viewBytes(candidate,candidate.json.images[source].bufferView));}
const report={accepted:false,source:{path:input,sha256:fileSha(input),bytes:fs.statSync(input).size},candidate:{path:out,sha256:fileSha(out),bytes:fs.statSync(out).size},hoodie:{triangles:b.triangles,vertices:b.attributes.POSITION.count,newAtlasSize:4096},nativeJsonRigAndClipsExact:true,nativeAnimationChannelCount:channels,nativeAnimationAndInverseBindAccessorBytesExact:protectedAccessors.size,protectedOtherMeshAccessorBytesExact:true,protectedOtherMaterialsAndImageBytesExact:true,changedBufferViews:[...replacements.keys()]};
fs.writeFileSync(reportPath,JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify(report));fs.closeSync(g.fd);fs.closeSync(candidate.fd);
