import type { Bone, Quaternion, Vector3 } from 'three';
import type { GltfRider } from '../gltfRider';
export function createSelectedRiderClass(metadata: unknown): typeof GltfRider;
export function selectedGripPositionBike(driver: {
  sideZ: Record<string, number>; gripProfileHash?: string;
  gripSocketPositionBike?: Record<string, number[]>;
  gripSocketQuaternionBike?: Record<string, number[]>;
}, side: string): Vector3;
type PronationBinding = {
  byId: Map<string, Bone>;
  rests: Map<string, { rotationXYZW: number[] }>;
};
type PronationCalibration = {
  wrist: string; restWrist: Quaternion;
  segments: { id: string; next: string; fraction: number }[];
};
export function calibrateSelectedForearmPronation(driver: {
  sideZ: Record<string, number>; gripProfileHash?: string;
  gripSocketPositionBike?: Record<string, number[]>;
  gripSocketQuaternionBike?: Record<string, number[]>;
  forearmPronation?: { schema: string; gripProfileHash: string };
}, binding: PronationBinding, chain: string[], wrist: string): PronationCalibration | null;
export function applySelectedForearmPronation(binding: PronationBinding,
  calibration: PronationCalibration, targetWristQ: Quaternion,
  tolerance?: number): { radians: number; singular: boolean };
