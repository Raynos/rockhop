import { expect, it } from 'vitest';
import { Bone, Group, Quaternion, Vector3 } from 'three';
import { applySelectedForearmPronation, calibrateSelectedForearmPronation } from './selected/rider.mjs';

const axis = new Vector3(.3, .8, -.2).normalize();
const transverse = new Vector3().crossVectors(axis, new Vector3(1, 0, 0)).normalize();
const profile = () => ({
  sideZ: { left: -1, right: 1 }, gripProfileHash: 'a'.repeat(64),
  gripSocketPositionBike: { left: [.25, .84, -.33], right: [.25, .84, .33] },
  gripSocketQuaternionBike: { left: [0, 0, 0, 1], right: [0, 0, 0, 1] },
  forearmPronation: { schema: 'native-segment-twist-v1', gripProfileHash: 'a'.repeat(64) },
});
function fixture(sign = 1) {
  const root = new Group(), proximal = new Bone(), distal = new Bone(), wrist = new Bone(), digit = new Bone();
  root.add(proximal); proximal.add(distal); distal.add(wrist); wrist.add(digit);
  root.quaternion.setFromAxisAngle(new Vector3(1, 2, 3).normalize(), .7);
  root.position.set(3, -5, 2); root.scale.setScalar(1.3);
  proximal.position.set(.1, .4, -.3);
  proximal.quaternion.setFromAxisAngle(transverse, -.4);
  distal.position.copy(axis).multiplyScalar(.1);
  wrist.position.copy(axis).multiplyScalar(.3);
  wrist.quaternion.setFromAxisAngle(transverse, sign * .23);
  digit.position.set(.01, .07, -.02); digit.quaternion.setFromAxisAngle(axis, .8);
  const byId = new Map([['proximal', proximal], ['distal', distal], ['wrist', wrist], ['digit', digit]]);
  const rests = new Map([...byId].map(([id, bone]) => [id, { translation: bone.position.toArray(), rotationXYZW: bone.quaternion.toArray(), scale: bone.scale.toArray() }]));
  root.updateWorldMatrix(true, true);
  const binding = { byId, rests }, calibration = calibrateSelectedForearmPronation(profile(), binding, ['proximal', 'distal'], 'wrist')!;
  return { root, proximal, distal, wrist, digit, binding, calibration };
}
const angularError = (a: Quaternion, b: Quaternion) => 2 * Math.acos(Math.min(1, Math.abs(a.dot(b))));

it('leaves undeclared production and fitted profiles unchanged and rejects a mismatched opt-in', () => {
  const f = fixture(), before = f.proximal.matrixWorld.toArray(), driver = profile();
  expect(calibrateSelectedForearmPronation({ sideZ: {} }, f.binding, [], 'absent')).toBeNull();
  const { forearmPronation: _declaration, ...unqualified } = driver;
  expect(calibrateSelectedForearmPronation(unqualified, f.binding, [], 'absent')).toBeNull();
  driver.forearmPronation.gripProfileHash = 'b'.repeat(64);
  expect(() => calibrateSelectedForearmPronation(driver, f.binding, ['proximal', 'distal'], 'wrist')).toThrow('exact fitted');
  expect(f.proximal.matrixWorld.toArray()).toEqual(before);
});

it.each([-1, 1])('transfers signed axial rotation to native segments while preserving the complete hand (%s)', sign => {
  const f = fixture(sign), { proximal, distal, wrist, digit, binding, calibration } = f;
  expect(calibration.segments[0]!.fraction).toBeCloseTo(.25, 12);
  expect(calibration.segments[1]!.fraction).toBe(1);
  const base = distal.getWorldQuaternion(new Quaternion()).normalize();
  const swing = new Quaternion().setFromAxisAngle(transverse, .4);
  const target = base.clone().multiply(new Quaternion().setFromAxisAngle(axis, sign * 1.2)).multiply(swing).multiply(calibration.restWrist);
  wrist.quaternion.copy(base.clone().invert().multiply(target));
  wrist.updateWorldMatrix(false, true);
  const positions = [proximal, distal, wrist, digit].map(bone => bone.getWorldPosition(new Vector3()));
  const digitQ = digit.getWorldQuaternion(new Quaternion()).normalize(), digitLocal = digit.quaternion.toArray();
  const result = applySelectedForearmPronation(binding, calibration, target);
  expect(result.radians).toBeCloseTo(sign * 1.2, 12); expect(result.singular).toBe(false);
  [proximal, distal, wrist, digit].forEach((bone, i) => expect(bone.getWorldPosition(new Vector3()).distanceTo(positions[i]!)).toBeLessThan(1e-12));
  expect(angularError(wrist.getWorldQuaternion(new Quaternion()).normalize(), target)).toBeLessThan(5e-8);
  expect(angularError(digit.getWorldQuaternion(new Quaternion()).normalize(), digitQ)).toBeLessThan(5e-8);
  expect(digit.quaternion.toArray()).toEqual(digitLocal);
  const residual = wrist.quaternion.clone().multiply(calibration.restWrist.clone().invert());
  expect(Math.abs(new Vector3(residual.x, residual.y, residual.z).dot(axis))).toBeLessThan(1e-12);
  expect(angularError(residual, swing)).toBeLessThan(5e-8);
  for (const [id, bone] of binding.byId) {
    expect(bone.position.toArray()).toEqual(binding.rests.get(id)!.translation);
    expect(bone.scale.toArray()).toEqual(binding.rests.get(id)!.scale);
  }
});

it('is independent of quaternion sign, global orientation and a full native reset', () => {
  const f = fixture(), { binding, calibration } = f;
  const target = f.distal.getWorldQuaternion(new Quaternion()).normalize()
    .multiply(new Quaternion().setFromAxisAngle(axis, 1.1)).multiply(calibration.restWrist);
  const first = applySelectedForearmPronation(binding, calibration, target);
  const expected = [...binding.byId.values()].map(b => b.quaternion.toArray());
  for (const [id, bone] of binding.byId) bone.quaternion.fromArray(binding.rests.get(id)!.rotationXYZW);
  f.root.updateWorldMatrix(true, true);
  const negated = new Quaternion(-target.x, -target.y, -target.z, -target.w);
  expect(applySelectedForearmPronation(binding, calibration, negated).radians).toBeCloseTo(first.radians, 12);
  [...binding.byId.values()].forEach((b, i) => expect(angularError(b.quaternion, new Quaternion().fromArray(expected[i]!))).toBeLessThan(5e-8));
});

it('retains a finite aimed forearm when transverse 180-degree swing has undefined twist', () => {
  const f = fixture(), before = f.proximal.getWorldQuaternion(new Quaternion()).normalize();
  const target = f.distal.getWorldQuaternion(new Quaternion()).normalize()
    .multiply(new Quaternion().setFromAxisAngle(transverse, Math.PI)).multiply(f.calibration.restWrist);
  expect(applySelectedForearmPronation(f.binding, f.calibration, target)).toEqual({ radians: 0, singular: true });
  expect(angularError(f.proximal.getWorldQuaternion(new Quaternion()).normalize(), before)).toBeLessThan(5e-8);
  expect(f.wrist.matrixWorld.elements.every(Number.isFinite)).toBe(true);
});

it('rejects bent or disconnected native forearm declarations before posing', () => {
  const f = fixture(); f.wrist.position.x += .1; f.root.updateWorldMatrix(true, true);
  expect(() => calibrateSelectedForearmPronation(profile(), f.binding, ['proximal', 'distal'], 'wrist')).toThrow('collinear');
  expect(() => calibrateSelectedForearmPronation(profile(), f.binding, ['proximal'], 'wrist')).toThrow('actual connected');
});
