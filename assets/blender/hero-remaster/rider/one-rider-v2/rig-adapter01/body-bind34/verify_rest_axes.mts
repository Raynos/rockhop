/** CPU-only actual private driver rest-axis proof; no material/render claim. */
import fs from 'node:fs';
import assert from 'node:assert/strict';
import { pathToFileURL } from 'node:url';
import * as THREE from 'three';
import { loadRigAt } from '../../../../../../../src/render/hero/gltfTestUtils';
import { prepareHero } from '../../../../../../../src/render/hero/lod';
const evidence = 'docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/body-bind34';
const report = JSON.parse(fs.readFileSync(evidence + '/mapping-report.json', 'utf8'));
const { GltfRider } = await import(pathToFileURL(process.cwd() + '/harness/out/hero-remaster/body34-fresh-rig-cpu/rider.mjs').href);
Object.assign(globalThis, {document: {createElement: () => ({width:128,height:64,getContext: () => ({createRadialGradient: () => ({addColorStop(){}}),scale(){},fillRect(){}})})}});
const gltf = await loadRigAt(pathToFileURL(report.candidate), true);
await prepareHero(gltf);
const rider = new GltfRider(gltf, {complete(){}});
assert.equal(rider.debug.bones,19);
const rows = report.restAxes.map((row: {bone:string;anatomicalWorldDirection:number[]}) => {
  const actual = rider.d0.get(row.bone) as THREE.Vector3;
  assert(actual, row.bone);
  const error = actual.distanceTo(new THREE.Vector3().fromArray(row.anatomicalWorldDirection));
  assert(error < 1e-6, row.bone + ' anatomical-axis mismatch');
  return {bone:row.bone,actualDirection:actual.toArray(),expectedDirection:row.anatomicalWorldDirection,error};
});
assert.equal(rows.length,14);
assert.equal(rider.newRiderHandTargetQ.size,2);
assert(rider.gripSockets.every(Boolean) && rider.soleSockets.every(Boolean));
const result = {status:'PASS actual private driver14anatomical axes and19bone/4socket census',
 sourceSHA256:report.candidateSHA256, rows, maximumAxisVectorError:Math.max(...rows.map((r:{error:number})=>r.error)),
 mappedHands:2,sockets:4,limits:'CPU rest state only. Actual posed surface/contacts in cpu-adaptation-audit; no moving appearance/Garage/phone pass.'};
fs.writeFileSync(evidence + '/rest-axis-verification.json',JSON.stringify(result,null,2)+'\n');
console.log(JSON.stringify(result,null,2));
