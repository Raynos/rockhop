import {readFile,writeFile}from'node:fs/promises';
import{pathToFileURL}from'node:url';
import path from'node:path';
import{createHash}from'node:crypto';
const here=path.dirname(new URL(import.meta.url).pathname),manifest=JSON.parse(await readFile(path.join(here,'runtime/manifest.json'),'utf8'));
const root='/Users/raynos/projects/games/rockhop/node_modules/three';
const T=await import(pathToFileURL(path.join(root,'build/three.module.js')));
const{GLTFLoader}=await import(pathToFileURL(path.join(root,'examples/jsm/loaders/GLTFLoader.js')));
const bytes=await readFile(manifest.glb),sha=createHash('sha256').update(bytes).digest('hex');if(sha!==manifest.frozenGLBSHA256)throw Error('Frozen GLBchanged');
const n=bytes.readUInt32LE(12),doc=JSON.parse(bytes.subarray(20,20+n));
for(const m of doc.meshes??[])for(const p of m.primitives)delete p.material;delete doc.materials;delete doc.images;delete doc.textures;
const jb=Buffer.from(JSON.stringify(doc)),jpad=Buffer.concat([jb,Buffer.alloc((-jb.length)&3,32)]),tail=bytes.subarray(20+n),buf=Buffer.alloc(20+jpad.length+tail.length);bytes.copy(buf,0,0,12);buf.writeUInt32LE(buf.length,8);buf.writeUInt32LE(jpad.length,12);buf.writeUInt32LE(0x4e4f534a,16);jpad.copy(buf,20);tail.copy(buf,20+jpad.length);
const g=await new GLTFLoader().parseAsync(buf.buffer.slice(buf.byteOffset,buf.byteOffset+buf.byteLength),'');
const meshes=[];g.scene.traverse(o=>{if(o.isSkinnedMesh)meshes.push(o)});g.scene.updateMatrixWorld(true);
const sk=meshes[0].skeleton,bones=sk.bones,bind=sk.boneInverses.map(m=>m.clone().invert());
const matrix=a=>new T.Matrix4().set(...a.flat());const results=[];let max=0,count=0;
for(const row of manifest.poses){
 const wanted=row.matrices.map((a,i)=>matrix(a).multiply(bind[i]));
 for(let i=0;i<bones.length;i++){
  const parent=bones.indexOf(bones[i].parent),pw=parent>=0?wanted[parent]:bones[i].parent?.matrixWorld??new T.Matrix4();
  const local=pw.clone().invert().multiply(wanted[i]);local.decompose(bones[i].position,bones[i].quaternion,bones[i].scale);
 }
 for(const m of meshes)if(m.morphTargetInfluences)m.morphTargetInfluences.fill(0);
 g.scene.updateMatrixWorld(true);for(const m of meshes)m.skeleton.update();
 const primitive=[];
 for(let k=0;k<meshes.length;k++){
  const refbuf=await readFile(row.references[k]),ref=new Float64Array(refbuf.buffer.slice(refbuf.byteOffset,refbuf.byteOffset+refbuf.byteLength));
  const m=meshes[k],p=new T.Vector3();let peak=0,sq=0;const vertices=m.geometry.getAttribute('position').count;
  if(ref.length!==vertices*3)throw Error('Reference vertex count differs');
  for(let i=0;i<vertices;i++){m.getVertexPosition(i,p).applyMatrix4(m.matrixWorld);const d=Math.hypot(p.x-ref[3*i],p.y-ref[3*i+1],p.z-ref[3*i+2]);peak=Math.max(peak,d);sq+=d*d;}
  count+=vertices;max=Math.max(max,peak);primitive.push({index:k,vertices,maxM:peak,rmsM:Math.sqrt(sq/vertices)});
 }
 results.push({id:row.id,primitive});
}
const result={engineRevision:T.REVISION,sourceSHA256:sha,poseCount:results.length,vertexComparisons:count,maxDistanceM:max,pass:max<manifest.toleranceM,method:'Stock GLTFLoader+SkinnedMesh.getVertexPosition; world-space deformation matrices mapped through frozen inversebind to parent-relative node TRS. All morph targets0; geometry/weights untouched. In-memory materials removed only for CPUparse.',limits:['CPUlinear skinning only,noGPU/PBR equivalence claim.','No AnimationMixer/keyframe export or gameplay integration acceptance.','Directworldmatrices converted to localTRS; not copied quaternions between bonebases.'],results};await writeFile(path.join(here,'runtime/parity.json'),JSON.stringify(result,null,2));process.stdout.write(JSON.stringify({...result,results:undefined}));
