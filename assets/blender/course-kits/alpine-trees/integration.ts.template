/** A1 botanical trial. Phone source maps are the only staged tier.
 * Full/near prototypes are shared by all clusters and rendered as instances.
 * Source texture names resolve outside catalog hash folders at the fetch boundary.
 */
import * as THREE from 'three';
import type { GLTF } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { mergeGeometries } from 'three/examples/jsm/utils/BufferGeometryUtils.js';
import { modelAssetUrl, modelResourceUrl } from '../../hero/urls';
import { fogify } from '../../lighting/environment';

export const ALPINE_TREE_VARIANTS = [
  'pine-a', 'pine-b', 'pine-c', 'pine-young', 'fir-a', 'fir-b',
  'snag-a', 'snag-b', 'sapling-pine', 'sapling-fir',
] as const;
export type AlpineTreeVariant = typeof ALPINE_TREE_VARIANTS[number];
export interface AlpineTreePlacement {
  variant: AlpineTreeVariant;
  x: number;
  y: number;
  z: number;
  scale?: number;
  yaw?: number;
}
export const ALPINE_TREE_MODEL = 'models/course-kits/alpine-trees/trees.glb';
export const ALPINE_TREE_LOD_MODEL = 'models/course-kits/alpine-trees/trees-lod.glb';
const MAP_NAMES = new Set([
  'pine_bark-diffuse.phone.webp', 'pine_bark-nor_gl.phone.webp', 'pine_bark-arm.phone.webp',
  'fir_bark-diffuse.phone.webp', 'fir_bark-nor_gl.phone.webp', 'fir_bark-arm.phone.webp',
  'bark_willow_02-diffuse.phone.webp', 'bark_willow_02-nor_gl.phone.webp', 'bark_willow_02-arm.phone.webp',
  'cards-albedo.phone.webp', 'cards-normal.phone.webp', 'cards-arm.phone.webp',
  'impostor-albedo.phone.webp', 'impostor-normal.phone.webp',
]);
const FRAMES: Readonly<Record<AlpineTreeVariant, readonly [number, number, number]>> = {
  'pine-a': [14.09245033, 28.18490066, 0], 'pine-b': [9.78806854, 19.57613708, 1],
  'pine-c': [17.84098068, 35.68196136, 2], 'pine-young': [8.03162501, 16.06325003, 3],
  'fir-a': [12.63780035, 25.2756007, 4], 'fir-b': [15.75899981, 31.51799961, 5],
  'snag-a': [7.19680118, 14.39360235, 10], 'snag-b': [6.29700849, 12.59401697, 11],
  'sapling-pine': [2.94153269, 5.88306539, 12], 'sapling-fir': [2.97693439, 5.95386878, 13],
};
type Prototype = { geometry: THREE.BufferGeometry; material: THREE.MeshStandardMaterial };
type TreeBank = Map<string, Prototype>;
export interface AlpineTreeKit {
  cluster(placements: readonly AlpineTreePlacement[]): THREE.LOD;
  /** Permanent distant bank: shared atlas material, four triangles per tree, no full/near instances. */
  farCluster(placements: readonly AlpineTreePlacement[]): THREE.Group;
  release(): void;
  readonly prototypeBytes: number;
  readonly textureBytes: number;
}
export interface AlpineTreeLoadOptions {
  signal?: AbortSignal;
  /** Far-only loads two phone atlas maps and skips both model banks. */
  banks?: 'full-near' | 'far-only';
  /** Browser/store root including a trailing slash; defaults to Vite's relative base. */
  assetRoot?: string;
  /** Called once per shared material, before any cluster can draw. */
  completeMaterial?: (material: THREE.MeshStandardMaterial) => void;
  onError?: (error: unknown) => void;
}

/** Only the explicit map allowlist is redirected; model snapshots stay catalog URLs. */
export function alpineTreeResourceUrl(url: string, assetRoot: string): string {
  const parsed = new URL(url, assetRoot);
  const name = parsed.pathname.substring(parsed.pathname.lastIndexOf('/') + 1);
  if (!MAP_NAMES.has(name)) return url;
  return new URL(modelResourceUrl(`models/course-kits/alpine-trees/${name}`), assetRoot).href;
}

function expandedAttribute(attribute: THREE.BufferAttribute | THREE.InterleavedBufferAttribute): THREE.Float32BufferAttribute {
  const values = new Float32Array(attribute.count * attribute.itemSize);
  for (let i = 0; i < attribute.count; i++) {
    values[i * attribute.itemSize] = attribute.getX(i);
    if (attribute.itemSize > 1) values[i * attribute.itemSize + 1] = attribute.getY(i);
    if (attribute.itemSize > 2) values[i * attribute.itemSize + 2] = attribute.getZ(i);
  }
  return new THREE.Float32BufferAttribute(values, attribute.itemSize);
}

function crossGeometry(variant: AlpineTreeVariant): THREE.BufferGeometry {
  const [width, height, slot] = FRAMES[variant];
  const u0 = slot % 4 / 4, v0 = Math.floor(slot / 4) / 4;
  const positions: number[] = [], normals: number[] = [], uvs: number[] = [], indices: number[] = [];
  for (const angle of [0, Math.PI / 2]) {
    const base = positions.length / 3;
    for (const [x, y, u, v] of [[-width / 2, 0, u0, v0], [width / 2, 0, u0 + .25, v0],
      [width / 2, height, u0 + .25, v0 + .25], [-width / 2, height, u0, v0 + .25]]) {
      positions.push(x! * Math.cos(angle), y!, -x! * Math.sin(angle));
      normals.push(Math.sin(angle), 0, Math.cos(angle));
      uvs.push(u!, 1 - v!);
    }
    indices.push(base, base + 1, base + 2, base, base + 2, base + 3);
  }
  return new THREE.BufferGeometry().setAttribute('position', new THREE.Float32BufferAttribute(positions, 3))
    .setAttribute('normal', new THREE.Float32BufferAttribute(normals, 3))
    .setAttribute('uv', new THREE.Float32BufferAttribute(uvs, 2)).setIndex(indices);
}

/** CourseAssets-compatible wrapper; the parent supplies real ground-contact placements. */
export async function loadAlpineTreeCourse(
  clusters: readonly (readonly AlpineTreePlacement[])[],
  options: AlpineTreeLoadOptions = {},
): Promise<{ root: THREE.Group; textureBytes: number; dispose: () => void }> {
  const kit = await loadAlpineTreeKit(options);
  if (!kit) throw new Error('Alpine tree assets failed or were cancelled');
  try {
    if (options.signal?.aborted) { kit.release(); throw new Error('Alpine tree course was cancelled'); }
    const root = new THREE.Group(); root.name = 'alpine-authored-trees';
    for (const cluster of clusters) root.add(kit.cluster(cluster));
    return { root, textureBytes: kit.textureBytes, dispose: kit.release };
  } catch (error) {
    kit.release(); options.onError?.(error);
    throw error;
  }
}

/** Demand-load only for an A1 candidate view. An abort owns late loader resolutions. */
export async function loadAlpineTreeKit(options: AlpineTreeLoadOptions = {}): Promise<AlpineTreeKit | null> {
  if (options.signal?.aborted) return null;
  const assetRoot = options.assetRoot ?? new URL(import.meta.env.BASE_URL, document.baseURI).href;
  const manager = new THREE.LoadingManager().setURLModifier(url => alpineTreeResourceUrl(url, assetRoot));
  const failedResources = new Set<string>();
  manager.onError = url => { failedResources.add(url); };
  const geometries = new Set<THREE.BufferGeometry>();
  const materials = new Set<THREE.Material>();
  const textures = new Set<THREE.Texture>();
  const instances = new Set<THREE.InstancedMesh>();
  const sharedMaterials = new Map<string, THREE.MeshStandardMaterial>();
  const banks = new Map<'full' | 'near', TreeBank>();
  let released = false;
  let prototypeBytes = 0;
  const collectTexture = (material: THREE.MeshStandardMaterial): void => {
    for (const key of ['map', 'normalMap', 'roughnessMap', 'metalnessMap', 'aoMap'] as const) {
      const texture = material[key];
      if (texture) textures.add(texture);
    }
  };
  const ownDocument = (gltf: GLTF): void => {
    gltf.scene.traverse(object => {
      if (!(object instanceof THREE.Mesh)) return;
      geometries.add(object.geometry);
      for (const material of Array.isArray(object.material) ? object.material : [object.material]) {
        materials.add(material);
        collectTexture(material as THREE.MeshStandardMaterial);
      }
    });
  };
  const disposeOwned = (): void => {
    for (const mesh of instances) mesh.dispose();
    for (const geometry of geometries) geometry.dispose();
    for (const material of materials) material.dispose();
    const closed = new Set<unknown>();
    for (const texture of textures) {
      const image = texture.image as { close?: () => void } | undefined;
      texture.dispose();
      if (image?.close && !closed.has(image)) { closed.add(image); image.close(); }
    }
    instances.clear(); geometries.clear(); materials.clear(); textures.clear(); banks.clear(); sharedMaterials.clear();
  };
  const release = (): void => {
    released = true;
    options.signal?.removeEventListener('abort', release);
    disposeOwned();
  };
  options.signal?.addEventListener('abort', release, { once: true });
  try {
    // Far-only background banks avoid all model decoding and prototype allocations.
    if (options.banks !== 'far-only') {
      const [{ GLTFLoader }, { MeshoptDecoder }] = await Promise.all([
        import('three/examples/jsm/loaders/GLTFLoader.js'),
        import('three/examples/jsm/libs/meshopt_decoder.module.js'),
      ]);
      if (released) return null;
      const loader = new GLTFLoader(manager).setMeshoptDecoder(MeshoptDecoder);
      // Sequential parsing allows near/full material sharing and prompt cleanup after abort.
      for (const [level, logical] of [['near', ALPINE_TREE_LOD_MODEL], ['full', ALPINE_TREE_MODEL]] as const) {
        const gltf = await loader.loadAsync(new URL(modelAssetUrl(logical), assetRoot).href);
        ownDocument(gltf);
        if (released) { disposeOwned(); return null; }
        // GLTFLoader can resolve after an image fails, leaving a null source map.
        // Own the resolved document before rejecting so its partial resources retire.
        if (failedResources.size) throw new Error(`Alpine tree resources failed: ${[...failedResources].join(', ')}`);
        gltf.scene.updateMatrixWorld(true);
        const bank: TreeBank = new Map();
        gltf.scene.traverse(object => {
          if (!(object instanceof THREE.Mesh)) return;
          const source = object.material as THREE.MeshStandardMaterial;
          let material = sharedMaterials.get(source.name);
          if (!material) {
            material = source; sharedMaterials.set(source.name, material);
            fogify(material); options.completeMaterial?.(material);
          }
          const geometry = object.geometry.clone();
          // Expand only transformed attributes. Packed UV and vertex colours stay packed.
          geometry.setAttribute('position', expandedAttribute(geometry.getAttribute('position')));
          geometry.setAttribute('normal', expandedAttribute(geometry.getAttribute('normal')));
          geometry.applyMatrix4(object.matrixWorld); geometry.computeBoundingSphere();
          geometries.add(geometry);
          for (const attribute of Object.values(geometry.attributes) as (THREE.BufferAttribute | THREE.InterleavedBufferAttribute)[]) {
            prototypeBytes += attribute instanceof THREE.InterleavedBufferAttribute ? attribute.data.array.byteLength : attribute.array.byteLength;
          }
          prototypeBytes += geometry.index?.array.byteLength ?? 0;
          bank.set(object.name, { geometry, material });
        });
        for (const variant of ALPINE_TREE_VARIANTS) for (const part of ['bark', 'branches']) {
          if (!bank.has(`${variant}__${part}`)) throw new Error(`Missing Alpine ${level} prototype ${variant}__${part}`);
        }
        banks.set(level, bank);
      }
    }
    const textureLoader = new THREE.TextureLoader(manager);
    const farMap = await textureLoader.loadAsync(new URL('models/course-kits/alpine-trees/impostor-albedo.phone.webp', assetRoot).href);
    textures.add(farMap);
    if (released) { disposeOwned(); return null; }
    farMap.flipY = false; farMap.colorSpace = THREE.SRGBColorSpace;
    const farNormal = await textureLoader.loadAsync(new URL('models/course-kits/alpine-trees/impostor-normal.phone.webp', assetRoot).href);
    textures.add(farNormal);
    if (released) { disposeOwned(); return null; }
    farNormal.flipY = false;
    const farMaterial = fogify(new THREE.MeshStandardMaterial({ map: farMap, normalMap: farNormal,
      alphaTest: .45, roughness: .92, side: THREE.DoubleSide }));
    materials.add(farMaterial); options.completeMaterial?.(farMaterial);
    const farCluster = (placements: readonly AlpineTreePlacement[]): THREE.Group => {
      if (released) throw new Error('Alpine tree kit is released');
      const root = new THREE.Group(); root.name = 'alpine-far-bank';
      if (!placements.length) return root;
      const center = new THREE.Vector3();
      for (const p of placements) center.add(new THREE.Vector3(p.x, p.y, p.z));
      center.multiplyScalar(1 / placements.length); root.position.copy(center);
      const matrix = new THREE.Matrix4(), rotation = new THREE.Quaternion(), scale = new THREE.Vector3();
      const crosses = placements.map(p => {
        rotation.setFromAxisAngle(THREE.Object3D.DEFAULT_UP, p.yaw ?? 0); scale.setScalar(p.scale ?? 1);
        matrix.compose(new THREE.Vector3(p.x, p.y, p.z).sub(center), rotation, scale);
        return crossGeometry(p.variant).applyMatrix4(matrix);
      });
      const geometry = mergeGeometries(crosses, false);
      for (const cross of crosses) cross.dispose();
      if (!geometry) throw new Error('Alpine far cross attributes cannot merge');
      geometries.add(geometry); geometry.computeBoundingSphere();
      const mesh = new THREE.Mesh(geometry, farMaterial); mesh.name = 'alpine-far'; root.add(mesh);
      return root;
    };
    return {
      farCluster,
      get prototypeBytes() { return prototypeBytes; },
      textureBytes: (options.banks === 'far-only' ? 1.3333333333333333 : 6.333333333333333) * 1024 * 1024,
      release,
      cluster(placements) {
        if (released) throw new Error('Alpine tree kit is released');
        if (!banks.size) throw new Error('Alpine far-only kit has no full/near prototypes');
        const root = new THREE.LOD(); root.name = 'alpine-tree-cluster';
        if (!placements.length) return root;
        const center = new THREE.Vector3();
        for (const p of placements) center.add(new THREE.Vector3(p.x, p.y, p.z));
        center.multiplyScalar(1 / placements.length); root.position.copy(center);
        const matrix = new THREE.Matrix4(), rotation = new THREE.Quaternion(), scale = new THREE.Vector3();
        const placementMatrix = (p: AlpineTreePlacement): THREE.Matrix4 => {
          rotation.setFromAxisAngle(THREE.Object3D.DEFAULT_UP, p.yaw ?? 0); scale.setScalar(p.scale ?? 1);
          return matrix.compose(new THREE.Vector3(p.x, p.y, p.z).sub(center), rotation, scale);
        };
        for (const [level, distance] of [['full', 0], ['near', 26]] as const) {
          const group = new THREE.Group(); group.name = `alpine-${level}`;
          const variants = new Map<AlpineTreeVariant, AlpineTreePlacement[]>();
          for (const p of placements) variants.set(p.variant, [...(variants.get(p.variant) ?? []), p]);
          for (const [variant, entries] of variants) for (const part of ['bark', 'branches']) {
            const prototype = banks.get(level)!.get(`${variant}__${part}`)!;
            const mesh = new THREE.InstancedMesh(prototype.geometry, prototype.material, entries.length);
            instances.add(mesh); mesh.name = `alpine-${level}-${variant}-${part}`;
            entries.forEach((p, i) => mesh.setMatrixAt(i, placementMatrix(p)));
            mesh.instanceMatrix.needsUpdate = true; mesh.computeBoundingSphere();
            mesh.castShadow = level === 'full'; mesh.receiveShadow = true; group.add(mesh);
          }
          root.addLevel(group, distance, .08);
        }
        const far = farCluster(placements); far.position.sub(center);
        root.addLevel(far, 65, .08);
        return root;
      },
    };
  } catch (error) {
    release();
    if (!options.signal?.aborted) options.onError?.(error);
    return null;
  }
}
