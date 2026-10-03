/** Private geometry-derived socket contract; marker positions are proposals. */
import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import { pathToFileURL } from 'node:url';
import { Vector3 } from 'three';
import { loadRigAt } from '../../../src/render/hero/gltfTestUtils.ts';
import { prepareHero } from '../../../src/render/hero/lod.ts';
import { GltfRider } from '../../../src/render/hero/GltfRider.ts';
import { readGlbChunks } from './metadata.mjs';
const [sourceFile,patchFile,outFile,receiptFile]=process.argv.slice(2);assert(receiptFile&&!fs.existsSync(outFile));
const sha=b=>crypto.createHash('sha256').update(b).digest('hex'),sourceBytes=fs.readFileSync(sourceFile),patchBytes=fs.readFileSync(patchFile);
assert.equal(sha(sourceBytes),'ecc3bb87b2b9ff934c20345e47b422665f676a23f26a84622b6ec42cc0d42181');
assert.equal(sha(patchBytes),'48d1379f0ebce75c328b22ea7fdbc35fc4f42bbd8c67531b821cfb18947dd209');
const patches=JSON.parse(patchBytes),{json,bin}=readGlbChunks(sourceBytes),expected=structuredClone(json);
const g=await loadRigAt(pathToFileURL(path.resolve(sourceFile)),true);g.scene.updateMatrixWorld(true);
const bindings=new Map();for(const[o,a]of g.parser.associations)if(o.isBone&&a.nodes!==undefined)bindings.set(json.nodes[a.nodes].name,{object:o,node:a.nodes});
assert.equal(bindings.size,51);const rows=[];
for(const side of ['L','R'])for(const kind of ['palm','sole']){
  const patch=patches.surfaces.find(s=>s.label===`body-${kind}-${side}`);assert(patch);
  const normal=kind==='palm'?new Vector3(...patches.handFrames[side].proposedPalmarNormal):new Vector3(0,-1,0);
  const selected=patch.triangles.filter(t=>new Vector3(...t.fileWorldOutwardNormal).dot(normal)>0);assert(selected.length);
  const vertices=new Map(patch.vertices.map(v=>[v.vertexID,v])),center=new Vector3();let area=0;
  for(const t of selected){const p=t.vertexIDs.map(i=>new Vector3(...vertices.get(i).fileWorldM));const a=p[1].clone().sub(p[0]).cross(p[2].clone().sub(p[0])).length()/2;area+=a;center.addScaledVector(p[0].clone().add(p[1]).add(p[2]).multiplyScalar(1/3),a);}
  center.multiplyScalar(1/area);const parent=bindings.get(`${kind==='palm'?'hand':'foot'}.${side}`);assert(parent);
  const local=parent.object.worldToLocal(center.clone()),name=`${kind==='palm'?'grip':'sole'}Socket.${side}`,index=json.nodes.length;
  assert(!json.nodes.some(n=>n.name===name));
  // Identity local rotation inherits current anatomical hand/foot orientation;
  // the engine captures that rest frame. No legacy orientation/offset copied.
  json.nodes.push({name,translation:local.toArray(),extras:{rockhopPrivateContract:'UNACCEPTED geometry-derived diagnostic marker'}});
  (json.nodes[parent.node].children??=[]).push(index);
  rows.push({name,parentNativeJoint:json.nodes[parent.node].name,parentNode:parent.node,node:index,localTranslationM:local.toArray(),fileWorldProposalM:center.toArray(),
    sourcePatch:patch.label,normalRule:kind==='palm'?'outward normal dot owner palmar normal > 0':'outward normal dot file -Y > 0',
    selectedTriangleIDs:selected.map(t=>t.triangleID),sourceIDs:[...new Set(selected.flatMap(t=>t.sourceIDs))].sort((a,b)=>a-b),areaM2:area,
    orientation:'Inherit anatomical parent rest orientation; no extra local rotation',limits:'Area centroid marker proposal only, not measured grip/peg contact or accepted load-bearing surface.'});
}
const jb=Buffer.from(JSON.stringify(json)),pad=Buffer.alloc((4-jb.length%4)%4,32),jsonBytes=Buffer.concat([jb,pad]);
const header=Buffer.alloc(20);header.writeUInt32LE(0x46546c67,0);header.writeUInt32LE(2,4);header.writeUInt32LE(28+jsonBytes.length+bin.length,8);header.writeUInt32LE(jsonBytes.length,12);header.writeUInt32LE(0x4e4f534a,16);
const bh=Buffer.alloc(8);bh.writeUInt32LE(bin.length);bh.writeUInt32LE(0x004e4942,4);const derivative=Buffer.concat([header,jsonBytes,bh,bin]);
fs.mkdirSync(path.dirname(outFile),{recursive:true});fs.writeFileSync(outFile,derivative);const result=readGlbChunks(derivative);assert(result.bin.equals(bin));
for(const row of rows){(expected.nodes[row.parentNode].children??=[]).push(row.node);expected.nodes.push(json.nodes[row.node]);}assert.deepEqual(expected,result.json);
const loaded=await loadRigAt(pathToFileURL(path.resolve(outFile)),true);loaded.scene.updateMatrixWorld(true);
const checked=[];for(const row of rows){const node=loaded.scene.getObjectByName(row.name.replaceAll('.',''));assert(node);const actual=node.getWorldPosition(new Vector3());const residual=actual.distanceTo(new Vector3(...row.fileWorldProposalM));assert(residual<1e-10);checked.push({name:row.name,worldResidualM:residual});}
await prepareHero(loaded);const rider=new GltfRider(loaded,{complete(){}});assert(rider.gripSockets.every(Boolean)&&rider.soleSockets.every(Boolean));
const report={status:'UNACCEPTED_PRIVATE_SOCKET_CONTRACT_READY_NOT_FIT_ACCEPTANCE',sourceSHA256:sha(sourceBytes),derivativeSHA256:sha(derivative),patchSHA256:sha(patchBytes),
  identicalBINSHA256:sha(bin),onlyJSONChanges:'Four child nodes under original hand/foot bones; appended child references. Skin51 unchanged; all other JSON/BIN exact.',rows,actualLoader:checked,
  engineConstructorRecognizesAllSockets:true,gripOffsets:rider.gripOffsets.map(v=>v.toArray()),gripRestQ:rider.gripRestQ.map(q=>q.toArray()),
  codeSHA256:sha(fs.readFileSync(new URL(import.meta.url))),limits:['Private metadata derivative of human-rejected05 only, no source/wardrobe promotion.',
    'Body patches and facing hemisphere give explicit geometry ancestry. Centroid marker contact locations remain proposals.',
    'Current engine sole marker is measurement-only and does not offset ankle IK. Named sockets alone cannot certify sole support, seated support or complete footwear.',
    'Moving physical-body branch must be checked separately; protected body/head51bind retained exactly.']};
fs.mkdirSync(path.dirname(receiptFile),{recursive:true});fs.writeFileSync(receiptFile,JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({status:report.status,derivativeSHA256:report.derivativeSHA256,gripOffsets:report.gripOffsets}));
