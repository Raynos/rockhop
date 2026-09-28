/** Bounded Pro-only override experiment. Run: pnpm exec tsx prototypes/bike-envelope/tune.ts */
import { createHash } from 'node:crypto';
import { mkdirSync, writeFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { hashPhysicsState } from '../../src/core/hash';
import { packFrame, quantizeInput } from '../../src/core/replay';
import type { BikeClass, InputFrame, PhysicsState, TrackDef } from '../../src/core/types';
import { createBikePhysicsV2 } from '../../src/physics/v2/bike';
import type { PartialTuningV2 } from '../../src/physics/v2/tuning';
import { course } from '../../src/tracks/author';
import { compileTrack } from '../../src/tracks/compile';

const HZ = 120;
const RISE = 2.4;
const FOOT = 30;
const ANGLES = [58, 59, 60, 60.25, 60.5, 60.75, 61, 61.25, 61.5, 62, 63, 64] as const;
const SPEEDS = [7, 9, 11] as const;
const SCRIPTS = ['forward', 'preload-snap', 'late-snap'] as const;
const SEEDS = [1, 2, 3] as const;
const MAX_TICKS = HZ * 14;

type Script = (typeof SCRIPTS)[number];
type Profile = { id: string; bike: BikeClass; forceN: number; rearTravelM: number; frontTravelM: number; woodMu: number; stoneMu: number; chassisKg: number; chassisInertia: number; override?: PartialTuningV2 };

const profiles: Profile[] = [
  { id: 'rookie-stock', bike: 'rookie', forceN: 880, rearTravelM: 0.26, frontTravelM: 0.24, woodMu: 1.8, stoneMu: 1.9, chassisKg: 58, chassisInertia: 11.9 },
  { id: 'pro-stock', bike: 'pro', forceN: 1000, rearTravelM: 0.26, frontTravelM: 0.24, woodMu: 1.8, stoneMu: 1.9, chassisKg: 54, chassisInertia: 11 },
  { id: 'pro-force1150', bike: 'pro', forceN: 1150, rearTravelM: 0.26, frontTravelM: 0.24, woodMu: 1.8, stoneMu: 1.9, chassisKg: 54, chassisInertia: 11, override: { engine: { Fpeak: 1150 } } },
  { id: 'pro-balanced1200', bike: 'pro', forceN: 1200, rearTravelM: 0.30, frontTravelM: 0.28, woodMu: 2.0, stoneMu: 2.1, chassisKg: 54, chassisInertia: 11, override: { engine: { Fpeak: 1200 }, suspension: { rear: { travel: 0.30 }, front: { travel: 0.28 } }, tyre: { mu: { wood: 2.0, stone: 2.1 } } } },
  { id: 'pro-heavy1400', bike: 'pro', forceN: 1400, rearTravelM: 0.34, frontTravelM: 0.32, woodMu: 2.2, stoneMu: 2.3, chassisKg: 64, chassisInertia: 14.5, override: { engine: { Fpeak: 1400 }, suspension: { rear: { travel: 0.34 }, front: { travel: 0.32 } }, tyre: { mu: { wood: 2.2, stone: 2.3 } }, chassis: { mass: 64, inertia: 14.5 } } },
];

type Row = {
  profile: string; bike: BikeClass; angleDeg: number; speedMps: number; script: Script; seed: number;
  reachedShelf: boolean; clearedShelf: boolean; finished: boolean; fault: string | null;
  footSpeedMps: number | null; landingSpeedMps: number | null;
  maxRearTravelM: number; maxFrontTravelM: number; landingRearTravelM: number | null; landingFrontTravelM: number | null;
  ticks: number; inputSha256: string; finalHash: string; exactReplay: boolean;
};
type StopRow = { profile: string; seed: number; stopX: number | null; stopDistanceM: number | null; targetHit: boolean; fault: string | null; maxPitchDeg: number; finalHash: string; exactReplay: boolean };
type AirRow = { profile: string; seed: number; peakCorrectionRateDegS: number; correctionAngleDeg: number; fault: string | null; finalHash: string; exactReplay: boolean };

function shelfTrack(angleDeg: number): { def: TrackDef; shelfStart: number; shelfEnd: number } {
  const b = course(`pro-tune-${angleDeg}`, `Pro tune ${angleDeg}`, 'hard')
    .meta({ biome: 'quarry', technique: 'steep plank to high shelf' })
    .flat(FOOT)
    .steepPlank({ angleDeg, rise: RISE });
  const shelfStart = b.cursor;
  b.box({ width: 9, height: RISE, surface: 'stone' });
  const shelfEnd = b.cursor;
  b.ramp({ length: 18, height: RISE, direction: 'down', surface: 'stone' }).flat(12);
  return { def: b.finish(30, { checkpointRule: false }), shelfStart, shelfEnd };
}

function intent(x: number, speed: number, target: number, script: Script): InputFrame {
  let throttle = speed < target ? 1 : 0;
  let brake = speed > target + 0.7 ? 0.25 : 0;
  let lean = 0.55;
  const snapEnd = script === 'late-snap' ? FOOT + 0.1 : FOOT - 0.4;
  const snapStart = script === 'late-snap' ? FOOT - 2.7 : FOOT - 3.2;
  if (script !== 'forward' && x >= snapStart && x < snapEnd) {
    lean = -0.7; throttle = 0.3; brake = 0;
  } else if (x >= snapEnd && x < FOOT + 4) {
    lean = 1; throttle = 1; brake = 0;
  } else if (x >= FOOT + 4) {
    lean = 0.25; throttle = speed < 10 ? 0.8 : 0.15; brake = 0;
  }
  return quantizeInput({ throttle, brake, lean });
}

function runShelf(def: TrackDef, shelfStart: number, shelfEnd: number, p: Profile, angleDeg: number, target: number, script: Script, seed: number, replayFrames?: readonly InputFrame[]): { row: Row; frames: InputFrame[] } {
  const world = createBikePhysicsV2(HZ, p.override);
  world.loadTrack(compileTrack(def), seed, { bike: p.bike });
  world.teleport({ pos: { x: 15, y: 0.34 }, angle: 0, vel: { x: target, y: 0 } });
  const frames: InputFrame[] = [];
  const bytes: number[] = [];
  let state: PhysicsState = world.getState();
  let reachedShelf = false, clearedShelf = false, leftShelf = false, landed = false;
  let footSpeedMps: number | null = null, landingSpeedMps: number | null = null;
  let rearTravel = 0, frontTravel = 0, landingRear = 0, landingFront = 0, landingTick = -1;
  let ticks = 0;
  for (; ticks < MAX_TICKS; ticks++) {
    const frame = replayFrames?.[ticks] ?? intent(state.wheels.rear.pos.x, state.bike.vel.x, target, script);
    frames.push(frame); bytes.push(...packFrame(frame));
    world.step(frame); state = world.getState();
    const x = state.wheels.rear.pos.x, y = state.wheels.rear.pos.y;
    if (footSpeedMps === null && x >= FOOT) footSpeedMps = state.bike.vel.x;
    if (x >= shelfStart && y >= RISE + 0.15) reachedShelf = true;
    if (x >= shelfEnd && y >= RISE + 0.15) clearedShelf = true;
    if (clearedShelf && !state.wheels.rear.grounded && !state.wheels.front.grounded) leftShelf = true;
    if (leftShelf && !landed && (state.wheels.rear.grounded || state.wheels.front.grounded)) {
      landed = true; landingTick = ticks; landingSpeedMps = state.bike.vel.x;
    }
    rearTravel = Math.max(rearTravel, state.wheels.rear.compression * p.rearTravelM);
    frontTravel = Math.max(frontTravel, state.wheels.front.compression * p.frontTravelM);
    if (landingTick >= 0 && ticks - landingTick < HZ / 2) {
      landingRear = Math.max(landingRear, state.wheels.rear.compression * p.rearTravelM);
      landingFront = Math.max(landingFront, state.wheels.front.compression * p.frontTravelM);
    }
    if (state.faulted || state.finishTime !== null) { ticks++; break; }
  }
  return { row: {
    profile: p.id, bike: p.bike, angleDeg, speedMps: target, script, seed,
    reachedShelf, clearedShelf, finished: state.finishTime !== null, fault: state.faulted,
    footSpeedMps, landingSpeedMps, maxRearTravelM: rearTravel, maxFrontTravelM: frontTravel,
    landingRearTravelM: landed ? landingRear : null, landingFrontTravelM: landed ? landingFront : null,
    ticks, inputSha256: createHash('sha256').update(Uint8Array.from(bytes)).digest('hex'),
    finalHash: hashPhysicsState(state), exactReplay: false,
  }, frames };
}

function controlTrack(): TrackDef {
  return course('pro-tune-stop', 'Pro tune stop', 'hard')
    .meta({ biome: 'quarry', technique: 'braking precision on flat stone' })
    .flat(100).finish(30, { checkpointRule: false });
}

/** Brake at a fixed x=30 m from a common 10 m/s roll; target is x=36..37. */
function runStop(def: TrackDef, p: Profile, seed: number, replayFrames?: readonly InputFrame[]): { row: StopRow; frames: InputFrame[] } {
  const world = createBikePhysicsV2(HZ, p.override);
  world.loadTrack(compileTrack(def), seed, { bike: p.bike });
  world.teleport({ pos: { x: 15, y: 0.34 }, angle: 0, vel: { x: 10, y: 0 } });
  let state = world.getState();
  const frames: InputFrame[] = [];
  let stopX: number | null = null, maxPitchDeg = -Infinity;
  for (let tick = 0; tick < HZ * 7; tick++) {
    const frame = replayFrames?.[tick] ?? quantizeInput(state.wheels.rear.pos.x < 30
      ? { throttle: state.bike.vel.x < 10 ? 1 : 0, lean: 0 }
      : { brake: 1, lean: 0 });
    frames.push(frame); world.step(frame); state = world.getState();
    maxPitchDeg = Math.max(maxPitchDeg, state.bike.angle * 180 / Math.PI);
    if (state.wheels.rear.pos.x >= 30 && state.bike.vel.x <= 0.5) { stopX = state.wheels.rear.pos.x; break; }
    if (state.faulted) break;
  }
  return { row: {
    profile: p.id, seed, stopX, stopDistanceM: stopX === null ? null : stopX - 30,
    targetHit: stopX !== null && stopX >= 36 && stopX <= 37 && !state.faulted,
    fault: state.faulted, maxPitchDeg, finalHash: hashPhysicsState(state), exactReplay: false,
  }, frames };
}

/** Same airborne lean release for each profile; tests whether extra climb ability has a control cost. */
function runAir(def: TrackDef, p: Profile, seed: number, replayFrames?: readonly InputFrame[]): { row: AirRow; frames: InputFrame[] } {
  const world = createBikePhysicsV2(HZ, p.override);
  world.loadTrack(compileTrack(def), seed, { bike: p.bike });
  world.teleport({ pos: { x: 10, y: 6 }, angle: 0, vel: { x: 10, y: 0 } });
  let state = world.getState();
  const frames: InputFrame[] = [];
  let angleBeforeRelease = 0;
  let peakCorrectionRateDegS = 0;
  for (let tick = 0; tick < 90; tick++) {
    const frame = replayFrames?.[tick] ?? quantizeInput({ lean: tick < 24 ? -1 : 0, throttle: 0.2 });
    frames.push(frame); world.step(frame); state = world.getState();
    if (tick === 23) angleBeforeRelease = state.bike.angle;
    if (tick >= 24 && tick < 84) peakCorrectionRateDegS = Math.max(peakCorrectionRateDegS, Math.abs(state.bike.angVel * 180 / Math.PI));
  }
  return { row: {
    profile: p.id, seed, peakCorrectionRateDegS,
    correctionAngleDeg: (state.bike.angle - angleBeforeRelease) * 180 / Math.PI,
    fault: state.faulted, finalHash: hashPhysicsState(state), exactReplay: false,
  }, frames };
}

const rows: Row[] = [];
const stopRows: StopRow[] = [];
const airRows: AirRow[] = [];
for (const angleDeg of ANGLES) {
  const { def, shelfStart, shelfEnd } = shelfTrack(angleDeg);
  for (const target of SPEEDS) for (const script of SCRIPTS) for (const seed of SEEDS) for (const p of profiles) {
    const first = runShelf(def, shelfStart, shelfEnd, p, angleDeg, target, script, seed);
    const replay = runShelf(def, shelfStart, shelfEnd, p, angleDeg, target, script, seed, first.frames);
    first.row.exactReplay = first.row.finalHash === replay.row.finalHash && first.row.inputSha256 === replay.row.inputSha256 && first.row.ticks === replay.row.ticks;
    if (!first.row.exactReplay) throw new Error(`shelf replay drift: ${angleDeg} ${target} ${script} ${seed} ${p.id}`);
    rows.push(first.row);
  }
}
const stopDef = controlTrack();
for (const seed of SEEDS) for (const p of profiles) {
  const first = runStop(stopDef, p, seed);
  const replay = runStop(stopDef, p, seed, first.frames);
  first.row.exactReplay = first.row.finalHash === replay.row.finalHash && first.frames.length === replay.frames.length;
  if (!first.row.exactReplay) throw new Error(`stop replay drift: ${seed} ${p.id}`);
  stopRows.push(first.row);
  const air = runAir(stopDef, p, seed);
  const airReplay = runAir(stopDef, p, seed, air.frames);
  air.row.exactReplay = air.row.finalHash === airReplay.row.finalHash && air.frames.length === airReplay.frames.length;
  if (!air.row.exactReplay) throw new Error(`air replay drift: ${seed} ${p.id}`);
  airRows.push(air.row);
}

const out = resolve(dirname(fileURLToPath(import.meta.url)), '../../docs/evidence/bike-envelope/tuning-results.json');
mkdirSync(dirname(out), { recursive: true });
writeFileSync(out, `${JSON.stringify({ hz: HZ, physics: 'v2', riseM: RISE, anglesDeg: ANGLES, speedsMps: SPEEDS, scripts: SCRIPTS, seeds: SEEDS, profiles: profiles.map(({ override: _discard, ...p }) => p), rows, stopRows, airRows }, null, 2)}\n`);
for (const p of profiles) {
  const at = rows.filter((r) => r.profile === p.id);
  const stop = stopRows.find((r) => r.profile === p.id);
  const air = airRows.find((r) => r.profile === p.id);
  console.info(`${p.id}: shelf ${at.filter((r) => r.reachedShelf).length}/${at.length}, clear ${at.filter((r) => r.clearedShelf).length}/${at.length}, finish ${at.filter((r) => r.finished).length}/${at.length}; stop ${stop?.stopX?.toFixed(2) ?? 'none'} m, hit ${stop?.targetHit}; air peak ${air?.peakCorrectionRateDegS.toFixed(0)}°/s`);
}
console.info(`${rows.length} shelf + ${stopRows.length} stop + ${airRows.length} air cases, all exact replays; ${out}`);
