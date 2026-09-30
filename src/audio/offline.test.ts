import { describe, expect, it } from 'vitest';
import { renderScript } from './offline';
import { blankState } from './tools/fixture';

const moving = (): ReturnType<typeof blankState> => {
  const state = blankState();
  state.engine = { rpm: 7200, throttleEff: 1, limiter: false };
  state.bike.vel.x = 8;
  state.wheels.rear.spinVel = 20;
  state.wheels.front.spinVel = 20;
  return state;
};
const peak = (pcm: Float32Array): number => pcm.reduce((largest, sample) => Math.max(largest, Math.abs(sample)), 0);

describe('offline live-scene consistency', () => {
  it('front scenes silence a stale moving bike while the procedural fallback music remains available', () => {
    for (const scene of ['menu', 'map', 'results'] as const) {
      const engine = renderScript(moving, 0.3, { scene, solo: 'engine' });
      const tyres = renderScript(moving, 0.3, { scene, solo: 'tyres' });
      expect(peak(engine.pcm), scene).toBe(0);
      expect(peak(tyres.pcm), scene).toBe(0);
    }
    expect(peak(renderScript(moving, 0.3, { scene: 'run', solo: 'engine' }).pcm)).toBeGreaterThan(0.01);
    expect(peak(renderScript(moving, 1, { scene: 'menu', solo: 'music' }).pcm)).toBeGreaterThan(0.001);
  });

  it('master mute applies from the first sample, including the front fallback music', () => {
    for (const scene of ['menu', 'run', 'results'] as const) {
      const muted = renderScript(moving, 0.3, { scene, masterVolume: 0 });
      expect(peak(muted.pcm), scene).toBe(0);
      expect(Math.abs(muted.pcm[0]!), scene).toBe(0);
    }
  });
});
