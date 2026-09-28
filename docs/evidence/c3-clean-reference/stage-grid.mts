/* Bounded continuation grid from a verified clean C3 prefix.
   Usage: tsx stage-grid.mts <stage-number> <prefix-recording> */
import fs from 'node:fs';
import path from 'node:path';
import { expandFrames, quantizeInput } from '../../../src/core/replay';
import { recordingFromFrames } from '../../../harness/bot/bot';
import { createSimFor } from '../../../harness/lib/sim';
import { loadRecording, saveRecording } from '../../../harness/lib/recording';
import type { InputFrame } from '../../../src/core/types';

const stage = Number(process.argv[2] || 2);
const dir = path.resolve('docs/evidence/c3-clean-reference');
const prefixFile = process.argv[3] || path.join(dir, 'best-progress.rec.json');
const base = loadRecording(prefixFile);
const original = [...expandFrames(loadRecording('harness/inputs/c3-hull-breach/bot-3.json'))];
const prefix = [...expandFrames(base)];
const endTick = prefix.length;
const source = [...prefix, ...original.slice(endTick)];
const check = await createSimFor(base);
const prefixRun = check.run(prefix);
if (check.phase() !== 'riding' || prefixRun.events.some(event => event.type === 'fault')) {
  throw new Error(`stage ${stage}: source prefix is not clean`);
}
const fromX = check.state().bike.pos.x;
const sim = await createSimFor(base);
const started = performance.now();
let tried = 0;
let bestX = fromX;
let best: { frames: InputFrame[]; parameter: Record<string, number>; maxX: number; faultTick: number | null } | null = null;
let selected: { frames: InputFrame[]; parameter: Record<string, number>; hash: string } | null = null;
outer: for (const offset of [-240, -180, -120, -60, -20])
  for (const brakeTicks of [0, 15, 30, 45, 60, 90, 120])
    for (const brakeLean of [-1, 0, 1])
      for (const throttle of [0, .5, 1])
        for (const lean of [-1, 0, 1]) {
          if (performance.now() - started > 120_000) break outer;
          tried++;
          const start = endTick + offset;
          sim.reload();
          const frames: InputFrame[] = [];
          let maxX = 0;
          let faultTick: number | null = null;
          for (let i = 0; i < Math.max(original.length + 900, endTick + 2000); i++) {
            const src = source[i] ?? quantizeInput({ throttle: 1 });
            const frame = i >= start && i < start + brakeTicks
              ? quantizeInput({ brake: 1, lean: brakeLean })
              : i >= start + brakeTicks && i < endTick + 150
                ? quantizeInput({ throttle, lean })
                : src.restart ? { ...src, restart: false } : src;
            frames.push(frame);
            const events = sim.step(frame);
            maxX = Math.max(maxX, sim.state().bike.pos.x);
            if (events.some(event => event.type === 'fault')) { faultTick = i + 1; break; }
            if (events.some(event => event.type === 'finish')) {
              selected = { frames, parameter: { start, brakeTicks, brakeLean, throttle, lean }, hash: sim.hash() };
              break outer;
            }
          }
          if (maxX > bestX) {
            bestX = maxX;
            best = { frames, parameter: { start, brakeTicks, brakeLean, throttle, lean }, maxX, faultTick };
          }
        }

let replay: Record<string, unknown> | null = null;
if (selected) {
  const recording = recordingFromFrames(sim, selected.frames, `C3 Rookie clean stage ${stage}`);
  const fresh = await createSimFor(recording);
  const run = fresh.run(expandFrames(recording));
  const faultEvents = run.events.filter(event => event.type === 'fault').length;
  const exact = run.hash === selected.hash && fresh.phase() === 'finished' && faultEvents === 0;
  replay = { exact, phase: fresh.phase(), faultEvents, finishTime: run.state.finishTime,
    hash: run.hash, ticks: run.ticks };
  if (exact) saveRecording(path.join(dir, 'rookie-zero-fault.rec.json'), recording);
}
if (best && !selected) {
  const cleanFrames = best.faultTick ? best.frames.slice(0, best.faultTick - 1) : best.frames;
  const recording = recordingFromFrames(sim, cleanFrames, `C3 Rookie stage ${stage} clean prefix`);
  saveRecording(path.join(dir, `stage-${stage}-best-progress.rec.json`), recording);
}
const report = { stage, prefixFile, fromX, endTick, tried,
  wallMs: Math.round(performance.now() - started), bestX,
  best: best ? { parameter: best.parameter, maxX: best.maxX, faultTick: best.faultTick } : null,
  found: !!selected, parameter: selected?.parameter ?? null, replay };
fs.writeFileSync(path.join(dir, `stage-${stage}-result.json`), JSON.stringify(report, null, 2) + '\n');
console.log(JSON.stringify(report));
