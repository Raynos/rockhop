/** Isolated, deterministic bike-role sweep. Run: pnpm exec tsx harness/bike-role-probe.mts */
import { createHash } from 'node:crypto';
import { mkdirSync, writeFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { hashPhysicsState } from '../src/core/hash';
import { packFrame, quantizeInput } from '../src/core/replay';
import type { InputFrame, PhysicsState, TrackDef } from '../src/core/types';
import { createBikePhysicsV2 } from '../src/physics/v2/bike';
import type { PartialTuningV2 } from '../src/physics/v2/tuning';
import { course } from '../src/tracks/author';
import { compileTrack } from '../src/tracks/compile';

const HZ = 120;
const DEG = 180 / Math.PI;
type Profile = { id: string; bike: 'rookie' | 'pro'; over?: PartialTuningV2 };
const profiles: Profile[] = [
  { id: 'starter', bike: 'rookie' },
  { id: 'pro-stock', bike: 'pro' },
  // Preserve the existing geometry and tyre material identity. More mid-range pull and suspension stroke
  // must earn their keep in the measured routes rather than merely inflating a Garage stat bar.
  { id: 'pro-pull', bike: 'pro', over: { engine: { Fpeak: 1050, curveF: [1, 1, 1, 1, 0.78, 0.55, 0.35] } } },
  { id: 'pro-enduro', bike: 'pro', over: { engine: { Fpeak: 1050, curveF: [1, 1, 1, 1, 0.78, 0.55, 0.35] }, suspension: { rear: { travel: 0.30, cComp: 700, cReb: 500 }, front: { travel: 0.28, cComp: 600, cReb: 480 } } } },
  { id: 'pro-torque', bike: 'pro', over: { engine: { Fpeak: 1100, curveF: [1, 1, 1, 1, 0.76, 0.52, 0.35] }, suspension: { rear: { travel: 0.30, cComp: 700, cReb: 500 }, front: { travel: 0.28, cComp: 600, cReb: 480 } } } },
];

type Row = { task: string; profile: string; variant: number; finished: boolean; fault: string | null; ticks: number; maxRearCompressionM: number; maxFrontCompressionM: number; maxPitchDeg: number; peakAbsPitchRateDegS: number; hash: string; inputSha256: string; replayExact: boolean };

function shelf(angleDeg: number): TrackDef {
  return course(`role-shelf-${angleDeg}`, 'Role shelf', 'hard')
    .meta({ biome: 'quarry', technique: 'high shelf' })
    .flat(30).steepPlank({ angleDeg, rise: 2.4 })
    .box({ width: 9, height: 2.4, surface: 'stone' })
    .ramp({ length: 18, height: 2.4, direction: 'down', surface: 'stone' })
    .flat(12).finish(30, { checkpointRule: false });
}

const FLAT = course('role-flat', 'Role flat', 'hard').meta({ biome: 'quarry', technique: 'landing' }).flat(120).finish(30, { checkpointRule: false });

function run(task: 'shelf' | 'drop' | 'balance', variant: number, p: Profile, replay?: readonly InputFrame[]): { row: Row; frames: InputFrame[] } {
  const angleDeg = task === 'shelf' ? ([59, 60, 60.25, 60.5, 60.75, 61][variant % 6] ?? 59) : 0;
  const def = task === 'shelf' ? shelf(angleDeg) : FLAT;
  const world = createBikePhysicsV2(HZ, p.over);
  world.loadTrack(compileTrack(def), 1, { bike: p.bike });
  const target = task === 'shelf' ? ([7, 9, 11][Math.floor(variant / 6) % 3] ?? 7) : 8;
  if (task === 'shelf') world.teleport({ pos: { x: 15, y: 0.34 }, angle: 0, vel: { x: target, y: 0 } });
  else if (task === 'drop') world.teleport({ pos: { x: 15, y: 0.34 + ([2.5, 3, 3.5, 4][variant % 4] ?? 2.5) }, angle: 5 / DEG, vel: { x: [4, 7, 10][Math.floor(variant / 4) % 3] ?? 4, y: 0 } });
  else world.teleport({ pos: { x: 15, y: 0.34 }, angle: 32 / DEG, vel: { x: [3, 5, 7][variant % 3] ?? 3, y: 0 } });
  let state: PhysicsState = world.getState();
  const frames: InputFrame[] = [], bytes: number[] = [];
  let maxRearCompressionM = 0, maxFrontCompressionM = 0, maxPitchDeg = -Infinity, peakAbsPitchRateDegS = 0;
  const limit = task === 'shelf' ? 14 * HZ : task === 'drop' ? 3 * HZ : 4 * HZ;
  let ticks = 0;
  for (; ticks < limit; ticks++) {
    let intent: Partial<InputFrame>;
    if (task === 'shelf') {
      const x = state.wheels.rear.pos.x, speed = state.bike.vel.x;
      const script = Math.floor(variant / 18) % 3;
      const snapStart = script === 2 ? 27.3 : 26.8;
      const snapEnd = script === 2 ? 30.1 : 29.6;
      intent = { throttle: speed < target ? 1 : 0, brake: speed > target + 0.7 ? 0.25 : 0, lean: 0.55 };
      if (script !== 0 && x >= snapStart && x < snapEnd) intent = { throttle: 0.3, lean: -0.7 };
      else if (x >= snapEnd && x < 34) intent = { throttle: 1, lean: 1 };
      else if (x >= 34) intent = { throttle: speed < 10 ? 0.8 : 0.15, lean: 0.25 };
    } else if (task === 'drop') intent = { throttle: 0.2, lean: [0, 0.5, 1][Math.floor(variant / 12) % 3] ?? 0 };
    else intent = { throttle: [0, 0.35, 0.7][Math.floor(variant / 3) % 3] ?? 0, lean: [-0.3, 0, 0.3][Math.floor(variant / 9) % 3] ?? 0 };
    const frame = replay?.[ticks] ?? quantizeInput(intent);
    frames.push(frame); bytes.push(...packFrame(frame));
    world.step(frame); state = world.getState();
    maxRearCompressionM = Math.max(maxRearCompressionM, state.wheels.rear.compression * (p.over?.suspension?.rear?.travel ?? 0.26));
    maxFrontCompressionM = Math.max(maxFrontCompressionM, state.wheels.front.compression * (p.over?.suspension?.front?.travel ?? 0.24));
    maxPitchDeg = Math.max(maxPitchDeg, state.bike.angle * DEG);
    peakAbsPitchRateDegS = Math.max(peakAbsPitchRateDegS, Math.abs(state.bike.angVel * DEG));
    if (state.faulted || state.finishTime !== null || (task === 'drop' && ticks >= 2 * HZ) || (task === 'balance' && ticks >= 3 * HZ)) { ticks++; break; }
  }
  return { row: { task, profile: p.id, variant, finished: state.finishTime !== null, fault: state.faulted, ticks, maxRearCompressionM, maxFrontCompressionM, maxPitchDeg, peakAbsPitchRateDegS, hash: hashPhysicsState(state), inputSha256: createHash('sha256').update(Uint8Array.from(bytes)).digest('hex'), replayExact: false }, frames };
}

const rows: Row[] = [];
for (const task of ['shelf', 'drop', 'balance'] as const) {
  const n = task === 'shelf' ? 54 : task === 'drop' ? 36 : 27;
  for (let variant = 0; variant < n; variant++) for (const p of profiles) {
    const first = run(task, variant, p);
    const second = run(task, variant, p, first.frames);
    first.row.replayExact = first.row.hash === second.row.hash && first.row.inputSha256 === second.row.inputSha256 && first.row.ticks === second.row.ticks;
    if (!first.row.replayExact) throw new Error(`Replay drift ${task} ${variant} ${p.id}`);
    rows.push(first.row);
  }
}
const out = resolve('docs/evidence/bike-role-loop/probe.json');
mkdirSync(resolve('docs/evidence/bike-role-loop'), { recursive: true });
writeFileSync(out, JSON.stringify({ hz: HZ, profiles, rows }, null, 2) + '\n');
for (const p of profiles) {
  const a = rows.filter((r) => r.profile === p.id);
  const s = a.filter((r) => r.task === 'shelf');
  const d = a.filter((r) => r.task === 'drop');
  const b = a.filter((r) => r.task === 'balance');
  console.log(`${p.id}: shelf finishes ${s.filter((r) => r.finished).length}/${s.length}, drop no-fault ${d.filter((r) => !r.fault).length}/${d.length}, balance no-fault ${b.filter((r) => !r.fault).length}/${b.length}`);
}
console.log(`${rows.length} exact replays; ${out}`);
