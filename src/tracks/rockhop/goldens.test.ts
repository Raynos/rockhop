/**
 * Every ROCKHOP course's skill-3 golden (`harness/inputs/<id>/bot-3.json`, the recording the store evidence, the
 * clip sheets and `harness:determinism` stand on) still finishes when replayed in node on today's
 * physics and today's geometry. The C3 Rookie reference intentionally includes one breach failure and a clean
 * retry, asserted separately with its exact finish hash. A physics or geometry change that breaks a golden fails here, in CI, instead of in
 * the next evidence run: a736a26f (riding-poses physics) left all sixteen short of the line (1-10 faults each) and
 * nothing red said so. Re-record with `pnpm harness:bot <id>` on the new tree.
 */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { describe, expect, it } from 'vitest';
import { expandFrames, quantizeInput } from '../../core/replay';
import { createSim, createSimFor } from '../../../harness/lib/sim';
import { loadRecording } from '../../../harness/lib/recording';
import { ROCKHOP_ALL } from '../index';

const INPUTS = fileURLToPath(new URL('../../../harness/inputs/', import.meta.url));

describe('ROCKHOP goldens replay in node', () => {
  it.each(ROCKHOP_ALL.filter((t) => t.id !== 'c3-hull-breach').map((t) => [t.id] as const))('%s: bot-3.json finishes with 0 faults', async (id) => {
    const file = path.join(INPUTS, id, 'bot-3.json');
    expect(fs.existsSync(file), `${id} has no golden`).toBe(true);
    const rec = loadRecording(file);
    expect(rec.header.trackId).toBe(id);
    expect(rec.header.bike ?? 'rookie').toBe('rookie');
    const sim = await createSimFor(rec);
    sim.run(expandFrames(rec));
    expect({ phase: sim.phase(), faults: sim.faults() }).toEqual({ phase: 'finished', faults: 0 });
  });

  it('C3 Rookie breach reference crashes once, then finishes with the pinned hash', async () => {
    const rec = loadRecording(path.join(INPUTS, 'c3-hull-breach', 'bot-3.json'));
    const sim = await createSimFor(rec);
    sim.run(expandFrames(rec));
    expect({ phase: sim.phase(), faults: sim.faults(), hash: sim.hash() }).toEqual({
      phase: 'finished', faults: 1, hash: '979d7d28f04cc732',
    });
  });

  it('C3 Pro has a fault-free reference on the same breach', async () => {
    const rec = loadRecording(path.join(INPUTS, 'c3-hull-breach', 'bot-3-pro.json'));
    const sim = await createSimFor(rec);
    sim.run(expandFrames(rec));
    expect({ phase: sim.phase(), faults: sim.faults(), hash: sim.hash() }).toEqual({
      phase: 'finished', faults: 0, hash: '516f6212e2cf6954',
    });
  });

  it('C1 Pro brake line clears without a fault', async () => {
    const rec = loadRecording(path.join(INPUTS, 'c1-low-tide', 'bot-3-pro.json'));
    const sim = await createSimFor(rec);
    sim.run(expandFrames(rec));
    expect({ phase: sim.phase(), faults: sim.faults() }).toEqual({ phase: 'finished', faults: 0 });
  });

  it.each(['rookie', 'pro'] as const)('C1 %s cannot clear by holding GO for 90 seconds', async (bike) => {
    const sim = await createSim('c1-low-tide', undefined, 120, { bike });
    const go = quantizeInput({ throttle: 1 });
    for (let tick = 0; tick < 90 * sim.hz && sim.phase() !== 'finished'; tick++) sim.step(go);
    expect(sim.phase()).not.toBe('finished');
    expect(sim.faults()).toBeGreaterThan(0);
  });

  it('C2 Pro corrected landing clears without a fault', async () => {
    const rec = loadRecording(path.join(INPUTS, 'c2-crane-hop', 'bot-3-pro.json'));
    const sim = await createSimFor(rec);
    sim.run(expandFrames(rec));
    expect({ phase: sim.phase(), faults: sim.faults(), hash: sim.hash() }).toEqual({
      phase: 'finished', faults: 0, hash: '64ec5d60318654fd',
    });
  });

  it.each(['rookie', 'pro'] as const)('C2 %s cannot clear by holding GO for 90 seconds', async (bike) => {
    const sim = await createSim('c2-crane-hop', undefined, 120, { bike });
    const go = quantizeInput({ throttle: 1 });
    for (let tick = 0; tick < 90 * sim.hz && sim.phase() !== 'finished'; tick++) sim.step(go);
    expect(sim.phase()).not.toBe('finished');
    expect(sim.faults()).toBeGreaterThan(0);
  });
});
