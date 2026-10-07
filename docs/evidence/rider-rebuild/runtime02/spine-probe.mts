import fs from 'node:fs';
import crypto from 'node:crypto';
import path from 'node:path';
import { pathToFileURL } from 'node:url';
import * as THREE from 'three';
import { loadRigAt } from '../../../../src/render/hero/gltfTestUtils.ts';
import { FrameBuilder } from '../../../../src/render/frame.ts';
import { BIKE_GEOMETRY_V2 } from '../../../../src/render/hero/assetFrame.ts';
import { makeRiderRigPose, riderPoseAtLean, RIDER_TORSO_REST } from '../../../../src/core/riderGeometry.ts';
import { invertAnthropometricCOM, measureAnthropometricCOM } from '../../../../harness/rider-rebuild/anthropometric-inverse.mjs';
import { resetHumanoidPose } from '../../../../harness/rider-rebuild/new-humanoid-contract.mjs';
import { createPrivateRiderClass } from '../../../../harness/rider-rebuild/private-rider.mjs';
const source = path.resolve(process.argv[2]), contract = path.resolve(process.argv[3]);
const metadata = JSON.parse(fs.readFileSync(contract, 'utf8'));
metadata.sourceSHA256 = crypto.createHash('sha256').update(fs.readFileSync(source)).digest('hex');
metadata.driver.nearSimilarityTolerance = 1e-4;
const gltf = await loadRigAt(pathToFileURL(source), true);
const candidates = [];
for (const palmDegrees of [-15, -30, -45, -60, -75, -90]) {
  const theta = palmDegrees * Math.PI / 180;
  metadata.driver.palmForwardBike = [Math.cos(theta), Math.sin(theta), 0];
  metadata.driver.palmNormalBike = [Math.sin(theta), -Math.cos(theta), 0];
  const Rider = createPrivateRiderClass(metadata), rider = new Rider(gltf, { complete() {} });
  const bike = new THREE.Group(); bike.position.set(BIKE_GEOMETRY_V2.chassisToAxle.x, BIKE_GEOMETRY_V2.chassisToAxle.y, 0);
  bike.updateWorldMatrix(true, true); rider.attach({ frame: bike });
  const rows = [];
  for (const lean of [-1, -.5, 0, .3, .5, .75, 1]) {
    const original = riderPoseAtLean(lean, makeRiderRigPose()), f = new FrameBuilder().frame;
    f.riderBody.present = true; f.riderBody.relX = original.com.x + bike.position.x; f.riderBody.relY = original.com.y + bike.position.y;
    f.riderBody.relAngle = original.torsoAngle - RIDER_TORSO_REST; f.rider.lean = lean;
    const p = rider.physicsTarget(f), flexes = [];
    for (let degrees = -30; degrees <= 30; degrees += 5) {
      const flex = degrees * Math.PI / 180;
      const evaluate = hips => { resetHumanoidPose(rider.binding); rider.poseFromHips(f, p, hips, flex);
        return rider.toBike(measureAnthropometricCOM(rider, rider.anthropometry)); };
      const inverse = invertAnthropometricCOM(evaluate, p.requestedCOM, [p.hips.x, p.hips.y], 8); evaluate(inverse.hips);
      const gripM = [...rider.debug.gripErr], soleM = [...rider.debug.soleErr];
      flexes.push({ degrees, hips: inverse.hips, comResidualM: inverse.residualM, gripM, soleM,
        maxGapM: Math.max(...gripM, ...soleM), reach: [...rider.debug.armStretch, ...rider.debug.legStretch],
        pelvisQ: rider.bone(rider.role('pelvis')).quaternion.toArray() });
    }
    const best = [...flexes].sort((a,b)=>a.maxGapM-b.maxGapM)[0];
    rows.push({ lean, best, flexes });
  }
  candidates.push({ palmDegrees, maxGapM: Math.max(...rows.map(r=>r.best.maxGapM)), rows }); rider.dispose();
}
fs.writeFileSync(process.argv[4], JSON.stringify({ accepted: false, sourceSHA256: metadata.sourceSHA256, candidates },null,2)+'\n');
console.log(JSON.stringify(candidates.map(({palmDegrees,maxGapM,rows})=>({palmDegrees,maxGapM,rows:rows.map(({lean,best})=>({lean,degrees:best.degrees,gapM:best.maxGapM,gripM:best.gripM,soleM:best.soleM}))})),null,2));
