/** Run actual seeded builders in Node; canvas pixels are stubbed, placements are not. */
import * as THREE from 'three';
import { readFileSync, writeFileSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { A1 } from '../../../../src/tracks/rockhop/alpine';
import { compileTrack } from '../../../../src/tracks/compile';
import { MaterialLibrary } from '../../../../src/render/materials/library';
import { BIOMES } from '../../../../src/render/biomes';
import { buildBiomeKit } from '../../../../src/render/world/biomeKit';
import { buildRideSurfaces } from '../../../../src/render/world/deck';
import { buildObstacles } from '../../../../src/render/world/obstacles';
import { buildGates } from '../../../../src/render/world/gates';
import { PropBatch } from '../../../../src/render/world/props';
import type { ArtLibrary } from '../../../../src/render/art/library';

const noop = () => {};
const gradient = { addColorStop: noop };
const context = new Proxy<Record<string, unknown>>({}, { get(target, key) {
  if (key in target) return target[key as string];
  if (key === 'createLinearGradient' || key === 'createRadialGradient') return () => gradient;
  if (key === 'getImageData' || key === 'createImageData') return (_x: number, _y: number, w: number, h: number) => ({ data: new Uint8ClampedArray((w ?? _x) * (h ?? _y) * 4) });
  if (key === 'measureText') return () => ({ width: 100 });
  return noop;
} });
Object.defineProperty(globalThis, 'document', { value: { createElement: () => ({ width: 0, height: 0, getContext: () => context }) }, configurable: true });
const textures = new Map<string, THREE.Texture>();
const art = {
  texture(id: string) {
    let texture = textures.get(id);
    if (!texture) { texture = new THREE.DataTexture(new Uint8Array([128,128,128,255]), 1, 1); textures.set(id, texture); }
    return texture;
  },
  entry() { return { bytes: 0 }; },
  has() { return true; },
  bitmap() { return { width: 512, height: 512 }; },
} as unknown as ArtLibrary;
const rows: { name: string; index: number; x: number; y: number; z: number; matrix: number[] }[] = [];
const originalAdd = PropBatch.prototype.add;
PropBatch.prototype.add = function(...args: Parameters<typeof originalAdd>) {
  originalAdd.apply(this, args);
  if (/^pine(?:far)?\d$/.test(this.name) || this.name === 'contactshadow') {
    const matrix = this.items[this.items.length - 1]!.m.elements.slice();
    rows.push({ name: this.name, index: this.items.length - 1, x: matrix[12]!, y: matrix[13]!, z: matrix[14]!, matrix });
  }
};
const compiled = compileTrack(A1);
PropBatch.CHUNK_M = 40;
const library = new MaterialLibrary(A1.seed);
const kit = buildBiomeKit(compiled, BIOMES.alpine, library, art, 'high');
PropBatch.prototype.add = originalAdd;
const proposal = JSON.parse(readFileSync(new URL('../../../../docs/evidence/course-remaster/alpine-tree-kit/a1-placement-proposal.json', import.meta.url), 'utf8'));
const ranges = proposal.replaceExistingTreeRanges as [number, number][];
const trees = rows.filter(row => /^pine\d$/.test(row.name));
const selected = trees.filter(row => row.z < 0 && row.z > -28 && ranges.some(([x0,x1]) => row.x >= x0 && row.x <= x1));
const selectedShadows = rows.filter(row => row.name === 'contactshadow' && selected.some(tree => Math.abs(tree.x-row.x)<1e-8 && Math.abs(tree.z-row.z)<1e-8));
const ribbons = buildRideSurfaces(compiled, BIOMES.alpine, library);
const obstacles = buildObstacles(compiled, library);
const gates = buildGates(compiled, BIOMES.alpine, library, art);
function constructed(group: THREE.Group) {
  let meshes = 0, triangles = 0, materialDraws = 0, shadowMeshes = 0;
  group.traverse(object => {
    if (!(object instanceof THREE.Mesh)) return;
    meshes++; if (object.castShadow) shadowMeshes++;
    materialDraws += Array.isArray(object.material) ? object.geometry.groups.length : 1;
    triangles += (object.geometry.index?.count ?? object.geometry.getAttribute('position').count) / 3 * (object instanceof THREE.InstancedMesh ? object.count : 1);
  });
  return { meshes, materialDraws, triangles, shadowMeshes };
}
const worldGroups = { biome: kit.group, rideSurfaces: ribbons.group, rideSupports: ribbons.supports, obstacles: obstacles.group, gates: gates.group };
const worldCounts = Object.fromEntries(Object.entries(worldGroups).map(([name, group]) => [name, constructed(group)]));
const allWorld = new THREE.Group(); allWorld.add(...Object.values(worldGroups));
const allWorldCounts = constructed(allWorld);
const report = {
  track: A1.id, trackHash: compiled.hash, seed: A1.seed, detail: 'high', chunkMetres: PropBatch.CHUNK_M,
  note: 'Actual seeded biome builder; dummy art pixels enter the same present-art branch without changing RNG. These are constructed geometry counts, not GPU frame samples.',
  sourceHashes: Object.fromEntries(['src/render/world/zones/zoneKit.ts','src/render/world/biomeKit.ts','src/tracks/rockhop/alpine.ts'].map(file => [file, createHash('sha256').update(readFileSync(file)).digest('hex')])),
  biomeReportedDraws: kit.drawCalls, biomeConstructedMeshNodes: worldCounts.biome!.meshes, biomeConstructedTriangles: worldCounts.biome!.triangles,
  constructedWorld: worldCounts, constructedWorldTotal: allWorldCounts,
  allOriginalTreePlacements: rows.filter(row => /^pine/.test(row.name)),
  removeTrees: selected, removeContactShadows: selectedShadows,
};
writeFileSync(new URL('../../../../docs/evidence/course-remaster/alpine-tree-kit/a1-existing-tree-audit.json', import.meta.url), JSON.stringify(report, null, 2)+'\n');
console.log(JSON.stringify({ biomeReportedDraws: kit.drawCalls, constructedWorldTotal: allWorldCounts, removeTrees: selected.map(({name,index,x,z})=>({name,index,x,z})), removeContactShadows: selectedShadows.map(({index,x,z})=>({index,x,z})) }, null, 2));
