/** Isolated class-role probe: pnpm exec tsx prototypes/pro-envelope-v2/sweep.mts */
import { createHash } from 'node:crypto';
import { mkdirSync, writeFileSync } from 'node:fs';
import { hashPhysicsState } from '../../src/core/hash';
import { packFrame, quantizeInput } from '../../src/core/replay';
import type { InputFrame, TrackDef } from '../../src/core/types';
import { createBikePhysicsV2 } from '../../src/physics/v2/bike';
import type { PartialTuningV2 } from '../../src/physics/v2/tuning';
import { course } from '../../src/tracks/author';
import { compileTrack } from '../../src/tracks/compile';

const HZ = 120;
const DEG = 180 / Math.PI;
type Family = 'shelf' | 'gap' | 'drop' | 'balance';
type Profile = { id: string; bike: 'rookie' | 'pro'; over?: PartialTuningV2 };
const PROFILES: Profile[] = [
  { id: 'starter-stock', bike: 'rookie' },
  { id: 'pro-stock', bike: 'pro' },
  { id: 'pro-midrange', bike: 'pro', over: { engine: { Fpeak: 1050, curveF: [1, 1, 1, 1, 0.78, 0.55, 0.35] } } },
  { id: 'pro-enduro', bike: 'pro', over: { engine: { Fpeak: 1050, curveF: [1, 1, 1, 1, 0.78, 0.55, 0.35] }, suspension: { rear: { travel: 0.30, cComp: 700, cReb: 500 }, front: { travel: 0.28, cComp: 600, cReb: 480 } } } },
  { id: 'pro-grip', bike: 'pro', over: { engine: { Fpeak: 1050, curveF: [1, 1, 1, 1, 0.78, 0.55, 0.35] }, tyre: { mu: { wood: 2.05, stone: 2.15, snow: 1.35 } } } },
];

type Case = { family: Family; geometry: number; speed: number; script: number };
type Row = Case & { profile: string; goal: boolean; finished: boolean; fault: string | null; ticks: number; maxRearX: number; minRearY: number; maxPitchDeg: number; finalHash: string; inputSha256: string; replayExact: boolean };

function track(c: Case): { def: TrackDef; goalX: number; goalY: number } {
  const b = course(`pro-v2-${c.family}-${c.geometry}`, 'Role probe', 'hard').meta({ biome: 'quarry', technique: 'class envelope' });
  if (c.family === 'shelf') {
    b.flat(30).steepPlank({ angleDeg: c.geometry, rise: 2.4 });
    const goalX = b.cursor + 8;
    b.box({ width: 8, height: 2.4, surface: 'stone' }).ramp({ length: 18, height: 2.4, direction: 'down', surface: 'stone' }).flat(12);
    return { def: b.finish(30, { checkpointRule: false }), goalX, goalY: 2.55 };
  }
  if (c.family === 'gap') {
    b.flat(30).ramp({ length: 5, height: 0.8, surface: 'wood' }).gap({ width: c.geometry });
    const goalX = b.cursor + 1;
    b.box({ width: 8, height: 0.8, surface: 'wood' }).ramp({ length: 10, height: 0.8, direction: 'down', surface: 'wood' }).flat(12);
    return { def: b.finish(30, { checkpointRule: false }), goalX, goalY: 0.7 };
  }
  b.flat(120);
  return { def: b.finish(30, { checkpointRule: false }), goalX: 0, goalY: 0 };
}

function scripted(c: Case, tick: number, rearX: number, velX: number): InputFrame {
  if (c.family === 'drop') return quantizeInput({ throttle: [0, 0.3][c.script % 2], lean: [0, 0.5, 1][Math.floor(c.script / 2)] });
  if (c.family === 'balance') return quantizeInput({ throttle: [0, 0.35, 0.7][c.script % 3], lean: [-0.3, 0, 0.3][Math.floor(c.script / 3)] });
  const foot = 30;
  let throttle = velX < c.speed ? 1 : 0;
  let brake = velX > c.speed + 0.7 ? 0.25 : 0;
  let lean = 0.55;
  if (c.script === 1 && rearX >= foot - 3.2 && rearX < foot - 0.4) { throttle = 0.3; brake = 0; lean = -0.7; }
  else if (c.script === 2 && rearX >= foot - 2.7 && rearX < foot + 0.1) { throttle = 0.3; brake = 0; lean = -0.7; }
  else if (rearX >= foot - 0.4 && rearX < foot + 4) { throttle = 1; brake = 0; lean = 1; }
  else if (rearX >= foot + 4) { throttle = velX < 10 ? 0.8 : 0.15; brake = 0; lean = 0.25; }
  // tick is included deliberately: a future fixed-time gesture remains replayable.
  void tick;
  return quantizeInput({ throttle, brake, lean });
}

function run(c: Case, p: Profile, playback?: readonly InputFrame[]): { row: Row; frames: InputFrame[] } {
  const { def, goalX, goalY } = track(c);
  const world = createBikePhysicsV2(HZ, p.over);
  world.loadTrack(compileTrack(def), 1, { bike: p.bike });
  if (c.family === 'drop') world.teleport({ pos: { x: 15, y: 0.34 + c.geometry }, angle: 5 / DEG, vel: { x: c.speed, y: 0 } });
  else if (c.family === 'balance') world.teleport({ pos: { x: 15, y: 0.34 }, angle: 32 / DEG, vel: { x: c.speed, y: 0 } });
  else world.teleport({ pos: { x: 15, y: 0.34 }, angle: 0, vel: { x: c.speed, y: 0 } });
  let state = world.getState();
  const frames: InputFrame[] = [];
  const bytes: number[] = [];
  let goal = false, maxRearX = -Infinity, minRearY = Infinity, maxPitchDeg = -Infinity;
  const limit = HZ * (c.family === 'shelf' || c.family === 'gap' ? 14 : c.family === 'drop' ? 2.5 : 3.5);
  let ticks = 0;
  for (; ticks < limit; ticks++) {
    const frame = playback?.[ticks] ?? scripted(c, ticks, state.wheels.rear.pos.x, state.bike.vel.x);
    frames.push(frame); bytes.push(...packFrame(frame));
    world.step(frame); state = world.getState();
    const { x, y } = state.wheels.rear.pos;
    maxRearX = Math.max(maxRearX, x); minRearY = Math.min(minRearY, y); maxPitchDeg = Math.max(maxPitchDeg, state.bike.angle * DEG);
    if ((c.family === 'shelf' || c.family === 'gap') && x >= goalX && y >= goalY) goal = true;
    if (state.faulted || state.finishTime !== null) { ticks++; break; }
  }
  if (c.family === 'drop' || c.family === 'balance') goal = !state.faulted;
  return { row: { ...c, profile: p.id, goal, finished: state.finishTime !== null, fault: state.faulted, ticks, maxRearX, minRearY, maxPitchDeg, finalHash: hashPhysicsState(state), inputSha256: createHash('sha256').update(Uint8Array.from(bytes)).digest('hex'), replayExact: false }, frames };
}

const cases: Case[] = [];
for (const geometry of [59, 60, 60.25, 60.5, 60.75, 61]) for (const speed of [7, 9, 11]) for (const script of [0, 1, 2]) cases.push({ family: 'shelf', geometry, speed, script });
for (const geometry of [3.5, 4.5, 5.5, 6.5]) for (const speed of [7, 9, 11]) for (const script of [0, 1, 2]) cases.push({ family: 'gap', geometry, speed, script });
for (const geometry of [2.5, 3, 3.5, 4]) for (const speed of [4, 7, 10]) for (const script of [0, 1, 2, 3, 4, 5]) cases.push({ family: 'drop', geometry, speed, script });
for (const speed of [3, 5, 7]) for (const script of [0, 1, 2, 3, 4, 5, 6, 7, 8]) cases.push({ family: 'balance', geometry: 32, speed, script });

const rows: Row[] = [];
for (const c of cases) for (const p of PROFILES) {
  const first = run(c, p);
  const again = run(c, p, first.frames);
  first.row.replayExact = first.row.finalHash === again.row.finalHash && first.row.inputSha256 === again.row.inputSha256 && first.row.ticks === again.row.ticks;
  if (!first.row.replayExact) throw new Error(`Replay drift: ${JSON.stringify(c)} ${p.id}`);
  rows.push(first.row);
}
mkdirSync('docs/evidence/pro-envelope-v2', { recursive: true });
writeFileSync('docs/evidence/pro-envelope-v2/rows.json', JSON.stringify({ hz: HZ, profiles: PROFILES, cases, rows }, null, 2) + '\n');
for (const p of PROFILES) for (const family of ['shelf', 'gap', 'drop', 'balance'] as const) {
  const r = rows.filter((x) => x.profile === p.id && x.family === family);
  console.info(`${p.id} ${family}: goal ${r.filter((x) => x.goal).length}/${r.length}, finished ${r.filter((x) => x.finished).length}/${r.length}, fault ${r.filter((x) => x.fault).length}/${r.length}`);
}
console.info(`${rows.length} exact replays; docs/evidence/pro-envelope-v2/rows.json`);
