/**
 * Candidate whole-Coast art kit for C1–C3. This leaf is deliberately not wired
 * into biomeKit: the old zone must finish its shared RNG calls before these
 * named families are replaced. See docs/evidence/course-remaster/coast-standard.
 */
import * as THREE from 'three';
import type { CompiledTrack } from '../../../core/types';
import type { MaterialLibrary } from '../../materials/library';
import { fogify } from '../../lighting/environment';
import { PropBatch, type WorldDetail } from '../props';
import * as G from './geo';

export type CoastTrackId = 'c1-low-tide' | 'c2-crane-hop' | 'c3-hull-breach';
export type CoastLandmarkKind = 'freighter' | 'barge' | 'salvage' | 'crane' | 'warehouse';

export interface CoastLandmark {
  kind: CoastLandmarkKind;
  x: number;
  z: number;
  scale: number;
  yaw: number;
}

export interface CoastStandardPlan {
  id: CoastTrackId;
  seed: number;
  x0: number;
  x1: number;
  seaY: number;
  landmarks: readonly CoastLandmark[];
  /** No scatter/large mass may enter the first-phone brake, jump, or breach views. */
  keepouts: readonly (readonly [number, number])[];
}

export interface CoastStandardOptions {
  lib: MaterialLibrary;
  detail: WorldDetail;
  /** Same callback used by the old ZoneKit; the deck/obstacles remain authoritative. */
  groundAt: (x: number, z: number) => number;
}

export interface CoastStandardKit {
  meshes: THREE.Mesh[];
  batches: PropBatch[];
  textureBytes: number;
  scroll: { tex: THREE.Texture; vx: number; vy: number }[];
  /** Call within the renderer's retired-world callback before its generic mesh traversal. */
  disposeMaps(): void;
  /** Standalone disposal (before integration, or when no world traversal owns it). */
  dispose(): void;
}

/** Apply only after buildZoneKit() and after extracting C1's tug fallback. */
export const COAST_STANDARD_REPLACE = {
  meshes: new Set(['terrain', 'zone:sea', 'zone:c1-wet-quay-skin']),
  batches: new Set([
    'foam', 'c1-exposed-tide', 'quay', 'pile', 'pierdeck', 'crane', 'crane-rust',
    'hull', 'hull-near', 'lighthouse', 'container', 'container-far', 'pallet',
    'tyres', 'tyreflat', 'drum', 'buoy', 'buoylying', 'bollard', 'rope', 'net',
    'scrap0', 'scrap1', 'trucktyre', 'c1-inshore-coaster', 'c1-quay-warehouse',
    'c1-loading-bay', 'c1-quay-hoist',
  ]),
  /** Parent removes the photographic Coast plate, retaining only its sky/weather. */
  plate: 'sky-only',
} as const;

const LANDMARKS: Record<CoastTrackId, readonly CoastLandmark[]> = {
  'c1-low-tide': [
    { kind: 'freighter', x: 82, z: -82, scale: 1, yaw: -0.08 },
    { kind: 'warehouse', x: 104, z: -10.6, scale: 1, yaw: 0 },
    { kind: 'crane', x: 332, z: -50, scale: 0.82, yaw: 0 },
    { kind: 'warehouse', x: 390, z: -10.6, scale: 0.88, yaw: 0 },
    { kind: 'barge', x: 438, z: -60, scale: 0.8, yaw: 0.07 },
  ],
  'c2-crane-hop': [
    { kind: 'warehouse', x: 72, z: -11.0, scale: 0.85, yaw: 0 },
    { kind: 'barge', x: 191, z: -49, scale: 1, yaw: 0.04 },
    { kind: 'freighter', x: 391, z: -85, scale: 0.9, yaw: -0.12 },
  ],
  'c3-hull-breach': [
    { kind: 'salvage', x: 108, z: -55, scale: 0.9, yaw: -0.13 },
    { kind: 'warehouse', x: 210, z: -11.0, scale: 0.8, yaw: 0 },
    { kind: 'crane', x: 366, z: -60, scale: 0.75, yaw: 0.06 },
    { kind: 'freighter', x: 421, z: -102, scale: 0.8, yaw: -0.18 },
  ],
};

const KEEPOUTS: Record<CoastTrackId, readonly (readonly [number, number])[]> = {
  'c1-low-tide': [[180, 260]],
  'c2-crane-hop': [[90, 145], [282, 342]],
  'c3-hull-breach': [[130, 181], [245, 322], [347, 383]],
};

/** Pure plan; keyed material/placement variation never advances ZoneCtx.rng. */
export function planCoastStandard(track: CompiledTrack, x0: number, x1: number): CoastStandardPlan {
  const id = track.def.id as CoastTrackId;
  if (!(id in LANDMARKS)) throw new Error(`coast standard: unsupported track ${track.def.id}`);
  const floor = Math.min(...track.def.profile.map(p => p.y)) - 0.42;
  return {
    id, seed: track.def.seed, x0, x1, seaY: floor - 2.4,
    landmarks: LANDMARKS[id].filter(a => a.x >= x0 - 70 && a.x <= x1 + 70),
    keepouts: KEEPOUTS[id],
  };
}

function key(seed: number, x: number, channel: number): number {
  let n = (seed ^ Math.imul(Math.floor(x), 0x9e3779b9) ^ Math.imul(channel, 0x85ebca6b)) | 0;
  n ^= n >>> 16; n = Math.imul(n, 0x7feb352d); n ^= n >>> 15;
  n = Math.imul(n, 0x846ca68b); n ^= n >>> 16;
  return (n >>> 0) / 4294967296;
}

const S = (hex: number): G.RGB => G.rgb(hex);
const C = {
  concrete: S(0xa9a89e), wet: S(0x667a74), silt: S(0x52605a),
  oxide: S(0x9f553d), steel: S(0x8f9691), teal: S(0x397277),
  dark: S(0x303d3e), ivory: S(0xd2c9b3), yellow: S(0xd9a33b),
  timber: S(0x796349), rubber: S(0x333837), glass: S(0x50757a),
};

type Surface = 'concrete' | 'steel' | 'timber' | 'water';
function textureData(surface: Surface, size: number): { albedo: THREE.DataTexture; normal: THREE.DataTexture; orm: THREE.DataTexture } {
  const base = new Uint8Array(size * size * 4);
  const norm = new Uint8Array(size * size * 4);
  const orm = new Uint8Array(size * size * 4);
  const palette: Record<Surface, [number, number, number]> = {
    // Vertex colors carry the deliberate livery; these maps provide material
    // variation without multiplying dark paint into an unreadable near-black.
    concrete: [191, 188, 181], steel: [210, 213, 209], timber: [198, 183, 159], water: [40, 93, 105],
  };
  const [r, g, b] = palette[surface];
  for (let y = 0; y < size; y++) for (let x = 0; x < size; x++) {
    const p = (y * size + x) * 4;
    const fine = key(0x75a94, x + y * size, surface.charCodeAt(0)) - 0.5;
    const macro = Math.sin(x * 0.057 + y * 0.013) * Math.sin(y * 0.045 - x * 0.009);
    const joint = surface === 'concrete' && (x % (size / 4) < 2 || y % (size / 2) < 2) ? -34 : 0;
    const grain = surface === 'timber' ? 17 * Math.sin(y * 0.4 + 3 * Math.sin(x * 0.034)) : 0;
    const salt = surface === 'steel' ? 18 * Math.max(0, Math.sin(x * 0.14 + y * 0.027)) : 0;
    const wave = surface === 'water' ? 7 * Math.sin(x * 0.12 + y * 0.05) : 0;
    const v = Math.round(fine * 18 + macro * 10 + joint + grain + salt + wave);
    const rust = surface === 'steel' && macro > 0.52 ? 18 : 0;
    base[p] = Math.max(0, Math.min(255, r + v + rust));
    base[p + 1] = Math.max(0, Math.min(255, g + v - rust * 0.7));
    base[p + 2] = Math.max(0, Math.min(255, b + v - rust));
    base[p + 3] = 255;
    const nx = surface === 'water' ? 23 * Math.cos(x * 0.12 + y * 0.05) : fine * 24 + macro * 8;
    const ny = surface === 'water' ? 18 * Math.sin(x * 0.06 - y * 0.1) : fine * 20 - macro * 7;
    norm[p] = Math.round(128 + nx); norm[p + 1] = Math.round(128 + ny);
    norm[p + 2] = 248; norm[p + 3] = 255;
    orm[p] = 255;
    orm[p + 1] = surface === 'water' ? 116 : surface === 'steel' ? 167 + Math.round(fine * 20) : surface === 'timber' ? 213 : 218;
    orm[p + 2] = surface === 'steel' ? 112 : 0;
    orm[p + 3] = 255;
  }
  const tex = (pixels: Uint8Array, srgb = false): THREE.DataTexture => {
    const t = new THREE.DataTexture(pixels, size, size, THREE.RGBAFormat);
    t.wrapS = t.wrapT = THREE.RepeatWrapping;
    t.magFilter = THREE.LinearFilter;
    t.minFilter = THREE.LinearMipmapLinearFilter;
    t.generateMipmaps = true;
    if (srgb) t.colorSpace = THREE.SRGBColorSpace;
    t.needsUpdate = true;
    return t;
  };
  return { albedo: tex(base, true), normal: tex(norm), orm: tex(orm) };
}

function surfaceMaterial(surface: Surface, size: number, lib: MaterialLibrary): { material: THREE.MeshStandardMaterial; maps: THREE.DataTexture[] } {
  const maps = textureData(surface, size);
  const material = fogify(new THREE.MeshStandardMaterial({
    color: 0xffffff, map: maps.albedo, normalMap: maps.normal,
    roughnessMap: maps.orm, metalnessMap: maps.orm,
    roughness: 1, metalness: 1, vertexColors: true,
    envMapIntensity: surface === 'water' ? 0.22 : 0.42,
  }));
  // Empty name marks this as owned to ThreeRenderer.clearWorld(), whose
  // retirement queue waits for its shader program before disposing it.
  material.userData['coastStandardSurface'] = surface;
  material.normalScale.set(surface === 'water' ? 0.28 : 0.5, surface === 'water' ? 0.28 : 0.5);
  lib.complete(material);
  return { material, maps: [maps.albedo, maps.normal, maps.orm] };
}

function stripGeometry(cols: readonly number[], rows: readonly number[],
  yAt: (x: number, z: number) => number, tint: (x: number, z: number, y: number) => G.RGB,
  gap: readonly [number, number] | null = null): THREE.BufferGeometry {
  const pos: number[] = [], uv: number[] = [], col: number[] = [], indices: number[] = [];
  for (let i = 0; i < cols.length; i++) for (let j = 0; j < rows.length; j++) {
    const x = cols[i]!, z = rows[j]!, y = yAt(x, z), rgb = tint(x, z, y);
    pos.push(x, y, z); uv.push(x / 8, z / 8); col.push(...rgb);
    if (i && j && !(gap && rows[j - 1] === gap[0] && z === gap[1])) {
      const a = (i - 1) * rows.length + j - 1, b = i * rows.length + j - 1;
      indices.push(a, a + 1, b, b, a + 1, b + 1);
    }
  }
  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  geo.setAttribute('uv', new THREE.Float32BufferAttribute(uv, 2));
  geo.setAttribute('color', new THREE.Float32BufferAttribute(col, 3));
  geo.setIndex(indices); geo.computeVertexNormals();
  return geo;
}

function hullGeometry(length: number, beam: number, depth: number, palette: G.RGB): THREE.BufferGeometry {
  const sections = [-0.5, -0.45, -0.3, 0, 0.3, 0.43, 0.5];
  const shape = [0.22, 0.67, 0.95, 1, 0.94, 0.6, 0.08];
  const p: number[] = [], uv: number[] = [], c: number[] = [], idx: number[] = [];
  const n = 8;
  for (let i = 0; i < sections.length; i++) {
    const x = sections[i]! * length, b = beam * shape[i]! / 2;
    const sheer = i > 4 ? (i - 4) * 0.24 : 0;
    const ring: [number, number][] = [
      [-b, depth + sheer], [-b * 0.96, depth * 0.55], [-b * 0.74, 0.0], [-b * 0.34, -1.4],
      [b * 0.34, -1.4], [b * 0.74, 0.0], [b * 0.96, depth * 0.55], [b, depth + sheer],
    ];
    for (let j = 0; j < n; j++) {
      const [z, y] = ring[j]!;
      p.push(x, y, z); uv.push((x / length + 0.5) * 3, j / (n - 1));
      const shade = j < 2 || j > 5 ? 0.94 : j === 3 || j === 4 ? 0.55 : 0.8;
      c.push(palette[0] * shade, palette[1] * shade, palette[2] * shade);
      if (i && j) {
        const a = (i - 1) * n + j - 1, b = i * n + j - 1;
        idx.push(a, b, a + 1, a + 1, b, b + 1);
      }
    }
  }
  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.Float32BufferAttribute(p, 3));
  geo.setAttribute('uv', new THREE.Float32BufferAttribute(uv, 2));
  geo.setAttribute('color', new THREE.Float32BufferAttribute(c, 3));
  geo.setIndex(idx); geo.computeVertexNormals();
  return geo;
}

function shipGeometry(kind: 'freighter' | 'barge' | 'salvage', low: boolean): THREE.BufferGeometry {
  const L = kind === 'freighter' ? 51 : kind === 'barge' ? 32 : 39;
  const B = kind === 'barge' ? 9.5 : 8.4;
  const H = kind === 'barge' ? 2.7 : 4.1;
  const parts: THREE.BufferGeometry[] = [hullGeometry(L, B, H, kind === 'salvage' ? C.oxide : C.teal)];
  parts.push(G.box(L * 0.84, 0.24, B * 0.72, -L * 0.02, H + 0.05, 0, C.dark));
  // Continuous gunwale and a true superstructure establish scale in the tight side camera.
  for (const side of [-1, 1]) {
    parts.push(G.box(L * 0.8, 0.18, 0.16, -L * 0.03, H + 0.85, side * B * 0.38, C.ivory));
    for (let x = -L * 0.38; x <= L * 0.35; x += low ? 7.2 : 3.6)
      parts.push(G.box(0.12, 0.9, 0.12, x, H + 0.48, side * B * 0.38, C.dark));
  }
  const cabinX = kind === 'barge' ? -L * 0.34 : -L * 0.3;
  parts.push(G.box(L * 0.22, 4.2, B * 0.52, cabinX, H + 2.2, 0, C.ivory));
  parts.push(G.box(L * 0.24, 0.25, B * 0.58, cabinX, H + 4.45, 0, C.dark));
  for (let x = cabinX - L * 0.08; x <= cabinX + L * 0.08; x += low ? 2.9 : 1.45) {
    parts.push(G.box(0.8, 0.62, 0.035, x, H + 3.15, B * 0.265, C.glass));
    parts.push(G.box(0.8, 0.62, 0.035, x, H + 3.15, -B * 0.265, C.glass));
  }
  parts.push(G.box(0.15, 5.1, 0.15, cabinX + 0.8, H + 7, 0, C.dark));
  parts.push(G.box(2.0, 0.13, 0.13, cabinX + 0.8, H + 8.75, 0, C.yellow));
  if (kind === 'barge') {
    for (let row = 0; row < 2; row++) for (let i = 0; i < 3; i++) {
      const x = -L * 0.03 + i * 5.7, y = H + 1.4 + row * 2.55;
      parts.push(G.box(5.4, 2.4, B * 0.47, x, y, 0, (i + row) % 2 ? C.oxide : C.steel));
      if (!low) for (let k = -2; k <= 2; k++) parts.push(G.box(0.045, 2.15, B * 0.48, x + k * 1.05, y, 0, C.dark));
    }
  } else {
    const covers = low ? 3 : 5;
    for (let i = 0; i < covers; i++) {
      const x = -L * 0.04 + i * (20 / (covers - 1));
      parts.push(G.box(4.5, 0.18, B * 0.68, x, H + 0.4, 0, kind === 'salvage' ? C.oxide : C.steel));
      parts.push(G.box(0.12, 0.65, B * 0.66, x + 2.1, H + 0.62, 0, C.dark));
    }
    for (const x of [-L * 0.1, L * 0.24]) {
      parts.push(G.box(0.18, 7.7, 0.18, x, H + 4.1, -B * 0.13, C.dark));
      parts.push(G.beam(x, H + 7.8, -B * 0.13, x + 6, H + 6.2, -B * 0.13, 0.14, C.yellow));
    }
  }
  if (kind === 'salvage') {
    for (let i = 0; i < (low ? 3 : 6); i++) {
      const x = -L * 0.28 + i * 4.1;
      parts.push(G.box(0.23, H + 2.3, 0.18, x, H * 0.53, B * 0.52, C.oxide, 0.08 * (i % 2 ? -1 : 1)));
    }
  }
  return G.merge(parts);
}

function craneGeometry(low: boolean): THREE.BufferGeometry {
  const parts: THREE.BufferGeometry[] = [];
  for (const side of [-1, 1]) {
    parts.push(G.box(0.44, 21, 0.44, side * 4.8, 10.5, side * 3.1, C.oxide));
    parts.push(G.beam(side * 4.8, 2, side * 3.1, -side * 4.8, 20, -side * 3.1, 0.21, C.dark));
  }
  parts.push(G.box(19, 0.58, 7.2, 0, 21.6, 0, C.yellow));
  for (let i = -8; i <= 8; i += low ? 8 : 4) {
    parts.push(G.beam(i, 21.3, -3.2, i + 3.6, 23.3, -3.2, 0.16, C.dark));
    parts.push(G.beam(i, 21.3, 3.2, i + 3.6, 23.3, 3.2, 0.16, C.dark));
  }
  parts.push(G.box(2.9, 2.2, 2.9, -1.8, 23.0, 0, C.ivory));
  parts.push(G.box(2.4, 0.95, 0.05, -1.8, 23.15, 1.48, C.glass));
  parts.push(G.box(0.12, 8, 0.12, 5.8, 17.3, 0, C.dark));
  parts.push(G.box(1.5, 0.6, 1.0, 5.8, 13.0, 0, C.yellow));
  return G.merge(parts);
}

function craneFootGeometry(): THREE.BufferGeometry {
  const parts: THREE.BufferGeometry[] = [G.box(13.5, 0.5, 9.2, 0, -0.25, 0, C.timber)];
  for (const x of [-5.2, 5.2]) for (const z of [-3.4, 3.4]) {
    parts.push(G.cyl(0.42, 0.48, 6.8, 10, x, -3.65, z, C.timber));
    parts.push(G.box(1.1, 0.2, 1.1, x, -0.5, z, C.dark));
  }
  for (const side of [-1, 1]) parts.push(G.box(13.1, 0.2, 0.2, 0, 0.28, side * 4.4, C.yellow));
  return G.merge(parts);
}

function warehouseGeometry(low: boolean): THREE.BufferGeometry {
  const parts: THREE.BufferGeometry[] = [
    G.box(17, 5.2, 7.2, 0, 2.6, 0, C.concrete),
    G.box(18, 0.45, 8, 0, 5.45, 0, C.dark),
    G.box(6.1, 4.5, 0.09, 0, 2.3, 3.67, C.dark),
    G.box(5.7, 0.22, 0.12, 0, 4.45, 3.75, C.yellow),
  ];
  for (let i = 0; i < (low ? 2 : 4); i++) {
    parts.push(G.box(0.1, 4.1, 0.08, -2.55 + i * (low ? 5.1 : 1.7), 2.35, 3.78, C.steel));
    parts.push(G.box(0.18, 5.1, 7.35, -7.6 + i * (low ? 15.3 : 5.1), 2.65, 0, C.oxide));
  }
  for (const x of [-6.5, 6.5]) parts.push(G.box(2.2, 1.1, 0.06, x, 3.9, 3.65, C.glass));
  return G.merge(parts);
}

function pierGeometry(low: boolean): THREE.BufferGeometry {
  const parts: THREE.BufferGeometry[] = [
    G.box(15.5, 0.32, 20, 0, -0.16, 0, C.timber),
    G.box(15.7, 0.28, 0.28, 0, -0.02, -9.9, C.dark),
    G.box(15.7, 0.28, 0.28, 0, -0.02, 9.9, C.dark),
  ];
  for (const side of [-1, 1]) {
    parts.push(G.box(0.22, 0.5, 20.2, side * 7.6, -0.24, 0, C.steel));
    for (const z of [-7.5, 0, 7.5]) {
      parts.push(G.cyl(0.31, 0.39, 6.6, 10, side * 6.6, -3.3, z, C.timber));
      parts.push(G.cyl(0.34, 0.34, 0.22, 10, side * 6.6, -0.35, z, C.dark));
    }
  }
  for (let z = -9.2; z <= 9.3; z += low ? 3.2 : 1.35) {
    parts.push(G.box(15.0, 0.035, 0.065, 0, 0.014, z, C.dark));
  }
  return G.merge(parts);
}

function serviceBayGeometry(low: boolean): THREE.BufferGeometry {
  const parts: THREE.BufferGeometry[] = [
    G.box(10, 0.18, 6.4, 0, 0.05, 0, C.concrete),
    G.box(0.22, 0.08, 5.8, -4.55, 0.18, 0, C.yellow),
    G.box(0.22, 0.08, 5.8, 4.55, 0.18, 0, C.yellow),
    G.box(4.4, 2.5, 2.3, -1.1, 1.39, -1.15, C.oxide),
    G.box(3.7, 0.12, 2.4, -1.1, 2.72, -1.15, C.dark),
    G.cyl(0.71, 0.71, 0.28, 14, 3.3, 0.51, 0.35, C.dark),
    G.cyl(0.42, 0.42, 0.31, 14, 3.3, 0.51, 0.35, C.steel),
  ];
  for (let i = 0; i < (low ? 2 : 4); i++) {
    parts.push(G.box(0.075, 2.2, 2.4, -2.85 + i * (low ? 3.3 : 1.1), 1.39, -1.15, C.dark));
  }
  for (const x of [-4.1, 4.1]) {
    parts.push(G.cyl(0.12, 0.15, 0.75, 9, x, 0.55, 2.4, C.dark));
    parts.push(G.box(0.38, 0.11, 0.12, x, 0.92, 2.4, C.steel));
  }
  return G.merge(parts);
}

/** All geometry is cosmetic. The exact ridden deck and obstacle colliders are untouched. */
export function buildCoastStandard(plan: CoastStandardPlan, options: CoastStandardOptions): CoastStandardKit {
  const { lib, detail, groundAt: gy } = options;
  const low = detail === 'low';
  const meshes: THREE.Mesh[] = [], batches: PropBatch[] = [], scroll: CoastStandardKit['scroll'] = [];
  const ownedGeo = new Set<THREE.BufferGeometry>(), ownedMat = new Set<THREE.Material>(), ownedTex = new Set<THREE.Texture>();
  const size = detail === 'low' ? 128 : 256;
  const skin = Object.fromEntries((['concrete', 'steel', 'timber', 'water'] as const).map(surface => {
    const item = surfaceMaterial(surface, size, lib);
    ownedMat.add(item.material); item.maps.forEach(t => ownedTex.add(t));
    return [surface, item.material];
  })) as Record<Surface, THREE.MeshStandardMaterial>;
  const batch = (name: string, geo: THREE.BufferGeometry, material: THREE.Material, shadow = false): PropBatch => {
    ownedGeo.add(geo);
    const b = new PropBatch(`coast-standard:${name}`, geo, material, shadow);
    batches.push(b); return b;
  };
  const mesh = (name: string, geo: THREE.BufferGeometry, mat: THREE.Material, shadow = false): THREE.Mesh => {
    ownedGeo.add(geo);
    const m = new THREE.Mesh(geo, mat); m.name = `zone:coast-standard:${name}`;
    m.castShadow = shadow; m.receiveShadow = true; meshes.push(m); return m;
  };
  const cols = new Set<number>();
  for (let x = plan.x0 - 20; x <= plan.x1 + 20; x += 4) cols.add(x);
  const xs = [...cols].sort((a, b) => a - b);
  const nearZ = 2.0;
  const groundRows = [-24, -20, -18, -16, -14, -12, -8, -3, nearZ, 3.4, 5, 8, 12, 45];
  const tint = (x: number, z: number, y: number): G.RGB => {
    const wet = Math.max(0, Math.min(1, (plan.seaY + 0.7 - y) / 2.8));
    const stain = 0.88 + key(plan.seed, x * 0.4 + z * 3, 2) * 0.12;
    const base = z < -12 ? C.silt : z < -3 ? C.wet : z >= nearZ ? C.concrete : C.concrete;
    return [base[0] * (1 - wet * 0.2) * stain, base[1] * (1 - wet * 0.13) * stain, base[2] * stain];
  };
  mesh('shore-and-yard', stripGeometry(xs, groundRows, gy, tint, [-3, nearZ]), skin.concrete);

  // The horizontal quay face and its cap vary with the original ground profile.
  const faceRows = [-13.35, -13.0, -12.7, -12.55];
  mesh('profiled-quay-face', stripGeometry(xs, faceRows,
    (x, z) => z < -13 ? plan.seaY - 1.1 : gy(x, -12) + 0.025,
    (_x, z) => z < -13 ? C.dark : z > -12.6 ? C.concrete : C.wet), skin.concrete);
  const cap = batch('quay-cap-and-joints', G.merge([
    G.box(9.65, 0.18, 0.5, 0, 0.09, 0, C.concrete),
    G.box(0.11, 0.21, 0.56, -4.8, 0.11, 0, C.dark),
  ]), skin.concrete, false);
  const pile = batch('piles', G.merge([
    G.cyl(0.18, 0.22, 1, 9, 0, 0.5, 0, C.timber),
    G.cyl(0.23, 0.23, 0.16, 9, 0, 0.82, 0, C.dark),
  ]), skin.timber, false);
  const fender = batch('fenders', G.merge([
    G.cyl(0.38, 0.38, 0.16, 12, 0, 0.45, 0, C.rubber, 'z'),
    G.cyl(0.23, 0.23, 0.18, 10, 0, 0.45, 0, C.dark, 'z'),
  ]), skin.steel, false);
  const cleat = batch('mooring-cleats', G.merge([
    G.box(0.7, 0.16, 0.17, 0, 0.22, 0, C.dark),
    G.box(0.16, 0.28, 0.16, -0.24, 0.2, 0, C.steel),
    G.box(0.16, 0.28, 0.16, 0.24, 0.2, 0, C.steel),
  ]), skin.steel, false);
  for (let x = Math.ceil(plan.x0 / 10) * 10; x < plan.x1 + 10; x += 10) {
    const y = gy(x, -12);
    cap.add(x + 5, y - 0.025, -12.55);
    if (key(plan.seed, x, 3) > 0.16) {
      const h = Math.max(1, y - plan.seaY + 1.5);
      pile.add(x + 1.8, plan.seaY - 1.5, -13.4, 0, 1, null, 0, h);
      pile.add(x + 8.2, plan.seaY - 1.5, -13.4, 0, 1, null, 0, h);
    }
    if (key(plan.seed, x, 4) > 0.57) fender.add(x + 5.3, y - 1.5, -13.0, 0, 1);
    if (key(plan.seed, x, 5) > 0.62) cleat.add(x + 4.8, y, -12.1);
  }

  // One opaque sea mesh with a shore-to-deep color ramp; only the small normal map scrolls.
  const seaRows = [-205, -150, -100, -55, -27, -19, -16.5];
  const seaX = [plan.x0 - 260, plan.x0 - 130, ...xs, plan.x1 + 130, plan.x1 + 260];
  const sea = mesh('tidal-water', stripGeometry(seaX, seaRows, () => plan.seaY,
    (x, z) => {
      const light = 0.95 + key(plan.seed, x + z, 8) * 0.08;
      const shore = Math.max(0, Math.min(1, (z + 80) / 66));
      return [0.78 * light, (0.83 + shore * 0.2) * light, (0.91 + shore * 0.2) * light];
    }), skin.water);
  sea.receiveShadow = false;
  scroll.push({ tex: skin.water.normalMap!, vx: 0.007, vy: -0.013 });

  // The break line is a connected narrow strip at each actual ground/water crossing.
  const foamPos: number[] = [], foamColor: number[] = [], foamUv: number[] = [], foamIdx: number[] = [];
  let last: number | null = null;
  for (const x of xs) {
    const high = gy(x, -12) > plan.seaY, low = gy(x, -24) <= plan.seaY;
    if (!(high && low)) { last = null; continue; }
    let a = -24, b = -12;
    for (let n = 0; n < 9; n++) {
      const m = (a + b) * 0.5;
      if (gy(x, m) < plan.seaY) a = m; else b = m;
    }
    const z = (a + b) * 0.5, width = 0.28 + 0.23 * key(plan.seed, x, 7);
    const v = foamPos.length / 3;
    foamPos.push(x, plan.seaY + 0.035, z - width, x, plan.seaY + 0.039, z + width);
    foamColor.push(0.55, 0.75, 0.78, 0.88, 0.94, 0.9);
    foamUv.push(x / 3, 0, x / 3, 1);
    if (last !== null) foamIdx.push(last, last + 1, v, v, last + 1, v + 1);
    last = v;
  }
  if (foamIdx.length) {
    const geo = new THREE.BufferGeometry();
    geo.setAttribute('position', new THREE.Float32BufferAttribute(foamPos, 3));
    geo.setAttribute('color', new THREE.Float32BufferAttribute(foamColor, 3));
    geo.setAttribute('uv', new THREE.Float32BufferAttribute(foamUv, 2));
    geo.setIndex(foamIdx); geo.computeVertexNormals();
    const foamMat = fogify(new THREE.MeshStandardMaterial({ color: 0xffffff, vertexColors: true, roughness: 0.78, metalness: 0, side: THREE.DoubleSide }));
    lib.complete(foamMat); ownedMat.add(foamMat);
    mesh('shore-break-line', geo, foamMat).receiveShadow = false;
  }

  // A few deliberately placed dimensional masses, rather than the old 2.4 m scrap lottery.
  const ship = new Map<'freighter' | 'barge' | 'salvage', PropBatch>();
  let crane: PropBatch | null = null, craneFoot: PropBatch | null = null, warehouse: PropBatch | null = null;
  for (const a of plan.landmarks) {
    if (a.kind === 'warehouse') {
      warehouse ??= batch('warehouse', warehouseGeometry(low), skin.concrete);
      warehouse.add(a.x, gy(a.x, a.z) - 0.06, a.z, a.yaw, a.scale);
    } else if (a.kind === 'crane') {
      crane ??= batch('harbor-crane', craneGeometry(low), skin.steel);
      craneFoot ??= batch('harbor-crane-pier', craneFootGeometry(), skin.timber);
      const deckY = plan.seaY + 2.2;
      craneFoot.add(a.x, deckY, a.z, a.yaw, a.scale);
      crane.add(a.x, deckY, a.z, a.yaw, a.scale);
    } else {
      let vessel = ship.get(a.kind);
      if (!vessel) {
        vessel = batch(a.kind, shipGeometry(a.kind, low), skin.steel);
        ship.set(a.kind, vessel);
      }
      vessel.add(a.x, plan.seaY, a.z, a.yaw, a.scale);
    }
  }
  const workLight = batch('dock-light', G.merge([
    G.cyl(0.07, 0.09, 6.4, 8, 0, 3.2, 0, C.dark),
    G.box(1.5, 0.28, 0.72, 0.42, 6.6, 0, C.yellow),
    G.box(1.15, 0.06, 0.48, 0.42, 6.41, 0, C.ivory),
  ]), skin.steel);
  for (let x = Math.ceil(plan.x0 / 55) * 55; x < plan.x1; x += 55) {
    if (plan.keepouts.some(([a, b]) => x >= a - 8 && x <= b + 8)) continue;
    if (key(plan.seed, x, 9) < 0.22) continue;
    workLight.add(x, gy(x, -9.8), -9.8);
  }
  const pier = batch('pile-pier', pierGeometry(low), skin.timber);
  const bay = batch('service-bay', serviceBayGeometry(low), skin.steel);
  for (let x = Math.ceil((plan.x0 + 26) / 78) * 78; x < plan.x1 - 14; x += 78) {
    if (plan.keepouts.some(([a, b]) => x >= a - 18 && x <= b + 18)) continue;
    if (key(plan.seed, x, 10) > 0.34) {
      // The shore end meets groundAt(x,-12); the six-metre timber piles descend
      // below the waterline. The ridden line stays on the separate collider deck.
      pier.add(x, gy(x, -12) - 0.06, -23, 0, 1);
    }
    if (key(plan.seed, x, 11) > 0.28) bay.add(x + 14, gy(x + 14, -8.3) - 0.05, -8.3);
  }
  if (plan.id === 'c3-hull-breach') for (const x of [225, 430]) {
    // The long wreck beach otherwise has no service bay after the three
    // protected riding windows. Keep both clusters beyond their camera reads.
    bay.add(x, gy(x, -8.3) - 0.05, -8.3);
  }
  const textureBytes = ownedTex.size * size * size * 4 * 1.33;
  let disposed = false, mapsDisposed = false;
  const disposeMaps = (): void => {
    if (mapsDisposed) return;
    mapsDisposed = true;
    for (const tex of ownedTex) tex.dispose();
  };
  return {
    meshes, batches, textureBytes, scroll, disposeMaps,
    dispose() {
      if (disposed) return;
      disposed = true;
      for (const geo of ownedGeo) geo.dispose();
      for (const mat of ownedMat) mat.dispose();
      disposeMaps();
      meshes.length = 0; batches.length = 0; scroll.length = 0;
    },
  };
}
