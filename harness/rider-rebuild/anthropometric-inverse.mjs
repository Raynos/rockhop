import { Quaternion, Vector3 } from 'three';

const vector = () => new Vector3();
const first = ids => Array.isArray(ids) ? ids[0] : ids;
const assert = (ok, message) => { if (!ok) throw new Error(`Rider anthropometry: ${message}`); };
const sides = ['left', 'right'];
const suffix = side => side === 'left' ? 'Left' : 'Right';

/** Segment mass proxy, explicitly approximate de Leva fractions on actual posed anatomy.
 * Native head/toe extents supply the endpoints; no generic stature/limb lengths.
 * Must calibrate once in source REST after the declared asset-to-bike placement.
 */
export function calibrateAnthropometry(rider, metadata) {
  assert(metadata.nativeRest?.frame === 'X-left,-Y-forward,Z-up', 'Declare the author native rest frame');
  const sourceByName = new Map(metadata.nativeRest.bones.map(row => [row.name, row]));
  const authoredNames = metadata.specification.jointNames;
  const placement = new Quaternion().fromArray(metadata.driver.assetToBikeQuaternionXYZW);
  const ends = new Map();
  const endpoint = id => {
    const row = sourceByName.get(authoredNames[id]); assert(row, `Missing actual native tail ${id}`);
    const nativeToBike = xyz => new Vector3(xyz[0], xyz[2], -xyz[1]).applyQuaternion(placement);
    const bone = rider.bone(id); bone.updateWorldMatrix(true, false);
    assert(bone.getWorldPosition(vector()).distanceTo(nativeToBike(row.head)) < 1e-5, `Native/export rest head changed ${id}`);
    ends.set(id, nativeToBike(row.tail).applyMatrix4(bone.matrixWorld.clone().invert()));
  };
  const head = first(rider.roles.head); endpoint(head);
  for (const side of sides) {
    endpoint(first(rider.roles['toe' + suffix(side)] ?? rider.roles['foot' + suffix(side)]));
    endpoint(rider.binding.contract.hands[side].digits.middle.at(-1));
  }
  return {
    head, ends, roles: rider.roles, hands: rider.binding.contract.hands,
    mass: { headNeck: 0.0694, trunk: 0.4346, upperArm: 0.0271, forearm: 0.0162, hand: 0.0061, thigh: 0.1416, shin: 0.0433, foot: 0.0137 },
    fraction: { trunk: 0.5, headNeck: 0.5, upperArm: 0.5772, forearm: 0.4574, hand: 0.5, thigh: 0.4095, shin: 0.4395, foot: 0.5 },
    approximation: 'Adult male segment mass fractions on measured joint centres/head and toe extents; not tissue-density integration',
  };
}

/** Return world COM proxy from the ACTUAL posed joint hierarchy and rigid extents. */
export function measureAnthropometricCOM(rider, calibration) {
  const point = id => rider.bone(id).getWorldPosition(vector());
  const tail = id => calibration.ends.get(id).clone().applyMatrix4(rider.bone(id).matrixWorld);
  const joint = role => point(first(calibration.roles[role]));
  const mean = points => points.reduce((sum, p) => sum.add(p), vector()).divideScalar(points.length);
  const hips = mean(sides.map(side => joint('thigh' + suffix(side))));
  const shoulders = mean(sides.map(side => joint('upperArm' + suffix(side))));
  const total = vector();
  const addSegment = (name, start, end) => total.addScaledVector(start.clone().lerp(end, calibration.fraction[name]), calibration.mass[name]);
  addSegment('trunk', hips, shoulders);
  addSegment('headNeck', shoulders, tail(calibration.head));
  for (const side of sides) {
    const s = suffix(side), shoulder = joint('upperArm' + s), elbow = joint('forearm' + s), wrist = joint('wrist' + s);
    const hip = joint('thigh' + s), knee = joint('shin' + s), ankle = joint('foot' + s);
    addSegment('upperArm', shoulder, elbow); addSegment('forearm', elbow, wrist);
    addSegment('hand', wrist, tail(calibration.hands[side].digits.middle.at(-1)));
    addSegment('thigh', hip, knee); addSegment('shin', knee, ankle);
    const toe = first(calibration.roles['toe' + s] ?? calibration.roles['foot' + s]);
    addSegment('foot', ankle, tail(toe));
  }
  assert(total.toArray().every(Number.isFinite), 'Nonfinite posed COM');
  return total;
}

/** Invert measured COM→hips at fixed torso articulation; physical COM is an input.
 * evaluate([hipX,hipY]) must start from a fresh full rest pose and return bike-frame COM.
 * Trust-region/backtracking bounds numerical steps, not visible anatomy/contact targets.
 */
export function invertAnthropometricCOM(evaluate, target, initial, maxIterations = 16) {
  let best = [...initial], bestError = Infinity, iterations = 0;
  const error = hips => {
    const com = evaluate(hips), residual = [target.x - com.x, target.y - com.y];
    assert(residual.every(Number.isFinite), 'Nonfinite inverse sample');
    return { com, residual, norm: Math.hypot(...residual) };
  };
  let sample = error(best);
  for (; iterations < maxIterations; iterations++) {
    if (sample.norm < bestError) bestError = sample.norm;
    if (sample.norm < 1e-6) break;
    const h = 1e-4, x = error([best[0] + h, best[1]]), y = error([best[0], best[1] + h]);
    const a = (x.com.x - sample.com.x) / h, b = (y.com.x - sample.com.x) / h;
    const c = (x.com.y - sample.com.y) / h, d = (y.com.y - sample.com.y) / h, determinant = a * d - b * c;
    if (Math.abs(determinant) < 1e-8) break;
    const step = [(d * sample.residual[0] - b * sample.residual[1]) / determinant,
      (-c * sample.residual[0] + a * sample.residual[1]) / determinant];
    const length = Math.hypot(...step), scale = length > 0.1 ? 0.1 / length : 1;
    let improved = false;
    for (let weight = scale; weight >= scale / 32; weight /= 2) {
      const candidate = best.map((value, k) => value + step[k] * weight), next = error(candidate);
      if (next.norm < sample.norm) { best = candidate; sample = next; improved = true; break; }
    }
    if (!improved) break;
  }
  const measured = error(best);
  return { hips: best, residualM: measured.norm, com: measured.com.toArray(), iterations, converged: measured.norm < 1e-5 };
}
