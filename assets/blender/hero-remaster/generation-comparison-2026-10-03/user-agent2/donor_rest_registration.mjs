/** Read-only actual GLTFLoader rest-world registration; no old rig adoption. */
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { pathToFileURL } from 'node:url';
import * as T from 'three';
const [file, output] = process.argv.slice(2);
if (!file || !output || fs.existsSync(output)) throw new Error('Pinned input and fresh output required');
const hash = b => crypto.createHash('sha256').update(b).digest('hex');
const bytes = fs.readFileSync(file), pin = 'b7f4f22790124c664f9907104e5b17b77775b4c5c995f715d62be640bbcc8754';
if (hash(bytes) !== pin) throw new Error('Different donor');
const length = bytes.readUInt32LE(12), json = JSON.parse(bytes.subarray(20,20+length)), binary = bytes.subarray(28+length);
const helper = path.resolve('src/render/hero/gltfTestUtils.ts');
const { loadRigAt } = await import(pathToFileURL(helper));
const gltf = await loadRigAt(pathToFileURL(path.resolve(file)), true);
gltf.scene.updateMatrixWorld(true); fs.mkdirSync(output,{recursive:true});
const arrayHash = a => hash(Buffer.from(a.buffer,a.byteOffset,a.byteLength));
const bounds = points => { const b=new T.Box3();for(const v of points)b.expandByPoint(v);return [b.min.toArray(),b.max.toArray()]; };
const matrix = m=>m.toArray(); const rows=[];
for (const [mesh, association] of gltf.parser.associations) {
 if (!mesh.isSkinnedMesh) continue;
 mesh.skeleton.update();const p=mesh.geometry.getAttribute('position'),w=mesh.geometry.getAttribute('skinWeight'),j=mesh.geometry.getAttribute('skinIndex');
 const raw=[],world=[],blender=[],groups=new Map(),mass=new Map();let maxRawWorld=0,maxFormulaError=0,maxWeightSumError=0;
 for(let i=0;i<p.count;i++){
  const rv=new T.Vector3().fromBufferAttribute(p,i),actual=mesh.getVertexPosition(i,new T.Vector3()).applyMatrix4(mesh.matrixWorld);
  raw.push(rv);world.push(actual);blender.push(new T.Vector3(actual.x-.65,-actual.z,actual.y));maxRawWorld=Math.max(maxRawWorld,rv.distanceTo(actual));
  const sum=new T.Vector3(),base=rv.clone().applyMatrix4(mesh.bindMatrix);let dominant='',largest=-1,weightSum=0;
  for(let k=0;k<4;k++){
   const weight=w.getComponent(i,k),id=j.getComponent(i,k),bone=mesh.skeleton.bones[id];
   if(weight===0)continue;
   const transform=new T.Matrix4().multiplyMatrices(bone.matrixWorld,mesh.skeleton.boneInverses[id]);
   sum.addScaledVector(base.clone().applyMatrix4(transform),weight);weightSum+=weight;
   mass.set(bone.name,(mass.get(bone.name)??0)+weight);
   if(weight>largest){dominant=bone.name;largest=weight;}
  }
  sum.applyMatrix4(mesh.bindMatrixInverse).applyMatrix4(mesh.matrixWorld);
  maxFormulaError=Math.max(maxFormulaError,sum.distanceTo(actual));maxWeightSumError=Math.max(maxWeightSumError,Math.abs(weightSum-1));
  if(!groups.has(dominant))groups.set(dominant,{ids:[],points:[]});groups.get(dominant).ids.push(i);groups.get(dominant).points.push(blender.at(-1));
 }
 const attributes={};for(const[name,a]of Object.entries(mesh.geometry.attributes))attributes[name]={count:a.count,itemSize:a.itemSize,normalized:a.normalized,arrayType:a.array.constructor.name,sha256:arrayHash(a.array)};
 const mid=association.meshes,pid=association.primitives,primitive=json.meshes[mid].primitives[pid];
 const f64=new Float64Array(world.flatMap(v=>v.toArray())),surface=path.join(output,`mesh${mid}-primitive${pid}-fileworld.f64`);fs.writeFileSync(surface,Buffer.from(f64.buffer));
 const joints=mesh.skeleton.bones.map((b,id)=>({id,name:b.name,fileWorldPosition:b.getWorldPosition(new T.Vector3()).toArray(),matrixWorld:matrix(b.matrixWorld),inverseBind:matrix(mesh.skeleton.boneInverses[id])}));
 rows.push({mesh:mid,primitive:pid,node:association.nodes,name:mesh.name,material:primitive.material,vertices:p.count,rawBounds:bounds(raw),actualFileWorldBounds:bounds(world),normalizedBlenderBounds:bounds(blender),maxRawToActualRestDistanceM:maxRawWorld,maxIndependentFormulaErrorM:maxFormulaError,maxWeightSumError,meshWorld:matrix(mesh.matrixWorld),bindMatrix:matrix(mesh.bindMatrix),bindMatrixInverse:matrix(mesh.bindMatrixInverse),bindMode:mesh.bindMode,morphInfluences:mesh.morphTargetInfluences??null,attributes,dominantJointRegions:Object.fromEntries([...groups].map(([name,g])=>[name,{vertices:g.ids.length,boundsNormalizedBlender:bounds(g.points),sourceVertexIDs:g.ids}])),skinJointMass:Object.fromEntries(mass),joints,worldSurface:{path:surface,sha256:hash(fs.readFileSync(surface)),format:'float64 little-endian xyz, original POSITION row order',count:p.count}});
}
const images=json.images.map((im,index)=>{const view=json.bufferViews[im.bufferView],data=binary.subarray(view.byteOffset??0,(view.byteOffset??0)+view.byteLength);return {index,name:im.name,mimeType:im.mimeType,bytes:data.length,sha256:hash(data)};});
const r={status:'READ-ONLY actual GLTFLoader file-world rest registration; not appearance/fit acceptance',sourceFile:file,sourceSHA256:pin,recipeSHA256:hash(fs.readFileSync(import.meta.filename)),loaderHelperSHA256:hash(fs.readFileSync(helper)),threeRevision:T.REVISION,coordinateConvention:'File-world glTF Xforward/Yup/Zleft metres; canonical Blender [X-.65,-Z,Y], root offset removed ONCE, no1.015 scaling',worldFormula:'meshWorld * bindInverse * sum(weight * boneWorld * inverseBind * bindMatrix * rawPosition)',runtimeConditioning:false,gameplayWrapper:false,animationsPlayed:false,rows,materials:json.materials,textures:json.textures,images,limits:['Images omitted only in Node memory; original UV/material/image source recorded separately, disk unchanged','Rest skin/world registration does not prove correct anatomy, gloves/boots semantic role or fit','Joint roles describe old donor registration only; old skeleton/weights/anatomy are not adopted']};
if(hash(fs.readFileSync(file))!==pin)throw new Error('Source changed');
fs.writeFileSync(path.join(output,'registration.json'),JSON.stringify(r,null,2)+'\n');
console.log(JSON.stringify(rows.map(r=>({mesh:r.mesh,primitive:r.primitive,material:r.material,vertices:r.vertices,raw:r.rawBounds,actual:r.actualFileWorldBounds,blender:r.normalizedBlenderBounds,delta:r.maxRawToActualRestDistanceM,formula:r.maxIndependentFormulaErrorM,dominant:Object.fromEntries(Object.entries(r.dominantJointRegions).map(([k,v])=>[k,{vertices:v.vertices,bounds:v.boundsNormalizedBlender}]))})),null,2));
