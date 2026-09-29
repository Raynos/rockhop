import * as THREE from 'three';
import { expect, it, vi } from 'vitest';
import { compileTrack, getTrack, hashColliders } from '../../tracks';
import type { MaterialLibrary } from '../materials/library';
import { MaterialLibrary as RealMaterialLibrary } from '../materials/library';
import { buildObstacles } from './obstacles';

it('Snow Line retains its wood ramps, crate and plank in one material batch without merge errors', () => {
  const track = compileTrack(getTrack('p3-snow-line')!);
  const before = hashColliders(track.colliders);
  const lib = { get: () => new THREE.MeshStandardMaterial() } as unknown as MaterialLibrary;
  const errors = vi.spyOn(console, 'error').mockImplementation(() => {});
  try {
    const result = buildObstacles(track, lib);
    expect(errors.mock.calls).toEqual([]);
    const plywood = result.group.getObjectByName('obstacles:plywood') as THREE.Mesh | undefined;
    expect(plywood).toBeDefined();
    expect(hashColliders(track.colliders)).toBe(before);
    // Compare the full material batch to rendering each placed obstacle independently:
    // batching may change indexing, but it must not discard any triangle or its attributes.
    const rows = (mesh: THREE.Mesh | undefined): string[] => {
      if (!mesh) return [];
      const g = mesh.geometry;
      const attrs = ['position', 'normal', 'uv'].map(name => g.getAttribute(name));
      const out: string[] = [];
      for (let j = 0; j < (g.index?.count ?? attrs[0]!.count); j++) {
        const i = g.index ? g.index.getX(j) : j;
        out.push(attrs.flatMap(a => Array.from({ length: a.itemSize }, (_, k) => a.array[i * a.itemSize + k])).join(','));
      }
      return out.sort();
    };
    const expected: string[] = [];
    for (const placed of track.placed) {
      const part = buildObstacles({ ...track, placed: [placed], colliders: track.colliders.filter(c => placed.colliderIds.includes(c.id)), hazards: [] }, lib);
      expected.push(...rows(part.group.getObjectByName('obstacles:plywood') as THREE.Mesh | undefined));
    }
    expect(rows(plywood)).toEqual(expected.sort());
    expect(errors.mock.calls).toEqual([]);
  } finally { errors.mockRestore(); }
});

it('Container Step skins retain the exact authored collision and batch both reference colors', () => {
  const track = compileTrack(getTrack('lab-box-climb')!);
  const before = hashColliders(track.colliders);
  const lib = { get: () => new THREE.MeshStandardMaterial() } as unknown as MaterialLibrary;
  const result = buildObstacles(track, lib);
  expect(hashColliders(track.colliders)).toBe(before);
  expect(result.group.getObjectByName('obstacles:labContainerRed')).toBeDefined();
  expect(result.group.getObjectByName('obstacles:labContainerIvory')).toBeDefined();
  expect(result.group.getObjectByName('obstacles:darkSteel')).toBeDefined();
  expect(result.drawCalls).toBeLessThan(10);
});

it('D3 high bridge adds a truss below the one-way deck and keeps the lower road open', () => {
  const track = compileTrack(getTrack('d3-rope-walk')!);
  const placed = track.placed.find((p) => p.kind === 'open-platform')!;
  const deckOnly = { ...track, placed: [placed], colliders: track.colliders.filter((c) => placed.colliderIds.includes(c.id)), hazards: [] };
  const collisionHash = hashColliders(track.colliders);
  const bridge = buildObstacles(deckOnly, new RealMaterialLibrary(1));
  const generic = buildObstacles({ ...deckOnly, def: { ...track.def, id: 'other-track' } }, new RealMaterialLibrary(1));
  expect(hashColliders(track.colliders)).toBe(collisionHash);
  expect(bridge.drawCalls).toBe(generic.drawCalls);
  expect(bridge.triangles).toBeGreaterThan(generic.triangles);
  expect(bridge.triangles).toBeLessThan(2000);
  for (const mesh of bridge.group.children as THREE.Mesh[]) {
    const p = mesh.geometry.getAttribute('position');
    for (let i = 0; i < p.count; i++) {
      const x = p.getX(i), y = p.getY(i), z = p.getZ(i);
      expect(y).toBeLessThanOrEqual(3.5);
      // Keep visible steel out of the traversable lower corridor, including the rider's headroom.
      if (x > 397 && x < 429 && Math.abs(z) < 1.6) expect(y).toBeGreaterThan(2.15);
    }
  }
});
