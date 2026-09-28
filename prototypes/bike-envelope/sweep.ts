/**
 * Isolated, reproducible class-envelope probe. Run: pnpm exec tsx prototypes/bike-envelope/sweep.ts
 * Uses the shipping CourseBuilder, compiler and v2 solver; never registers a campaign course.
 */
import { createHash } from 'node:crypto';
import { mkdirSync, writeFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, resolve } from 'node:path';
import { quantizeInput, packFrame } from '../../src/core/replay';
import { hashPhysicsState } from '../../src/core/hash';
import type { BikeClass, InputFrame, PhysicsState, TrackDef } from '../../src/core/types';
import { createBikePhysicsV2 } from '../../src/physics/v2/bike';
import { course } from '../../src/tracks/author';
import { compileTrack } from '../../src/tracks/compile';

const HZ = 120;
const ANGLES = [50, 55, 60, 65] as const;
const SPEEDS = [6, 9] as const;
const SCRIPTS = ['forward', 'preload-snap'] as const;
const SEEDS = [1, 2, 3] as const;
const BIKES: BikeClass[] = ['rookie', 'pro'];
const RISE = 2.4;
const FOOT = 30;
const MAX_TICKS = HZ * 12;

type Script = (typeof SCRIPTS)[number];
type Row = {
  angleDeg: number; riseM: number; approachTargetMps: number; script: Script; seed: number; bike: BikeClass;
  footX: number; shelfStartX: number; shelfEndX: number; finishX: number;
  reachedShelf: boolean; clearedShelf: boolean; landedAfterShelf: boolean; finished: boolean;
  fault: string | null; ticks: number; footSpeedMps: number | null; shelfSpeedMps: number | null;
  landingSpeedMps: number | null; maxRearX: number; maxRearY: number; finalRearX: number;
  maxRearCompression: number; maxFrontCompression: number;
  maxRearTravelM: number; maxFrontTravelM: number; landingRearTravelM: number | null; landingFrontTravelM: number | null;
  inputSha256: string; stateHash: string; replayExact: boolean;
};

function track(angleDeg: number): { def: TrackDef; shelfStartX: number; shelfEndX: number } {
  const b = course(`bike-envelope-${angleDeg}`, `Bike envelope ${angleDeg}`, 'hard')
    .meta({ biome: 'quarry', technique: 'steep plank and high shelf' })
    .flat(FOOT)
    .steepPlank({ angleDeg, rise: RISE });
  const shelfStartX = b.cursor;
  b.box({ width: 9, height: RISE, surface: 'stone' });
  const shelfEndX = b.cursor;
  b.ramp({ length: 18, height: RISE, direction: 'down', surface: 'stone' })
    .flat(12);
  return { def: b.finish(30, { checkpointRule: false }), shelfStartX, shelfEndX };
}

/** A fixed 9 m/s or 6 m/s roll from x=15. Position gates stay independent of class speed. */
function inputAt(x: number, speed: number, approach: number, script: Script): InputFrame {
  let throttle = speed < approach ? 1 : 0;
  let brake = speed > approach + 0.7 ? 0.25 : 0;
  let lean = 0.55;
  if (script === 'preload-snap' && x >= FOOT - 3.2 && x < FOOT - 0.4) {
    lean = -0.7;
    throttle = 0.3;
    brake = 0;
  } else if (x >= FOOT - 0.4 && x < FOOT + 4) {
    lean = 1;
    throttle = 1;
    brake = 0;
  } else if (x >= FOOT + 4) {
    lean = 0.25;
    throttle = speed < 10 ? 0.8 : 0.15;
    brake = 0;
  }
  return quantizeInput({ throttle, brake, lean });
}

function one(def: TrackDef, shelfStartX: number, shelfEndX: number, angleDeg: number, approach: number, script: Script, seed: number, bike: BikeClass, frames?: readonly InputFrame[]): { row: Row; frames: InputFrame[] } {
  const world = createBikePhysicsV2(HZ);
  world.loadTrack(compileTrack(def), seed, { bike });
  // Identical controlled rolling start, settled onto the same flat 15 m before the foot.
  world.teleport({ pos: { x: 15, y: 0.34 }, angle: 0, vel: { x: approach, y: 0 } });
  const applied: InputFrame[] = [];
  const bytes: number[] = [];
  let reachedShelf = false;
  let clearedShelf = false;
  let landedAfterShelf = false;
  let footSpeedMps: number | null = null;
  let shelfSpeedMps: number | null = null;
  let landingSpeedMps: number | null = null;
  let hasLeftShelf = false;
  let maxRearX = -Infinity;
  let maxRearY = -Infinity;
  let maxRearCompression = 0;
  let maxFrontCompression = 0;
  let landingTick = -1;
  let landingRearCompression = 0;
  let landingFrontCompression = 0;
  let ticks = 0;
  let state: PhysicsState = world.getState();
  for (; ticks < MAX_TICKS; ticks++) {
    const frame = frames?.[ticks] ?? inputAt(state.wheels.rear.pos.x, state.bike.vel.x, approach, script);
    applied.push(frame);
    bytes.push(...packFrame(frame));
    world.step(frame);
    state = world.getState();
    const rearX = state.wheels.rear.pos.x;
    const rearY = state.wheels.rear.pos.y;
    maxRearX = Math.max(maxRearX, rearX);
    maxRearY = Math.max(maxRearY, rearY);
    if (footSpeedMps === null && rearX >= FOOT) footSpeedMps = state.bike.vel.x;
    // x alone can pass the shelf while the bike is falling below it. Require rear-wheel height too.
    if (!reachedShelf && rearX >= shelfStartX && rearY >= RISE + 0.15) {
      reachedShelf = true;
      shelfSpeedMps = state.bike.vel.x;
    }
    if (rearX >= shelfEndX && rearY >= RISE + 0.15) clearedShelf = true;
    if (clearedShelf && !state.wheels.rear.grounded && !state.wheels.front.grounded) hasLeftShelf = true;
    if (hasLeftShelf && !landedAfterShelf && (state.wheels.rear.grounded || state.wheels.front.grounded)) {
      landedAfterShelf = true;
      landingTick = ticks;
      landingSpeedMps = state.bike.vel.x;
    }
    maxRearCompression = Math.max(maxRearCompression, state.wheels.rear.compression);
    maxFrontCompression = Math.max(maxFrontCompression, state.wheels.front.compression);
    if (landingTick >= 0 && ticks - landingTick < HZ / 2) {
      landingRearCompression = Math.max(landingRearCompression, state.wheels.rear.compression);
      landingFrontCompression = Math.max(landingFrontCompression, state.wheels.front.compression);
    }
    if (state.faulted || state.finishTime !== null) { ticks++; break; }
  }
  const inputSha256 = createHash('sha256').update(Uint8Array.from(bytes)).digest('hex');
  const row: Row = {
    angleDeg, riseM: RISE, approachTargetMps: approach, script, seed, bike,
    footX: FOOT, shelfStartX, shelfEndX, finishX: def.finishX,
    reachedShelf, clearedShelf, landedAfterShelf, finished: state.finishTime !== null,
    fault: state.faulted, ticks, footSpeedMps, shelfSpeedMps, landingSpeedMps,
    maxRearX, maxRearY, finalRearX: state.wheels.rear.pos.x,
    maxRearCompression, maxFrontCompression,
    maxRearTravelM: maxRearCompression * 0.26, maxFrontTravelM: maxFrontCompression * 0.24,
    landingRearTravelM: landedAfterShelf ? landingRearCompression * 0.26 : null,
    landingFrontTravelM: landedAfterShelf ? landingFrontCompression * 0.24 : null,
    inputSha256, stateHash: hashPhysicsState(state), replayExact: false,
  };
  return { row, frames: applied };
}

const rows: Row[] = [];
for (const angleDeg of ANGLES) {
  const { def, shelfStartX, shelfEndX } = track(angleDeg);
  for (const approach of SPEEDS) for (const script of SCRIPTS) for (const seed of SEEDS) for (const bike of BIKES) {
    const first = one(def, shelfStartX, shelfEndX, angleDeg, approach, script, seed, bike);
    const replay = one(def, shelfStartX, shelfEndX, angleDeg, approach, script, seed, bike, first.frames);
    first.row.replayExact = replay.row.stateHash === first.row.stateHash && replay.row.inputSha256 === first.row.inputSha256 && replay.row.ticks === first.row.ticks;
    if (!first.row.replayExact) throw new Error(`replay drift: ${angleDeg} ${approach} ${script} ${seed} ${bike}`);
    rows.push(first.row);
  }
}

const out = resolve(dirname(fileURLToPath(import.meta.url)), '../../docs/evidence/bike-envelope/results.json');
mkdirSync(dirname(out), { recursive: true });
writeFileSync(out, `${JSON.stringify({ hz: HZ, physics: 'v2', angleDeg: ANGLES, riseM: RISE, speedsMps: SPEEDS, scripts: SCRIPTS, seeds: SEEDS, rows }, null, 2)}\n`);
for (const angleDeg of ANGLES) {
  const at = rows.filter((r) => r.angleDeg === angleDeg);
  console.info(`${angleDeg}°: ` + BIKES.map((bike) => {
    const b = at.filter((r) => r.bike === bike);
    return `${bike} shelf ${b.filter((r) => r.reachedShelf).length}/${b.length}, finish ${b.filter((r) => r.finished).length}/${b.length}`;
  }).join(' | '));
}
console.info(`${rows.length} runs, ${rows.filter((r) => r.replayExact).length} exact replays; ${out}`);
