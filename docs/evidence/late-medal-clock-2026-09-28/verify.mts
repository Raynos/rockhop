/** Recheck final-four medal clocks against pinned clean lines and a 600 s passive-input sample. */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { expandFrames, quantizeInput } from '../../../src/core/replay';
import { medalFor, targetForBike } from '../../../src/game/rules';
import { ROCKHOP_TRACKS } from '../../../src/tracks/rockhop';
import { createSim, createSimFor } from '../../../harness/lib/sim';
import { loadRecording } from '../../../harness/lib/recording';
import { srcFingerprint } from '../../../harness/lib/metrics';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../../..');
const codes = new Set(['D3', 'S1', 'S2', 'S3']);
const before = JSON.parse(fs.readFileSync(path.join(root, 'docs/evidence/campaign-medal-audit/audit.json'), 'utf8'));
const passiveBefore = JSON.parse(fs.readFileSync(path.join(root, 'docs/evidence/campaign-retarget/held-go.json'), 'utf8'));
const rows = [];
const passive = [];
const go = quantizeInput({ throttle: 1 });
const limitS = 600;

for (const course of ROCKHOP_TRACKS.filter(c => codes.has(c.code))) {
  for (const bike of ['rookie', 'pro'] as const) {
    const old = before.rows.find((r: { code: string; bike: string }) => r.code === course.code && r.bike === bike);
    if (!old || old.status !== 'clean') throw new Error(`missing clean baseline ${course.code} ${bike}`);
    const recording = loadRecording(path.join(root, `harness/inputs/${course.id}/bot-3${bike === 'pro' ? '-pro' : ''}.json`));
    const passes = [];
    for (let attempt = 0; attempt < 2; attempt++) {
      const sim = await createSimFor(recording);
      sim.run(expandFrames(recording));
      passes.push({ phase: sim.phase(), clearS: sim.runTime(), faults: sim.faults(), hash: sim.hash(), routeCrossed: sim.rules.counters().diamondRouteCrossed });
    }
    const actual = passes[0]!;
    if (actual.phase !== 'finished' || actual.faults !== 0 || passes[1]!.hash !== actual.hash || passes[1]!.clearS !== actual.clearS ||
        actual.hash !== old.hash || Math.abs(actual.clearS - old.clearS) > 0.0005 || actual.routeCrossed !== old.diamondRouteCrossed) {
      throw new Error(`replay changed ${course.code} ${bike}: ${JSON.stringify({ old, passes })}`);
    }
    const authored = course.def.meta!.targetTimeS!;
    const effectiveGold = targetForBike(authored, bike)!;
    const diamond = effectiveGold * 0.85;
    const medal = medalFor(actual.clearS, actual.faults, authored, bike, course.def.diamondGoal ? actual.routeCrossed : undefined);
    if (bike === 'pro' && medal !== 'platinum') throw new Error(`upper Pro missed Diamond ${course.code}`);
    if (bike === 'rookie' && medal !== 'gold') throw new Error(`lower Rookie missed Gold ${course.code}`);
    rows.push({ code: course.code, bike, reference: recording.header.note, before: { goldS: old.goldS, diamondS: old.diamondS, diamondHeadroomS: old.diamondHeadroomS, medal: old.medal },
      after: { authoredGoldS: authored, effectiveGoldS: effectiveGold, diamondS: diamond, diamondHeadroomS: diamond - actual.clearS, medal },
      replay: actual, exactSecondReplay: true, sameHashAsBefore: true });

    const held = await createSim(course.id, undefined, 120, { bike });
    const oldHeld = passiveBefore.rows.find((r: { code: string; bike: string; seed: number }) => r.code === course.code && r.bike === bike && r.seed === held.seed);
    if (!oldHeld) throw new Error(`missing passive baseline ${course.code} ${bike} seed ${held.seed}`);
    let ticks = 0;
    while (ticks < limitS * 120 && held.phase() !== 'finished') { held.step(go); ticks++; }
    const result = { code: course.code, bike, seed: held.seed, ticks, phase: held.phase(), faults: held.faults(), hash: held.hash(),
      samePhaseFaultsHashAsBefore: held.phase() === oldHeld.phase && held.faults() === oldHeld.faults && held.hash() === oldHeld.hash };
    if (!result.samePhaseFaultsHashAsBefore || result.phase === 'finished') throw new Error(`passive outcome changed/cleared ${JSON.stringify(result)}`);
    passive.push(result);
  }
}

const report = { schema: 1, sourceFingerprint: srcFingerprint(), baselineFingerprint: before.sourceFingerprint,
  method: 'Two fresh exact Node replays per pinned recording, then 600 s held GO per course and bike against prior same-seed baseline; timing metadata only',
  rows, passive };
fs.writeFileSync(path.join(root, 'docs/evidence/late-medal-clock-2026-09-28/report.json'), JSON.stringify(report, null, 2) + '\n');
console.log(JSON.stringify({ replayRows: rows.length, passiveRows: passive.length, proDiamondMarginsS: rows.filter(r => r.bike === 'pro').map(r => ({ code: r.code, before: r.before.diamondHeadroomS, after: Number(r.after.diamondHeadroomS.toFixed(3)) })) }, null, 2));
