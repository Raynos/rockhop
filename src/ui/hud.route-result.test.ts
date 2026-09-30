// @vitest-environment jsdom
import { describe, expect, it } from 'vitest';
import type { RunResult } from '../core/types';
import { medalFor, targetForBike } from '../game/rules';
import { D3 } from '../tracks/rockhop/quarry';
import { medalHints } from './hud';

// Measured current-Pro lower finish (pro-envelope/d3-pro-mechanic.json,
// hash 1a78b2cf3f3e2f3f). Keep the small regression fixture inside CI's sparse tree.
const lower = { time: 31.933333333333334, proof: false };
const result: Pick<RunResult, 'medal' | 'targetTimeS' | 'time' | 'faults' | 'routeProof'> = {
  medal: medalFor(lower.time, 0, D3.meta!.targetTimeS, 'pro', lower.proof),
  targetTimeS: targetForBike(D3.meta!.targetTimeS, 'pro'),
  time: lower.time,
  faults: 0,
  routeProof: { goalId: D3.diamondGoal!.id, crossed: lower.proof },
};

describe('results explain the missing Diamond route', () => {
  it('gives the measured fast, clean lower-route Gold finish an actionable route goal', () => {
    expect(result.medal).toBe('gold');
    expect(result.time).toBeLessThan(result.targetTimeS! * 0.85);
    expect(medalHints(result)).toMatchObject({ next: 'platinum', text: { platinum: 'Take the upper route to earn' } });
  });

  it('retains unmet clock and no-bail requirements alongside the missing route', () => {
    expect(medalHints({ ...result, time: 35, faults: 1 }).text.platinum)
      .toBe('Take the upper route · 0:33.469 · no bails to earn');
    expect(medalHints({ ...result, faults: 1 }).text.platinum)
      .toBe('Take the upper route · no bails to earn');
    expect(medalHints({ ...result, time: 35 }).text.platinum)
      .toBe('Take the upper route · 0:33.469 to earn');
  });

  it('preserves crossed, unknown and ordinary-course clock/bail instructions', () => {
    const { routeProof: _routeProof, ...ordinary } = result;
    for (const variant of [{ ...result, routeProof: { goalId: D3.diamondGoal!.id, crossed: true } }, ordinary]) {
      expect(medalHints({ ...variant, time: 35 }).text.platinum).toBe('0:33.469 to earn');
      expect(medalHints({ ...variant, faults: 1 }).text.platinum).toBe('No bails to earn');
    }
    expect(medalHints({ medal: 'gold', targetTimeS: 30, time: 28, faults: 0 }).text.platinum)
      .toBe('0:25.500 to earn');
  });

  it('does not make the upper route a requirement for Silver or Gold', () => {
    expect(medalHints({ ...result, medal: 'bronze', faults: 6 }))
      .toMatchObject({ next: 'silver', text: { silver: '≤ 5 bails to earn' } });
    expect(medalHints({ ...result, medal: 'silver', faults: 2 }))
      .toMatchObject({ next: 'gold', text: { gold: '≤ 1 bail to earn' } });
  });
});
