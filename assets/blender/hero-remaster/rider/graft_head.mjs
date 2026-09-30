/** Graft authored head details while preserving original rig and clip bytes. */
import fs from 'node:fs';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
const [sourcePath,donorPath,outPath]=process.argv.slice(2);
if(!outPath)throw new Error('graft_head source-uncompressed.glb donor.glb output.glb');
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
// Patch only existing head positions/normals. Everything else stays byte exact.
const bodyNode=d.nodes.find(n=>n.name==='Street_remaster_neural_full_body');assert(bodyNode?.mesh!=null);
const body=d.meshes[bodyNode.mesh];assert(body.primitives.length===1);
const attrs=body.primitives[0].attributes,position=accessorInfo(src,attrs.POSITION),normal=accessorInfo(src,attrs.NORMAL);
const key=p=>p.map(v=>Math.round(v*1e5)).join(',');
const patches=new Map(report.headVertexPatches.map(p=>[key(p.old),p]));
const allowed=new Set();let patched=0;
for(let i=0;i<position.a.count;i++){
 const p=[0,1,2].map(axis=>src.bin.readFloatLE(position.offset+i*position.stride+axis*4));
 const patch=patches.get(key(p));if(!patch)continue;
 for(let axis=0;axis<3;axis++){
  const po=position.offset+i*position.stride+axis*4,no=normal.offset+i*normal.stride+axis*4;
  src.bin.writeFloatLE(patch.position[axis],po);src.bin.writeFloatLE(patch.normal[axis],no);
  for(let lane=0;lane<4;lane++){allowed.add(po+lane);allowed.add(no+lane)}
 }
 patched++;
}
const original=read(sourcePath);let outsideHeadByteDifferences=0;
for(let i=0;i<original.bin.length;i++)if(original.bin[i]!==src.bin[i]&&!allowed.has(i))outsideHeadByteDifferences++;
assert.equal(outsideHeadByteDifferences,0);
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
const proof={source:sourcePath,donor:donorPath,output:outPath,sha256:crypto.createHash('sha256').update(out).digest('hex'),bytes:out.length,headVerticesPatched:patched,extraTriangles:report.extraTriangles,hairClumps:report.hairClumps,originalAnimationMetadataPreserved:true,originalSkinMetadataPreserved:true,originalNodeTransformsPreserved:true,outsideHeadByteDifferences};
fs.writeFileSync(outPath+'.json',JSON.stringify(proof,null,2)+'\n');console.log(JSON.stringify(proof));
