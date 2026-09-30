/** Frozen v1 -> separate v2 sampler candidate. No geometry/image mutation. */
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import {readGlb,glbStats} from '../../glb_stats.mjs';
import {verifyBike} from '../../verify_hero_art.mjs';
const dir=path.dirname(new URL(import.meta.url).pathname);
const evidence=path.resolve(dir,'../../../../docs/evidence/hero-remaster/bike');
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const reports=[];
for(const variant of ['rookie','pro'])for(const lod of [false,true]){
 const suffix=lod?'-lod':'';
 const input=path.join(dir,`bike-${variant}-remaster${suffix}.glb`);
 const output=path.join(dir,`bike-${variant}-remaster-v2${suffix}.glb`);
 const original=fs.readFileSync(input),{doc,bin}=readGlb(original);
 const material=doc.materials.find(m=>m.name==='bike_remaster_pbr');assert(material);
 const texIds=new Set([material.pbrMetallicRoughness.baseColorTexture.index,material.pbrMetallicRoughness.metallicRoughnessTexture.index,material.normalTexture.index,material.occlusionTexture?.index].filter(x=>x!=null));
 const changed=[];
 for(const index of texIds){
  const texture=doc.textures[index],sampler=doc.samplers[texture.sampler];
  texture.sampler=doc.samplers.length;
  doc.samplers.push({...sampler,minFilter:9729,magFilter:9729});
  changed.push({texture:index,name:doc.images[texture.source].name,oldMinFilter:sampler.minFilter,newMinFilter:9729});
 }
 const json=Buffer.from(JSON.stringify(doc));const padded=Buffer.concat([json,Buffer.alloc((4-json.length%4)%4,32)]);
 const result=Buffer.alloc(28+padded.length+bin.length);result.writeUInt32LE(0x46546c67,0);result.writeUInt32LE(2,4);result.writeUInt32LE(result.length,8);result.writeUInt32LE(padded.length,12);result.writeUInt32LE(0x4e4f534a,16);padded.copy(result,20);result.writeUInt32LE(bin.length,20+padded.length);result.writeUInt32LE(0x004e4942,24+padded.length);bin.copy(result,28+padded.length);
 fs.writeFileSync(output,result);
 assert.equal(sha(readGlb(result).bin),sha(bin),'all geometry and image bytes are exactly unchanged');
 const source=path.join(dir,`baseline-${variant}.decoded.glb`);
 const verification=await verifyBike(source,output,{tris:lod?6000:33500,draws:24});
 reports.push({variant,lod,inputSha256:sha(original),outputSha256:sha(result),binaryIdentical:true,changed,verification,stats:glbStats(output)});
}
fs.writeFileSync(path.join(evidence,'sampling-v2.json'),JSON.stringify(reports,null,2)+'\n');
console.log(JSON.stringify(reports.map(r=>({variant:r.variant,lod:r.lod,sha256:r.outputSha256,bytes:r.stats.bytes,changed:r.changed})),null,2));
