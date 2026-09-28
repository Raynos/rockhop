/** Exact Node/browser proof for an opt-in upper deck, with a lower-route control. */
import { createSim } from './lib/sim';
import { launchBrowser } from './lib/browser';
import { HookClient, openGame } from './lib/hook';
import { startServer } from './lib/server';
import { InputRecorder, encodeJSON, expandFrames, quantizeInput } from '../src/core/replay';
import type { TrackDef } from '../src/core/types';
import { registerTrack } from '../src/tracks';
import { decodeSnapshot } from '../src/game/hook';
import { medalFor } from '../src/game/rules';

function fixture(id: string, upper: boolean): TrackDef {
  return {
    id, name: 'Open Deck Proof', tier: 'beginner', seed: 712,
    profile: [{ x: -10, y: 0 }, { x: 120, y: 0 }],
    obstacles: [{ kind: 'open-platform', pos: { x: 20, y: 0 }, params: { length: 30, height: 2.5, thickness: 0.18, surface: 'wood' } }],
    checkpoints: [], start: { pos: upper ? { x: 21, y: 2.5 } : { x: 0, y: 0 }, angle: 0 }, finishX: 65,
    diamondGoal: { id: 'upper-deck', platformObstacleIndex: 0, x: 35, minRearY: 2.7 },
    meta: { biome: 'industrial', technique: 'cross the upper deck', targetTimeS: 90 },
  };
}

const fixtures = [fixture('route-upper-proof', true), fixture('route-lower-proof', false)];
for (const track of fixtures) registerTrack(track);
const rows = [];
const server = await startServer({ dev: true });
const browser = await launchBrowser({ width: 852, height: 392 });
try {
  await openGame(browser.page, server.url);
  await browser.page.evaluate(async (tracks) => {
    const modulePath = '/src/tracks/index.ts';
    const { registerTrack } = await import(modulePath);
    for (const track of tracks) registerTrack(track);
  }, fixtures);
  const hook = new HookClient(browser.page);
  for (const track of fixtures) {
    const sim = await createSim(track.id, track.seed, 120, { bike: 'rookie' });
    const recorder = new InputRecorder({ version: 1, trackId: track.id, seed: track.seed, physicsHz: 120, bike: 'rookie', physics: 'v2' });
    for (let tick = 0; tick < 120 * 20 && sim.phase() !== 'finished'; tick++) {
      const frame = quantizeInput({ throttle: 0.65, lean: 0.2 });
      recorder.push(frame);
      sim.step(frame);
    }
    if (sim.phase() !== 'finished') throw new Error(`${track.id}: no finish (${sim.phase()}, x=${sim.state().bike.pos.x}, faults=${sim.faults()})`);
    const json = encodeJSON(recorder.toRecording());
    const replay = await createSim(track.id, track.seed, 120, { bike: 'rookie' });
    replay.run(expandFrames(recorder.toRecording()));
    const browserRun = await hook.runRecording(json);
    const browserCounters = decodeSnapshot(await browser.page.evaluate(() => window.__rockhop!.snapshot())).counters;
    const crossed = sim.rules.counters().diamondRouteCrossed === true;
    const expected = track.id === 'route-upper-proof';
    const row = { track: track.id, finishTick: sim.runTicks(), faults: sim.faults(),
      nodeHash: sim.hash(), replayHash: replay.hash(), browserHash: browserRun.hash,
      nodeProof: crossed, replayProof: replay.rules.counters().diamondRouteCrossed === true,
      browserProof: browserCounters?.diamondRouteCrossed === true,
      medal: medalFor(sim.runTime(), sim.faults(), track.meta!.targetTimeS, 'rookie', crossed) };
    rows.push(row);
    if (crossed !== expected || row.replayProof !== crossed || row.browserProof !== crossed ||
        row.nodeHash !== row.replayHash || row.nodeHash !== row.browserHash || sim.faults() !== 0) {
      throw new Error(`route mismatch: ${JSON.stringify(row)}`);
    }
  }
} finally {
  await browser.close();
  await server.close();
}
process.stdout.write(`${JSON.stringify(rows, null, 2)}\n`);
