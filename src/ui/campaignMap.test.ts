import { describe, expect, it } from 'vitest';
import type { Medal } from '../core/types';
import { ROCKHOP_ALL } from '../tracks';
import { buildCampaignMarkers } from './campaignMap';

const medals: Record<string, Medal> = {
  'c1-low-tide': 'gold',
  'c2-crane-hop': 'silver',
  'c3-hull-breach': 'bronze',
};

describe('3D island campaign markers', () => {
  it('orders exactly twelve towers by the shipped route', () => {
    const markers = buildCampaignMarkers(ROCKHOP_ALL, () => null);
    expect(markers.map((marker) => marker.code)).toEqual([
      'C1', 'C2', 'C3', 'A1', 'A2', 'A3', 'D1', 'D2', 'D3', 'S1', 'S2', 'S3',
    ]);
    expect(markers.map((marker) => marker.region)).toEqual([
      'coast', 'coast', 'coast', 'alpine', 'alpine', 'alpine',
      'quarry', 'quarry', 'quarry', 'snowline', 'snowline', 'snowline',
    ]);
    expect(markers.slice(0, 3).every((marker) => !marker.locked)).toBe(true);
    expect(markers.slice(3).every((marker) => marker.locked)).toBe(true);
    expect(markers[3]?.rule).toBe('Medal every Coast track');
  });

  it('opens Alpine after all three Coast medals and preserves earned tower colors', () => {
    const markers = buildCampaignMarkers(ROCKHOP_ALL, (id) => medals[id] ?? null);
    expect(markers.slice(0, 3).map((marker) => marker.medal)).toEqual(['gold', 'silver', 'bronze']);
    expect(markers.slice(3, 6).every((marker) => !marker.locked)).toBe(true);
    expect(markers.slice(6).every((marker) => marker.locked)).toBe(true);
    expect(markers[6]?.rule).toBe('Medal every Alpine track');
  });
});
