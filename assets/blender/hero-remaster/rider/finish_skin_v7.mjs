/** Material-only V7 finish; retain every packed V6 geometry and motion stream. */
import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import {execFileSync} from 'node:child_process';
import {MeshoptEncoder} from 'meshoptimizer/encoder';
import {MeshoptDecoder} from 'three/examples/jsm/libs/meshopt_decoder.module.js';
import {readGlb,writeGlb} from '../../hero_art_pack.mjs';
const [input,out,...options]=process.argv.slice(2);assert(input&&out,'finish_skin_v7 source-packed.glb output-packed.glb [--paint-only]');
const source=fs.readFileSync(input),g=readGlb(source),d=g.doc,b=g.bin,cache=new Map();await MeshoptDecoder.ready;
function acc(ai){
 const a=d.accessors[ai],v=d.bufferViews[a.bufferView],ex=v.extensions?.EXT_meshopt_compression;
 let bytes;
 if(ex){if(!cache.has(a.bufferView)){const dst=Buffer.alloc(v.byteLength);MeshoptDecoder.decodeGltfBuffer(dst,ex.count,ex.byteStride,b.subarray(ex.byteOffset??0,(ex.byteOffset??0)+ex.byteLength),ex.mode,ex.filter??'NONE');cache.set(a.bufferView,dst);}bytes=cache.get(a.bufferView);}
 else bytes=b.subarray(v.byteOffset??0,(v.byteOffset??0)+v.byteLength);
 const count={SCALAR:1,VEC2:2,VEC3:3,VEC4:4}[a.type],size={5121:1,5123:2,5125:4,5126:4}[a.componentType],fn={5121:'readUInt8',5123:'readUInt16LE',5125:'readUInt32LE',5126:'readFloatLE'}[a.componentType];
 return Array.from({length:a.count},(_,i)=>Array.from({length:count},(_,j)=>bytes[fn]((a.byteOffset??0)+i*(v.byteStride??count*size)+j*size)));
}
const body=d.nodes.find(n=>n.name==='Street_remaster_neural_full_body'),p=d.meshes[body.mesh].primitives[0],positions=acc(p.attributes.POSITION),uv=acc(p.attributes.TEXCOORD_0),ids=acc(p.indices).map(v=>v[0]),joints=acc(p.attributes.JOINTS_0),weights=acc(p.attributes.WEIGHTS_0),names=d.skins[body.skin].joints.map(i=>d.nodes[i].name);
const seamMap=JSON.parse(fs.readFileSync(input+'.seams.json'));
const pointKey=p=>p.map(v=>Math.round(v*1e6)).join(',');
const edgeKey=(a,b)=>[pointKey(a),pointKey(b)].sort().join('|');
const contourEdges=new Set(seamMap.seams.flatMap(side=>side.joins.filter(j=>j.join==='body').flatMap(join=>join.orderedPairs.map((p,i)=>edgeKey(p.restPosition,join.orderedPairs[(i+1)%join.orderedPairs.length].restPosition)))));
const forceSkinTriangles=[],seenCutEdges=new Set();
for(let i=0;i<ids.length;i+=3){const ps=ids.slice(i,i+3).map(j=>positions[j]);const matches=[0,1,2].map(j=>edgeKey(ps[j],ps[(j+1)%3])).filter(k=>contourEdges.has(k));matches.forEach(k=>seenCutEdges.add(k));if(matches.length)forceSkinTriangles.push(i/3);}
assert.equal(seenCutEdges.size,contourEdges.size,'every actual body cut edge is included');
const geometry={positions,uv,forceSkinTriangles,triangles:Array.from({length:ids.length/3},(_,i)=>ids.slice(i*3,i*3+3)),forearmWeight:weights.map((ws,i)=>ws.reduce((n,w,j)=>n+(/^(forearm|hand)\.[LR]$/.test(names[joints[i][j]])?w:0),0)),headDominant:weights.map((ws,i)=>names[joints[i][ws.indexOf(Math.max(...ws))]]==='head')};
const stem=path.join(path.dirname(out),'work',path.basename(out,'.glb'));fs.mkdirSync(path.dirname(stem),{recursive:true});
const geometryPath=stem+'.geometry.json',imagePath=stem+'.source.jpg',paintedPath=stem+'.body.png';
fs.writeFileSync(geometryPath,JSON.stringify(geometry));
const bodyMaterial=d.materials[p.material],imageIndex=d.textures[bodyMaterial.pbrMetallicRoughness.baseColorTexture.index].source,im=d.images[imageIndex],v=d.bufferViews[im.bufferView];assert.equal(im.mimeType,'image/jpeg');fs.writeFileSync(imagePath,b.subarray(v.byteOffset??0,(v.byteOffset??0)+v.byteLength));
const paletteOption=options.find(x=>x.startsWith('--palette='));const paletteArgs=paletteOption?['--target',JSON.parse(fs.readFileSync(paletteOption.slice(10))).skinSelection.targetSRGB.join(',')]:[];
execFileSync(process.env.BLENDER??'/Applications/Blender.app/Contents/MacOS/Blender',['-b','--python-exit-code','1','--python','assets/blender/hero-remaster/rider/paint_skin_v7.py','--','--geometry',geometryPath,'--image',imagePath,'--out',paintedPath,'--material-split',...paletteArgs],{stdio:'inherit'});
const paint=JSON.parse(fs.readFileSync(paintedPath+'.json'));
if(options.includes('--paint-only'))process.exit(0);
const original=structuredClone(d),sha=bytes=>crypto.createHash('sha256').update(bytes).digest('hex');
const selected=new Set(paint.selectedFaceIndices),cloth=[],skin=[];
for(let i=0;i<ids.length;i+=3)(selected.has(i/3)?skin:cloth).push(...ids.slice(i,i+3));
assert(skin.length>0&&cloth.length>0);
await MeshoptEncoder.ready;
const chunks=[b];let actual=b.length;const decodedStreams=[];
function indexStream(indices){
 const raw=Buffer.alloc(indices.length*4);indices.forEach((v,i)=>raw.writeUInt32LE(v,i*4));
 const encoded=Buffer.from(MeshoptEncoder.encodeGltfBuffer(raw,indices.length,4,'TRIANGLES'));
 const padding=Buffer.alloc(-actual&3);chunks.push(padding);actual+=padding.length;
 const offset=actual;chunks.push(encoded);actual+=encoded.length;
 const fallback=1;assert(d.buffers[fallback]);const virtual=d.buffers[fallback].byteLength;d.buffers[fallback].byteLength+=raw.length;
 const view=d.bufferViews.length;d.bufferViews.push({buffer:fallback,byteOffset:virtual,byteLength:raw.length,extensions:{EXT_meshopt_compression:{buffer:0,byteOffset:offset,byteLength:encoded.length,count:indices.length,byteStride:4,mode:'TRIANGLES'}}});
 const accessor=d.accessors.length;d.accessors.push({bufferView:view,componentType:5125,count:indices.length,type:'SCALAR'});
 const verify=Buffer.alloc(raw.length);MeshoptDecoder.decodeGltfBuffer(verify,indices.length,4,encoded,'TRIANGLES');decodedStreams.push(Array.from({length:indices.length},(_,i)=>verify.readUInt32LE(i*4)));
 return {accessor,compressedBytes:encoded.length,decodedBytes:raw.length};
}
const compact=options.includes('--compact');
const usedVertices=new Set(skin),seamWitnesses=seamMap.seams.flatMap(side=>side.joins.filter(j=>j.join==='body').flatMap(join=>join.orderedPairs.flatMap(pair=>pair.source.vertexIndices)));
const compactVertices=[...new Set([...usedVertices,...seamWitnesses])].sort((a,b)=>a-b),oldToCompact=new Map(compactVertices.map((old,i)=>[old,i]));
const compactAttributeProof=[];
function compactAttribute(id){
 const a=d.accessors[id],view=d.bufferViews[a.bufferView],ex=view.extensions?.EXT_meshopt_compression;
 let bytes;
 if(ex){if(!cache.has(a.bufferView)){const dst=Buffer.alloc(view.byteLength);MeshoptDecoder.decodeGltfBuffer(dst,ex.count,ex.byteStride,b.subarray(ex.byteOffset??0,(ex.byteOffset??0)+ex.byteLength),ex.mode,ex.filter??'NONE');cache.set(a.bufferView,dst);}bytes=cache.get(a.bufferView);}
 else bytes=b.subarray(view.byteOffset??0,(view.byteOffset??0)+view.byteLength);
 const components={SCALAR:1,VEC2:2,VEC3:3,VEC4:4}[a.type],size={5120:1,5121:1,5122:2,5123:2,5125:4,5126:4}[a.componentType],activeBytes=components*size,sourceStride=view.byteStride??activeBytes,stride=Math.ceil(activeBytes/4)*4;
 const raw=Buffer.alloc(compactVertices.length*stride);
 compactVertices.forEach((old,i)=>{const start=(a.byteOffset??0)+old*sourceStride;bytes.copy(raw,i*stride,start,start+activeBytes);});
 const encoded=Buffer.from(MeshoptEncoder.encodeGltfBuffer(raw,compactVertices.length,stride,'ATTRIBUTES'));
 const verify=Buffer.alloc(raw.length);MeshoptDecoder.decodeGltfBuffer(verify,compactVertices.length,stride,encoded,'ATTRIBUTES','NONE');
 compactVertices.forEach((old,i)=>{const start=(a.byteOffset??0)+old*sourceStride;assert.deepEqual(verify.subarray(i*stride,i*stride+activeBytes),bytes.subarray(start,start+activeBytes),'every decoded attribute component is exact');});
 const padding=Buffer.alloc(-actual&3);chunks.push(padding);actual+=padding.length;const offset=actual;chunks.push(encoded);actual+=encoded.length;
 const virtual=d.buffers[1].byteLength;d.buffers[1].byteLength+=raw.length;const bufferView=d.bufferViews.length;
 d.bufferViews.push({buffer:1,byteOffset:virtual,byteLength:raw.length,byteStride:stride,extensions:{EXT_meshopt_compression:{buffer:0,byteOffset:offset,byteLength:encoded.length,count:compactVertices.length,byteStride:stride,mode:'ATTRIBUTES',filter:'NONE'}}});
 const accessor=d.accessors.length,copy={...a,bufferView,byteOffset:0,count:compactVertices.length};
 delete copy.min;delete copy.max;
 if(a.type==='VEC3'&&a.componentType===5126){const ps=compactVertices.map(old=>positions[old]);copy.min=[0,1,2].map(c=>Math.min(...ps.map(p=>p[c])));copy.max=[0,1,2].map(c=>Math.max(...ps.map(p=>p[c])));}
 d.accessors.push(copy);compactAttributeProof.push({sourceAccessor:id,newAccessor:accessor,sourceComponentType:a.componentType,sourceNormalized:a.normalized??false,vertices:compactVertices.length,decodedComponentBitsIdentical:true,filter:'NONE',compressedBytes:encoded.length,decodedBytes:raw.length});return accessor;
}
const skinAttributes=compact?Object.fromEntries(Object.entries(p.attributes).map(([name,id])=>[name,compactAttribute(id)])):structuredClone(p.attributes);
const clothIndex=indexStream(cloth),skinIndex=indexStream(compact?skin.map(old=>oldToCompact.get(old)):skin);
function canonicalTriangle(t){return [t,t.slice(1).concat(t[0]),t.slice(2).concat(t.slice(0,2))].map(x=>x.join(',')).sort()[0];}
function triangleSet(indices){const set=new Map();for(let i=0;i<indices.length;i+=3){const key=canonicalTriangle(indices.slice(i,i+3));set.set(key,(set.get(key)??0)+1);}return set;}
assert.deepEqual(triangleSet(decodedStreams[0].concat(compact?decodedStreams[1].map(i=>compactVertices[i]):decodedStreams[1])),triangleSet(ids),'decoded split triangle set preserves original oriented faces and multiplicities');
p.indices=clothIndex.accessor;
const skinMaterial=d.materials.length;d.materials.push({name:'Street V7 clean warm forearm skin',pbrMetallicRoughness:{baseColorFactor:[...paint.targetLinear,1],roughnessFactor:.72,metallicFactor:0}});
const skinMesh=d.meshes.length;d.meshes.push({name:'Street_forearm_skin',primitives:[{...structuredClone(p),attributes:skinAttributes,indices:skinIndex.accessor,material:skinMaterial}]});
const bodyIndex=d.nodes.indexOf(body),parentIndex=d.nodes.findIndex(n=>n.children?.includes(bodyIndex));assert(parentIndex>=0);
const skinNode=d.nodes.length;d.nodes.push({...structuredClone(body),name:'Street_forearm_skin',mesh:skinMesh});d.nodes[parentIndex].children.push(skinNode);
const repair=d.nodes.find(n=>n.name==='Street_continuous_wrists'),repairPrimitive=d.meshes[repair.mesh].primitives[0],oldColour=repairPrimitive.attributes.COLOR_0;assert(oldColour!=null);delete repairPrimitive.attributes.COLOR_0;repairPrimitive.material=skinMaterial;
// Retain the original entire packed BIN chunk, all original accessor/view
// descriptions, original skin metadata and clip metadata verbatim.
assert.deepEqual(d.skins,original.skins);assert.deepEqual(d.animations,original.animations);
for(let i=0;i<original.accessors.length;i++)assert.deepEqual(d.accessors[i],original.accessors[i]);
for(let i=0;i<original.bufferViews.length;i++)assert.deepEqual(d.bufferViews[i],original.bufferViews[i]);
for(let i=0;i<original.nodes.length;i++){const expected=structuredClone(original.nodes[i]);if(i===parentIndex)expected.children.push(skinNode);assert.deepEqual(d.nodes[i],expected);}
for(let i=0;i<original.meshes.length;i++)for(let j=0;j<original.meshes[i].primitives.length;j++){
 const expected=structuredClone(original.meshes[i].primitives[j]);
 if(i===body.mesh)expected.indices=clothIndex.accessor;
 if(i===repair.mesh){delete expected.attributes.COLOR_0;expected.material=skinMaterial;}
 assert.deepEqual(d.meshes[i].primitives[j],expected,'only approved material/index bindings change');
}
assert.deepEqual(d.images,original.images);assert.deepEqual(d.textures,original.textures);assert.deepEqual(d.materials.slice(0,original.materials.length),original.materials);
const bin=Buffer.concat(chunks);assert.deepEqual(bin.subarray(0,b.length),b);d.buffers[0].byteLength=bin.length;
const output=writeGlb(d,bin);fs.writeFileSync(out,output);
for(const side of seamMap.seams)for(const join of side.joins)if(join.join==='body')for(const pair of join.orderedPairs){pair.source.originalMeshName=pair.source.meshName;pair.source.meshName='Street_forearm_skin';if(compact){pair.source.originalVertexIndices=pair.source.vertexIndices;pair.source.vertexIndices=pair.source.vertexIndices.map(old=>oldToCompact.get(old));assert(pair.source.vertexIndices.every(i=>i!=null));}}
seamMap.asset=out;seamMap.assetSHA256=sha(output);seamMap.materialSourceAssetSHA256=sha(source);seamMap.materialSourceMapSHA256=sha(fs.readFileSync(input+'.seams.json'));fs.writeFileSync(out+'.seams.json',JSON.stringify(seamMap,null,2)+'\n');
const {selectedFaceIndices,...selection}=paint;
const proof={source:input,sourceSHA256:sha(source),output:out,sha256:sha(output),bytes:output.length,originalPackedBINPrefixByteIdentical:true,originalGeometryAccessorsAndBufferViewsUnchanged:true,positionsNormalsUVsJointsWeightsRigClipsUnchanged:true,originalOrientedTriangleSetAndMultiplicityUnchanged:true,originalBodyTriangles:ids.length/3,bodyClothTriangles:cloth.length/3,exposedSkinTriangles:skin.length/3,sourceVertexColourAccessorBytesRetained:true,changedAttributeBindings:[{mesh:repair.name,attribute:'COLOR_0',oldAccessor:oldColour,newAccessor:null,reason:'Approved material-only disconnection of noisy V6 vertex albedo; stored original colour bytes retained.'}],changedIndexBindings:[{mesh:body.name,oldAccessor:original.meshes[body.mesh].primitives[0].indices,newAccessor:clothIndex.accessor},{mesh:'Street_forearm_skin',newAccessor:skinIndex.accessor}],seamCorrespondenceGroupCardinalityAndPositionsUnchanged:true,compactForearm:compact?{vertices:compactVertices.length,referencedVertices:usedVertices.size,mandatoryUnreferencedSeamWitnesses:compactVertices.length-usedVertices.size,compactVertexToOriginal:compactVertices,attributes:compactAttributeProof,oldToNewSeamRemapExplicit:true,originalBodyBuffersUntouched:true}:null,seamSourceMeshRemap:{from:body.name,to:'Street_forearm_skin'},skinSelection:selection,materialTradeoff:{drawsBefore:4,drawsAfter:5,originalImageBytesUnchanged:true,indexStreams:[clothIndex,skinIndex],addedTransferBytes:output.length-source.length,newIndexStreamsDecodedBytes:clothIndex.decodedBytes+skinIndex.decodedBytes,liveDecodedIndexDeltaBytes:clothIndex.decodedBytes+skinIndex.decodedBytes-ids.length*4,bodyVertexAttributeAccessorsShared:!compact,forearmAttributeCopyIsCompact:compact,losslessAtlasRouteRejected:{fullBodyJPEGBytes:305303,fullBodyPNGBytes:4103707,reason:'About3.8MB image growth to repaint4195skin texels is disproportionate.'}},artStatus:'requires parent actual moving engine judgment'};
fs.writeFileSync(out+'.json',JSON.stringify(proof,null,2)+'\n');console.log(JSON.stringify(proof));
