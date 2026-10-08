/** Proposed narrow Garage integration. Parent decides whether/where to import it.
 * No surface reads, optimizer, asset replacement, or per-frame geometry scans.
 */
import { resetHumanoidPose } from '../../../../harness/rider-rebuild/new-humanoid-contract.mjs';
const check = (ok, why) => { if (!ok) throw new Error(`Authored Garage: ${why}`); };

export function prepareAuthoredGaragePose(rider, receipt, bikeName) {
  check(receipt.pins.rider.sha256 === rider.debug.candidate.sourceSHA256, 'Selected source hash changed');
  const selected = receipt.bikes.find(row => row.name === bikeName);
  check(selected && selected.status === 'UNACCEPTED_NUMERICAL_CANDIDATE', 'Failed authoring may not silently replace the Garage pose');
  check(JSON.stringify(selected.frames.soles) === JSON.stringify(rider.driver.selectedPegSurfaceBike)
    && JSON.stringify(selected.frames.soleInFoot) === JSON.stringify(rider.driver.selectedSoleInFoot)
    && JSON.stringify(selected.frames.soleRotationXYZW) === JSON.stringify(rider.driver.soleQuaternionBike), 'Measured sole calibration changed');
  for (const palm of selected.frames.palms) check(palm.rotationXYZW.every((v, i) =>
    v === rider.handTargets.get(palm.side).toArray()[i]), 'Calibrated palm orientation changed');
  const control = [...selected.controls];
  check(control.length === 4 && control.every(Number.isFinite), 'Invalid authored controls');
  return frame => {
    check(rider.stage && rider.bike && !rider.clip, 'Authored candidate is Garage-only with original selected rig');
    resetHumanoidPose(rider.binding);
    rider.bike.frame.updateMatrixWorld(true);
    const p = rider.physicsTarget(frame);
    p.torsoAngle = control[2]; p.headAngle = selected.headAngleRadians;
    const breath = selected.breathingRadians * Math.sin(rider.stageTime * 2);
    rider.poseFromHips(frame, p, control.slice(0, 2), control[3] + breath);
    rider.bike.frame.updateMatrixWorld(true);
    return { accepted: false, bike: bikeName, controls: control, breathingRadians: breath,
      source: 'selected-seated-author04', stance: 'Authored candidate; moving art remains unaccepted' };
  };
}
