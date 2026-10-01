/** CPU-only recorded-state reconstruction; no renderer, GPU or asset write. */
/* oxlint-disable typescript/no-explicit-any -- isolated diagnostic object inventory. */
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import * as THREE from 'three';
import { pathToFileURL } from 'node:url';
import { build } from 'vite';
import { patchNewRiderSource } from '../../../../../../../../harness/hero-remaster/new-rider-private-adapter.mjs';
import { loadRigAt } from '../../../../../../../../src/render/hero/gltfTestUtils';
import { prepareHero } from '../../../../../../../../src/render/hero/lod';
import { GltfBike } from '../../../../../../../../src/render/hero/gltfBike';
import { FrameBuilder } from '../../../../../../../../src/render/frame';
const root=process.cwd(),out=path.resolve(process.argv.find(a=>a.startsWith('--out='))?.slice(6)??path.join(root,'docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/played-surfaces11/hip-audit01'));
fs.mkdirSync(out,{recursive:true});assert(!fs.existsSync(path.join(out,'pose-manifest.json')),'A fresh CPU audit output directory is required');
const source='/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/rig-adapter01/body-bind11/guarded-correction01/rider.glb';
const sourceSHA256=crypto.createHash('sha256').update(fs.readFileSync(source)).digest('hex');
const bundle=path.join(root,'harness/out/hero-remaster/hip-audit01-cpu');
await build({configFile:false,publicDir:false,logLevel:'error',build:{ssr:'src/render/hero/gltfRider.ts',outDir:bundle,emptyOutDir:true,minify:false,rollupOptions:{external:['three',/^three\//],output:{entryFileNames:'rider.mjs'}}},plugins:[{name:'actual-private-adapter',enforce:'pre',transform(code,id){return id.toLowerCase().endsWith('/src/render/hero/gltfrider.ts')?{code:patchNewRiderSource(code,true,false),map:null}:null;}}]});
const {GltfRider}=await import(pathToFileURL(bundle+'/rider.mjs').href);
(globalThis as any).document={createElement:()=>({width:128,height:64,getContext:()=>({createRadialGradient:()=>({addColorStop(){}}),scale(){},fillRect(){}})})};
const lib:any={complete(){}};
const bg=await loadRigAt(pathToFileURL(root+'/public/models/bike-rookie.glb'),true);await prepareHero(bg);const bike=new GltfBike(bg,lib);
const g=await loadRigAt(pathToFileURL(source),true);await prepareHero(g);const rider=new GltfRider(g,lib);rider.attach(bike);bike.root.updateMatrixWorld(true);
const meshes:THREE.SkinnedMesh[]=[];rider.scene.traverse((o:THREE.Object3D)=>{const m=o as THREE.SkinnedMesh;if(m.isSkinnedMesh&&m.name.startsWith('Protected')&&!m.name.endsWith('_1'))meshes.push(m);});assert.equal(meshes.length,2);
const save=(name:string,values:number[])=>{const a=new Float64Array(values);fs.writeFileSync(path.join(out,name+'.f64'),Buffer.from(a.buffer));return {file:name+'.f64',values:a.length,sha256:crypto.createHash('sha256').update(Buffer.from(a.buffer)).digest('hex')};};
const primitiveRows=meshes.map((m,mi)=>{
 const attrs:Record<string,unknown>={};for(const name of ['position','normal','uv','skinIndex','skinWeight']){const a=m.geometry.getAttribute(name);attrs[name]={itemSize:a.itemSize,count:a.count,...save(`mesh${mi}-${name}`,Array.from({length:a.count},(_,i)=>Array.from({length:a.itemSize},(_,j)=>a.getComponent(i,j))).flat())};}
 const ix=m.geometry.index;assert(ix);return {mesh:m.name,index:save(`mesh${mi}-triangles`,Array.from({length:ix.count},(_,i)=>ix.getX(i))),attributes:attrs,bones:m.skeleton.bones.map(b=>b.name),inverseBindOriginPositions:m.skeleton.boneInverses.map((matrix,j)=>({name:m.skeleton.bones[j]!.name,sourceWorld:new THREE.Vector3().setFromMatrixPosition(matrix.clone().invert()).toArray()}))};
});
const captured=JSON.parse(fs.readFileSync(path.join(root,'docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/played-surfaces11/framed04/report.json'),'utf8'));
const roi=JSON.parse(fs.readFileSync(path.join(root,'docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/played-surfaces11/framed04/source-roi.json'),'utf8'));
const history=[];
for(const version of ['05','06','08']){
 const file=source.replace('body-bind11/guarded-correction01','body-bind'+version), bytes=fs.readFileSync(file);
 const h=await loadRigAt(pathToFileURL(file),true);let body:THREE.SkinnedMesh|null=null;
 h.scene.traverse((o:THREE.Object3D)=>{const m=o as THREE.SkinnedMesh;if(m.isSkinnedMesh&&m.geometry.getAttribute('position').count===22240)body=m;});assert(body);const m=body as THREE.SkinnedMesh;
 const attributes:Record<string,unknown>={};for(const name of ['position','skinIndex','skinWeight']){const a=m.geometry.getAttribute(name);attributes[name]={itemSize:a.itemSize,count:a.count,...save(`history${version}-${name}`,Array.from({length:a.count},(_,i)=>Array.from({length:a.itemSize},(_,j)=>a.getComponent(i,j))).flat())};}
 history.push({version,source:file,sha256:crypto.createHash('sha256').update(bytes).digest('hex'),mesh:m.name,bones:m.skeleton.bones.map(b=>b.name),inverseBindOriginPositions:m.skeleton.boneInverses.map((matrix,j)=>({name:m.skeleton.bones[j]!.name,sourceWorld:new THREE.Vector3().setFromMatrixPosition(matrix.clone().invert()).toArray()})),attributes,limits:'Untouched decoded source weights before historical runtime conditioning; historical material appearance is not reconstructed.'});
}
const bodywork=bike.root.getObjectByName('bodywork') as THREE.Mesh;assert(bodywork);
const bodyworkIndex=bodywork.geometry.index;assert(bodyworkIndex);
const bodyworkSource={positions:save('bike-bodywork-source-positions',Array.from({length:bodywork.geometry.getAttribute('position').count},(_,i)=>new THREE.Vector3().fromBufferAttribute(bodywork.geometry.getAttribute('position'),i).toArray()).flat()),triangles:save('bike-bodywork-triangles',Array.from({length:bodyworkIndex.count},(_,i)=>bodyworkIndex.getX(i))),source:'/public/models/bike-rookie.glb',sourceSHA256:crypto.createHash('sha256').update(fs.readFileSync(root+'/public/models/bike-rookie.glb')).digest('hex')};
const rows=[];
for(const i of [258,35,75,90,96,102]){
 const sample=captured.samples[i],before=JSON.stringify(sample.state);const f=new FrameBuilder().build(sample.state,1);bike.update(f);rider.update(f);bike.root.updateMatrixWorld(true);rider.scene.updateWorldMatrix(true,true);
 const frameInverse=bike.frame.matrixWorld.clone().invert(),dump=[];
 for(const [mi,m] of meshes.entries()){
  const pos=m.geometry.getAttribute('position'),normal=m.geometry.getAttribute('normal'),si=m.geometry.getAttribute('skinIndex'),sw=m.geometry.getAttribute('skinWeight');
  const points:number[]=[],normals:number[]=[];
  const prefix=new THREE.Matrix4().multiplyMatrices(frameInverse,m.matrixWorld).multiply(m.bindMatrixInverse);
  const deltas=m.skeleton.bones.map((b,j)=>new THREE.Matrix4().multiplyMatrices(b.matrixWorld,m.skeleton.boneInverses[j]!));
  for(let v=0;v<pos.count;v++){
   points.push(...m.localToWorld(m.getVertexPosition(v,new THREE.Vector3())).applyMatrix4(frameInverse).toArray());
   const matrix=new THREE.Matrix4();matrix.elements.fill(0);
   for(let lane=0;lane<4;lane++){const w=sw.getComponent(v,lane);if(!w)continue;const d=deltas[si.getComponent(v,lane)]!;for(let k=0;k<16;k++)matrix.elements[k]!+=w*d.elements[k]!;}
   matrix.premultiply(prefix).multiply(m.bindMatrix);const n=new THREE.Vector3().fromBufferAttribute(normal,v).applyMatrix3(new THREE.Matrix3().setFromMatrix4(matrix));normals.push(...n.normalize().toArray());
  }
  dump.push({mesh:m.name,positions:save(`sample${i}-mesh${mi}-positions`,points),gpuRuleSkinnedNormals:save(`sample${i}-mesh${mi}-normals`,normals)});
 }
 const contacts=[];
 for(const e of [...roi.hands,...roi.feet]){
  const m=rider.scene.getObjectByName(e.meshName) as THREE.SkinnedMesh,bm=bike.root.getObjectByName(e.bikeMeshName)!;const inverse=bm.matrixWorld.clone().invert();const kind=e.bikeMeshName==='handlebar'?'hand':'sole';const p=path.join('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/rig-adapter01/played-surfaces11/framed04',`${kind}-${e.side}.f32`);
  // Use Buffer's explicit byte range: retained samples are float32 serialization.
  const raw=fs.readFileSync(p);let max=0;
  for(let j=0;j<e.sourceVertices.length;j++){const v=m.localToWorld(m.getVertexPosition(e.sourceVertices[j],new THREE.Vector3())).applyMatrix4(inverse);const offset=(i*e.sourceVertices.length+j)*12;const played=new THREE.Vector3(raw.readFloatLE(offset),raw.readFloatLE(offset+4),raw.readFloatLE(offset+8));max=Math.max(max,v.distanceTo(played));}
  contacts.push({kind,side:e.side,maximumCPUvsActualPlayedSurfaceM:max});
 }
 assert.equal(JSON.stringify(sample.state),before);const bpos=bodywork.geometry.getAttribute('position');const bodyworkBikeFrame=save(`sample${i}-bike-bodywork-positions`,Array.from({length:bpos.count},(_,j)=>bodywork.localToWorld(new THREE.Vector3().fromBufferAttribute(bpos,j)).applyMatrix4(frameInverse).toArray()).flat());
 const bonePoints=meshes[0]!.skeleton.bones.map(b=>({name:b.name,bikeFramePosition:b.getWorldPosition(new THREE.Vector3()).applyMatrix4(frameInverse).toArray()}));
 rows.push({i,tick:sample.tick,lean:sample.state.rider.lean,bodyworkBikeFrame,bonePoints,debug:structuredClone(rider.debug),playedDebug:sample.debug,contacts,dump});
}
assert.equal(crypto.createHash('sha256').update(fs.readFileSync(source)).digest('hex'),sourceSHA256);
fs.writeFileSync(path.join(out,'pose-manifest.json'),JSON.stringify({source,sourceSHA256,sourceUnchanged:true,primitives:primitiveRows,history,bodyworkSource,rows,limits:'CPU reconstructed recorded states using actual private adapter; CPU-versus-played surface errors declare pose correspondence. No GPU/material rendering or asset changes.'},null,2)+'\n');console.log(JSON.stringify(rows.map(r=>({i:r.i,contacts:r.contacts}))));
