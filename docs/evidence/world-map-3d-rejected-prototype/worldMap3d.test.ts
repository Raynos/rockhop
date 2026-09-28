// @vitest-environment jsdom
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { ROCKHOP_ALL } from '../tracks';
import { ANCHOR, buildRegions } from './worldMap';
import { mapPoint, terrainHeight, WorldMapDiorama } from './worldMap3d';

beforeEach(() => { vi.spyOn(HTMLCanvasElement.prototype, 'getContext').mockReturnValue(null); });
afterEach(() => { vi.restoreAllMocks(); });

describe('procedural 3D world map', () => {
  it('models the twelve campaign destinations on terrain with biome relief', () => {
    const map = new WorldMapDiorama(document.createElement('canvas'), buildRegions(ROCKHOP_ALL, () => null));
    expect(map.places.size).toBe(12);
    expect(map.places.get('c1-low-tide')?.children.length).toBeGreaterThan(3);
    expect(map.places.get('s3-whiteout')?.children.length).toBeGreaterThan(3);
    for (const [id, p] of map.places) {
      const a = ANCHOR[id]!;
      expect(p.position.x).toBeCloseTo(mapPoint(a.x, a.y).x);
      expect(p.position.y).toBeCloseTo(terrainHeight(a.x, a.y) + 0.17);
    }
    expect(terrainHeight(1300, 260)).toBeGreaterThan(terrainHeight(120, 660));
    expect(map.sceneRoot.children.length).toBeGreaterThan(15);
    map.select('c1-low-tide');
    expect(map.places.get('c1-low-tide')?.children.some((child) => child.visible && child.type === 'Mesh')).toBe(true);
    map.dispose();
  });
});
