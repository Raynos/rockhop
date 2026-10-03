/** Independent finite boot/body/self/component contacts on actual captured mesh rows. */
import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import { triangleRows, bvhContacts } from './triangle-bvh.mjs';
const [folder, outFile, restDir] = process.argv.slice(2); assert(outFile && restDir && !fs.existsSync(outFile));
const sha = b => crypto.createHash('sha256').update(b).digest('hex');
const reportBytes = fs.readFileSync(path.join(folder,'report.json')), report = JSON.parse(reportBytes);
assert.deepEqual(report.errors,[]); assert.equal(report.cases.length,2);
const restReceiptBytes=fs.readFileSync(path.join(restDir,'receipt.json')),rest=JSON.parse(restReceiptBytes),restBytes=fs.readFileSync(path.join(restDir,'positions.f64'));
assert.equal(sha(restBytes),rest.positionsSHA256);
const restData=new Float64Array(restBytes.buffer,restBytes.byteOffset,restBytes.byteLength/8);let restOffset=0;
const restParts=rest.actualBoot.map(part=>{const vertices=Array.from({length:part.rows},()=>{const v=Array.from(restData.subarray(restOffset,restOffset+3));restOffset+=3;return v;});return triangleRows(vertices,part.faces,part.nativeIDs);});
const [restBody,restUpper,restSole]=restParts;
const restContacts={upperBody:bvhContacts(restUpper,restBody),soleBody:bvhContacts(restSole,restBody),upperSelf:bvhContacts(restUpper,restUpper,true,true),soleSelf:bvhContacts(restSole,restSole,true,true),upperSole:bvhContacts(restUpper,restSole,true)};
console.log(JSON.stringify({canonicalRest:Object.fromEntries(Object.entries(restContacts).map(([k,v])=>[k,v.pairs]))}));
const results=[];
for (const c of report.cases) {
  const bytes=fs.readFileSync(path.join(folder,c.id,'surface-positions.f64'));assert.equal(sha(bytes),c.surfacePositionsSHA256);
  const data=new Float64Array(bytes.buffer,bytes.byteOffset,bytes.byteLength/8), contract=c.init.actualBoot;
  const stride=contract.reduce((sum,p)=>sum+p.rows*3,0);assert.equal(data.length,stride*c.samples.length);
  const rows=[];
  for(let frame=0;frame<c.samples.length;frame++){
    let offset=frame*stride;
    const parts=contract.map(part=>{const vertices=Array.from({length:part.rows},()=>{const v=Array.from(data.subarray(offset,offset+3));offset+=3;assert(v.every(Number.isFinite));return v;});return triangleRows(vertices,part.faces,part.nativeIDs);});
    const [body,upper,sole]=parts;
    rows.push({inputTick:c.samples[frame].inputTick,upperBody:bvhContacts(upper,body),soleBody:bvhContacts(sole,body),upperSelf:bvhContacts(upper,upper,true,true),soleSelf:bvhContacts(sole,sole,true,true),upperSole:bvhContacts(upper,sole,true)});
  }
  const maxima=Object.fromEntries(['upperBody','soleBody','upperSelf','soleSelf','upperSole'].map(key=>[key,Math.max(...rows.map(r=>r[key].pairs))]));
  results.push({id:c.id,frames:rows.length,positionsSHA256:sha(bytes),maxima,rows});console.log(JSON.stringify({id:c.id,frames:rows.length,maxima}));
}
const proof={status:'UNACCEPTED_ACTUAL_BOOT_BODY_COMPONENT_FINITE_CONTACT_AUDIT',reportSHA256:sha(reportBytes),candidateSHA256:report.candidate.sha256,
  auditCodeSHA256:sha(fs.readFileSync(new URL(import.meta.url))),predicateSHA256:sha(fs.readFileSync('harness/hero-remaster/user-agent3-2026-10-03/triangle-contacts.mjs')),broadphaseSHA256:sha(fs.readFileSync('harness/hero-remaster/user-agent3-2026-10-03/triangle-bvh.mjs')),canonicalRestReceiptSHA256:sha(restReceiptBytes),canonicalRestContacts:restContacts,results,
  limits:['19 actual backwards-lean sampled frames percontrol, not every tick, continuous/swept collision or enclosed body volume test.',
    'Finite contact includes coplanar touching and does not report depth. Self/component pairs sharing native09 vertex IDs are excluded as intended adjacency; body pairs are never excluded.',
    'Actual CPU GLTF skin readback in engine world metres, not GPU surface validation or physical phone cost. Current wedge shape and peg load-bearing semantics remain unaccepted.',
    'Read-only audit is not consumed collision response or wearable art acceptance. Root alone judges the played comparison.']};
fs.writeFileSync(outFile,JSON.stringify(proof,null,2)+'\n');
