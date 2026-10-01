/** Bake actual validated runtime weights into immutable private GLB source. */
import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import { pathToFileURL } from 'node:url';
import type * as THREE from 'three';
import { build } from 'vite';
import { patchNewRiderSource } from './new-rider-private-adapter.mjs';
import { loadRigAt } from '../../src/render/hero/gltfTestUtils';
import { prepareHero } from '../../src/render/hero/lod';
import type { MaterialLibrary } from '../../src/render/materials/library';
const base='/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/rig-adapter01';
const source=base+'/body-bind08/rider.glb',out=path.resolve('docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/body-bind09');fs.mkdirSync(out,{recursive:true});fs.mkdirSync(base+'/body-bind09',{recursive:true});
const bundle=path.resolve('harness/out/hero-remaster/bake-rim-cpu');
await build({configFile:false,publicDir:false,logLevel:'error',build:{ssr:'src/render/hero/gltfRider.ts',outDir:bundle,emptyOutDir:true,minify:false,rollupOptions:{external:['three',/^three\//],output:{entryFileNames:'rider.mjs'}}},plugins:[{name:'actual-skin-bake',enforce:'pre',transform(code,id){return id.toLowerCase().endsWith('/src/render/hero/gltfrider.ts')?{code:patchNewRiderSource(code,true,true),map:null}:null;}}]});
const {GltfRider}=await import(pathToFileURL(bundle+'/rider.mjs').href);
const g=await loadRigAt(pathToFileURL(source),true);await prepareHero(g);const rider=new GltfRider(g,{complete(){}} as unknown as MaterialLibrary);
const meshes:THREE.SkinnedMesh[]=[];rider.scene.traverse((o:THREE.Object3D)=>{if((o as THREE.SkinnedMesh).isSkinnedMesh)meshes.push(o as THREE.SkinnedMesh);});assert.equal(meshes.length,5);
const raw=fs.readFileSync(source),jl=raw.readUInt32LE(12),j=JSON.parse(raw.subarray(20,20+jl).toString('utf8'));const bl=raw.readUInt32LE(20+jl),binary=raw.subarray(28+jl,28+jl+bl),patched=Buffer.from(binary),allowed=new Set<number>();
type Accessor={bufferView:number;count:number;type:string;componentType:number;byteOffset?:number};
const accessor=(i:number)=>j.accessors[i] as Accessor;
const loc=(i:number)=>{const a=accessor(i),v=j.bufferViews[a.bufferView],size=({SCALAR:1,VEC2:2,VEC3:3,VEC4:4,MAT4:16} as Record<string,number>)[a.type]! * ({5121:1,5123:2,5125:4,5126:4} as Record<number,number>)[a.componentType]!;return{a,size,stride:v.byteStride??size,start:(v.byteOffset??0)+(a.byteOffset??0)};};
const rows=[];
for(const document of j.meshes)for(const primitive of document.primitives){
 const position=loc(primitive.attributes.POSITION),m=meshes.find(m=>m.geometry.getAttribute('position').count===position.a.count);assert(m,'Unique actual primitive count required');
 assert.equal(meshes.filter(x=>x.geometry.getAttribute('position').count===position.a.count).length,1);
 const p=m.geometry.getAttribute('position');for(let i=0;i<p.count;i++)for(let lane=0;lane<3;lane++)assert.equal(p.getComponent(i,lane),binary.readFloatLE(position.start+i*position.stride+lane*4));
 const changed:Record<string,number>={};
 for(const [attribute,name] of [['skinIndex','JOINTS_0'],['skinWeight','WEIGHTS_0']]){
  const a=loc(primitive.attributes[name!]);const v:THREE.BufferAttribute|THREE.InterleavedBufferAttribute=m.geometry.getAttribute(attribute!);assert.equal(a.a.count,v.count);assert.equal(v.itemSize,4);assert([5121,5123,5126].includes(a.a.componentType));
  for(let i=0;i<v.count;i++)for(let lane=0;lane<4;lane++){
   const at=a.start+i*a.stride+lane*({5121:1,5123:2,5126:4} as Record<number,number>)[a.a.componentType]!,value=v.getComponent(i,lane);assert(Number.isFinite(value));
   if(a.a.componentType===5126)patched.writeFloatLE(value,at);else if(a.a.componentType===5123)patched.writeUInt16LE(value,at);else patched.writeUInt8(value,at);
   for(let b=0;b<({5121:1,5123:2,5126:4} as Record<number,number>)[a.a.componentType]!;b++)allowed.add(at+b);
  }
  changed[name!]=Array.from({length:a.a.count},(_,i)=>Array.from({length:a.size},(_,b)=>binary[a.start+i*a.stride+b]!==patched[a.start+i*a.stride+b]?1:0).reduce<number>((s,v)=>s+v,0)).reduce((s,v)=>s+v,0);
 }
 rows.push({mesh:m.name,material:primitive.material,changed});
}
let changedBytes=0;for(let i=0;i<binary.length;i++)if(binary[i]!==patched[i]){assert(allowed.has(i));changedBytes++;}
assert(rows.filter(r=>Object.values(r.changed).some(Boolean)).every(r=>[0,2].includes(r.material)),'Only original body and hood skin may change');
const originalJSON=structuredClone(j),node=j.nodes.find((n:{extras?:Record<string,unknown>})=>typeof n.extras?.rockhopRiderContactAdapter==='string');assert(node&&!node.extras.rockhopRiderSkinConditioned);node.extras.rockhopRiderSkinConditioned=1;
const check=structuredClone(j);delete check.nodes.find((n:{extras?:Record<string,unknown>})=>n.extras?.rockhopRiderSkinConditioned===1).extras.rockhopRiderSkinConditioned;assert.deepEqual(check,originalJSON);
const json=Buffer.from(JSON.stringify(j)),jsonPad=Buffer.concat([json,Buffer.alloc((4-json.length%4)%4,32)]),header=Buffer.alloc(20);header.writeUInt32LE(0x46546c67,0);header.writeUInt32LE(2,4);header.writeUInt32LE(28+jsonPad.length+patched.length,8);header.writeUInt32LE(jsonPad.length,12);header.writeUInt32LE(0x4e4f534a,16);const bh=Buffer.alloc(8);bh.writeUInt32LE(patched.length,0);bh.writeUInt32LE(0x004e4942,4);const result=Buffer.concat([header,jsonPad,bh,patched]);assert.equal(result.length,result.readUInt32LE(8));fs.writeFileSync(base+'/body-bind09/rider.glb',result);
const sha=(b:Buffer)=>crypto.createHash('sha256').update(b).digest('hex');assert.equal(sha(fs.readFileSync(source)),sha(raw));
fs.writeFileSync(out+'/bake-report.json',JSON.stringify({source,sourceSHA256:sha(raw),candidateSHA256:sha(result),sourceUnchanged:true,rows,changedBytes,allBytesOutsideSkinExact:true,onlyMetadataAddition:'rockhopRiderSkinConditioned=1 on existing NEW contact-adapter node',restGeometryNormalsUVIndicesMorphImagesMaterialsAnimationBindsSocketsExact:true,privateRim:rider.scene.userData.rockhopPrivateClothRim,scope:'CPU actual production skin conditioning plus exact hood-authority rim reconciliation; frozen source09 must skip repeated conditioning. No physics/player/bike change or moving acceptance.'},null,2)+'\n');console.log('SKIN_BAKE_PASS',sha(result),changedBytes);
