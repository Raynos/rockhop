/** Inspect actual played skin deformation; source geometry/materials remain untouched. */
import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import * as THREE from 'three';
import { pathToFileURL } from 'node:url';
import { build } from 'vite';
import { patchNewRiderSource } from './new-rider-private-adapter.mjs';
import { loadRigAt } from '../../src/render/hero/gltfTestUtils';
import { prepareHero } from '../../src/render/hero/lod';
import { GltfBike } from '../../src/render/hero/gltfBike';
import { FrameBuilder } from '../../src/render/frame';
import type { PhysicsState } from '../../src/core/types';
import type { MaterialLibrary } from '../../src/render/materials/library';
const arg=(name:string,fallback:string)=>process.argv.find(a=>a.startsWith('--'+name+'='))?.slice(name.length+3)??fallback;
const out=path.resolve(arg('out','docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/body-bind05/cloth-audit01'));fs.mkdirSync(out,{recursive:true});
const captured=JSON.parse(fs.readFileSync('docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/body-bind05/played03/hands/report.json','utf8')) as {samples:{i:number;tick:number;state:PhysicsState}[]};
(globalThis as unknown as {document:unknown}).document={createElement:()=>({width:128,height:64,getContext:()=>({createRadialGradient:()=>({addColorStop(){}}),scale(){},fillRect(){}})})};
const source=arg('source','/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/rig-adapter01/body-bind05/rider.glb'),results=[];
for(const variant of ['conditioned','source-weights']){
 const bundle=path.resolve('harness/out/hero-remaster/cloth-audit-'+variant);
 await build({configFile:false,publicDir:false,logLevel:'error',build:{ssr:'src/render/hero/gltfRider.ts',outDir:bundle,emptyOutDir:true,minify:false,rollupOptions:{external:['three',/^three\//],output:{entryFileNames:'rider.mjs'}}},plugins:[{name:'cloth-audit',enforce:'pre',transform(code,id){if(!id.toLowerCase().endsWith('/src/render/hero/gltfrider.ts'))return null;let s=patchNewRiderSource(code);if(variant==='source-weights'){const a='this.releaseSleeveGeometry.push(conditionSleeveSkin(mesh));';assert.equal(s.split(a).length,2);s=s.replace(a,'this.releaseSleeveGeometry.push(() => {});');}return{code:s,map:null};}}]});
 const {GltfRider}=await import(pathToFileURL(bundle+'/rider.mjs').href),lib={complete(){}} as unknown as MaterialLibrary;
 const bg=await loadRigAt(pathToFileURL(path.resolve('public/models/bike-rookie.glb')),true);await prepareHero(bg);const bike=new GltfBike(bg,lib),g=await loadRigAt(pathToFileURL(source),true);await prepareHero(g);const rider=new GltfRider(g,lib);rider.attach(bike);bike.root.updateMatrixWorld(true);
 const meshes:THREE.SkinnedMesh[]=[];rider.scene.traverse((o:THREE.Object3D)=>{const m=o as THREE.SkinnedMesh;if(m.isSkinnedMesh&&m.name.startsWith('Protected'))meshes.push(m);});assert.equal(meshes.length,3);
 const rests=meshes.map(m=>Array.from({length:m.geometry.getAttribute('position').count},(_,i)=>{const v=m.getVertexPosition(i,new THREE.Vector3());m.localToWorld(v);return bike.frame.worldToLocal(v);}));
 const joinGroups=new Map<string,{mesh:number;vertex:number}[]>();
 for(const [mi,m] of meshes.entries()) {
  if(m.name.endsWith('_1'))continue;
  const position=m.geometry.getAttribute('position');
  for(let vertex=0;vertex<position.count;vertex++) {
   const key=[position.getX(vertex),position.getY(vertex),position.getZ(vertex)].map(c=>Math.round(c*1e6)).join(',');
   const group=joinGroups.get(key)??[];group.push({mesh:mi,vertex});joinGroups.set(key,group);
  }
 }
 const sharedJoin=[...joinGroups.values()].filter(group=>new Set(group.map(v=>v.mesh)).size>1);
 assert(sharedJoin.length>250,'Expected actual shared body/hood rim vertices');
 const rows=[];
 for(const sample of captured.samples.filter(s=>[49,120,420,468].includes(s.i))){
  const before=JSON.stringify(sample.state),f=new FrameBuilder().build(sample.state,1);bike.update(f);rider.update(f);bike.root.updateMatrixWorld(true);assert.equal(JSON.stringify(sample.state),before);
  const actualPosed=meshes.map(m=>Array.from({length:m.geometry.getAttribute('position').count},(_,i)=>bike.frame.worldToLocal(m.localToWorld(m.getVertexPosition(i,new THREE.Vector3())))));
  const seamSeparations=sharedJoin.map(group=>Math.max(...group.flatMap(a=>group.map(b=>actualPosed[a.mesh]![a.vertex]!.distanceTo(actualPosed[b.mesh]![b.vertex]!)))));
  const faces: {region:string;mesh:string;triangle:number;indices:number[];stretch:number;areaRatio:number;restEdgesM:number[];posedEdgesM:number[];sourceNativePositions:number[][];weights:{bone:string;weight:number}[][]}[]=[];
  for(const [mi,m] of meshes.entries()){
   if (m.name.endsWith('_1')) continue; // Verified native glove material primitive.
   const rest=rests[mi]!,p=m.geometry.getAttribute('position'),index=m.geometry.index;assert(index);const si=m.geometry.getAttribute('skinIndex'),sw=m.geometry.getAttribute('skinWeight');
   const posed=Array.from({length:p.count},(_,i)=>bike.frame.worldToLocal(m.localToWorld(m.getVertexPosition(i,new THREE.Vector3()))));
   const weights=(i:number)=>Array.from({length:4},(_,lane)=>({bone:m.skeleton.bones[si.getComponent(i,lane)]!.name,weight:sw.getComponent(i,lane)})).filter(w=>w.weight>1e-5);
   for(let t=0;t<index.count/3;t++){
    const ids=[index.getX(t*3),index.getX(t*3+1),index.getX(t*3+2)],rv=ids.map(i=>rest[i]!),pv=ids.map(i=>posed[i]!),ws=ids.map(weights);
    const height=rv.reduce((s,v)=>s+v.y/1.015,0)/3;
    if(height<.78||height>1.54)continue;
    const ra=new THREE.Triangle(...rv as [THREE.Vector3,THREE.Vector3,THREE.Vector3]).getArea();if(ra<1e-12)continue;
    const pa=new THREE.Triangle(...pv as [THREE.Vector3,THREE.Vector3,THREE.Vector3]).getArea(),re=rv.map((v,i)=>v.distanceTo(rv[(i+1)%3]!)),pe=pv.map((v,i)=>v.distanceTo(pv[(i+1)%3]!));
    const stretch=Math.max(...pe.map((v,i)=>v/Math.max(1e-8,re[i]!)));
    faces.push({region:height>1.3?'shoulder':height>.93?'midbody':'waist',mesh:m.name,triangle:t,indices:ids,stretch,areaRatio:pa/ra,restEdgesM:re,posedEdgesM:pe,sourceNativePositions:rv.map(v=>[-v.z/1.015,-v.x/1.015,v.y/1.015]),weights:ws});
   }
  }
  faces.sort((a,b)=>b.stretch-a.stretch);rows.push({i:sample.i,tick:sample.tick,sharedBodyHoodRimVertices:sharedJoin.length,maxBodyHoodSeparationM:Math.max(...seamSeparations),bodyHoodPairsOver1mm:seamSeparations.filter(d=>d>.001).length,garmentTriangles:faces.length,stretchedOver4:faces.filter(t=>t.stretch>4).length,areaCollapsedBelowQuarter:faces.filter(t=>t.areaRatio<.25).length,maxEdgeStretch:faces[0]!.stretch,regions:['waist','midbody','shoulder'].map(region=>{const fs=faces.filter(f=>f.region===region);return{region,triangles:fs.length,stretchedOver4:fs.filter(f=>f.stretch>4).length,maxEdgeStretch:fs[0]?.stretch,worst:fs.slice(0,12)};}),worst:faces.slice(0,40)});
 }
 results.push({variant,rows});
}
fs.writeFileSync(out+'/report.json',JSON.stringify({source,results,scope:'Actual recorded states and actual candidate production skin decoder, CPU-only. Source-weights variant bypasses only generic sleeve conditioner. Triangle stretch ranks diagnostics; no automatic repair or topology/collision acceptance.'},null,2)+'\n');console.log(JSON.stringify(results.map(r=>({variant:r.variant,rows:r.rows.map(({worst:_worst,regions,...r})=>({...r,regions:regions.map(({worst:_worst,...region})=>region)}))}))));
