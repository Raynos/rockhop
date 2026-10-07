import fs from 'node:fs';
import crypto from 'node:crypto';
import path from 'node:path';
import { pathToFileURL } from 'node:url';
import * as THREE from 'three';
import { loadRigAt } from '../../../../src/render/hero/gltfTestUtils.ts';
import { FrameBuilder } from '../../../../src/render/frame.ts';
import { BIKE_GEOMETRY_V2 } from '../../../../src/render/hero/assetFrame.ts';
import { makeRiderRigPose, riderPoseAtLean, RIDER_TORSO_REST } from '../../../../src/core/riderGeometry.ts';
import { createPrivateRiderClass } from '../../../../harness/rider-rebuild/private-rider.mjs';
const source = path.resolve(process.argv[2]), contract = path.resolve(process.argv[3]);
const metadata = JSON.parse(fs.readFileSync(contract, 'utf8'));
metadata.sourceSHA256 = crypto.createHash('sha256').update(fs.readFileSync(source)).digest('hex');
metadata.driver.nearSimilarityTolerance = 1e-4;
if (process.env.RIDER_REBUILD_POSE_CALIBRATION) Object.assign(metadata.driver,
  JSON.parse(fs.readFileSync(process.env.RIDER_REBUILD_POSE_CALIBRATION, 'utf8')).driver);
const gltf = await loadRigAt(pathToFileURL(source), true);
const Rider = createPrivateRiderClass(metadata), rider = new Rider(gltf, { complete() {} });
const frame = new THREE.Group();
frame.position.set(BIKE_GEOMETRY_V2.chassisToAxle.x, BIKE_GEOMETRY_V2.chassisToAxle.y, 0);
frame.updateWorldMatrix(true, true); rider.attach({ frame });
const rows = [];
for (let i = 0; i <= 40; i++) {
  const lean = -1 + i / 20, p = riderPoseAtLean(lean, makeRiderRigPose()), f = new FrameBuilder().frame;
  f.riderBody.present = true; f.riderBody.relX = p.com.x + frame.position.x; f.riderBody.relY = p.com.y + frame.position.y;
  f.riderBody.relAngle = p.torsoAngle - RIDER_TORSO_REST; f.rider.lean = lean;
  rider.update(f);
  rows.push({ lean, ...rider.debug.anthropometry, gripM: [...rider.debug.gripErr], soleM: [...rider.debug.soleErr],
    armReach: [...rider.debug.armStretch], legReach: [...rider.debug.legStretch] });
}
const summary = { accepted: false, source, sourceSHA256: metadata.sourceSHA256,
  approximation: rider.anthropometry.approximation, maxGripM: Math.max(...rows.flatMap(r=>r.gripM)),
  maxSoleM: Math.max(...rows.flatMap(r=>r.soleM)), maxCOMResidualM: Math.max(...rows.map(r=>r.residualM)),
  armLengthsM: rider.limbs.get('armLeft').lengths, legLengthsM: rider.limbs.get('legLeft').lengths,
  cpuElapsedMs: rows.map(r=>r.elapsedMs).sort((a,b)=>a-b), rows };
fs.writeFileSync(process.argv[4], JSON.stringify(summary, null, 2) + '\n');
console.log(JSON.stringify({ sourceSHA256: summary.sourceSHA256, maxGripM: summary.maxGripM,
  maxSoleM: summary.maxSoleM, maxCOMResidualM: summary.maxCOMResidualM, cpuMedianMs: summary.cpuElapsedMs[20], cpuMaxMs: summary.cpuElapsedMs.at(-1) }));
