/** Current registered Alpine held-GO and committed-bot probe. */
import { readFileSync, writeFileSync } from 'node:fs';
import { createSim } from '../lib/sim';
import { decodeJSON, iterateFrames } from '../../src/core/replay';
import { medalFor } from '../../src/game/rules';
import { getTrack } from '../../src/tracks';

const ids = ['a1-sawdust', 'a2-log-jam', 'a3-timberline'];
const GO = { throttle: 1, brake: 0, lean: 0, hop: false, restart: false } as const;
const rows = [];
for (const id of ids) {
  const track = getTrack(id)!;
  for (const bike of ['rookie', 'pro'] as const) {
    const sim = await createSim(id, track.seed, 120, { bike });
    let maxX = 0;
    let finishTick: number | null = null;
    let firstFault: unknown = null;
    for (let tick = 0; tick < 600 * 120; tick++) {
      const s = sim.state();
      const x = s.bike.pos.x;
      maxX = Math.max(maxX, x);
      for (const e of sim.step(GO)) {
        if (e.type === 'fault') firstFault ??= { tick: tick + 1, x: +x.toFixed(2), checkpoint: s.checkpoint, reason: e.reason };
        if (e.type === 'finish') finishTick = tick + 1;
      }
      if (finishTick !== null) break;
    }
    const row = { id, bike, mode: 'held GO', finishTick, timeS: finishTick === null ? null : finishTick / 120,
      medal: finishTick === null ? null : medalFor(finishTick / 120, sim.faults(), track.meta?.targetTimeS ?? 50, bike),
      faults: sim.faults(), firstFault, maxX: +maxX.toFixed(2), finishX: track.finishX, hash: sim.hash() };
    rows.push(row);
    process.stdout.write(`${id} ${bike} GO ${row.finishTick ? `CLEAR ${row.timeS}` : `STUCK ${row.maxX}`} faults=${row.faults}\n`);
    const fixture = JSON.parse(readFileSync(new URL(`../../harness/inputs/${id}/bot-3.json`, import.meta.url), 'utf8'));
    const rec = decodeJSON(JSON.stringify(fixture));
    const bot = await createSim(id, rec.header.seed, 120, { bike });
    let botFinish: number | null = null;
    let botTick = 0;
    for (const frame of iterateFrames(rec)) {
      botTick++;
      if (bot.step(frame).some((e) => e.type === 'finish')) botFinish = botTick;
    }
    const botRow = { id, bike, mode: 'bot-3 fixture', finishTick: botFinish, timeS: botFinish === null ? null : botFinish / 120,
      medal: botFinish === null ? null : medalFor(botFinish / 120, bot.faults(), track.meta?.targetTimeS ?? 50, bike),
      faults: bot.faults(), maxX: +bot.state().bike.pos.x.toFixed(2), hash: bot.hash() };
    rows.push(botRow);
    process.stdout.write(`${id} ${bike} bot ${botRow.finishTick ? `CLEAR ${botRow.timeS}` : 'FAIL'} faults=${botRow.faults}\n`);
  }
}
writeFileSync(new URL('../../docs/evidence/alpine-retarget/probe.json', import.meta.url), `${JSON.stringify(rows, null, 2)}\n`);
