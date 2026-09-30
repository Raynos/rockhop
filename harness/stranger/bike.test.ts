import { describe, expect, it } from 'vitest';
import { ROCKHOP_TRACKS } from '../../src/tracks/rockhop';
import { bikeForTrack, campaignBikeForTrack, defaultStrangerBike, reflexBikesForTrack } from './bike';

describe('stranger bike mirrors a new campaign profile', () => {
  it('defaults the first eight courses to Rookie and the final four to earned Pro', () => {
    expect(ROCKHOP_TRACKS.map(({ id }) => [id, campaignBikeForTrack(id)])).toEqual([
      ['c1-low-tide', 'rookie'], ['c2-crane-hop', 'rookie'], ['c3-hull-breach', 'rookie'],
      ['a1-sawdust', 'rookie'], ['a2-log-jam', 'rookie'], ['a3-timberline', 'rookie'],
      ['d1-dust-devil', 'rookie'], ['d2-conveyor', 'rookie'],
      ['d3-rope-walk', 'pro'], ['s1-lift-line', 'pro'], ['s2-cornice', 'pro'], ['s3-whiteout', 'pro'],
    ]);
    expect(defaultStrangerBike('d3-rope-walk')).toBe('pro');
  });

  it('honors explicit diagnostic bike choices and retains legacy stranger defaults', () => {
    expect(bikeForTrack('s3-whiteout', 'rookie')).toBe('rookie');
    expect(bikeForTrack('c1-low-tide', 'pro')).toBe('pro');
    expect(defaultStrangerBike('h2-gap-chain')).toBe('pro');
  });

  it('selects career bikes for reflex runs without changing retired defaults or both-bike sweeps', () => {
    expect(reflexBikesForTrack('d2-conveyor', undefined)).toEqual(['rookie']);
    expect(reflexBikesForTrack('d3-rope-walk', undefined)).toEqual(['pro']);
    expect(reflexBikesForTrack('h2-gap-chain', undefined)).toEqual(['rookie']);
    expect(reflexBikesForTrack('d3-rope-walk', 'rookie')).toEqual(['rookie']);
    expect(reflexBikesForTrack('d3-rope-walk', 'both')).toEqual(['rookie', 'pro']);
  });
});
