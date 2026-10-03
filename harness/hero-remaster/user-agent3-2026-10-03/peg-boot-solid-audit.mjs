/** Whole rendered peg assembly versus frozen actual boot poses; no new movie or pose injection. */
import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import { Matrix4, Vector3, Quaternion } from 'three';
import { Game } from '../../../src/game/game.ts';
import { createBikePhysicsV2 } from '../../../src/physics/v2/bike.ts';
import { decodeJSON, expandFrames } from '../../../src/core/replay.ts';
import { FrameBuilder } from '../../../src/render/frame.ts';
import { triangleRows,bvhContacts } from './triangle-bvh.mjs';
import { makeClosedSolidQuery } from './closed-solid-query.mjs';
const [packet,inventoryFile,fixturesFile,outFile]=process.argv.slice(2);assert(outFile&&!fs.existsSync(outFile));
const sha=b=>crypto.createHash('sha256').update(b).digest('hex'),reportBytes=fs.readFileSync(path.join(packet,'report.json')),report=JSON.parse(reportBytes),inventoryBytes=fs.readFileSync(inventoryFile),inventory=JSON.parse(inventoryBytes),fixtures=JSON.parse(fs.readFileSync(fixturesFile));
assert.equal(inventory.badEdgeCount,0);assert(inventory.components.every(c=>c.euler===2&&c.signedVolumeM3>0&&c.selfContact.pairs===0));
const query=makeClosedSolidQuery(inventory.verticesFrameLocalM,inventory.triangleVertexIDs,inventory.components),pegTriangles=triangleRows(inventory.verticesFrameLocalM,inventory.triangleVertexIDs),results=[];
for(const c of report.cases){
 const fixture=fixtures.cases.find(f=>f.id===c.fixtureId);assert(fixture);
 const recordingBytes=fs.readFileSync(path.join(path.dirname(fixturesFile),fixture.recording));assert.equal(sha(recordingBytes),c.recordingSHA256);
 const rec=decodeJSON(recordingBytes.toString()),inputs=expandFrames(rec),game=new Game({physics:createBikePhysicsV2(rec.header.physicsHz),physicsHz:rec.header.physicsHz,renderer:{setTrack(){},onEvent(){},setQuality(){},setBikeClass(){}},autoSkipCountdown:true,ghostEnabled:false});game.loadTrack(rec.header.trackId,rec.header.seed,rec.header.bike);
 const positionsBytes=fs.readFileSync(path.join(packet,c.id,'surface-positions.f64'));assert.equal(sha(positionsBytes),c.surfacePositionsSHA256);const data=new Float64Array(positionsBytes.buffer,positionsBytes.byteOffset,positionsBytes.byteLength/8),contract=c.init.actualBoot,stride=contract.reduce((s,p)=>s+p.rows*3,0),rows=[];let frame=0,maximumReferenceFrameResidualM=0;
 for(let tick=1;tick<=c.everyInputTickCount;tick++){
  game.setInput(inputs[tick-1]);game.step(1);const sample=c.samples[frame];if(sample?.inputTick!==tick)continue;assert.equal(game.hashState(),sample.stateHash);
  const f=new FrameBuilder().build(game.getState(),1),offset=new Vector3(...inventory.chassisToFrameOffsetM).applyAxisAngle(new Vector3(0,0,1),f.bikeAngle).add(new Vector3(f.bikeX,f.bikeY,0)),matrix=new Matrix4().compose(offset,new Quaternion().setFromAxisAngle(new Vector3(0,0,1),f.bikeAngle),new Vector3(1,1,1));
  for(const[side,s]of sample.arch.sides.entries())maximumReferenceFrameResidualM=Math.max(maximumReferenceFrameResidualM,new Vector3(-.14,.031,side===0?.2:-.2).applyMatrix4(matrix).distanceTo(new Vector3(...s.pegWorldM)));
  assert(maximumReferenceFrameResidualM<1e-12,'Independent chassis frame must match observed actual peg references');const inverse=matrix.clone().invert();let cursor=frame*stride;
  const parts=contract.map(part=>{const points=Array.from({length:part.rows},()=>{const p=new Vector3().fromArray(data,cursor).applyMatrix4(inverse);cursor+=3;return p.toArray();});return{name:part.name,points,triangles:triangleRows(points,part.faces,part.nativeIDs),nativeIDs:part.nativeIDs};});
  const partResults=parts.filter(p=>p.name!=='body').map(part=>{
   const inside=[],boundary=[];
   part.points.forEach((point,row)=>{const result=query(point);if(result.inside)inside.push({row,nativeID:part.nativeIDs[row],pointFrameLocalM:point,hits:result.hits});else if(result.boundary)boundary.push({row,nativeID:part.nativeIDs[row]});});
   return {part:part.name,surfaceContacts:bvhContacts(part.triangles,pegTriangles),insideRows:inside.length,insideUniqueNativeVertices:new Set(inside.map(v=>v.nativeID)).size,boundaryRows:boundary.length,maximumSampledVertexPenetrationM:Math.max(0,...inside.flatMap(v=>v.hits.map(h=>h.penetrationM))),insideWitnesses:inside};
  });
  const sole=parts.find(p=>p.name==='sole'),byID=new Map();
  sole.points.forEach((p,i)=>{const id=sole.nativeIDs[i];if(byID.has(id))assert(new Vector3(...p).distanceTo(new Vector3(...byID.get(id)))<1e-12);else byID.set(id,p);});
  const nativeIDs=[...byID.keys()],indexByID=new Map(nativeIDs.map((id,i)=>[id,i])),soleVertices=nativeIDs.map(id=>byID.get(id)),soleFaces=contract.find(p=>p.name==='sole').faces.map(f=>f.map(i=>indexByID.get(sole.nativeIDs[i]))),edgeUses=new Map();
  soleFaces.forEach((face,id)=>face.forEach((a,k)=>{const b=face[(k+1)%3],key=[Math.min(a,b),Math.max(a,b)].join(',');const list=edgeUses.get(key)??[];list.push({face:id,direction:a<b?1:-1});edgeUses.set(key,list);}));
  assert([...edgeUses.values()].every(e=>e.length===2&&e[0].direction+e[1].direction===0),'Rubber volume must be closed and consistently oriented before reverse membership');
  const adj=soleFaces.map(()=>new Set());for(const list of edgeUses.values())for(const a of list)for(const b of list)if(a.face!==b.face)adj[a.face].add(b.face);
  const visited=new Set(),soleComponents=[];
  for(let i=0;i<soleFaces.length;i++)if(!visited.has(i)){const stack=[i],ids=[];while(stack.length){const id=stack.pop();if(visited.has(id))continue;visited.add(id);ids.push(id);stack.push(...adj[id]);}
   const used=[...new Set(ids.flatMap(id=>soleFaces[id]))],edges=new Set(ids.flatMap(id=>soleFaces[id].map((a,k)=>{const b=soleFaces[id][(k+1)%3];return[Math.min(a,b),Math.max(a,b)].join(',');}))),volume=ids.reduce((sum,id)=>{const[a,b,c]=soleFaces[id].map(i=>new Vector3(...soleVertices[i]));return sum+a.dot(b.clone().cross(c))/6;},0),selfRows=triangleRows(soleVertices,ids.map(id=>soleFaces[id])),self=bvhContacts(selfRows,selfRows,true,true);
   assert.equal(used.length-edges.size+ids.length,2);assert(volume>0&&self.pairs===0,'Reverse rubber volume must be positive and non-self-contacting');
   soleComponents.push({component:soleComponents.length,triangles:ids,euler:2,signedVolumeM3:volume,selfContactPairs:self.pairs,bounds:{min:[0,1,2].map(k=>Math.min(...used.map(i=>soleVertices[i][k]))),max:[0,1,2].map(k=>Math.max(...used.map(i=>soleVertices[i][k])))}});}
  const reverseQuery=makeClosedSolidQuery(soleVertices,soleFaces,soleComponents),pegInsideSole=[];
  inventory.verticesFrameLocalM.forEach((point,vertexID)=>{const result=reverseQuery(point);if(result.inside)pegInsideSole.push({vertexID,pointFrameLocalM:point,hits:result.hits});});
  rows.push({inputTick:tick,frameMatrixColumnMajor:matrix.toArray(),parts:partResults,qualifiedClosedRubberComponents:soleComponents.map(({triangles,...rest})=>({...rest,triangles:triangles.length})),pegVerticesInsideSole:pegInsideSole,maximumSampledPegVertexRubberDepthM:Math.max(0,...pegInsideSole.flatMap(v=>v.hits.map(h=>h.penetrationM)))});frame++;
 }
 assert.equal(frame,c.samples.length);const summary={id:c.id,frames:frame,maximumReferenceFrameResidualM,maximumUpperPegSurfacePairs:Math.max(...rows.map(r=>r.parts[0].surfaceContacts.pairs)),maximumSolePegSurfacePairs:Math.max(...rows.map(r=>r.parts[1].surfaceContacts.pairs)),maximumInsideBootRows:Math.max(...rows.map(r=>r.parts.reduce((s,p)=>s+p.insideRows,0))),maximumSampledVertexPenetrationM:Math.max(...rows.flatMap(r=>r.parts.map(p=>p.maximumSampledVertexPenetrationM))),maximumPegVerticesInsideSole:Math.max(...rows.map(r=>r.pegVerticesInsideSole.length)),maximumSampledPegVertexRubberDepthM:Math.max(...rows.map(r=>r.maximumSampledPegVertexRubberDepthM)),rows};results.push(summary);console.log(JSON.stringify({...summary,rows:undefined}));
}
const proof={status:'UNACCEPTED_RENDERED_PEG_SOLID_INTERSECTION_AUDIT',captureReportSHA256:sha(reportBytes),inventorySHA256:sha(inventoryBytes),codeSHA256:sha(fs.readFileSync(new URL(import.meta.url))),querySHA256:sha(fs.readFileSync('harness/hero-remaster/user-agent3-2026-10-03/closed-solid-query.mjs')),bikeDriverSHA256:sha(fs.readFileSync('src/render/hero/gltfBike.ts')),results,
 limits:['Closed actual peg components query sampled boot vertices plus full finite triangle contacts. No new cosmetic capture, pose injection, boot source change or collider response.', '19 actual frames percontrol, not swept/every-tick collision. Maximum vertex depth samples vertices; it is not a full triangle penetration-depth bound.', 'Peg compound components intentionally overlap; query reports union membership but does not estimate force, contact area or load bearing.', 'Root rejects wedge art and finds seating visually inconclusive. No player/garment/physical phone acceptance.']};
fs.mkdirSync(path.dirname(outFile),{recursive:true});fs.writeFileSync(outFile,JSON.stringify(proof,null,2)+'\n');
