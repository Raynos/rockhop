/** One restart tick after the crane crash must return to checkpoint 2 on both bikes. */
import { writeFileSync } from 'node:fs';
import { launchBrowser } from '../../harness/lib/browser';
import { HookClient, openGame } from '../../harness/lib/hook';
import { recordingHeader } from '../../harness/lib/recording';
import { createSim } from '../../harness/lib/sim';
import { startServer } from '../../harness/lib/server';
import { InputRecorder } from '../../src/core/replay';
import { registerTrack } from '../../src/tracks';
import { C2_CHALLENGE } from './candidate';

registerTrack(C2_CHALLENGE);
const server = await startServer({ dev: true });
const browser = await launchBrowser({ width: 852, height: 392 });
const rows = [];
try {
  await openGame(browser.page, server.url);
  await browser.page.evaluate(async () => {
    const [{ C2_CHALLENGE }, { registerTrack }] = await Promise.all([
      import('/prototypes/c2-challenge/candidate.ts'), import('/src/tracks/index.ts'),
    ]);
    registerTrack(C2_CHALLENGE);
  });
  const hook = new HookClient(browser.page);
  for (const bike of ['rookie', 'pro'] as const) {
    const sim = await createSim(C2_CHALLENGE.id, C2_CHALLENGE.seed, 120, { bike });
    const recorder = new InputRecorder(recordingHeader(sim, 'standalone C2 crane-fault one-tick restart'));
    const GO = { throttle: 1, brake: 0, lean: 0, hop: false, restart: false } as const;
    let craneFaultTick = -1;
    let craneFaultX = 0;
    let checkpoint = -1;
    for (let tick = 0; tick < 90 * sim.hz; tick++) {
      const before = sim.state();
      recorder.push(GO);
      const events = sim.step(GO);
      if (before.bike.pos.x > 280 && events.some((event) => event.type === 'fault')) {
        craneFaultTick = tick + 1;
        craneFaultX = before.bike.pos.x;
        checkpoint = before.checkpoint;
        break;
      }
    }
    if (craneFaultTick < 0) throw new Error(`${bike} GO did not fault at crane`);
    const faultsBefore = sim.faults();
    const restart = { ...GO, restart: true };
    recorder.push(restart);
    sim.step(restart);
    const state = sim.state();
    const json = `${JSON.stringify({ magic: 'TRIN', ...recorder.toRecording() })}\n`;
    writeFileSync(new URL(`../../docs/evidence/c2-challenge/${bike}-one-tick-restart.json`, import.meta.url), json);
    const browserRun = await hook.runRecording(json);
    const browserPhase = await browser.page.evaluate(() => window.__rockhop!.phase());
    const row = {
      bike, craneFaultTick, craneFaultX: +craneFaultX.toFixed(2), restartTick: craneFaultTick + 1,
      checkpoint, nodeCheckpoint: state.checkpoint, browserCheckpoint: browserRun.state.checkpoint,
      nodeBikeX: state.bike.pos.x, browserBikeX: browserRun.state.bike.pos.x,
      nodeFaultsBefore: faultsBefore, nodeFaultsAfter: sim.faults(),
      nodePhase: sim.phase(), browserPhase, nodeHash: sim.hash(), browserHash: browserRun.hash,
      exact: sim.hash() === browserRun.hash && sim.phase() === 'riding' && browserPhase === 'riding'
        && sim.faults() === faultsBefore && state.checkpoint === checkpoint && browserRun.state.checkpoint === checkpoint,
    };
    rows.push(row);
    process.stdout.write(`${bike} ${JSON.stringify(row)}\n`);
    if (!row.exact) throw new Error(`${bike} restart differs`);
  }
} finally {
  await browser.close();
  await server.close();
}
writeFileSync(new URL('../../docs/evidence/c2-challenge/restart-verify.json', import.meta.url), `${JSON.stringify(rows, null, 2)}\n`);
