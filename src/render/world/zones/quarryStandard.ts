/**
 * Candidate D1–D3 quarry production kit. The old ZoneKit must finish its RNG
 * sequence before its named generic families are replaced by this leaf.
 * Ridden ribbons, obstacles and the D3 high/low bridge are never modified.
 */
import * as THREE from 'three';
import type { ColliderPolyline, CompiledTrack } from '../../../core/types';
import type { MaterialLibrary } from '../../materials/library';
import { fogify } from '../../lighting/environment';
import { PropBatch, type WorldDetail } from '../props';
import * as G from './geo';

export type QuarryTrackId = 'd1-dust-devil' | 'd2-conveyor' | 'd3-rope-walk';
export type QuarryLandmarkKind = 'drill' | 'crusher' | 'haul' | 'gantry' | 'ridge';
export interface QuarryLandmark { kind: QuarryLandmarkKind; x: number; z: number; scale: number; yaw: number }
export interface QuarryContact { x0: number; x1: number; bottomY: number; topY: number; colliderId: number }
export interface QuarryStandardPlan {
  id: QuarryTrackId; seed: number; x0: number; x1: number; pitY: number;
  landmarks: readonly QuarryLandmark[];
  contacts: readonly QuarryContact[];
  protectedWindows: readonly (readonly [number, number])[];
  poolRanges: readonly (readonly [number, number])[];
}
export interface QuarryStandardOptions {
  lib: MaterialLibrary; detail: WorldDetail;
  /** Existing zoneGround('quarry',...) — only used along the rim and near face. */
  groundAt: (x: number, z: number) => number;
}
export interface QuarryStandardKit {
  meshes: THREE.Mesh[]; batches: PropBatch[]; textureBytes: number;
  scroll: { tex: THREE.Texture; vx: number; vy: number }[];
  /** Renderer calls this inside the retired-world callback before generic mesh traversal. */
  disposeMaps(): void;
  /** Standalone cancellation before the world owns these meshes. */
  dispose(): void;
}

/** Keep D1's accepted exact-collider edge/witness batches and all obstacle art. */
export const QUARRY_STANDARD_REPLACE = {
  meshes: new Set(['terrain', 'zone:pitfloor', 'zone:pool']),
  batches: new Set([
    'bench0', 'bench1', 'block0', 'block1', 'block2', 'rubble', 'rubblepile',
    'scrub', 'surveypole', 'rail', 'orecart', 'hut', 'haultruck', 'headframe',
    'conveyor', 'zrock0', 'zrock1', 'zrock2', 'zrockfar', 'contactshadow',
  ]),
  plate: 'sky-and-haze-only',
} as const;

const LANDMARKS: Record<QuarryTrackId, readonly QuarryLandmark[]> = {
  'd1-dust-devil': [
    { kind: 'crusher', x: 49, z: -43, scale: 0.9, yaw: 0 },
    { kind: 'drill', x: 156, z: -45, scale: 1, yaw: 0.08 },
    { kind: 'gantry', x: 290, z: -47, scale: 0.85, yaw: -0.04 },
    { kind: 'haul', x: 358, z: -39, scale: 0.9, yaw: Math.PI },
  ],
  'd2-conveyor': [
    { kind: 'gantry', x: 106, z: -49, scale: 0.95, yaw: 0 },
    { kind: 'crusher', x: 286, z: -43, scale: 1.15, yaw: 0.03 },
    { kind: 'haul', x: 489, z: -37, scale: 1, yaw: Math.PI },
  ],
  'd3-rope-walk': [
    { kind: 'haul', x: 109, z: -37, scale: 0.9, yaw: 0 },
    { kind: 'drill', x: 289, z: -52, scale: 0.8, yaw: 0.05 },
    { kind: 'crusher', x: 458, z: -53, scale: 0.78, yaw: -0.08 },
  ],
};
const WINDOWS: Record<QuarryTrackId, readonly (readonly [number, number])[]> = {
  'd1-dust-devil': [[24, 47], [84, 123], [183, 209], [261, 283]],
  'd2-conveyor': [[38, 84], [193, 271], [350, 456]],
  'd3-rope-walk': [[38, 65], [190, 222], [276, 304], [346, 437]],
};
const POOLS: Record<QuarryTrackId, readonly (readonly [number, number])[]> = {
  'd1-dust-devil': [[134, 219]], 'd2-conveyor': [[70, 157], [322, 386]],
  'd3-rope-walk': [[69, 153], [247, 319]],
};

/** Four D1 flank traces are derived from the *actual* compiled ledge colliders. */
export function planQuarryStandard(track: CompiledTrack, x0: number, x1: number): QuarryStandardPlan {
  const id = track.def.id as QuarryTrackId;
  if (!(id in LANDMARKS)) throw new Error(`quarry standard: unsupported track ${track.def.id}`);
  const contacts: QuarryContact[] = [];
  if (id === 'd1-dust-devil') for (const p of track.placed) {
    if (p.kind !== 'ledge' || p.pos.x < 90 || p.pos.x >= 120) continue;
    const collider = track.colliders.find(c => c.id === p.colliderIds[0]) as ColliderPolyline | undefined;
    if (collider?.kind !== 'polyline' || collider.points.length < 3) throw new Error(`quarry contact: absent ledge at ${p.pos.x}`);
    contacts.push({ x0: collider.points[0]!.x, x1: collider.points.at(-1)!.x,
      bottomY: collider.points[0]!.y, topY: collider.points[1]!.y, colliderId: collider.id });
  }
  if (id === 'd1-dust-devil' && contacts.length !== 4) throw new Error(`quarry contact: expected four terrace ledges, got ${contacts.length}`);
  const floor = Math.min(...track.def.profile.map(p => p.y)) - 0.42;
  return { id, seed: track.def.seed, x0, x1, pitY: floor - 9.1,
    contacts, protectedWindows: WINDOWS[id], poolRanges: POOLS[id],
    landmarks: LANDMARKS[id].filter(a => a.x > x0 - 40 && a.x < x1 + 40) };
}

function key(seed: number, x: number, channel: number): number {
  let n = (seed ^ Math.imul(Math.floor(x), 0x9e3779b9) ^ Math.imul(channel, 0x85ebca6b)) | 0;
  n ^= n >>> 16; n = Math.imul(n, 0x7feb352d); n ^= n >>> 15;
  n = Math.imul(n, 0x846ca68b); n ^= n >>> 16;
  return (n >>> 0) / 4294967296;
}
const rgb = (hex: number): G.RGB => G.rgb(hex);
const C = {
  pale: rgb(0xc8b69a), bed: rgb(0xa88969), shade: rgb(0x756e65),
  dark: rgb(0x3d3935), steel: rgb(0x777d78), oxide: rgb(0x945640),
  yellow: rgb(0xe1ad39), dust: rgb(0xd2bb94), pool: rgb(0x245a5c),
  glass: rgb(0x59787d), tyre: rgb(0x25292a),
};
type Surface = 'strata' | 'dust' | 'steel' | 'pool';
function textureData(surface: Surface, size: number): [THREE.DataTexture, THREE.DataTexture, THREE.DataTexture] {
  const albedo = new Uint8Array(size * size * 4), normal = new Uint8Array(size * size * 4), orm = new Uint8Array(size * size * 4);
  const base: Record<Surface, readonly [number, number, number]> = {
    strata: [221, 202, 171], dust: [214, 196, 166], steel: [206, 210, 203], pool: [37, 91, 99],
  };
  const [red, green, blue] = base[surface];
  for (let y = 0; y < size; y++) for (let x = 0; x < size; x++) {
    const i = (y * size + x) * 4;
    const n = key(0x73151, x + y * size, surface.charCodeAt(0)) - 0.5;
    const strata = surface === 'strata' ? 15 * Math.sin(y * 0.095 + 0.3 * Math.sin(x * 0.033)) : 0;
    const aggregate = surface === 'dust' ? 12 * Math.sin(x * 0.13 + y * 0.18) : 0;
    const oxide = surface === 'steel' ? 16 * Math.max(0, Math.sin(x * 0.1 - y * 0.05)) : 0;
    const ripple = surface === 'pool' ? 8 * Math.sin(x * 0.1 + y * 0.041) : 0;
    const v = Math.round(14 * n + strata + aggregate + ripple);
    albedo[i] = Math.max(0, Math.min(255, red + v + oxide));
    albedo[i + 1] = Math.max(0, Math.min(255, green + v - oxide * 0.5));
    albedo[i + 2] = Math.max(0, Math.min(255, blue + v - oxide));
    albedo[i + 3] = 255;
    normal[i] = Math.round(128 + (surface === 'pool' ? 20 * Math.cos(x * 0.1 + y * 0.041) : n * 22));
    normal[i + 1] = Math.round(128 + (surface === 'strata' ? 15 * Math.cos(y * 0.095) : n * 15));
    normal[i + 2] = 248; normal[i + 3] = 255;
    orm[i] = 255; orm[i + 1] = surface === 'pool' ? 111 : surface === 'steel' ? 171 : 222;
    orm[i + 2] = surface === 'steel' ? 92 : 0; orm[i + 3] = 255;
  }
  const tex = (pixels: Uint8Array, srgb: boolean): THREE.DataTexture => {
    const t = new THREE.DataTexture(pixels, size, size, THREE.RGBAFormat);
    t.wrapS = t.wrapT = THREE.RepeatWrapping;
    t.minFilter = THREE.LinearMipmapLinearFilter; t.magFilter = THREE.LinearFilter;
    t.generateMipmaps = true;
    if (srgb) t.colorSpace = THREE.SRGBColorSpace;
    t.needsUpdate = true;
    return t;
  };
  return [tex(albedo, true), tex(normal, false), tex(orm, false)];
}
function material(surface: Surface, size: number, lib: MaterialLibrary): [THREE.MeshStandardMaterial, THREE.DataTexture[]] {
  const [map, normalMap, packed] = textureData(surface, size);
  const m = fogify(new THREE.MeshStandardMaterial({ color: 0xffffff, map, normalMap,
    roughnessMap: packed, metalnessMap: packed, roughness: 1, metalness: 1,
    vertexColors: true, envMapIntensity: surface === 'pool' ? 0.18 : 0.35 }));
  m.normalScale.set(surface === 'pool' ? 0.22 : 0.5, surface === 'pool' ? 0.22 : 0.5);
  m.userData['quarryStandardSurface'] = surface; // empty name => renderer retires its program
  lib.complete(m);
  return [m, [map, normalMap, packed]];
}

function groundGeometry(cols: readonly number[], rows: readonly number[],
  height: (x: number, z: number) => number,
  tint: (x: number, z: number, y: number) => G.RGB,
  gap: readonly [number, number] | null = null): THREE.BufferGeometry {
  const pos: number[] = [], uv: number[] = [], col: number[] = [], idx: number[] = [];
  for (let i = 0; i < cols.length; i++) for (let j = 0; j < rows.length; j++) {
    const x = cols[i]!, z = rows[j]!, y = height(x, z), c = tint(x, z, y);
    pos.push(x, y, z); uv.push(x / 6, z / 5); col.push(...c);
    if (i && j && !(gap && rows[j - 1] === gap[0] && z === gap[1])) {
      const a = (i - 1) * rows.length + j - 1, b = i * rows.length + j - 1;
      idx.push(a, a + 1, b, b, a + 1, b + 1);
    }
  }
  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  geo.setAttribute('uv', new THREE.Float32BufferAttribute(uv, 2));
  geo.setAttribute('color', new THREE.Float32BufferAttribute(col, 3));
  geo.setIndex(idx); geo.computeVertexNormals();
  return geo;
}

/** Excavation is an open stepped void below the actual road, never a rear wall above it. */
export function quarryCutY(plan: QuarryStandardPlan, groundAt: (x: number, z: number) => number, x: number, z: number): number {
  if (z >= -9) return groundAt(x, z);
  const rim = groundAt(x, -9);
  const pit = plan.pitY;
  const t = (a: number, b: number): number => Math.max(0, Math.min(1, (z - a) / (b - a)));
  const wav = (key(plan.seed, x * 0.2, 21) - 0.5) * 0.32;
  if (z >= -13) return rim - (1 - t(-13, -9)) * 2.1;
  if (z >= -21) return rim - 2.1 + wav;
  if (z >= -25) return rim - 2.1 - (1 - t(-25, -21)) * 2.35;
  if (z >= -33) return rim - 4.45 + wav;
  if (z >= -37) return rim - 4.45 - (1 - t(-37, -33)) * 2.25;
  if (z >= -45) return rim - 6.7 + wav;
  if (z >= -51) return pit + (rim - 6.7 - pit) * t(-51, -45);
  return pit + 0.09 * Math.sin(x * 0.09 + z * 0.13);
}

function contactBedding(plan: QuarryStandardPlan): THREE.BufferGeometry | null {
  if (!plan.contacts.length) return null;
  const parts: THREE.BufferGeometry[] = [];
  for (const c of plan.contacts) {
    const y = c.topY - 0.14;
    const len = c.x1 - c.x0;
    // A narrow bedding seam and open cut ribs sit behind z=-3 and below the
    // exact ledge top. They create no fake road, lip or long retaining slab.
    parts.push(G.box(len - 0.12, 0.08, 0.18, (c.x0 + c.x1) / 2, y, -3.34, C.shade));
    for (let x = c.x0 + 0.35; x < c.x1 - 0.2; x += 1.35) {
      const h = Math.max(0.25, y - c.bottomY + 0.24);
      parts.push(G.box(0.13, h, 0.52, x, y - h / 2, -3.7, C.bed));
    }
  }
  return G.merge(parts);
}

function drillGeometry(low: boolean): THREE.BufferGeometry {
  const p: THREE.BufferGeometry[] = [
    G.box(5.2, 0.65, 3.5, 0, 1.1, 0, C.steel),
    G.box(2.3, 2.9, 2.6, -1.1, 2.65, 0, C.yellow),
    G.box(1.8, 1.15, 0.05, -1.1, 3.35, 1.33, C.glass),
    G.box(0.52, 16, 0.52, 1.15, 8.8, -0.2, C.oxide),
    G.box(2.7, 0.55, 2.2, 1.15, 16.5, -0.2, C.dark),
    G.cyl(0.2, 0.2, 11.5, 8, 1.15, 5.5, -0.2, C.steel),
  ];
  for (const side of [-1, 1]) {
    p.push(G.box(6.0, 0.55, 0.56, 0, 0.55, side * 1.55, C.dark));
    for (let i = 0; i < (low ? 3 : 6); i++) p.push(G.box(0.12, 0.15, 0.6, -2.5 + i * (low ? 2.5 : 1.0), 0.55, side * 1.55, C.steel));
    p.push(G.beam(1.15, 1.0, side * 1.0, 1.15, 16.2, side * 1.0, 0.16, C.dark));
  }
  return G.merge(p);
}
function crusherGeometry(low: boolean): THREE.BufferGeometry {
  const p: THREE.BufferGeometry[] = [
    G.box(10.2, 1.0, 5.6, 0, 1.1, 0, C.dark),
    G.box(5.7, 6.8, 4.2, -1.8, 4.6, 0, C.oxide),
    G.box(7.1, 0.6, 4.5, -1.8, 8.2, 0, C.yellow),
    G.box(4.8, 1.0, 3.0, 2.4, 5.2, 0, C.steel),
    G.box(2.6, 2.1, 3.8, -1.8, 1.8, 3.1, C.dark),
  ];
  for (const side of [-1, 1]) {
    p.push(G.cyl(0.75, 0.75, 0.35, low ? 10 : 16, 2.9, 5.1, side * 2.3, C.dark, 'z'));
    for (let i = 0; i < (low ? 3 : 6); i++)
      p.push(G.box(0.18, 6.0, 0.12, -4.1 + i * (low ? 2.3 : 1.15), 4.6, side * 2.15, C.steel));
  }
  p.push(G.beam(2, 7.7, 0, 17, 4.1, -3.1, 0.5, C.oxide));
  p.push(G.beam(2, 7.2, 0, 17, 3.6, -3.1, 0.42, C.dark));
  for (const x of [6, 12, 16]) p.push(G.beam(x, 4.0, -3.1, x, 0.2, -3.1, 0.17, C.dark));
  return G.merge(p);
}
function haulGeometry(low: boolean): THREE.BufferGeometry {
  const p: THREE.BufferGeometry[] = [
    G.box(8.5, 2.9, 3.5, 0, 3.3, 0, C.yellow),
    G.box(7.3, 0.25, 3.7, 0.2, 4.9, 0, C.dark),
    G.box(2.8, 2.3, 3.2, -3.7, 3.6, 0, C.yellow),
    G.box(2.5, 0.95, 0.05, -3.7, 4.08, 1.64, C.glass),
    G.box(7.5, 0.9, 3.2, 0.5, 1.7, 0, C.oxide),
  ];
  for (const x of [-3.2, 2.7]) for (const side of [-1, 1]) {
    p.push(G.cyl(1.18, 1.18, 0.5, low ? 12 : 18, x, 1.2, side * 1.67, C.tyre, 'z'));
    p.push(G.cyl(0.5, 0.5, 0.52, 10, x, 1.2, side * 1.67, C.steel, 'z'));
  }
  return G.merge(p);
}
function gantryGeometry(low: boolean): THREE.BufferGeometry {
  const p: THREE.BufferGeometry[] = [G.box(21, 0.52, 5.8, 0, 11.2, 0, C.dark)];
  for (const x of [-9.5, 9.5]) for (const z of [-2.5, 2.5]) {
    p.push(G.box(0.34, 11, 0.34, x, 5.6, z, C.oxide));
    p.push(G.box(1.15, 0.24, 1.15, x, 0.15, z, C.steel));
  }
  for (let x = -9; x < 9; x += low ? 6 : 3) {
    p.push(G.beam(x, 11.2, -2.6, x + (low ? 6 : 3), 12.6, -2.6, 0.14, C.yellow));
    p.push(G.beam(x, 11.2, 2.6, x + (low ? 6 : 3), 12.6, 2.6, 0.14, C.yellow));
  }
  p.push(G.box(2.4, 2.1, 2.5, 1.9, 12.8, 0, C.yellow));
  p.push(G.box(2.2, 0.75, 0.05, 1.9, 13.3, 1.28, C.glass));
  return G.merge(p);
}
function ridgeGeometry(seed: number): THREE.BufferGeometry {
  const pos: number[] = [], col: number[] = [], idx: number[] = [];
  const xRows = [-9, -7, -5, -2, 0, 3, 5, 7, 9];
  for (let i = 0; i < xRows.length; i++) {
    const x = xRows[i]!, n = key(seed, i, 41);
    const h = i === 0 || i === xRows.length - 1 ? 1.1 : 2.2 + n * 3.4;
    for (const [z, y] of [[-5, 0], [-2.2, h], [2.8, 0]] as const) {
      pos.push(x, y, z); const k = z < 0 ? 0.74 : 1;
      col.push(C.bed[0] * k, C.bed[1] * k, C.bed[2] * k);
    }
    if (i) for (let j = 1; j < 3; j++) {
      const a = (i - 1) * 3 + j - 1, b = i * 3 + j - 1;
      idx.push(a, a + 1, b, b, a + 1, b + 1);
    }
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  g.setAttribute('color', new THREE.Float32BufferAttribute(col, 3));
  g.setAttribute('uv', new THREE.Float32BufferAttribute(new Float32Array(pos.length / 3 * 2), 2));
  g.setIndex(idx); g.computeVertexNormals(); return g;
}

export function buildQuarryStandard(plan: QuarryStandardPlan, options: QuarryStandardOptions): QuarryStandardKit {
  const { lib, detail, groundAt } = options;
  const low = detail === 'low', size = low ? 128 : 256;
  const meshes: THREE.Mesh[] = [], batches: PropBatch[] = [], scroll: QuarryStandardKit['scroll'] = [];
  const ownedGeo = new Set<THREE.BufferGeometry>(), ownedMat = new Set<THREE.Material>(), ownedTex = new Set<THREE.Texture>();
  const surfaces = Object.fromEntries((['strata', 'dust', 'steel', 'pool'] as const).map(s => {
    const [m, maps] = material(s, size, lib); ownedMat.add(m); maps.forEach(t => ownedTex.add(t)); return [s, m];
  })) as Record<Surface, THREE.MeshStandardMaterial>;
  const mesh = (name: string, geo: THREE.BufferGeometry, mat: THREE.Material): THREE.Mesh => {
    ownedGeo.add(geo); const m = new THREE.Mesh(geo, mat);
    m.name = `zone:quarry-standard:${name}`; m.receiveShadow = true;
    meshes.push(m); return m;
  };
  const batch = (name: string, geo: THREE.BufferGeometry, mat: THREE.Material): PropBatch => {
    ownedGeo.add(geo); const b = new PropBatch(`quarry-standard:${name}`, geo, mat, false);
    batches.push(b); return b;
  };
  const cols = new Set<number>();
  for (let x = plan.x0 - 20; x <= plan.x1 + 20; x += 3) cols.add(x);
  for (const c of plan.contacts) { cols.add(c.x0); cols.add(c.x1); }
  const xs = [...cols].sort((a, b) => a - b);
  const rows = [-112, -94, -79, -67, -55, -51, -45, -43, -37, -33, -29, -25, -21, -17, -13, -9, -7, -3, 2, 3.4, 5, 8, 13, 45];
  const height = (x: number, z: number): number => quarryCutY(plan, groundAt, x, z);
  mesh('excavated-terraces', groundGeometry(xs, rows, height, (x, z, y) => {
    const d = z >= -9 ? 0 : Math.max(0, Math.min(1, (-z - 9) / 50));
    const c = z >= 2 ? C.shade : z >= -3 ? C.pale : z >= -9 ? C.bed : d > 0.8 ? C.shade : C.bed;
    const facet = 0.9 + 0.13 * key(plan.seed, x * 0.47 + z, 15);
    const shade = Math.max(0.75, Math.min(1, 0.95 + (y - plan.pitY) * 0.01));
    return [c[0] * facet * shade, c[1] * facet * shade, c[2] * facet * shade];
  }, [-3, 2]), surfaces.strata);
  const bedding = contactBedding(plan);
  if (bedding) mesh('d1-contact-bedding', bedding, surfaces.strata);

  // Pools occupy selected pit-floor bays. The surrounding floor remains open;
  // there is no long cyan stripe across every camera frame.
  for (const [x0, x1] of plan.poolRanges) {
    const px = [x0, x0 + 8, x1 - 8, x1];
    const pz = [-68, -59, -51.5];
    const water = groundGeometry(px, pz, () => plan.pitY + 0.14, (x, z) => {
      const k = 0.84 + key(plan.seed, x + z, 22) * 0.16;
      return [C.pool[0] * k, C.pool[1] * k, C.pool[2] * k];
    });
    mesh('mineral-pool', water, surfaces.pool).receiveShadow = false;
  }
  scroll.push({ tex: surfaces.pool.normalMap!, vx: 0.003, vy: -0.006 });

  const ridge = batch('broken-far-ridge', ridgeGeometry(plan.seed ^ 0x9e37), surfaces.strata);
  for (let x = Math.ceil(plan.x0 / 72) * 72; x < plan.x1 + 70; x += 72) {
    if (key(plan.seed, x, 27) < 0.23) continue;
    ridge.add(x + 12 * key(plan.seed, x, 28), plan.pitY, -107 - 8 * key(plan.seed, x, 29),
      0, 0.9 + key(plan.seed, x, 30) * 0.45);
  }
  const machines = new Map<QuarryLandmarkKind, PropBatch>();
  for (const a of plan.landmarks) {
    let b = machines.get(a.kind);
    if (!b) {
      const geo = a.kind === 'drill' ? drillGeometry(low) : a.kind === 'crusher' ? crusherGeometry(low)
        : a.kind === 'haul' ? haulGeometry(low) : gantryGeometry(low);
      b = batch(a.kind, geo, surfaces.steel); machines.set(a.kind, b);
    }
    const y = a.z < -38 ? plan.pitY + 0.08 : height(a.x, a.z);
    b.add(a.x, y, a.z, a.yaw, a.scale);
  }
  const scree = batch('angular-scree', G.merge([
    G.box(0.8, 0.32, 0.65, -0.25, 0.15, 0, C.bed, 0.16),
    G.box(0.55, 0.19, 0.42, 0.42, 0.08, -0.22, C.pale, -0.2),
  ]), surfaces.strata);
  for (let x = Math.ceil(plan.x0 / 8) * 8; x < plan.x1; x += 8) {
    if (plan.protectedWindows.some(([a, b]) => x >= a - 6 && x <= b + 6)) continue;
    if (key(plan.seed, x, 31) < 0.46) continue;
    const z = key(plan.seed, x, 32) < 0.5 ? -7.7 : 6.8;
    scree.add(x, height(x, z) - 0.03, z, key(plan.seed, x, 33) * 0.5 - 0.25,
      0.55 + key(plan.seed, x, 34) * 0.5);
  }
  const textureBytes = ownedTex.size * size * size * 4 * 1.33;
  let mapsDisposed = false, disposed = false;
  const disposeMaps = (): void => {
    if (mapsDisposed) return; mapsDisposed = true;
    for (const t of ownedTex) t.dispose();
  };
  return { meshes, batches, textureBytes, scroll, disposeMaps,
    dispose() {
      if (disposed) return; disposed = true;
      for (const g of ownedGeo) g.dispose();
      for (const m of ownedMat) m.dispose();
      disposeMaps(); meshes.length = 0; batches.length = 0; scroll.length = 0;
    } };
}
