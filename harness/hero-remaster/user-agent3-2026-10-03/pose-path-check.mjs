/** Frozen candidate pose-branch limitation from actual played receipts and source. */
import fs from 'node:fs';
import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import { readGlbChunks } from './metadata.mjs';
const [candidateFile,receiptFile,controlFile,outFile]=process.argv.slice(2);assert(outFile&&!fs.existsSync(outFile));
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const candidateBytes=fs.readFileSync(candidateFile),receiptBytes=fs.readFileSync(receiptFile),controlBytes=fs.readFileSync(controlFile);
const g=readGlbChunks(candidateBytes).json,control=readGlbChunks(controlBytes).json,receipt=JSON.parse(receiptBytes);
assert.equal(sha(candidateBytes),'ecc3bb87b2b9ff934c20345e47b422665f676a23f26a84622b6ec42cc0d42181');assert.equal(receipt.candidate.sha256,sha(candidateBytes));
const sockets=json=>Object.fromEntries(['grip','sole'].map(role=>[role,['L','R'].map(side=>json.nodes.filter(n=>n.name===`${role}Socket.${side}`||n.name===`${role}Socket${side}`).map(n=>n.name))]));
const candidateSockets=sockets(g),controlSockets=sockets(control);assert(candidateSockets.grip.every(s=>s.length===0)&&candidateSockets.sole.every(s=>s.length===0));
const samples=receipt.cases.flatMap(c=>c.samples);assert.equal(samples.length,152);assert(samples.every(s=>s.socketDebug.physicalPose===false&&s.socketDebug.stance.on===false&&!s.poseInjection&&!s.stage));
const engineFile='src/render/hero/GltfRider.ts',engine=fs.readFileSync(engineFile,'utf8');
assert(engine.includes('this.debug.physicalPose = f.riderBody.present && this.gripSockets.every(Boolean) && this.bike !== null;'));
assert(engine.includes('const c = solveChain(r, this.chain);'));
const report={status:'UNACCEPTED05_PHYSICAL_BODY_POSE_BRANCH_UNREACHED',candidateSHA256:sha(candidateBytes),receiptSHA256:sha(receiptBytes),candidateSockets,
  negativeControl:{file:controlFile,sha256:sha(controlBytes),sockets:controlSockets,limits:'Source-node presence only; no new control render or physical/contact qualification.'},
  playedSamples:samples.length,allPhysicalPoseFalse:true,allStanceOff:true,normalFallbackUsesFrameDerivedRiderFields:true,completeSkinJoints:g.skins[0].joints.length,
  engineSource:{file:engineFile,sha256:sha(Buffer.from(engine)),guard:'riderBody.present AND both grip sockets AND attached bike'},checkCodeSHA256:sha(fs.readFileSync(new URL(import.meta.url))),
  rootReview:{broadPalmAndPlantarRegionIdentities:'Approved for diagnostic progress only',broadPosteriorJeans:'Clearance search only; not a seated support map',engineAnatomy:'Broad movement matches native04; foot/knee/hem and1.5s armpit defects retained. Tiny collar lip not discernible; appearance parity unproved.'},
  limits:['Existing05 films are actual recorded Game/live bike controls, not admission of authoritative COM/angle physical-body pose or seated support.',
    'Sockets must be owner-authored from current geometry/contact/orientation and actual bind. Adding markers alone does not qualify rejected garment/footwear enclosure or fit.',
    'The broad posterior patch projected values in the prior packet are geometric clearance/projection proxies, never load-bearing seat measurements.',
    'Next inferior gluteal, peg-bearing and palmar-facing subsets require posed normals and actual rider/bike witnesses; no root indices or acceptance threshold invented.',
    'Protected mannequin body/head/bind remains unchanged. Current wardrobe remains human-rejected; no source/player promotion.']};
fs.writeFileSync(outFile,JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({status:report.status,samples:report.playedSamples,candidateSockets,controlSockets}));
