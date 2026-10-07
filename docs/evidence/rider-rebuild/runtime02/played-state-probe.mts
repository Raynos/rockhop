import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { pathToFileURL } from 'node:url';
import * as THREE from 'three';
import { loadRigAt } from '../../../../src/render/hero/gltfTestUtils.ts';
import { FrameBuilder } from '../../../../src/render/frame.ts';
import { createPrivateRiderClass } from '../../../../harness/rider-rebuild/private-rider.mjs';

const build = path.resolve(process.argv[2]), input = path.resolve(process.argv[3]);
const receipt = JSON.parse(fs.readFileSync(path.join(build, 'rider-rebuild-inputs.json'), 'utf8'));
const catalog = JSON.parse(fs.readFileSync(path.join(build, 'model-catalog.json'), 'utf8'));
const played = JSON.parse(fs.readFileSync(input, 'utf8'));
const metadata = catalog.privateRiderMetadata, gltf = await loadRigAt(pathToFileURL(receipt.source), true);
const calibrationPath = process.env.RIDER_REBUILD_POSE_CALIBRATION ?? receipt.poseCalibration.path;
const calibrationBytes = fs.readFileSync(calibrationPath), calibration = JSON.parse(calibrationBytes.toString());
if (calibration.sourceSHA256 !== receipt.sourceSHA256) throw new Error('Pose calibration source changed');
if (process.env.RIDER_REBUILD_POSE_CALIBRATION) {
  delete metadata.driver.spineFlexTable; Object.assign(metadata.driver, calibration.driver);
}
const Rider = createPrivateRiderClass(metadata), rider = new Rider(gltf, { complete() {} });
const bikeModel = catalog.models.find(row => row.logical === 'models/bike-rookie.glb');
const bike = await loadRigAt(pathToFileURL(path.join(build, bikeModel.url)), true);
const rest = name => bike.scene.worldToLocal(bike.scene.getObjectByName(name)!.getWorldPosition(new THREE.Vector3()));
const offset = rest('attach_frame_origin').sub(rest('attach_chassis_com'));
const frame = new THREE.Group(); rider.attach({ frame });
const builder = new FrameBuilder(), rows = [];
for (const sample of played.samples) {
  const before = JSON.stringify(sample.state), f = builder.build(sample.state, 1);
  frame.position.copy(offset).applyAxisAngle(new THREE.Vector3(0, 0, 1), f.bikeAngle).add(new THREE.Vector3(f.bikeX, f.bikeY, 0));
  frame.rotation.z = f.bikeAngle; frame.updateWorldMatrix(true, true); rider.update(f);
  if (JSON.stringify(sample.state) !== before) throw new Error('Played physical state mutated');
  rows.push({ tick: sample.tick, stateHash: sample.hash, lean: f.rider.lean, physical: rider.debug.physicalPose,
    finite: rider.debug.allBoneFinite, gripM: [...rider.debug.gripErr], soleM: [...rider.debug.soleErr],
    inverse: structuredClone(rider.debug.anthropometry) });
}
const physical = rows.filter(row => row.physical);
const costs = physical.map(row => row.inverse.elapsedMs).sort((a, b) => a - b);
const report = { accepted: false, sourceSHA256: receipt.sourceSHA256,
  calibrationSHA256: crypto.createHash('sha256').update(calibrationBytes).digest('hex'),
  playedInput: { path: input, sha256: crypto.createHash('sha256').update(fs.readFileSync(input)).digest('hex') },
  sourceBikeChassisOffset: offset.toArray(), sampleCount: rows.length, physicalCount: physical.length,
  maxGripM: Math.max(...physical.flatMap(row => row.gripM)), maxSoleM: Math.max(...physical.flatMap(row => row.soleM)),
  maxCOMResidualM: Math.max(...physical.map(row => row.inverse.residualM)), allFinite: rows.every(row => row.finite), rows,
  solveCostMs: { median: costs[Math.floor(costs.length * 0.5)], p95: costs[Math.floor(costs.length * 0.95)], max: costs.at(-1) },
  maxFlexRadians: Math.max(...physical.map(row => Math.abs(row.inverse.spineFlexRadians))),
  limits: ['Actual played physics states evaluated on CPU; not a new browser replay or finish-time qualification',
    'Socket center errors do not qualify glove surfaces, phalange clearance, or moving art'] };
if (process.argv[5]) {
  const actual = JSON.parse(fs.readFileSync(process.argv[5], 'utf8'));
  if (actual.samples.length !== rows.length) throw new Error('Actual render sample count changed');
  report.actualRenderAgreement = { path: path.resolve(process.argv[5]),
    stateHashesEqual: rows.every((row, i) => row.stateHash === actual.samples[i].hash),
    maxSocketDifferenceM: Math.max(...rows.flatMap((row, i) => [...row.gripM, ...row.soleM]
      .map((value, k) => Math.abs(value - [...actual.samples[i].debug.gripErr, ...actual.samples[i].debug.soleErr][k])))),
    maxCOMResidualDifferenceM: Math.max(...rows.map((row, i) => Math.abs(row.inverse.residualM - actual.samples[i].debug.comResidual))) };
}
fs.writeFileSync(process.argv[4], JSON.stringify(report, null, 2) + '\n');
console.log(JSON.stringify({ sampleCount: report.sampleCount, physicalCount: report.physicalCount,
  maxGripM: report.maxGripM, maxSoleM: report.maxSoleM, maxCOMResidualM: report.maxCOMResidualM, allFinite: report.allFinite }));
