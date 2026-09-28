/* Bounded deterministic control search near the first C3 Rookie fault.
   Uses the pinned first-attempt prefix, changes only rider input, then resumes
   its remaining input with the post-crash restart edge suppressed. */
import fs from 'node:fs';
import path from 'node:path';
import { expandFrames, quantizeInput } from '../../../src/core/replay';
import { recordingFromFrames } from '../../../harness/bot/bot';
import { createSimFor } from '../../../harness/lib/sim';
import { loadRecording, saveRecording } from '../../../harness/lib/recording';
import type { InputFrame } from '../../../src/core/types';

const dir = path.resolve('docs/evidence/c3-clean-reference');
const base = loadRecording('harness/inputs/c3-hull-breach/bot-3.json');
const original = [...expandFrames(base)];
const sim = await createSimFor(base);
const searchStart = performance.now();
let tried = 0;
let bestX = 0;
let best: { frames: InputFrame[]; parameter: Record<string, number>; maxX: number; faultTick: number | null } | null = null;
let selected: { frames: InputFrame[]; parameter: Record<string, number>; hash: string; finishTime: number | null } | null = null;
outer: for (const start of [2180, 2240, 2300, 2360, 2420])
  for (const brakeTicks of [0, 15, 30, 45, 60, 90, 120])
    for (const brakeLean of [-1, 0, 1])
      for (const throttle of [0, .5, 1])
        for (const lean of [-1, 0, 1]) {
          if (performance.now() - searchStart > 120_000) break outer;
          tried++;
          sim.reload();
          const frames: InputFrame[] = [];
          let candidateX = 0;
          let faultTick: number | null = null;
          for (let i = 0; i < original.length + 900; i++) {
            const source = original[i] ?? quantizeInput({ throttle: 1 });
            const frame = i >= start && i < start + brakeTicks
              ? quantizeInput({ brake: 1, lean: brakeLean })
              : i >= start + brakeTicks && i < 2600
                ? quantizeInput({ throttle, lean })
                : source.restart ? { ...source, restart: false } : source;
            frames.push(frame);
            const events = sim.step(frame);
            candidateX = Math.max(candidateX, sim.state().bike.pos.x);
            if (events.some(event => event.type === 'fault')) { faultTick = i + 1; break; }
            if (events.some(event => event.type === 'finish')) {
              selected = { frames, parameter: { start, brakeTicks, brakeLean, throttle, lean },
                hash: sim.hash(), finishTime: sim.state().finishTime };
              break outer;
            }
          }
          if (candidateX > bestX) {
            bestX = candidateX;
            best = { frames, parameter: { start, brakeTicks, brakeLean, throttle, lean }, maxX: candidateX, faultTick };
          }
        }

let exact = false;
let replay: Record<string, unknown> | null = null;
if (selected) {
  const recording = recordingFromFrames(sim, selected.frames, 'C3 Rookie zero-fault control-grid candidate');
  const fresh = await createSimFor(recording);
  const result = fresh.run(expandFrames(recording));
  const faultEvents = result.events.filter(event => event.type === 'fault').length;
  exact = result.hash === selected.hash && fresh.phase() === 'finished' && faultEvents === 0;
  replay = { exact, phase: fresh.phase(), faultEvents, finishTime: result.state.finishTime,
    hash: result.hash, ticks: result.ticks };
  if (exact) saveRecording(path.join(dir, 'rookie-zero-fault.rec.json'), recording);
}
if (best && !selected) {
  const cleanFrames = best.faultTick ? best.frames.slice(0, best.faultTick - 1) : best.frames;
  const recording = recordingFromFrames(sim, cleanFrames, 'C3 Rookie best fault-free prefix from control grid');
  saveRecording(path.join(dir, 'best-progress.rec.json'), recording);
}
const report = { tried, wallMs: Math.round(performance.now() - searchStart), bestX,
  best: best ? { parameter: best.parameter, maxX: best.maxX, faultTick: best.faultTick } : null,
  found: !!selected, parameter: selected?.parameter ?? null, replay };
fs.mkdirSync(dir, { recursive: true });
fs.writeFileSync(path.join(dir, 'control-grid-result.json'), JSON.stringify(report, null, 2) + '\n');
console.log(JSON.stringify(report));
