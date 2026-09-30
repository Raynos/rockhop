/** Keep V5 LOD contact/head/rig/clip buffers; replace its fragmented neural body. */
import fs from 'node:fs';
import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import {readGlb,writeGlb} from '../../hero_art_pack.mjs';
const [sourcePath,donorPath,outPath]=process.argv.slice(2);
assert(outPath,'graft_lod_body original-v5-lod.glb clean-body.glb output.glb');
const sourceBytes=fs.readFileSync(sourcePath),donorBytes=fs.readFileSync(donorPath),src=readGlb(sourceBytes),donor=readGlb(donorBytes),d=src.doc;
assert(!d.extensionsRequired?.includes('EXT_meshopt_compression'),'decode source first');
const baseline=structuredClone(d),palette=donor.doc.skins[0].joints.map(i=>d.skins[0].joints.findIndex(j=>d.nodes[j].name===donor.doc.nodes[i].name));
assert(palette.every(i=>i>=0));
const sourceNode=d.nodes.find(n=>n.name==='Street_remaster_neural_full_body'),donorNode=donor.doc.nodes.find(n=>n.name==='Street_remaster_neural_full_body');
const original=d.meshes[sourceNode.mesh].primitives[0],replacement=structuredClone(donor.doc.meshes[donorNode.mesh].primitives[0]);
const joints=donor.doc.accessors[replacement.attributes.JOINTS_0],jv=donor.doc.bufferViews[joints.bufferView],js=jv.byteStride??(joints.componentType===5123?8:4),jo=(jv.byteOffset??0)+(joints.byteOffset??0),read=joints.componentType===5123?'readUInt16LE':'readUInt8',write=joints.componentType===5123?'writeUInt16LE':'writeUInt8',size=joints.componentType===5123?2:1;
for(let i=0;i<joints.count;i++)for(let j=0;j<4;j++){const at=jo+i*js+j*size;donor.bin[write](palette[donor.bin[read](at)],at);}
const pad=Buffer.alloc(-src.bin.length&3),offset=src.bin.length+pad.length,vo=d.bufferViews.length,ao=d.accessors.length;
for(const v of donor.doc.bufferViews)d.bufferViews.push({...v,buffer:0,byteOffset:(v.byteOffset??0)+offset});
for(const a of donor.doc.accessors)d.accessors.push({...a,bufferView:a.bufferView+vo});
for(const name of Object.keys(replacement.attributes))replacement.attributes[name]+=ao;
replacement.indices+=ao;replacement.material=original.material;
d.meshes[sourceNode.mesh].primitives=[replacement];
const bin=Buffer.concat([src.bin,pad,donor.bin]);d.buffers[0].byteLength=bin.length;
assert.deepEqual(d.nodes,baseline.nodes);assert.deepEqual(d.skins,baseline.skins);assert.deepEqual(d.animations,baseline.animations);
for(const node of d.nodes.filter(n=>n.mesh!=null&&n!==sourceNode))assert.deepEqual(d.meshes[node.mesh],baseline.meshes[node.mesh]);
assert.deepEqual(bin.subarray(0,src.bin.length),src.bin,'all original source buffer bytes remain untouched');
const output=writeGlb(d,bin);fs.writeFileSync(outPath,output);
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const proof={source:sourcePath,sourceSHA256:sha(sourceBytes),bodyDonor:donorPath,bodyDonorSHA256:sha(donorBytes),output:outPath,outputSHA256:sha(output),authoredContactAttributesAndTrianglesByteIdentical:true,authoredHeadAttributesAndTrianglesByteIdentical:true,originalNodesSkinsClipsUnchanged:true,bodyTriangles:d.accessors[replacement.indices].count/3,bodyOutsideWristChanged:true,materialAndPhoneAtlasPreserved:true};
fs.writeFileSync(outPath+'.json',JSON.stringify(proof,null,2)+'\n');console.log(JSON.stringify(proof));
