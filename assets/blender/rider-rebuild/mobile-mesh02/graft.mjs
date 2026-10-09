// Graft fresh selected component atlases into current source, retaining native rig.
import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import {MeshoptEncoder} from 'meshoptimizer/encoder';
import {MeshoptDecoder} from 'meshoptimizer/decoder';
import {openGlb,viewBytes,readAt,fileSha,sha} from '../download-opt01/geometry01/glb.mjs';
import {quantizeWeights} from '../download-opt01/geometry04/skin-envelope.mjs';
const [input,partsRoot,out,receipt]=process.argv.slice(2);
assert.equal(fileSha(input),'f814b8d7cde87b1e41b45eec75cd55fdea89b915bf9acae0e5a18b40d3a156af');
await Promise.all([MeshoptEncoder.ready,MeshoptDecoder.ready]);
const g=openGlb(input),j=structuredClone(g.json),changed=new Map(),components=[];
const types={1:'SCALAR',2:'VEC2',3:'VEC3',4:'VEC4'};
function newView(bytes,count,size,mode){const v=j.bufferViews.length;j.bufferViews.push({buffer:0,byteLength:bytes.length});changed.set(v,{bytes,count,size,mode});return v;}
function attribute(bytes,count,width,componentType){return {bufferView:newView(bytes,count,width*(componentType===5121?1:componentType===5123?2:4),'ATTRIBUTES'),componentType,count,type:types[width]};}
for(const [mi,name] of ['boot-L','boot-R','glove-L','glove-R'].entries()){
 const dir=path.join(partsRoot,name,...(mi>=2?['skin03','bake01']:['bake01'])),b=JSON.parse(fs.readFileSync(path.join(dir,'bake.json'))),p=j.meshes[mi].primitives[0];assert.equal(b.sourceSHA256,'127e316a8ff7910a4918b63f83e086e4e658062f102c73f17d0ee2f956750649');
 for(const [semantic,meta] of Object.entries(b.attributes)){
  if(semantic==='_NATIVE_ID')continue; // Authoring provenance remains in bake records, never a runtime shader field.
  let bytes=fs.readFileSync(path.join(dir,semantic+'.bin')),a;
  if(semantic==='WEIGHTS_0'){
   const f=new Float32Array(bytes.buffer,bytes.byteOffset,meta.count*4),q=new Uint16Array(meta.count*4);
   for(let v=0;v<meta.count;v++)q.set(quantizeWeights(Array.from(f.subarray(v*4,v*4+4))),v*4);
   bytes=Buffer.from(q.buffer);a=attribute(bytes,meta.count,4,5123);a.normalized=true;
  }else a=attribute(bytes,meta.count,meta.width,semantic==='JOINTS_0'?5121:5126);
  if(semantic==='POSITION'){a.min=meta.min;a.max=meta.max;}
  if(p.attributes[semantic]!==undefined)j.accessors[p.attributes[semantic]]=a;
  else{p.attributes[semantic]=j.accessors.length;j.accessors.push(a);}
 }
 const ia=j.accessors[p.indices];Object.assign(ia,attribute(fs.readFileSync(path.join(dir,'indices.bin')),b.indicesCount,1,5125));delete ia.min;delete ia.max;
 const mat=structuredClone(j.materials[p.material]);mat.name+=' / selected '+name+' new atlas';
 const images={};
 for(const kind of ['albedo','orm','normal']){
  const bytes=fs.readFileSync(path.join(dir,kind+'.png')),image=j.images.length;
  j.images.push({bufferView:newView(bytes,0,0,'IMAGE'),mimeType:'image/png',name:name+'_selected_atlas_'+kind});
  images[kind]={image,bytes:bytes.length,sha256:sha(bytes),width:2048,height:2048};
  images[kind].texture=j.textures.length;j.textures.push({sampler:0,source:image});
 }
 mat.pbrMetallicRoughness.baseColorTexture={index:images.albedo.texture};mat.pbrMetallicRoughness.metallicRoughnessTexture={index:images.orm.texture};mat.normalTexture={index:images.normal.texture};
 p.material=j.materials.length;j.materials.push(mat);components.push({mesh:mi,name,triangles:b.triangles,vertices:b.attributes.POSITION.count,images});
}
const used=new Set([...j.accessors.map(a=>a.bufferView),...j.images.map(i=>i.bufferView)]),map=new Map(),views=[],chunks=[];let offset=0,fallbackLength=0;
function append(bytes){const padding=(4-offset%4)%4;if(padding){chunks.push(Buffer.alloc(padding));offset+=padding;}const at=offset;chunks.push(bytes);offset+=bytes.length;return at;}
for(const old of [...used].sort((a,b)=>a-b)){
 const v=structuredClone(j.bufferViews[old]);map.set(old,views.length);
 if(changed.has(old)){
  const c=changed.get(old);delete v.extensions;delete v.byteStride;
  if(c.mode==='IMAGE'){v.buffer=0;v.byteOffset=append(c.bytes);}
  else{
   const encoded=MeshoptEncoder.encodeGltfBuffer(c.bytes,c.count,c.size,c.mode,0),decoded=Buffer.alloc(c.bytes.length);MeshoptDecoder.decodeGltfBuffer(decoded,c.count,c.size,encoded,c.mode);assert(c.bytes.equals(decoded));
   if(encoded.length<c.bytes.length){v.buffer=1;v.byteOffset=fallbackLength;fallbackLength+=c.bytes.length;v.extensions={EXT_meshopt_compression:{buffer:0,byteOffset:append(encoded),byteLength:encoded.length,byteStride:c.size,count:c.count,mode:c.mode,filter:'NONE'}};}
   else{v.buffer=0;v.byteOffset=append(c.bytes);}
  }
 }else{
  const e=v.extensions?.EXT_meshopt_compression;
  if(e){const bytes=readAt(g.fd,e.byteLength,g.binOffset+(e.byteOffset??0));e.byteOffset=append(bytes);v.buffer=1;v.byteOffset=fallbackLength;fallbackLength+=v.byteLength;}
  else{const bytes=readAt(g.fd,v.byteLength,g.binOffset+(v.byteOffset??0));v.buffer=0;v.byteOffset=append(bytes);}
 }
 views.push(v);
}
for(const a of j.accessors)a.bufferView=map.get(a.bufferView);for(const i of j.images)i.bufferView=map.get(i.bufferView);
append(Buffer.alloc(0));j.bufferViews=views;j.buffers=[{byteLength:offset},{byteLength:fallbackLength,extensions:{EXT_meshopt_compression:{fallback:true}}}];
let jb=Buffer.from(JSON.stringify(j));jb=Buffer.concat([jb,Buffer.alloc((4-jb.length%4)%4,32)]);
const h=Buffer.alloc(20),bh=Buffer.alloc(8);h.writeUInt32LE(0x46546c67);h.writeUInt32LE(2,4);h.writeUInt32LE(28+jb.length+offset,8);h.writeUInt32LE(jb.length,12);h.writeUInt32LE(0x4e4f534a,16);bh.writeUInt32LE(offset);bh.writeUInt32LE(0x004e4942,4);
fs.mkdirSync(path.dirname(out),{recursive:true});const fd=fs.openSync(out,'wx');for(const c of [h,jb,bh,...chunks])fs.writeSync(fd,c);fs.closeSync(fd);
const candidate=openGlb(out);for(const key of ['nodes','skins','animations','scenes','scene'])assert.deepEqual(candidate.json[key],g.json[key]);
const protectedAccessor=new Set(g.json.skins.map(s=>s.inverseBindMatrices));for(const a of g.json.animations)for(const s of a.samplers){protectedAccessor.add(s.input);protectedAccessor.add(s.output);}
for(let mi=4;mi<g.json.meshes.length;mi++)for(const p of g.json.meshes[mi].primitives)for(const a of [...Object.values(p.attributes),p.indices])protectedAccessor.add(a);
for(const a of protectedAccessor)assert.deepEqual(await viewBytes(candidate,candidate.json.accessors[a].bufferView),await viewBytes(g,g.json.accessors[a].bufferView));
const r={accepted:false,source:{path:input,sha256:fileSha(input)},output:{path:out,bytes:fs.statSync(out).size,sha256:fileSha(out)},components,nativeJsonRigAndClipsExact:true,protectedAccessorBytesExact:protectedAccessor.size,unchangedSourceCompressedViewsCopiedExactly:true,limits:'Old boot/glove source textures/materials retained as unreferenced records for downstream texture worker pruning. New selected-atlas PNGs require KTX2 encoding; this composition is not player art.'};
fs.writeFileSync(receipt,JSON.stringify(r,null,2)+'\n');console.log(JSON.stringify(r));fs.closeSync(g.fd);fs.closeSync(candidate.fd);
