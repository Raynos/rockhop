/** UNACCEPTED private played test only. Call AFTER prepareHero + prepareHeroMaterials.
 * No production import; no GLB, rig, geometry, iris or skin mutation.
 */
import * as THREE from 'three';

export const SOURCE22_SHA256 = 'cc20ab813669b628c8e5d21596b655188d7188770adc374377cebf40769232ff';
export const CORNEAL_MATERIAL = 'Conservative transparent corneal film';
export const EXPECTED_CORNEAL_GEOMETRY = '1893dace98039de7b40087c4cbc8ba40b9b95f6dfec7ada808ceba29b1fd9eca';

/** One isolated material replacement; caller must verify mapped source SHA and geometry hash first.
 * The geometry hash comes from audit_runtime.mts (524 render verts / 980 triangles after merge).
 * Renderer-local materials alone cannot bypass prepareHero safely, hence post-load private use.
 */
export function restoreNativeCorneaForPrivateTrial(
  root: THREE.Object3D,
  proof: { sourceSHA256: string; geometrySHA256: string },
): { material: THREE.MeshPhysicalMaterial; meshes: string[]; undo: () => void } {
  if (proof.sourceSHA256 !== SOURCE22_SHA256 || proof.geometrySHA256 !== EXPECTED_CORNEAL_GEOMETRY)
    throw new Error('Private optics24 requires frozen source22 and measured corneal geometry');
  const targets: THREE.Mesh[] = [];
  root.traverse(o => {
    const m = o as THREE.Mesh;
    if (!m.isMesh) return;
    const mats = Array.isArray(m.material) ? m.material : [m.material];
    if (mats.some(s => s.name === CORNEAL_MATERIAL)) targets.push(m);
  });
  if (targets.length !== 1) throw new Error('Expected exactly one merged corneal mesh, no global material matching');
  const mesh = targets[0]!;
  if (Array.isArray(mesh.material)) throw new Error('Cornea must be an isolated one-material mesh');
  const original = mesh.material as THREE.MeshStandardMaterial;
  if (!original.isMeshStandardMaterial || mesh.geometry.getAttribute('position').count !== 524 || mesh.geometry.index?.count !== 2940)
    throw new Error('Corneal geometry/material census differs from frozen CPU audit');
  if (original.opacity !== .035 || original.alphaTest !== .5 || original.transparent || !original.depthWrite || original.roughness !== .08)
    throw new Error('Apply optics24 only to measured post-prepareHero corneal flags');
  const physical = new THREE.MeshPhysicalMaterial();
  // Copy only the standard subset; MeshPhysicalMaterial.copy expects another physical material.
  THREE.MeshStandardMaterial.prototype.copy.call(physical, original);
  // Standard.copy resets defines and Material.copy omits compile hooks: restore both explicitly.
  physical.defines = { STANDARD: '', PHYSICAL: '' };
  physical.onBeforeCompile = original.onBeforeCompile;
  physical.customProgramCacheKey = original.customProgramCacheKey;
  physical.name = 'UNACCEPTED optics24 actual native cornea thin-film diagnostic';
  physical.opacity = 1;
  physical.alphaTest = 0;
  physical.transparent = true;
  physical.depthWrite = false;
  physical.side = THREE.FrontSide; // Authored donor side, not the body's runtime DoubleSide override.
  physical.transmission = 1;
  physical.thickness = 0; // Thin-film approximation, no invented eyeball volume or absorption distance.
  physical.ior = 1.5; // Three's default dielectric, not a measured anatomical corneal IOR.
  physical.attenuationDistance = Infinity;
  physical.attenuationColor.setRGB(1, 1, 1);
  physical.clearcoat = 0;
  physical.metalness = 0;
  physical.roughness = .08; // Retained authored corneal roughness; no parameter sweep.
  physical.needsUpdate = true;
  mesh.material = physical;
  return {material:physical,meshes:[mesh.name],undo:()=>{mesh.material=original;physical.dispose();}};
}
