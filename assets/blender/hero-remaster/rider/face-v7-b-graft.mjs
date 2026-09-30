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
// Original body vertex/index attributes stay immutable except its head index set.
const bodyNode=d.nodes.find(n=>n.name==='Street_remaster_neural_full_body');assert(bodyNode?.mesh!=null);
const body=d.meshes[bodyNode.mesh];assert(body.primitives.length===1);
const prim=body.primitives[0],position=accessorInfo(src,prim.attributes.POSITION),indices=accessorInfo(src,prim.indices);
const key=p=>p.map(v=>Math.round(v*1e5)).join(',');
const triKey=ps=>ps.map(key).sort().join(';');
const indexRead={5121:'readUInt8',5123:'readUInt16LE',5125:'readUInt32LE'};
const readIndex=i=>src.bin[indexRead[indices.a.componentType]](indices.offset+i*indices.stride);
const readPosition=i=>[0,1,2].map(c=>src.bin.readFloatLE(position.offset+i*position.stride+c*4));
const cell=p=>p.map(v=>Math.floor(v/1e-4)),grid=new Map();
for(let i=0;i<position.a.count;i++){const p=readPosition(i),k=cell(p).join(',');if(!grid.has(k))grid.set(k,[]);grid.get(k).push(p);}
const canonical=p=>p.map(v=>v.toString()).join(',');
function nearest(p){const c=cell(p);let best=null,distance=1e-5;for(let x=-1;x<=1;x++)for(let y=-1;y<=1;y++)for(let z=-1;z<=1;z++)for(const q of grid.get([c[0]+x,c[1]+y,c[2]+z].join(','))??[]){const dist=Math.hypot(...p.map((v,i)=>v-q[i]));if(dist<distance){best=q;distance=dist;}}assert(best,'Blender triangle maps to source geometry');return canonical(best);}
const remove=new Set(report.removedHeadTriangles.map(ps=>ps.map(nearest).sort().join(';')));
let removed=0;const kept=[];
for(let i=0;i<indices.a.count;i+=3){const ids=[0,1,2].map(k=>readIndex(i+k));if(remove.has(ids.map(readPosition).map(canonical).sort().join(';')))removed++;else kept.push(...ids);}
assert.equal(removed,report.removedHeadTriangleCount,'every head triangle identified');
const ib=Buffer.alloc(kept.length*4);kept.forEach((v,i)=>ib.writeUInt32LE(v,i*4));
const ip=Buffer.alloc(-src.bin.length&3),io=src.bin.length+ip.length;
src.bin=Buffer.concat([src.bin,ip,ib]);
const vi=d.bufferViews.length;d.bufferViews.push({buffer:0,byteOffset:io,byteLength:ib.length,target:34963});
prim.indices=d.accessors.length;d.accessors.push({bufferView:vi,componentType:5125,type:'SCALAR',count:kept.length,min:[kept.reduce((a,b)=>Math.min(a,b),Infinity)],max:[kept.reduce((a,b)=>Math.max(a,b),-Infinity)]});
const oldHairNode=d.nodes.find(n=>n.name===report.removedOldHairNode);assert(oldHairNode?.mesh!=null);
// Keep the original node transform but release its old 4,952-triangle tubes.
const oldHairMesh=oldHairNode.mesh;delete oldHairNode.mesh;delete oldHairNode.skin;
d.meshes.splice(oldHairMesh,1);for(const node of d.nodes)if(node.mesh>oldHairMesh)node.mesh--;
const original=read(sourcePath);assert(src.bin.subarray(0,original.bin.length).equals(original.bin),'all original attribute bytes identical');
const outsideHeadByteDifferences=0;
// New meshes reference the original immutable skin; remap donor joint indices.
const jointRead={5121:'readUInt8',5123:'readUInt16LE'},jointWrite={5121:'writeUInt8',5123:'writeUInt16LE'};
for(const mesh of donor.doc.meshes)for(const p of mesh.primitives){
 const info=accessorInfo(donor,p.attributes.JOINTS_0);assert(jointRead[info.a.componentType]);
 for(let i=0;i<info.a.count;i++)for(let lane=0;lane<4;lane++){
  const o=info.offset+i*info.stride+lane*getBytes(info.a),index=donor.bin[jointRead[info.a.componentType]](o);
  donor.bin[jointWrite[info.a.componentType]](palette[index],o);
 }
}
// Patch the exported donor boundary attributes with the exact source lanes.
// Blender's export can reorder UV vertices and normalize floating weights.
const skinAttrs=prim.attributes;
const sourcePositions=Array.from({length:position.a.count},(_,i)=>readPosition(i));
const neckPairs=[];
for(const node of donor.doc.nodes.filter(n=>n.mesh!=null))for(const p of donor.doc.meshes[node.mesh].primitives){
 const dp=accessorInfo(donor,p.attributes.POSITION),dj=accessorInfo(donor,p.attributes.JOINTS_0),dw=accessorInfo(donor,p.attributes.WEIGHTS_0),dn=accessorInfo(donor,p.attributes.NORMAL);
 const sj=accessorInfo(src,skinAttrs.JOINTS_0),sw=accessorInfo(src,skinAttrs.WEIGHTS_0),sn=accessorInfo(src,skinAttrs.NORMAL);
 const readLane=(g,info,i,lane)=>info.a.componentType===5126?g.bin.readFloatLE(info.offset+i*info.stride+lane*4):g.bin[jointRead[info.a.componentType]](info.offset+i*info.stride+lane*getBytes(info.a));
 const writeLane=(g,info,i,lane,value)=>info.a.componentType===5126?g.bin.writeFloatLE(value,info.offset+i*info.stride+lane*4):g.bin[jointWrite[info.a.componentType]](value,info.offset+i*info.stride+lane*getBytes(info.a));
 for(const join of report.neckSeamCorrespondence){
  const point=join.sourceVertexPosition;
  const sourceIds=sourcePositions.map((p,i)=>Math.hypot(...p.map((v,c)=>v-point[c]))<1e-6?i:-1).filter(i=>i>=0);assert(sourceIds.length);
  const si=sourceIds[0],donorIds=[];
  for(let i=0;i<dp.a.count;i++){
   const q=[0,1,2].map(c=>donor.bin.readFloatLE(dp.offset+i*dp.stride+c*4));
   if(Math.hypot(...q.map((v,c)=>v-point[c]))>=1e-6)continue;
   donorIds.push(i);
   for(let c=0;c<3;c++){donor.bin.writeFloatLE(sourcePositions[si][c],dp.offset+i*dp.stride+c*4);writeLane(donor,dn,i,c,readLane(src,sn,si,c));}
   for(let c=0;c<4;c++){writeLane(donor,dj,i,c,readLane(src,sj,si,c));writeLane(donor,dw,i,c,readLane(src,sw,si,c));}
  }
  assert(donorIds.length,'each original contour point is in donor mesh');
  neckPairs.push({sourceMeshName:bodyNode.name,sourceVertexIndices:sourceIds,repairMeshName:node.name,repairVertexIndices:donorIds,restPosition:sourcePositions[si]});
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
for(let i=0;i<oldNodes.length;i++){const before={...oldNodes[i]},after={...d.nodes[i]};delete before.children;delete after.children;delete before.mesh;delete after.mesh;delete before.skin;delete after.skin;assert.deepEqual(after,before)}
const json=Buffer.from(JSON.stringify(d)),jp=Buffer.concat([json,Buffer.alloc(-json.length&3,32)]),bp=Buffer.concat([bin,Buffer.alloc(-bin.length&3)]);
const out=Buffer.alloc(28+jp.length+bp.length);out.writeUInt32LE(0x46546c67,0);out.writeUInt32LE(2,4);out.writeUInt32LE(out.length,8);out.writeUInt32LE(jp.length,12);out.writeUInt32LE(0x4e4f534a,16);jp.copy(out,20);out.writeUInt32LE(bp.length,20+jp.length);out.writeUInt32LE(0x004e4942,24+jp.length);bp.copy(out,28+jp.length);
fs.writeFileSync(outPath,out);
const seams=JSON.parse(fs.readFileSync(sourcePath+'.seams.json'));seams.asset=outPath;seams.assetSHA256=crypto.createHash('sha256').update(out).digest('hex');seams.headGraft={sourceSHA256:report.sourceSHA256,originalAttributeBytesPreserved:true};fs.writeFileSync(outPath+'.seams.json',JSON.stringify(seams,null,2)+'\n');
fs.writeFileSync(outPath+'.neck.json',JSON.stringify({asset:outPath,assetSHA256:crypto.createHash('sha256').update(out).digest('hex'),neckCoverage:report.neckCoverage,orderedPairs:neckPairs},null,2)+'\n');
const proof={source:sourcePath,donor:donorPath,output:outPath,sha256:crypto.createHash('sha256').update(out).digest('hex'),bytes:out.length,removedHeadTriangles:removed,newHeadTriangles:report.newTriangles,originalAnimationMetadataPreserved:true,originalSkinMetadataPreserved:true,originalNodeTransformsPreserved:true,outsideHeadByteDifferences};
fs.writeFileSync(outPath+'.json',JSON.stringify(proof,null,2)+'\n');console.log(JSON.stringify(proof));
