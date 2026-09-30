/** Pack the connected head graft and publish actual decoded contour identities. */
import fs from 'node:fs';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import {execFileSync} from 'node:child_process';
import {MeshoptDecoder} from 'three/examples/jsm/libs/meshopt_decoder.module.js';
const [input,output]=process.argv.slice(2);assert(output);
execFileSync(process.execPath,['assets/blender/hero-remaster/rider/pack_wrists.mjs',input,output],{stdio:'inherit'});
const bytes=fs.readFileSync(output),n=bytes.readUInt32LE(12),doc=JSON.parse(bytes.subarray(20,20+n)),bin=bytes.subarray(28+n);
const raw=JSON.parse(fs.readFileSync(input+'.neck.json'));await MeshoptDecoder.ready;
const cache=new Map();
function positions(name){
 if(cache.has(name))return cache.get(name);
 const node=doc.nodes.find(n=>n.name===name),a=doc.accessors[doc.meshes[node.mesh].primitives[0].attributes.POSITION],v=doc.bufferViews[a.bufferView],ex=v.extensions?.EXT_meshopt_compression;
 let b;if(ex){b=Buffer.alloc(v.byteLength);MeshoptDecoder.decodeGltfBuffer(b,ex.count,ex.byteStride,bin.subarray(ex.byteOffset??0,(ex.byteOffset??0)+ex.byteLength),ex.mode,ex.filter??'NONE');}else b=bin.subarray(v.byteOffset??0,(v.byteOffset??0)+v.byteLength);
 const stride=v.byteStride??12,ps=Array.from({length:a.count},(_,i)=>[0,1,2].map(c=>b.readFloatLE((a.byteOffset??0)+i*stride+c*4)));cache.set(name,ps);return ps;
}
const pairs=raw.orderedPairs.map(p=>{
 const source=positions(p.sourceMeshName),repair=positions(p.repairMeshName),expected=source[p.sourceVertexIndices[0]];
 for(const q of [...p.sourceVertexIndices.map(i=>source[i]),...p.repairVertexIndices.map(i=>repair[i])])assert.deepEqual(q,expected,'packed contour coordinates match');
 return {source:{meshName:p.sourceMeshName,vertexIndices:p.sourceVertexIndices},repair:{meshName:p.repairMeshName,vertexIndices:p.repairVertexIndices},restPosition:expected,rawRestPosition:p.restPosition};
});
const contours=raw.neckCoverage.contours.map((points,i)=>({join:`neck-${i}`,closedCycle:true,orderedPairs:points.map(p=>{
 const pair=pairs.find(q=>Math.hypot(...q.rawRestPosition.map((v,c)=>v-p[c]))<1e-6);assert(pair,'every contour point has a source/graft pair');return pair;
})}));
const mapping={asset:output,assetSHA256:crypto.createHash('sha256').update(bytes).digest('hex'),rawAssetSHA256:raw.assetSHA256,coordinateWeldMetres:1e-5,seams:[{side:'neck',joins:contours}],sourceBoundaryEdges:raw.neckCoverage.sourceBoundaryEdges};
fs.writeFileSync(output+'.neck.json',JSON.stringify(mapping,null,2)+'\n');console.log(JSON.stringify({asset:output,sha256:mapping.assetSHA256,contours:contours.length,pairs:pairs.length}));
