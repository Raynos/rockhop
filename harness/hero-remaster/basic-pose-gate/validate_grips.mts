/** Verify unilateral source grip deformation, separately from grip contact. */
import fs from 'node:fs';
import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import {pathToFileURL} from 'node:url';
import path from 'node:path';
import * as THREE from 'three';
import {loadRigAt} from '../../../src/render/hero/gltfTestUtils';
import {createFixturePlayer,type PoseFixture} from './protocol';
const arg=(key:string)=>process.argv.find(a=>a.startsWith('--'+key+'='))?.slice(key.length+3);
const source=arg('source'),fixturePath=arg('fixture'),out=arg('out');assert(source&&fixturePath&&out);
assert(!fs.existsSync(out));
const sha=(p:string)=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
const sourceSHA256=sha(source),fixtureSHA256=sha(fixturePath);
const fixture:PoseFixture=JSON.parse(fs.readFileSync(fixturePath,'utf8'));
const gltf=await loadRigAt(pathToFileURL(path.resolve(source)),true);
const player=createFixturePlayer(gltf.scene,fixture),v=new THREE.Vector3();
const regions=player.meshes.map(mesh=>{
 const bySide:{L:Set<number>;R:Set<number>}={L:new Set(),R:new Set()};
 for(const [name,index]of Object.entries(mesh.morphTargetDictionary??{})){
  if(!/^gripClosed\.[LR]$/.test(name))continue;
  const side=name.endsWith('.L')?'L':'R';const delta=mesh.geometry.morphAttributes.position?.[index];assert(delta);
  for(let i=0;i<delta.count;i++)if(v.fromBufferAttribute(delta,i).length()>1e-9)bySide[side].add(i);
 }
 assert([...bySide.L].every(i=>!bySide.R.has(i)),'Source left/right grip deltas overlap');
 return {mesh,bySide};
});
const rows=[];
for(const side of ['L','R']as const){
 const frame=fixture.frames.find(f=>f.family==='grip.'+side&&f.closedGrip===1);assert(frame);
 const other:'L'|'R'=side==='L'?'R':'L';
 player.apply({...frame,closedGrip:0});
 const before=regions.map(({mesh})=>{
  const p=new Float64Array(mesh.geometry.getAttribute('position').count*3);
  for(let i=0;i<p.length/3;i++)p.set(mesh.localToWorld(mesh.getVertexPosition(i,v)).toArray(),i*3);
  return p;
 });
 player.apply(frame);
 let active=0,inactive=0,activeVertices=0,inactiveVertices=0;
 for(let k=0;k<regions.length;k++){
  const {mesh,bySide}=regions[k]!;
  for(const [name,index]of Object.entries(mesh.morphTargetDictionary??{}))
   if(/^gripClosed\.[LR]$/.test(name))assert.equal(mesh.morphTargetInfluences![index],name.endsWith('.'+side)?1:0);
  for(const which of [side,other])for(const i of bySide[which]){
   mesh.localToWorld(mesh.getVertexPosition(i,v));const distance=v.distanceTo(new THREE.Vector3().fromArray(before[k]!,i*3));
   if(which===side){active=Math.max(active,distance);activeVertices++;}
   else{inactive=Math.max(inactive,distance);inactiveVertices++;}
  }
 }
 assert(activeVertices>0&&inactiveVertices>0&&active>.001&&inactive<1e-8,'Unilateral grip control failed');
 rows.push({side,activeVertices,inactiveVertices,maximumActiveGripDisplacementM:active,maximumInactiveGripDisplacementM:inactive});
}
assert.equal(sha(source),sourceSHA256);assert.equal(sha(fixturePath),fixtureSHA256);
fs.writeFileSync(out,JSON.stringify({sourceSHA256,fixtureSHA256,rows,limits:['Open/closed comparison uses identical bones and actual Three.js skin positions.','This proves isolated source grip control, not natural fingers, cuff joins, palm/grip coverage or contact.']},null,2)+'\n');
console.log(JSON.stringify(rows));
