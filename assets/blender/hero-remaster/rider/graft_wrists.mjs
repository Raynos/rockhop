/** Graft measured continuous wrist topology while preserving original rig and clip bytes. */
import fs from 'node:fs';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
const [sourcePath,donorPath,outPath]=process.argv.slice(2);
if(!outPath)throw new Error('graft_wrists source-uncompressed.glb donor.glb output.glb');
function read(p){const bytes=fs.readFileSync(p),n=bytes.readUInt32LE(12);return{doc:JSON.parse(bytes.subarray(20,20+n)),bin:Buffer.from(bytes.subarray(28+n,28+n+bytes.readUInt32LE(20+n)))}}
const src=read(sourcePath),donor=read(donorPath),report=JSON.parse(fs.readFileSync(donorPath.replace(/\.glb$/,'.json'))),d=src.doc;
assert(!d.extensionsRequired?.includes('EXT_meshopt_compression'),'source must be decoded');
const oldAnimations=JSON.stringify(d.animations),oldSkins=JSON.stringify(d.skins);
const oldNodes=structuredClone(d.nodes);
const sourceSkin=d.skins[0],donorSkin=donor.doc.skins[0];
const sourceNames=sourceSkin.joints.map(i=>d.nodes[i].name);
const palette=donorSkin.joints.map(i=>sourceNames.indexOf(donor.doc.nodes[i].name));
assert(palette.every(i=>i>=0),'same original bones');
const getComponents=a=>({SCALAR:1,VEC2:2,VEC3:3,VEC4:4,MAT4:16})[a.type];
const getBytes=a=>({5121:1,5123:2,5125:4,5126:4})[a.componentType];
function accessorInfo(g,id){const a=g.doc.accessors[id],v=g.doc.bufferViews[a.bufferView];assert(!v.extensions?.EXT_meshopt_compression,'uncompressed accessor');return{a,v,offset:(v.byteOffset??0)+(a.byteOffset??0),stride:v.byteStride??getComponents(a)*getBytes(a)}}
// Keep source position/normal/UV/contact buffers exact; remove only malformed
// terminal forearm triangles and equalize UV-duplicate weights on the cut seam.
const bodyNode=d.nodes.find(n=>n.name==='Street_remaster_neural_full_body');assert(bodyNode?.mesh!=null);
const body=d.meshes[bodyNode.mesh];assert(body.primitives.length===1);
const primitive=body.primitives[0],attrs=primitive.attributes,position=accessorInfo(src,attrs.POSITION),joints=accessorInfo(src,attrs.JOINTS_0),weights=accessorInfo(src,attrs.WEIGHTS_0);
const key=p=>p.map(v=>Math.round(v*1e5)).join(',');
const faceKey=ps=>ps.map(key).sort().join('|');
const patches=new Map(report.bodyBoundaryWeightPatches.map(p=>[key(p.position),p.weights]));
const allowed=new Set();let patched=0;const positions=[];
assert.equal(weights.a.componentType,5126);
for(let i=0;i<position.a.count;i++){
 const p=[0,1,2].map(axis=>src.bin.readFloatLE(position.offset+i*position.stride+axis*4));positions.push(p);
 const patch=patches.get(key(p));if(!patch)continue;
 const ws=Object.entries(patch).sort((a,b)=>b[1]-a[1]).slice(0,4),total=ws.reduce((n,[_,w])=>n+w,0);
 for(let lane=0;lane<4;lane++){
  const [name,w]=ws[lane]??[sourceNames[0],0],jo=joints.offset+i*joints.stride+lane*getBytes(joints.a),wo=weights.offset+i*weights.stride+lane*4;
  if(joints.a.componentType===5123)src.bin.writeUInt16LE(sourceNames.indexOf(name),jo);else src.bin.writeUInt8(sourceNames.indexOf(name),jo);
  src.bin.writeFloatLE(w/total,wo);
  for(let n=0;n<getBytes(joints.a);n++)allowed.add(jo+n);for(let n=0;n<4;n++)allowed.add(wo+n);
 }
 patched++;
}
const index=accessorInfo(src,primitive.indices),readIndex=index.a.componentType===5123?'readUInt16LE':'readUInt32LE';
const deleted=new Set(report.removedTrianglePositions.map(faceKey)),remaining=[];let removed=0;
for(let i=0;i<index.a.count;i+=3){
 const tri=[0,1,2].map(j=>src.bin[readIndex](index.offset+(i+j)*index.stride));
 if(deleted.has(faceKey(tri.map(j=>positions[j])))){removed++;continue;}remaining.push(...tri);
}
assert.equal(removed,report.removedTrianglePositions.length,'every intended terminal triangle matched');
const original=read(sourcePath);let outsideJoinByteDifferences=0;
for(let i=0;i<original.bin.length;i++)if(original.bin[i]!==src.bin[i]&&!allowed.has(i))outsideJoinByteDifferences++;
assert.equal(outsideJoinByteDifferences,0);
const indexBytes=Buffer.alloc(remaining.length*4);remaining.forEach((x,i)=>indexBytes.writeUInt32LE(x,i*4));
const indexOffset=src.bin.length+(-src.bin.length&3),indexView=d.bufferViews.length;d.bufferViews.push({buffer:0,byteOffset:indexOffset,byteLength:indexBytes.length});
primitive.indices=d.accessors.length;d.accessors.push({bufferView:indexView,componentType:5125,count:remaining.length,type:'SCALAR'});
src.bin=Buffer.concat([src.bin,Buffer.alloc(-src.bin.length&3),indexBytes]);
// Retire only exact-zero-area inherited donor faces. Palms, finger and shoe
// positions/normals/UVs/weights remain byte-identical; every nonzero face keeps
// its original triangle and ordering.
const contactNode=d.nodes.find(n=>n.name==='Authored_grips_and_soles');
const contactPrimitive=d.meshes[contactNode.mesh].primitives[0];
const cp=accessorInfo(src,contactPrimitive.attributes.POSITION),ci=accessorInfo(src,contactPrimitive.indices);
const cr=ci.a.componentType===5123?'readUInt16LE':'readUInt32LE',contactRemaining=[],removedContactTriangles=[];
for(let at=0;at<ci.a.count;at+=3){
 const ids=[0,1,2].map(j=>src.bin[cr](ci.offset+(at+j)*ci.stride));
 const ps=ids.map(i=>[0,1,2].map(c=>src.bin.readFloatLE(cp.offset+i*cp.stride+c*4)));
 const u=ps[1].map((v,c)=>v-ps[0][c]),v=ps[2].map((v,c)=>v-ps[0][c]);
 const cross=[u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0]];
 if(cross.every(x=>x===0))removedContactTriangles.push({sourceTriangle:at/3,vertexIndices:ids,positions:ps});
 else contactRemaining.push(...ids);
}
if(removedContactTriangles.length){
 const bytes=Buffer.alloc(contactRemaining.length*4);contactRemaining.forEach((x,i)=>bytes.writeUInt32LE(x,i*4));
 const offset=src.bin.length+(-src.bin.length&3),view=d.bufferViews.length;
 d.bufferViews.push({buffer:0,byteOffset:offset,byteLength:bytes.length});
 contactPrimitive.indices=d.accessors.length;d.accessors.push({bufferView:view,componentType:5125,count:contactRemaining.length,type:'SCALAR'});
 src.bin=Buffer.concat([src.bin,Buffer.alloc(-src.bin.length&3),bytes]);
}
// New meshes reference the original immutable skin; remap donor joint indices.
const jointRead={5121:'readUInt8',5123:'readUInt16LE'},jointWrite={5121:'writeUInt8',5123:'writeUInt16LE'};
for(const mesh of donor.doc.meshes)for(const p of mesh.primitives){
 const info=accessorInfo(donor,p.attributes.JOINTS_0);assert(jointRead[info.a.componentType]);
 for(let i=0;i<info.a.count;i++)for(let lane=0;lane<4;lane++){
  const o=info.offset+i*info.stride+lane*getBytes(info.a),index=donor.bin[jointRead[info.a.componentType]](o);
  donor.bin[jointWrite[info.a.componentType]](palette[index],o);
 }
}
const pad=Buffer.alloc(-src.bin.length&3),binOffset=src.bin.length+pad.length;
const viewOffset=d.bufferViews.length,accessorOffset=d.accessors.length,materialOffset=d.materials.length,meshOffset=d.meshes.length;
assert(!donor.doc.textures?.length&&!donor.doc.images?.length,'details use vertex colours only');
for(const view of donor.doc.bufferViews)d.bufferViews.push({...view,buffer:0,byteOffset:(view.byteOffset??0)+binOffset});
for(const accessor of donor.doc.accessors)d.accessors.push({...accessor,bufferView:accessor.bufferView+viewOffset});
for(const material of donor.doc.materials)d.materials.push(material);
for(const mesh of donor.doc.meshes){const copy=structuredClone(mesh);for(const p of copy.primitives){for(const k of Object.keys(p.attributes))p.attributes[k]+=accessorOffset;if(p.indices!=null)p.indices+=accessorOffset;if(p.material!=null)p.material+=materialOffset}d.meshes.push(copy)}
const bodyIndex=d.nodes.indexOf(bodyNode),parentIndex=d.nodes.findIndex(n=>n.children?.includes(bodyIndex));assert(parentIndex>=0);
for(const node of donor.doc.nodes.filter(n=>n.mesh!=null)){
 const copy=structuredClone(node);delete copy.children;copy.mesh+=meshOffset;copy.skin=0;
 const i=d.nodes.length;d.nodes.push(copy);d.nodes[parentIndex].children.push(i);
}
for(const extension of donor.doc.extensionsUsed??[])if(!(d.extensionsUsed??=[]).includes(extension))d.extensionsUsed.push(extension);
const bin=Buffer.concat([src.bin,pad,donor.bin]);d.buffers[0].byteLength=bin.length;
assert.equal(JSON.stringify(d.animations),oldAnimations);assert.equal(JSON.stringify(d.skins),oldSkins);
for(let i=0;i<oldNodes.length;i++){const before={...oldNodes[i]},after={...d.nodes[i]};delete before.children;delete after.children;assert.deepEqual(after,before)}
const json=Buffer.from(JSON.stringify(d)),jp=Buffer.concat([json,Buffer.alloc(-json.length&3,32)]),bp=Buffer.concat([bin,Buffer.alloc(-bin.length&3)]);
const out=Buffer.alloc(28+jp.length+bp.length);out.writeUInt32LE(0x46546c67,0);out.writeUInt32LE(2,4);out.writeUInt32LE(out.length,8);out.writeUInt32LE(jp.length,12);out.writeUInt32LE(0x4e4f534a,16);jp.copy(out,20);out.writeUInt32LE(bp.length,20+jp.length);out.writeUInt32LE(0x004e4942,24+jp.length);bp.copy(out,28+jp.length);
fs.writeFileSync(outPath,out);
// Exact raw glTF vertex correspondence, carried unchanged by Meshopt packing.
function vertexLookup(meshName){
 const node=d.nodes.find(n=>n.name===meshName),prim=d.meshes[node.mesh].primitives[0];
 const info=accessorInfo({doc:d,bin},prim.attributes.POSITION),lookup=new Map();
 for(let i=0;i<info.a.count;i++){
  const p=[0,1,2].map(c=>bin.readFloatLE(info.offset+i*info.stride+c*4)),k=key(p);
  lookup.set(k,[...(lookup.get(k)??[]),i]);
 }
 return lookup;
}
const bridgeName='Street_continuous_wrists',bridgeLookup=vertexLookup(bridgeName),bodyLookup=vertexLookup(bodyNode.name),gloveLookup=vertexLookup('Authored_grips_and_soles');
const seamMap={asset:outPath,coordinateWeldMetres:1e-5,method:'Closed actual edge cycles; explicit co-located body↔repair and repair↔glove vertex groups. Every listed consecutive pair forms an original contour edge.',seams:report.seams.map(s=>({side:s.side,joins:['body','glove'].map(which=>{
 const meshName=which==='body'?bodyNode.name:'Authored_grips_and_soles',lookup=which==='body'?bodyLookup:gloveLookup;
 return {join:which,closedCycle:true,orderedPairs:s[which].sourcePositions.map((p,i)=>{const k=key(p),sourceIndices=lookup.get(k),repairIndices=bridgeLookup.get(k);assert(sourceIndices?.length&&repairIndices?.length,`seam ${s.side}/${which}/${i} maps every endpoint`);return{source:{meshName,vertexIndices:sourceIndices},repair:{meshName:bridgeName,vertexIndices:repairIndices},restPosition:p}})};
 })}))};
fs.writeFileSync(outPath+'.seams.json',JSON.stringify(seamMap,null,2)+'\n');
const proof={source:sourcePath,donor:donorPath,output:outPath,sha256:crypto.createHash('sha256').update(out).digest('hex'),bytes:out.length,boundaryWeightVerticesPatched:patched,removedTriangles:removed,extraTriangles:report.extraTriangles,removedExactZeroAreaContactTriangles:removedContactTriangles,nonzeroContactTrianglesPreserved:true,wristContours:report.sides,originalAnimationMetadataPreserved:true,originalSkinMetadataPreserved:true,originalNodeTransformsPreserved:true,outsideJoinByteDifferences};
fs.writeFileSync(outPath+'.json',JSON.stringify(proof,null,2)+'\n');console.log(JSON.stringify(proof));
