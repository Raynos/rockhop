import { describe, expect, it } from 'vitest';
import { NEUTRAL_INPUT } from '../../src/core/types';
import { createSim } from './sim';

describe('Node run rules at the start line', () => {
  it('retains a fault after a checkpointless respawn and clears it only on a full restart', async () => {
    const sim = await createSim('flat-test');
    sim.step({ ...NEUTRAL_INPUT, restart: true });
    expect(sim.state().checkpoint).toBe(-1);
    expect(sim.faults()).toBe(1);
    sim.step(NEUTRAL_INPUT);
    expect(sim.faults()).toBe(1);

    for (let tick = 0; tick < sim.rules.T.holdRestart; tick++) sim.step({ ...NEUTRAL_INPUT, restart: true });
    expect(sim.state().checkpoint).toBe(-1);
    expect(sim.faults()).toBe(0);
    expect(sim.runTime()).toBe(0);
  });
});
