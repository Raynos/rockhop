/** Re-evaluate captured native75 poses without opening geometry, textures or a browser. */
import fs from 'node:fs';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import { Bone, Group, Object3D, Vector3, Quaternion } from 'three';
import { calibrateSelectedForearmPronation, applySelectedForearmPronation } from '../../../../src/render/hero/selected/rider.mjs';
import { calibrateAnthropometry, measureAnthropometricCOM } from '../../../../src/render/hero/selected/mass.mjs';
const [source, contractFile, reportFile, output] = process.argv.slice(2);
assert(source && contractFile && reportFile && output);
assert(!fs.existsSync(output));
const sha = file => crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');
const report = JSON.parse(fs.readFileSync(reportFile)), metadata = JSON.parse(fs.readFileSync(contractFile));
assert.equal(report.source.sha256, metadata.sourceSHA256);
assert.equal(report.requestedGripProfileSHA256, metadata.driver.gripProfileHash);
const fd = fs.openSync(source, 'r'), head = Buffer.alloc(20); fs.readSync(fd, head, 0, 20, 0);
assert.equal(head.toString('ascii', 0, 4), 'glTF');
const json = Buffer.alloc(head.readUInt32LE(12)); fs.readSync(fd, json, 0, json.length, 20); fs.closeSync(fd);
const doc = JSON.parse(json.toString()), joints = new Set(doc.skins[0].joints);
assert.equal(joints.size, 75);
const root = new Group(), nodes = doc.nodes.map((n, i) => {
  const node = joints.has(i) ? new Bone() : new Object3D(); node.name = n.name;
  node.position.fromArray(n.translation ?? [0, 0, 0]); node.quaternion.fromArray(n.rotation ?? [0, 0, 0, 1]); node.scale.fromArray(n.scale ?? [1, 1, 1]);
  for (const key of ['position', 'quaternion', 'scale']) assert(node[key].toArray().every(Number.isFinite));
  return node;
});
for (let i = 0; i < nodes.length; i++) for (const child of doc.nodes[i].children ?? []) nodes[i].add(nodes[child]);
for (const i of doc.scenes[doc.scene ?? 0].nodes) root.add(nodes[i]);
root.quaternion.fromArray(metadata.driver.assetToBikeQuaternionXYZW); root.updateWorldMatrix(true, true);
const byId = new Map([...joints].map(i => [doc.nodes[i].name, nodes[i]]));
const rests = new Map([...byId].map(([id, bone]) => [id, { translation: bone.position.toArray(), rotationXYZW: bone.quaternion.toArray(), scale: bone.scale.toArray() }]));
const binding = { byId, rests, contract: { hands: metadata.specification.hands } }, roles = metadata.specification.roles;
const rider = { bone: id => byId.get(id), roles, binding };
const anthropometry = calibrateAnthropometry(rider, metadata);
const driver = structuredClone(metadata.driver);
driver.forearmPronation = { schema: 'native-segment-twist-v1', gripProfileHash: driver.gripProfileHash };
const sides = [['left', 'Left'], ['right', 'Right']].map(([side, suffix]) => ({ side,
  calibration: calibrateSelectedForearmPronation(driver, binding, roles['forearm' + suffix], roles['wrist' + suffix]) }));
const q = bone => bone.getWorldQuaternion(new Quaternion()).normalize(), p = bone => bone.getWorldPosition(new Vector3());
const angle = (a, b) => 2 * Math.acos(Math.min(1, Math.abs(a.dot(b))));
const principal = radians => Math.atan2(Math.sin(radians), Math.cos(radians));
const skeleton = nodes.find(n => n.name === 'RiderSkeleton'); assert(skeleton);
const samples = [];
for (const sample of report.played.motionSamples) {
  root.quaternion.identity(); skeleton.matrix.fromArray(sample.skeletonWorld); skeleton.matrixAutoUpdate = false;
  for (const row of sample.joints) {
    const bone = byId.get(row.id); assert(bone);
    bone.position.fromArray(row.position); bone.quaternion.fromArray(row.quaternion); bone.scale.fromArray(row.scale);
  }
  root.updateWorldMatrix(true, true);
  const replayError = Math.max(...sample.joints.flatMap(row => byId.get(row.id).matrixWorld.elements.map((v, k) => Math.abs(v - row.worldMatrix[k]))));
  assert(replayError < 1e-12, 'Actual recorded local TRS must reconstruct world matrices');
  const beforeCOM = measureAnthropometricCOM(rider, anthropometry), before = new Map([...byId].map(([id, bone]) => [id, { p: p(bone), q: q(bone), localQ: bone.quaternion.toArray() }]));
  const hands = [];
  for (const { side, calibration } of sides) {
    const wrist = byId.get(calibration.wrist), target = q(wrist), distal = byId.get(calibration.segments.at(-1).id);
    const axis = p(wrist).sub(p(distal)).normalize().applyQuaternion(q(distal).invert());
    const delta = wrist.quaternion.clone().multiply(calibration.restWrist.clone().invert());
    const axialBefore = principal(2 * Math.atan2(new Vector3(delta.x, delta.y, delta.z).dot(axis), delta.w));
    const result = applySelectedForearmPronation(binding, calibration, target, metadata.driver.nearSimilarityTolerance);
    const afterDelta = wrist.quaternion.clone().multiply(calibration.restWrist.clone().invert());
    const axisAfter = p(wrist).sub(p(distal)).normalize().applyQuaternion(q(distal).invert());
    const axialAfter = principal(2 * Math.atan2(new Vector3(afterDelta.x, afterDelta.y, afterDelta.z).dot(axisAfter), afterDelta.w));
    const changed = new Set([...calibration.segments.map(s => s.id), calibration.wrist]);
    const wristDescendants = []; wrist.traverse(n => { if (n.isBone) wristDescendants.push(n); });
    hands.push({ side, ...result, axialBefore, axialAfter,
      handPositionDeltaM: Math.max(...wristDescendants.map(bone => p(bone).distanceTo(before.get(bone.name).p))),
      handQuaternionDeltaRadians: Math.max(...wristDescendants.map(bone => angle(q(bone), before.get(bone.name).q))),
      fingerLocalQuaternionExact: wristDescendants.filter(bone => !changed.has(bone.name)).every(bone => JSON.stringify(bone.quaternion.toArray()) === JSON.stringify(before.get(bone.name).localQ)) });
  }
  const positionDeltaM = Math.max(...[...byId].map(([id, bone]) => p(bone).distanceTo(before.get(id).p)));
  const comDeltaM = measureAnthropometricCOM(rider, anthropometry).distanceTo(beforeCOM);
  for (const row of sample.joints) {
    const bone = byId.get(row.id); assert.deepEqual(bone.position.toArray(), row.position); assert.deepEqual(bone.scale.toArray(), row.scale);
  }
  assert(positionDeltaM < 1e-6); assert(comDeltaM < 1e-8);
  assert(hands.every(hand => Math.abs(hand.axialAfter) < 1e-6 && hand.fingerLocalQuaternionExact && !hand.singular), JSON.stringify(hands));
  samples.push({ tick: sample.tick, phase: sample.phase, replayError, positionDeltaM, comDeltaM, hands });
}
const result = { accepted: false, method: 'Header-only native75 reconstruction of actual played local TRS, byte-pinned input files; apply opted-in runtime helper to each recorded full-arm pose. No geometry load, render or physics replay.',
  recipeSHA256: sha(new URL(import.meta.url)),
  source: { path: source, sha256: sha(source), bytes: fs.statSync(source).size }, contract: { path: contractFile, sha256: sha(contractFile) }, played: { path: reportFile, sha256: sha(reportFile) },
  driver: { path: 'src/render/hero/selected/rider.mjs', sha256: sha('src/render/hero/selected/rider.mjs') }, activation: driver.forearmPronation,
  calibrations: sides.map(({ side, calibration }) => ({ side, segments: calibration.segments })),
  summary: { samples: samples.length, maximumReconstructionElementError: Math.max(...samples.map(s => s.replayError)),
    maximumNativeJointPositionDeltaM: Math.max(...samples.map(s => s.positionDeltaM)), maximumAnthropometricCOMDeltaM: Math.max(...samples.map(s => s.comDeltaM)),
    maximumHandPositionDeltaM: Math.max(...samples.flatMap(s => s.hands.map(h => h.handPositionDeltaM))),
    maximumHandQuaternionDeltaRadians: Math.max(...samples.flatMap(s => s.hands.map(h => h.handQuaternionDeltaRadians))),
    maximumWristAxialResidualRadians: Math.max(...samples.flatMap(s => s.hands.map(h => Math.abs(h.axialAfter)))),
    allNativeTranslationsAndScalesExact: true, allFingerLocalQuaternionsExact: true, singularSamples: 0 },
  limits: ['Re-evaluation of existing played poses is a construction invariant check, not a new played capture or moving-art approval.', 'Native float32 scale residuals give sub-micrometre differences; source translations/scales remain byte-exact.', 'Cuff/sleeve overlap, bar contact, physical iPhone FPS, new full-solver COM and replay checks remain required.'], samples };
assert.equal(result.source.sha256, report.source.sha256);
fs.writeFileSync(output, JSON.stringify(result, null, 2) + '\n'); console.log(JSON.stringify(result.summary));
