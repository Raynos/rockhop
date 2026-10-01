/** Recover unchanged actual handlebar surface islands, rather than inventing rod radius. */
import fs from 'node:fs';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import * as THREE from 'three';
import { loadRigAt } from '../../src/render/hero/gltfTestUtils';
const out='docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/bike-grip-surface02';fs.mkdirSync(out,{recursive:true});
const results=[];
for(const file of ['bike-rookie.glb','bike-pro.glb']){
 const p='public/models/'+file;const sourceSHA256=crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');const g=await loadRigAt(new URL('file://'+process.cwd()+'/'+p));g.scene.updateMatrixWorld(true);
 const meshes:THREE.Mesh[]=[];g.scene.traverse(o=>{if((o as THREE.Mesh).isMesh&&o.name.toLowerCase().includes('handlebar'))meshes.push(o as THREE.Mesh);});const gripRows=[];
 for(const mesh of meshes){
  const attr=mesh.geometry.getAttribute('position'),idx=mesh.geometry.index;assert(idx);const points=Array.from({length:attr.count},(_,i)=>mesh.localToWorld(new THREE.Vector3().fromBufferAttribute(attr,i)));const parent=points.map((_,i)=>i);const find=(i:number):number=>parent[i]===i?i:(parent[i]=find(parent[i]!));const union=(a:number,b:number)=>{a=find(a);b=find(b);if(a!==b)parent[b]=a;};const known=new Map<string,number>();
  for(let i=0;i<points.length;i++){const key=points[i]!.toArray().map(x=>Math.round(x*1e6)).join(',');const old=known.get(key);if(old!==undefined)union(old,i);else known.set(key,i);}
  for(let i=0;i<idx.count;i+=3){union(idx.getX(i),idx.getX(i+1));union(idx.getX(i),idx.getX(i+2));}
  const islands=new Map<number,{vertices:number[];triangles:number[][]}>();for(let i=0;i<points.length;i++){const root=find(i);if(!islands.has(root))islands.set(root,{vertices:[],triangles:[]});islands.get(root)!.vertices.push(i);}for(let i=0;i<idx.count;i+=3)islands.get(find(idx.getX(i)))!.triangles.push([idx.getX(i),idx.getX(i+1),idx.getX(i+2)]);
  for(const side of ['L','R']){
   const marker=g.scene.getObjectByName('attach_grip_'+side);assert(marker);const centre=marker.getWorldPosition(new THREE.Vector3());const sign=Math.sign(centre.z);const candidates=[];
   for(const [id,island] of islands){const bounds=new THREE.Box3().setFromPoints(island.vertices.map(i=>points[i]!));const size=bounds.getSize(new THREE.Vector3());const bc=bounds.getCenter(new THREE.Vector3());if(bc.distanceTo(centre)<.08&&size.z>.13&&size.z<.19)candidates.push({id,island,bounds,size,centre:bc});}
   assert.equal(candidates.length,1,'Expected one literal rubber-grip component');const c=candidates[0]!;
   // Recipe endpoints identify the original island; decoded positions determine its actual surface.
   const a=new THREE.Vector3(.932,.779,sign*.26),b=new THREE.Vector3(.915,.780,sign*.425);const axis=b.clone().sub(a).normalize();const length=a.distanceTo(b);const radial=c.island.vertices.map(i=>{const q=points[i]!.clone().sub(a);const t=q.dot(axis);return {vertex:i,point:points[i]!.toArray(),axialM:t,radialM:q.addScaledVector(axis,-t).length(),recipeTaperRadiusM:.017-.001*(t/length)};});const shell=radial.filter(r=>r.radialM>.014);const maxTaperErrorM=Math.max(...shell.map(r=>Math.abs(r.radialM-r.recipeTaperRadiusM)));assert(maxTaperErrorM<.0005,'Actual island fails source-cylinder hypothesis');
   const sourceMeshSurface={vertices:c.island.vertices.map(i=>({sourceVertex:i,point:points[i]!.toArray()})),triangles:c.island.triangles};
   gripRows.push({side,markerWorld:centre.toArray(),component:c.id,vertices:c.island.vertices.length,triangles:c.island.triangles.length,bounds:{min:c.bounds.min.toArray(),max:c.bounds.max.toArray()},recipeAxis:{a:a.toArray(),b:b.toArray(),unit:axis.toArray(),lengthM:length},decodedShellRadiusRangeM:[Math.min(...shell.map(r=>r.radialM)),Math.max(...shell.map(r=>r.radialM))],maxDecodedVsRecipeTaperErrorM:maxTaperErrorM,markerToRodAxisDistanceM:centre.clone().sub(a).addScaledVector(axis,-centre.clone().sub(a).dot(axis)).length(),radial,sourceMeshSurface});
  }
 }
 assert.equal(sourceSHA256,crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex'));results.push({asset:file,sourceSHA256,grips:gripRows});
}
assert.deepEqual(results[0]!.grips,results[1]!.grips,'Rookie/Pro actual grip surfaces differ');fs.writeFileSync(out+'/report.json',JSON.stringify({results,limits:'Actual decoded mesh islands and source-recipe taper witness; polygon faces are inside circumradius, so continuous triangle contact still required'},null,2)+'\n');console.log(JSON.stringify(results.map(r=>({asset:r.asset,grips:r.grips.map(g=>({side:g.side,triangles:g.triangles,radius:g.decodedShellRadiusRangeM,taperError:g.maxDecodedVsRecipeTaperErrorM,markerAxisDistance:g.markerToRodAxisDistanceM}))}))));
