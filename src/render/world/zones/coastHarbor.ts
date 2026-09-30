/** Offline authored Coast candidate. Parent owns hooks and original-item fallback.
 * No decoding occurs until loadCoastHarbor is invoked for a played course.
 */
import * as THREE from 'three';
import { GLTFLoader, type GLTF } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { MeshoptDecoder } from 'three/examples/jsm/libs/meshopt_decoder.module.js';
import type { CourseAssetDelivery } from '../courseAssets';
import { modelAssetUrl, modelResourceUrl } from '../../hero/urls';
import type { PropBatch } from '../props';
import { fogify } from '../../lighting/environment';

export const COAST_HARBOR_VARIANTS = ['cargo-freighter', 'cargo-barge', 'harbor-crane',
  'loading-pier', 'open-warehouse', 'logistics-yard', 'dock-station'] as const;
export type CoastHarborVariant = typeof COAST_HARBOR_VARIANTS[number];
export interface CoastHarborPlacement {
  variant: CoastHarborVariant;
  x: number; y: number; z: number;
  scale?: number; yaw?: number;
}
export interface CoastHarborOptions {
  /** Phone uses only the authored LOD bank, never desktop plus LOD together. */
  detail?: 'full' | 'lod';
  assetRoot?: string;
  signal?: AbortSignal;
  completeMaterial?: (material: THREE.MeshStandardMaterial) => void;
  /** Source-only candidate can use its authoring server before catalog staging. */
  resolveModel?: (logicalPath: string) => string;
  resolveResource?: (logicalPath: string) => string;
}
export const COAST_HARBOR_MAPS = ['coast-albedo.phone.webp', 'coast-normal.phone.webp', 'coast-arm.phone.webp'] as const;
const PREFIX = 'models/course-kits/coast-harbor/';
const MAPS = new Set<string>(COAST_HARBOR_MAPS);
const TEXTURE_KEYS = ['map', 'normalMap', 'roughnessMap', 'metalnessMap', 'aoMap', 'emissiveMap'] as const;

export function coastHarborResourceUrl(url: string, root: string,
  resolve: (logicalPath: string) => string = modelResourceUrl): string {
  const parsed = new URL(url, root);
  const name = parsed.pathname.slice(parsed.pathname.lastIndexOf('/') + 1);
  return MAPS.has(name) ? new URL(resolve(PREFIX + name), root).href : url;
}

/** Deliberate C1 terminals; no ZoneCtx.rng calls and no replacement side effects.
 * Tall near masses stay outside x180–260, the brake/landing reading window.
 * Ground contact belongs to the authoritative zoneGround callback.
 */
export function planC1Harbor(groundAt: (x: number, z: number) => number, seaY: number): CoastHarborPlacement[] {
  const placements: CoastHarborPlacement[] = [];
  const add = (variant: CoastHarborVariant, x: number, z: number, scale = 1, yaw = 0): void => {
    const wet = variant === 'cargo-freighter' || variant === 'cargo-barge';
    const y = wet ? seaY : variant === 'loading-pier' || variant === 'harbor-crane' ? seaY + 2.6 : groundAt(x, z);
    placements.push({ variant, x, y, z, scale, yaw });
  };
  for (const [x, z, scale, yaw] of [[40,-65,.90,.04],[137,-77,1,-.055],[313,-68,.94,.05],[433,-92,1.04,-.08]] as const)
    add('cargo-freighter', x, z, scale, yaw);
  // A low far-water vessel fills the protected window without a near mass.
  add('cargo-freighter',236,-118,.74,.035);
  for (const [x,z,scale,yaw] of [[64,-30,.72,.06],[330,-34,.68,-.04],[473,-55,.82,.03]] as const)
    add('cargo-barge',x,z,scale,yaw);
  for (const [x,z,scale] of [[28,-47,.82],[126,-51,.88],[306,-47,.82],[411,-53,.9]] as const) {
    add('loading-pier',x,z,scale); add('harbor-crane',x-4*scale,z+scale,scale);
  }
  for (const [x,scale] of [[32,.64],[109,.68],[282,.62],[370,.68],[450,.60]] as const)
    add('open-warehouse',x,-9.8,scale);
  for (const [x,z,scale,yaw] of [[8,-12,.7,.03],[61,-12,.67,-.04],[92,-12,.62,.04],
    [146,-12,.67,-.05],[276,-12,.6,.04],[316,-12,.63,-.03],[345,-12,.6,.035],
    [403,-12,.66,-.04],[477,-12,.6,.02]] as const) add('logistics-yard',x,z + 2.2,scale,yaw);
  for (const x of [23,49,78,103,143,165,274,298,331,359,392,423,461,489])
    add('dock-station',x,-5.8,.72,x%2 ? .06 : -.08);
  for (const x of [31,79,132,278,337,391,455,484]) add('dock-station',x,7.4,.65,.08);
  return placements;
}

type Part = { geometry: THREE.BufferGeometry; material: THREE.MeshStandardMaterial };
/** Instancing groups span 64 metres. Repeated actors share prototype geometry,
 * material and images; per-group instance buffers and bounds are the only copies.
 */
export async function loadCoastHarbor(placements: readonly CoastHarborPlacement[], options: CoastHarborOptions = {}): Promise<CourseAssetDelivery> {
  const root = new THREE.Group(); root.name = 'coast-authored-harbor';
  const geometries = new Set<THREE.BufferGeometry>();
  const materials = new Set<THREE.Material>();
  const textures = new Set<THREE.Texture>();
  const instances = new Set<THREE.InstancedMesh>();
  const failed = new Set<string>();
  let retired = false;
  const clearOwned = (): void => {
    root.clear();
    for (const mesh of instances) mesh.dispose();
    for (const geometry of geometries) geometry.dispose();
    for (const material of materials) material.dispose();
    const closed = new Set<unknown>();
    for (const texture of textures) {
      texture.dispose();
      const image = texture.image as { close?: () => void } | undefined;
      if (image?.close && !closed.has(image)) { closed.add(image); image.close(); }
    }
    instances.clear(); geometries.clear(); materials.clear(); textures.clear();
  };
  const dispose = (): void => {
    retired = true; options.signal?.removeEventListener('abort', dispose); clearOwned();
  };
  const own = (gltf: GLTF): void => {
    gltf.scene.traverse(object => {
      if (!(object instanceof THREE.Mesh)) return;
      geometries.add(object.geometry);
      for (const source of Array.isArray(object.material) ? object.material : [object.material]) {
        materials.add(source);
        for (const key of TEXTURE_KEYS) {
          const map = (source as THREE.MeshStandardMaterial)[key];
          if (map) textures.add(map); // before completeMaterial introduces library neutral maps
        }
      }
    });
  };
  try {
    if (options.signal?.aborted) throw new Error('Coast harbor cancelled');
    options.signal?.addEventListener('abort', dispose, { once: true });
    const assetRoot = options.assetRoot ?? new URL(import.meta.env.BASE_URL, document.baseURI).href;
    const manager = new THREE.LoadingManager().setURLModifier(url => coastHarborResourceUrl(url, assetRoot, options.resolveResource ?? modelResourceUrl));
    manager.onError = url => { failed.add(url); };
    if (retired) throw new Error('Coast harbor cancelled');
    const logical = PREFIX + (options.detail === 'full' ? 'coast-harbor.glb' : 'coast-harbor-lod.glb');
    const gltf = await new GLTFLoader(manager).setMeshoptDecoder(MeshoptDecoder)
      .loadAsync(new URL((options.resolveModel ?? modelAssetUrl)(logical), assetRoot).href);
    own(gltf); // late resolved resources are owned even if abort already cleared earlier resources
    if (retired) throw new Error('Coast harbor cancelled');
    if (failed.size) throw new Error(`Coast harbor required resources failed: ${[...failed].join(', ')}`);
    const bank = new Map<CoastHarborVariant, Part[]>();
    gltf.scene.updateMatrixWorld(true);
    for (const prototype of gltf.scene.children) {
      if (!(COAST_HARBOR_VARIANTS as readonly string[]).includes(prototype.name)) throw new Error(`Unknown Coast prototype: ${prototype.name}`);
      const parts: Part[] = [];
      prototype.traverse(object => {
        if (!(object instanceof THREE.Mesh)) return;
        if (Array.isArray(object.material)) throw new Error('Coast primitives must have one material');
        const material = object.material as THREE.MeshStandardMaterial;
        if (!material.isMeshStandardMaterial) throw new Error('Coast model requires PBR materials');
        if (material.name === 'coast manufactured PBR atlas' && (!material.map || !material.normalMap || !material.roughnessMap || !material.metalnessMap))
          throw new Error('Coast required PBR map missing');
        // Packed normals are normalized bytes. Expand only transformed position/normal,
        // preserving UV and other untouched arrays; every prototype is transformed once.
        const geometry = object.geometry;
        for (const name of ['position', 'normal']) {
          const attr = geometry.getAttribute(name);
          if (!attr) throw new Error(`Coast missing ${name}`);
          if (!(attr.array instanceof Float32Array) || attr.isInterleavedBufferAttribute) {
            const values = new Float32Array(attr.count * 3);
            for (let i = 0; i < attr.count; i++) values.set([attr.getX(i), attr.getY(i), attr.getZ(i)], i * 3);
            geometry.setAttribute(name, new THREE.Float32BufferAttribute(values, 3));
          }
        }
        geometry.applyMatrix4(object.matrixWorld); geometry.computeBoundingBox(); geometry.computeBoundingSphere();
        const positions = geometry.getAttribute('position');
        for (let i = 0; i < positions.count; i++) if (![positions.getX(i), positions.getY(i), positions.getZ(i)].every(Number.isFinite)) throw new Error('Coast nonfinite position');
        parts.push({ geometry, material });
      });
      if (!parts.length) throw new Error(`Empty Coast prototype: ${prototype.name}`);
      bank.set(prototype.name as CoastHarborVariant, parts);
    }
    for (const variant of COAST_HARBOR_VARIANTS) if (!bank.has(variant)) throw new Error(`Missing Coast prototype: ${variant}`);
    for (const source of materials) { const material = source as THREE.MeshStandardMaterial; fogify(material); options.completeMaterial?.(material); }
    const groups = new Map<string, CoastHarborPlacement[]>();
    for (const placement of placements) {
      if (![placement.x,placement.y,placement.z,placement.scale ?? 1,placement.yaw ?? 0].every(Number.isFinite) || (placement.scale ?? 1) <= 0)
        throw new Error('Invalid Coast placement');
      const key = `${Math.floor(placement.x / 64)}:${placement.variant}`;
      groups.set(key, [...(groups.get(key) ?? []), placement]);
    }
    const transform = new THREE.Object3D();
    for (const [key,group] of groups) {
      const parts = bank.get(group[0]!.variant);
      if (!parts) throw new Error(`Coast variant missing: ${group[0]!.variant}`);
      for (const [index,part] of parts.entries()) {
        const mesh = new THREE.InstancedMesh(part.geometry, part.material, group.length);
        mesh.name = `coast-harbor:${key}:${index}`; // unrecognised by WORLD_MESH => mid/far no shadow-map draws
        mesh.castShadow = false; mesh.receiveShadow = true;
        for (const [i,p] of group.entries()) {
          transform.position.set(p.x,p.y,p.z); transform.rotation.set(0,p.yaw ?? 0,0); transform.scale.setScalar(p.scale ?? 1); transform.updateMatrix(); mesh.setMatrixAt(i,transform.matrix);
        }
        mesh.instanceMatrix.needsUpdate = true; mesh.computeBoundingBox(); mesh.computeBoundingSphere(); instances.add(mesh); root.add(mesh);
      }
    }
    const images = new Set<unknown>(); let textureBytes = 0;
    for (const texture of textures) {
      const image = texture.image as { width?: number; height?: number } | undefined;
      if (image && !images.has(image)) { images.add(image); textureBytes += (image.width ?? 0) * (image.height ?? 0) * 4 * 4 / 3; }
    }
    return { root, textureBytes, dispose };
  } catch (error) { dispose(); throw error; }
}

/** Retain actual hero-window items; the parent builds removed items as fallback. */
export function removeC1HarborPlaceholders(batches: readonly PropBatch[]): void {
  const replaced = new Set(['container','container-far','pallet','tyres','tyreflat',
    'drum','buoy','buoylying','bollard','rope','net','scrap0','scrap1','trucktyre',
    'pierdeck','pile','quay','crane','crane-rust','hull','hull-near',
    'c1-inshore-coaster','c1-quay-warehouse','c1-loading-bay','c1-quay-hoist','contactshadow']);
  for (const batch of batches) if (replaced.has(batch.name)) {
    const kept = batch.items.filter(item => {
      const x = item.m.elements[12]!;
      // Keep the near brake/landing props; retire generic far-water hulls.
      return x >= 180 && x <= 260 && item.m.elements[14]! > -15;
    });
    batch.items.splice(0,batch.items.length,...kept);
  }
}
