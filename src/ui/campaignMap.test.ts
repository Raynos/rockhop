import { describe, expect, it } from 'vitest';
import type { Medal } from '../core/types';
import { ROCKHOP_ALL } from '../tracks';
import { CareerEconomy, PRO_PRICE } from './economy';
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

  it('requires eight Starter medals, one Pro purchase, and Pro equipped for courses 9–12', () => {
    const economy = new CareerEconomy(null);
    const ids = ROCKHOP_ALL.slice(0, 8).map((track) => track.id);
    const medalOf = (id: string) => economy.snapshot().medals[id] ?? null;
    ids.slice(0, 7).forEach((id) => economy.award(id, 'bronze'));
    let markers = buildCampaignMarkers(ROCKHOP_ALL, medalOf);
    expect(markers[8]).toMatchObject({ locked: true, garage: false, rule: 'Medal levels 01–08 to unlock the Pro run' });
    economy.award(ids[7]!, 'bronze');
    expect(economy.snapshot().wallet).toBe(800);
    markers = buildCampaignMarkers(ROCKHOP_ALL, medalOf);
    expect(markers[7]).toMatchObject({ locked: false, garage: false });
    expect(markers[8]).toMatchObject({ locked: true, garage: true, rule: 'Buy the Pro bike in Garage · 1840 Scrap' });
    expect(economy.purchasePro()).toBe('insufficient-scrap');
    ids.slice(0, 7).forEach((id) => economy.award(id, 'gold'));
    economy.award(ids[7]!, 'platinum');
    expect(economy.snapshot().wallet).toBe(PRO_PRICE);
    expect(economy.purchasePro()).toBe('purchased');
    markers = buildCampaignMarkers(ROCKHOP_ALL, medalOf, economy.snapshot());
    expect(markers[8]).toMatchObject({ locked: true, garage: true, rule: 'Equip the Pro bike in Garage' });
    expect(economy.equip('pro')).toBe(true);
    markers = buildCampaignMarkers(ROCKHOP_ALL, medalOf, economy.snapshot());
    expect(markers[8]).toMatchObject({ locked: false, garage: false });
    expect(markers[9]?.rule).toBe('Medal every Quarry track');
    economy.award(ROCKHOP_ALL[8]!.id, 'bronze');
    markers = buildCampaignMarkers(ROCKHOP_ALL, medalOf, economy.snapshot());
    expect(markers.slice(8).every((marker) => !marker.locked)).toBe(true);
    expect(economy.equip('rookie')).toBe(true);
    markers = buildCampaignMarkers(ROCKHOP_ALL, medalOf, economy.snapshot());
    expect(markers.slice(8).every((marker) => marker.locked && marker.garage)).toBe(true);
    expect(buildCampaignMarkers(ROCKHOP_ALL, medalOf, economy.snapshot(), true).slice(8).every((marker) => !marker.locked)).toBe(true);
  });
});
