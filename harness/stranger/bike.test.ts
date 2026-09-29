import { describe, expect, it } from 'vitest';
import { bikeForTrack, defaultStrangerBike } from './bike';

describe('stranger bike mirrors a new campaign profile', () => {
  it('starts every ROCKHOP course on the owned Rookie, even hard and extreme', () => {
    expect(defaultStrangerBike('d2-conveyor')).toBe('rookie');
    expect(defaultStrangerBike('d3-rope-walk')).toBe('rookie');
    expect(defaultStrangerBike('s3-whiteout')).toBe('rookie');
  });

  it('keeps earned Pro as an explicit route test and legacy tier defaults intact', () => {
    expect(bikeForTrack('s3-whiteout', 'pro')).toBe('pro');
    expect(defaultStrangerBike('h2-gap-chain')).toBe('pro');
  });
});
