// Physical native field scales; no triangle-ratio or arbitrary scale sweep.
import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import {Matrix4,Vector3} from 'three';
import {openGlb,accessorBytes,fileSha} from '../download-opt01/geometry01/glb.mjs';
const [intake,out]=process.argv.slice(2),meta=JSON.parse(fs.readFileSync(path.join(intake,'intake.json')));
assert.equal(meta.sha256,'127e316a8ff7910a4918b63f83e086e4e658062f102c73f17d0ee2f956750649');
const g=openGlb(meta.source),j=g.json,skin=j.skins[0],names=skin.joints.map(n=>j.nodes[n].name),side=meta.meshIndex===2?'L':'R',hand=names.indexOf('DEF-hand.'+side);assert(hand>=0);
const data=await accessorBytes(g,skin.inverseBindMatrices),f=new Float32Array(data.buffer,data.byteOffset,data.length/4),binds=skin.joints.map((_,i)=>new Matrix4().fromArray(f,i*16)),parent=new Map();
for(const [i,n] of j.nodes.entries())for(const c of n.children??[])parent.set(c,i);
function ancestry(node){const p=[];while(node!==undefined){p.push(node);node=parent.get(node);}return p;}
function pathLength(a,b){const pa=ancestry(a),pb=ancestry(b),common=pa.find(n=>pb.includes(n));assert(common!==undefined);let length=0;for(const p of [pa,pb])for(const n of p){if(n===common)break;assert(!j.nodes[n].matrix);assert((j.nodes[n].scale??[1,1,1]).every(s=>Math.abs(s-1)<1e-6));length+=Math.hypot(...(j.nodes[n].translation??[0,0,0]));}return length;}
const corners=[];for(let k=0;k<8;k++)corners.push(new Vector3(...[0,1,2].map(a=>meta.attributes.POSITION[(k&(1<<a))?'max':'min'][a])));
const rawJ=fs.readFileSync(path.join(intake,'JOINTS_0.bin')),rawW=fs.readFileSync(path.join(intake,'WEIGHTS_0.bin')),weights=new Float32Array(rawW.buffer,rawW.byteOffset,rawW.length/4),active=new Set([hand]);for(let i=0;i<rawJ.length;i++)if(weights[i]>0)active.add(rawJ[i]);
const measured=names.map(()=>0);const envelope=names.map((_,i)=>!active.has(i)||i===hand?0:pathLength(skin.joints[i],skin.joints[hand])+Math.max(...corners.map(p=>p.clone().applyMatrix4(binds[i]).length()+p.clone().applyMatrix4(binds[hand]).length())));
const reports=[];let samples=0;
for(const bike of ['rookie','pro']){
 const file=path.join('harness/out/rider-rebuild/selected-ankle-field42',`gameplay-${bike}01/report.json`),r=JSON.parse(fs.readFileSync(file));assert.equal(r.source.source.sha256,meta.sha256);reports.push({bike,sha256:fileSha(file),poses:r.played.motionSamples.length});
 for(const sample of r.played.motionSamples){samples++;const byName=new Map(sample.joints.map(q=>[q.id,q.worldMatrix])),m=names.map((name,i)=>new Matrix4().fromArray(byName.get(name)).multiply(binds[i]));for(const i of active)for(const p of corners)measured[i]=Math.max(measured[i],p.clone().applyMatrix4(m[i]).distanceTo(p.clone().applyMatrix4(m[hand])));}
}
const records=names.map((name,i)=>({joint:i,name,active:active.has(i),recordedWristRelativeMaxMeters:measured[i],fixedBoneRotationEnvelopeMeters:envelope[i],attributeWeightMeters:Math.max(measured[i],envelope[i])}));
const r={accepted:false,sourceSHA256:meta.sha256,meshIndex:meta.meshIndex,referenceJoint:hand,referenceName:names[hand],activeNativeJointIds:[...active].sort((a,b)=>a-b),sourceAabb:meta.attributes.POSITION,recordedPoses:samples,reports,fields:records,formula:'For arbitrary rigid joint rotations with original fixed local translation lengths, wrist-relative skinpoint distance <= native joint path length + norm(IBM_j*p)+norm(IBM_wrist*p). Max over eight original sourceAABBcorners bounds every restpoint in its convex hull. Attribute scalar is max(measured482pose displacement,envelope), in metres per unit normalized weight. Wrist field has zero relative displacement; sum-weight conservation leaves other fields controlling relative movement.',limits:'Not a hard Meshopt deformation error bound. No scaling of target triangle quota. Only original source-supported fields are calibrated; unused native fields carry no scale and cannot enter simplification. Original4slots retained and branch locks remain mandatory. Future drivers exceeding original local translation/scale bounds or corrected grip outside measured/bounded assumptions need fresh verification; atlas/interior/played art remain open.'};
fs.mkdirSync(path.dirname(out),{recursive:true});fs.writeFileSync(out,JSON.stringify(r,null,2)+'\n');fs.closeSync(g.fd);console.log(JSON.stringify({mesh:r.meshIndex,poses:samples,scales:records.filter(q=>q.name.endsWith('.'+side)).map(q=>({name:q.name,recorded:q.recordedWristRelativeMaxMeters,envelope:q.attributeWeightMeters}))}));
