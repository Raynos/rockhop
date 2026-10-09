import { expect, it } from 'vitest';
import { Quaternion, Vector3 } from 'three';
import { selectedGripPositionBike } from './selected/rider.mjs';
import { RIDER_PROFILE } from '../../core/riderGeometry';

const driver = () => ({
  sideZ: { left: -1, right: 1 }, gripProfileHash: 'a'.repeat(64),
  gripSocketPositionBike: { left: [.251, .839, -.331], right: [.251, .839, .331] },
  gripSocketQuaternionBike: { left: [0, 0, 0, 1], right: [0, 0, 0, 1] },
});

it('keeps the existing bilateral carrier when no fitted profile is declared', () => {
  for (const [side, sign] of [['left', -1], ['right', 1]] as const) {
    expect(selectedGripPositionBike({ sideZ: { [side]: sign } }, side).toArray())
      .toEqual([RIDER_PROFILE.grip.x, RIDER_PROFILE.grip.y, sign * RIDER_PROFILE.grip.z]);
  }
});

it('uses the fitted palm location independently of the physical bar axis', () => {
  const profile = driver(), point = selectedGripPositionBike(profile, 'left');
  expect(point.distanceTo(new Vector3(RIDER_PROFILE.grip.x, RIDER_PROFILE.grip.y, -RIDER_PROFILE.grip.z))).toBeGreaterThan(.05);
  point.applyQuaternion(new Quaternion().setFromAxisAngle(new Vector3(0, 0, 1), .45));
  expect(profile.gripSocketPositionBike.left).toEqual([.251, .839, -.331]);
});

it('rejects an unpinned, partial or nonfinite fitted pose before it can reach the limb solver', () => {
  const missingPin = driver(); missingPin.gripProfileHash = '';
  expect(() => selectedGripPositionBike(missingPin, 'left')).toThrow('identity');
  const badOtherHand = driver(); badOtherHand.gripSocketPositionBike.right[1] = NaN;
  expect(() => selectedGripPositionBike(badOtherHand, 'left')).toThrow('right');
  const badRotation = driver(); badRotation.gripSocketQuaternionBike.right[3] = 2;
  expect(() => selectedGripPositionBike(badRotation, 'left')).toThrow('orientation');
});
