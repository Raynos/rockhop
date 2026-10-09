import type { GltfRider } from '../gltfRider';
export function createSelectedRiderClass(metadata: unknown): typeof GltfRider;
export function selectedGripPositionBike(driver: {
  sideZ: Record<string, number>; gripProfileHash?: string;
  gripSocketPositionBike?: Record<string, number[]>;
  gripSocketQuaternionBike?: Record<string, number[]>;
}, side: string): import('three').Vector3;
