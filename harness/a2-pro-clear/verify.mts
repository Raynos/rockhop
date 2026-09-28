/** Select A2 Pro only after an exact Node/browser 0-fault finish on current source. */
import fs from 'node:fs';
import { decodeJSON, encodeJSON, expandFrames } from '../../src/core/replay';
import { createSimFor } from '../lib/sim';
import { srcFingerprint } from '../lib/metrics';
import { launchBrowser } from '../lib/browser';
import { HookClient, openGame } from '../lib/hook';
import { startServer } from '../lib/server';

const source = 'docs/evidence/alpine-retarget/a2-log-jam-pro-bot.rec.json';
const selected = 'harness/inputs/a2-log-jam/bot-3-pro.json';
const evidence = 'docs/evidence/a2-pro-clear/replay.json';
const rec = decodeJSON(fs.readFileSync(source, 'utf8'));
if (rec.header.trackId !== 'a2-log-jam' || rec.header.bike !== 'pro') throw new Error('expected A2 Pro');
const src = srcFingerprint();
const sim = await createSimFor(rec);
let finishTick: number | null = null;
let tick = 0;
for (const frame of expandFrames(rec)) {
  tick++;
  const events = sim.step(frame);
  if (finishTick === null && events.some((event) => event.type === 'finish')) finishTick = tick;
}
if (sim.phase() !== 'finished' || sim.faults() !== 0 || finishTick === null) throw new Error(`candidate failed: ${sim.phase()} faults=${sim.faults()}`);
const server = await startServer({ dev: true });
const browser = await launchBrowser({ width: 852, height: 392 });
let browserHash: string | null = null;
let browserFinishTick: number | null = null;
try {
  await openGame(browser.page, server.url);
  const hook = new HookClient(browser.page);
  const result = await hook.runRecording(encodeJSON(rec));
  browserHash = result.hash;
  const browserTime = await hook.finishTime();
  browserFinishTick = browserTime === null ? null : Math.round(browserTime * rec.header.physicsHz);
} finally {
  await browser.close();
  await server.close();
}
const row = { source, selected, src, bike: rec.header.bike, physics: rec.header.physics, ticks: tick, finishTick, browserFinishTick, finishTimeS: sim.runTime(), faults: sim.faults(), nodeHash: sim.hash(), browserHash, exact: finishTick === browserFinishTick && sim.hash() === browserHash };
fs.mkdirSync('docs/evidence/a2-pro-clear', { recursive: true });
fs.writeFileSync(evidence, `${JSON.stringify(row, null, 2)}\n`);
console.log(JSON.stringify(row, null, 2));
if (!row.exact) throw new Error('A2 Pro Node/browser mismatch');
rec.header.note = `bot skill=3 outcome=finished bike=pro physics=v2 src=${src} selected-from=alpine-retarget`;
fs.writeFileSync(selected, `${encodeJSON(rec)}\n`);
