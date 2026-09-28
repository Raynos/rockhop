/** A single restart input tick after the first GO crash must hard-cut to Marker 2, identically in browser. */
import { writeFileSync } from 'node:fs';
import { launchBrowser } from '../../harness/lib/browser';
import { HookClient, openGame } from '../../harness/lib/hook';
import { recordingHeader } from '../../harness/lib/recording';
import { createSim } from '../../harness/lib/sim';
import { startServer } from '../../harness/lib/server';
import { InputRecorder } from '../../src/core/replay';
import { registerTrack } from '../../src/tracks';
import { C1_CHALLENGE } from './candidate';

registerTrack(C1_CHALLENGE);
const server = await startServer({ dev: true });
const browser = await launchBrowser({ width: 852, height: 392 });
const rows = [];
try {
  await openGame(browser.page, server.url);
  await browser.page.evaluate(async () => {
    const [{ C1_CHALLENGE }, { registerTrack }] = await Promise.all([
      import('/prototypes/c1-challenge/candidate.ts'), import('/src/tracks/index.ts'),
    ]);
    registerTrack(C1_CHALLENGE);
  });
  const hook = new HookClient(browser.page);
  for (const bike of ['rookie', 'pro'] as const) {
    const sim = await createSim(C1_CHALLENGE.id, C1_CHALLENGE.seed, 120, { bike });
    const rec = new InputRecorder(recordingHeader(sim, 'standalone-c1-challenge first-fault one-tick restart'));
    const GO = { throttle: 1, brake: 0, lean: 0, hop: false, restart: false } as const;
    const RESTART = { ...GO, restart: true } as const;
    let faultTick = -1, firstFaultX = null, checkpointAtFault = null;
    for (let tick = 0; tick < 600 * sim.hz; tick++) {
      const before = sim.state();
      rec.push(GO);
      if (sim.step(GO).some((e) => e.type === 'fault')) {
        faultTick = tick + 1;
        firstFaultX = +before.bike.pos.x.toFixed(2);
        checkpointAtFault = before.checkpoint;
        break;
      }
    }
    if (faultTick < 0) throw new Error(`${bike} GO did not fault`);
    const faultsBefore = sim.faults();
    rec.push(RESTART);
    const restartEvents = sim.step(RESTART);
    const checkpointSpawnX = C1_CHALLENGE.checkpoints[checkpointAtFault!]?.spawn.pos.x;
    const state = sim.state();
    const json = `${JSON.stringify({ magic: 'TRIN', ...rec.toRecording() })}\n`;
    writeFileSync(new URL(`../../docs/evidence/c1-challenge/${bike}-one-tick-restart.json`, import.meta.url), json);
    const browserRun = await hook.runRecording(json);
    const browserPhase = await browser.page.evaluate(() => window.__rockhop!.phase());
    const row = {
      bike, faultTick, firstFaultX, checkpointAtFault, checkpointSpawnX,
      restartTick: faultTick + 1, restartEvents,
      nodePhase: sim.phase(), browserPhase,
      nodeCheckpoint: state.checkpoint, browserCheckpoint: browserRun.state.checkpoint,
      nodeBikeX: state.bike.pos.x, browserBikeX: browserRun.state.bike.pos.x,
      nodeFaultsBefore: faultsBefore, nodeFaultsAfter: sim.faults(),
      nodeHash: sim.hash(), browserHash: browserRun.hash,
      exact: sim.hash() === browserRun.hash && sim.phase() === 'riding' && browserPhase === 'riding' && sim.faults() === faultsBefore && state.checkpoint === checkpointAtFault && browserRun.state.checkpoint === checkpointAtFault && Math.abs(state.bike.pos.x - checkpointSpawnX!) < 1,
    };
    rows.push(row);
    process.stdout.write(`${bike} ${JSON.stringify(row)}\n`);
    if (!row.exact) throw new Error(`${bike} restart mismatch`);
  }
} finally {
  await browser.close();
  await server.close();
}
writeFileSync(new URL('../../docs/evidence/c1-challenge/restart-verify.json', import.meta.url), `${JSON.stringify(rows, null, 2)}\n`);
