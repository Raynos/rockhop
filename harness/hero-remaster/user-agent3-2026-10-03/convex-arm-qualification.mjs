/** Frozen actual-riding spawn qualification, independent of Rapier's query. */
import fs from 'node:fs';import path from 'node:path';import assert from 'node:assert/strict';import crypto from 'node:crypto';
import * as RAPIER from '@dimforge/rapier3d-compat';import {Vector3}from'three';
import{partitionArmFaces,closedConvexVolume,convexPointDistance}from'./convex-arm-collider.mjs';
import{meshContacts}from'./triangle-contacts.mjs';
const[spawnFile,handoffFile,outFile]=process.argv.slice(2);assert(outFile&&!fs.existsSync(outFile));const sha=b=>crypto.createHash('sha256').update(b).digest('hex'),spawnBytes=fs.readFileSync(spawnFile),handoffBytes=fs.readFileSync(handoffFile);
assert.equal(sha(handoffBytes),'7a3514711c0cc04bb0505ba6deca4de58d2591f9d007e46abe9153d3e2aab60a');
const spawn=JSON.parse(spawnBytes).spawn,handoff=JSON.parse(handoffBytes),body=spawn.body.map(p=>new Vector3(...p)),cloth=spawn.cloth.map(p=>new Vector3(...p)),parts=partitionArmFaces(handoff),identity={x:0,y:0,z:0,w:1};
assert(spawn.actualPhysicalPose&&spawn.stance&&spawn.tick===0&&spawn.webdriver&&spawn.audioContexts===0);await RAPIER.init();
const report={status:'UNACCEPTED_CLOSED_CONVEX_SOURCE_QUALIFICATION',spawnSHA256:sha(spawnBytes),handoffSHA256:sha(handoffBytes),actualPhysicalPose:true,rapier:RAPIER.version(),parts:[],
 limits:['Both convex source-enclosing solids overlap intentionally. Added concavity volume is measured by garment clearance, not accepted as fit.',
 'Qualification at exact actual riding spawn only. No garment solver or correction is run; live consumed response, self/inter-garment handling, held-out motion, phone and art remain open.',
 'Rapier point projection is audited as a separate uncertain query, never used to claim source enclosure. Half-space enclosure and watertight orientation qualify the mathematical solids.']};
for(const part of parts){const solid=closedConvexVolume(body,part),center=solid.vertices.reduce((s,p)=>s.add(p),new Vector3()).multiplyScalar(1/solid.vertices.length);
 const desc=RAPIER.ColliderDesc.convexMesh(new Float32Array(solid.vertices.flatMap(p=>p.clone().sub(center).toArray())),new Uint32Array(solid.faces.flat()));assert(desc);
 let rapierFalseOutsideMaximumM=0,rapierFalseOutsideCount=0,sourcePlaneMaximumM=0,sourceWitness=null;
 for(const row of part.rows){const p=body[row],independent=convexPointDistance(p,solid);assert(independent.inside);sourcePlaneMaximumM=Math.max(sourcePlaneMaximumM,independent.maximumPlaneM);
 const q=desc.shape.projectPoint(center,identity,p,true);if(!q.isInside){const distanceM=p.distanceTo(new Vector3(q.point.x,q.point.y,q.point.z));if(distanceM>2e-6){rapierFalseOutsideCount++;if(distanceM>rapierFalseOutsideMaximumM){rapierFalseOutsideMaximumM=distanceM;sourceWitness={row,bodyVertexID:handoff.nativeConsumedColliders.body.relevantArmVertices[row].bodyVertexID,pointWorldM:p.toArray(),rapierPointWorldM:[q.point.x,q.point.y,q.point.z],distanceM};}}}}
 const samples=[...cloth,...handoff.pattern.triangleVertexIDs.map(f=>f.reduce((s,i)=>s.add(cloth[i]),new Vector3()).multiplyScalar(1/3))],gaps=samples.map(p=>convexPointDistance(p,solid).signedDistanceM);
 const garmentSurface=meshContacts(cloth.map(p=>p.toArray()),handoff.pattern.triangleVertexIDs,solid.vertices.map(p=>p.toArray()),solid.faces),self=meshContacts(solid.vertices.map(p=>p.toArray()),solid.faces,solid.vertices.map(p=>p.toArray()),solid.faces,true);
 assert.equal(garmentSurface.pairs,0);assert.equal(self.pairs,0);assert(Math.min(...gaps)>=.002);
 report.parts.push({part,...solid.qualification,sourcePlaneMaximumM,garmentSamples:samples.length,minimumGarmentSignedGapM:Math.min(...gaps),garmentSurface,solidSelf:self,
 rapierQuery:{falseOutsideCount:rapierFalseOutsideCount,falseOutsideMaximumM:rapierFalseOutsideMaximumM,witness:sourceWitness,qualifiedForCorrection:false}});
}
report.sourceFacesAssigned=parts.reduce((n,p)=>n+p.sourceTriangleIDs.length,0);assert.equal(report.sourceFacesAssigned,1066);
fs.mkdirSync(path.dirname(outFile),{recursive:true});fs.writeFileSync(outFile,JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify(report.parts.map(p=>({part:p.part.name,vertices:p.vertices,faces:p.faces,gapM:p.minimumGarmentSignedGapM,falseOutside:p.rapierQuery.falseOutsideMaximumM}))));
