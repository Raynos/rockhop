/** Unaccepted, reversible played diagnostic. Never imported by production. */
import * as THREE from 'three';
export const SOURCE22_SHA256 = 'cc20ab813669b628c8e5d21596b655188d7188770adc374377cebf40769232ff';
export const EYE_MATERIAL = 'CC0 brown iris and sclera';
export const EXPECTED_EYE_GEOMETRY = 'a6ba58aa72d3da5fd0b31cb9e1c9af5cd3faa6055400f8647f74cf0ce9320f4a';
export function coatOpaqueEyesForPrivateTrial(root: THREE.Object3D,
  proof: {sourceSHA256: string; geometrySHA256: string}) {
  if (proof.sourceSHA256 !== SOURCE22_SHA256 || proof.geometrySHA256 !== EXPECTED_EYE_GEOMETRY)
    throw new Error('Eye29 requires frozen22 source and merged eye geometry');
  const targets: THREE.Mesh[] = [];
  root.traverse(o => {
    const m = o as THREE.Mesh;
    if (m.isMesh && !Array.isArray(m.material) && m.material.name === EYE_MATERIAL) targets.push(m);
  });
  if (targets.length !== 1) throw new Error('Expected one isolated merged opaque-eye mesh');
  const mesh = targets[0]!;
  const original = mesh.material as THREE.MeshStandardMaterial;
  if (!original.isMeshStandardMaterial || original.transparent || original.opacity !== 1 ||
      original.roughness !== .35 || original.metalness !== 0 ||
      mesh.geometry.getAttribute('position').count !== 552 || mesh.geometry.index?.count !== 3180)
    throw new Error('Opaque eye census differs from measured prepared22');
  const physical = new THREE.MeshPhysicalMaterial();
  THREE.MeshStandardMaterial.prototype.copy.call(physical, original);
  physical.defines = {STANDARD: '', PHYSICAL: ''};
  physical.onBeforeCompile = original.onBeforeCompile;
  physical.customProgramCacheKey = original.customProgramCacheKey;
  physical.name = 'UNACCEPTED29 opaque eye reflective coat';
  physical.clearcoat = 1;
  physical.clearcoatRoughness = .08; // Original authored corneal roughness; one fixed test.
  physical.transmission = 0;
  physical.needsUpdate = true;
  mesh.material = physical;
  return {material: physical, mesh, undo: () => {mesh.material = original; physical.dispose();}};
}
