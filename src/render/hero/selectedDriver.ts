import type { GltfRider } from './gltfRider';

export let selectedRiderClass: typeof GltfRider | undefined;
let request: Promise<typeof GltfRider> | undefined;

/** The native rig and metadata load only when its selected model has loaded. */
export function loadSelectedRiderClass(): Promise<typeof GltfRider> {
  return request ??= import('./selected/loader.mjs').then(async module => selectedRiderClass = await module.loadSelectedRiderClass())
    .catch((error: unknown) => { request = undefined; throw error; });
}
