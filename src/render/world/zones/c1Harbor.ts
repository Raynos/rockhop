/** C1 Low Tide's authored tug. The renderer owns async mounting and cancellation. */
import type * as THREE from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { MeshoptDecoder } from 'three/examples/jsm/libs/meshopt_decoder.module.js';
import type { MaterialLibrary } from '../../materials/library';
import { fogify } from '../../lighting/environment';
import { modelAssetUrl } from '../../hero/urls';

export interface C1HarborAsset {
  /** Local keel origin; place at seaY−1.25×scale to align its waterline. */
  root: THREE.Group;
  /** Resident image memory estimate. Shared neutral library maps are excluded. */
  textureBytes: number;
  /** Parent calls only after material link retirement or a canceled late load. */
  dispose(): void;
}

/** Load the four-draw Meshopt GLB without hero-rig preparation or world ownership. */
export async function loadC1Harbor(detail: 'full' | 'lod', lib: MaterialLibrary): Promise<C1HarborAsset> {
  const file = detail === 'lod' ? 'models/c1-harbor-tug-lod.glb' : 'models/c1-harbor-tug.glb';
  const gltf = await new GLTFLoader().setMeshoptDecoder(MeshoptDecoder).loadAsync(modelAssetUrl(file));
  const root = gltf.scene;
  root.name = 'c1:authored-working-tug';
  const geometries = new Set<THREE.BufferGeometry>();
  const materials = new Set<THREE.Material>();
  const ownedMaps = new Set<THREE.Texture>();
  let textureBytes = 0;
  let disposed = false;
  const dispose = (): void => {
    if (disposed) return;
    disposed = true;
    for (const g of geometries) g.dispose();
    for (const m of materials) m.dispose();
    // GLTFLoader may decode an embedded map to ImageBitmap. Texture.dispose()
    // releases its GPU upload, while the bitmap's decoded pixels need close().
    const closed = new Set<unknown>();
    for (const t of ownedMaps) {
      const image = t.image as { close?: () => void } | undefined;
      t.dispose();
      if (image?.close && !closed.has(image)) { closed.add(image); image.close(); }
    }
    root.clear();
  };
  try {
    root.traverse((o) => {
      const mesh = o as THREE.Mesh;
      if (!mesh.isMesh) return;
      geometries.add(mesh.geometry);
      for (const m of Array.isArray(mesh.material) ? mesh.material : [mesh.material]) {
        if (!m) continue;
        materials.add(m);
        const std = m as THREE.MeshStandardMaterial;
        if (!std.isMeshStandardMaterial) continue;
        if (std.map && !ownedMaps.has(std.map)) {
          ownedMaps.add(std.map); // captured before complete() attaches shared neutral maps
          const img = std.map.image as { width?: number; height?: number } | undefined;
          textureBytes += (img?.width ?? 0) * (img?.height ?? 0) * 4 * 1.33;
        }
        fogify(std);
        lib.complete(std);
      }
      mesh.castShadow = false; // midground model never adds a shadow-map draw
      mesh.receiveShadow = true;
    });
  } catch (error) {
    dispose();
    throw error;
  }
  return { root, textureBytes, dispose };
}
