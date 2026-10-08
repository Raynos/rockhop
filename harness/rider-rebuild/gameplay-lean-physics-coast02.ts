/** Actual coast correction to the failed full-brake preflight; physics and track unchanged. */
import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createBikePhysics } from '../../src/physics';
import { compileTrack, getTrack } from '../../src/tracks';
import { hashPhysicsState } from '../../src/core/hash';
import type { BikeClass, InputFrame } from '../../src/core/types';
import { FrameBuilder } from '../../src/render/frame';

const ROOT = fileURLToPath(new URL('../../', import.meta.url));
const output = process.argv[2];
assert(output, 'Pass one fresh JSON output path');
const out = path.resolve(output);
assert(out.startsWith(path.join(ROOT, 'docs/evidence/rider-rebuild/')) && !fs.existsSync(out));
const phases = [{ name: 'neutral', ticks: 240, lean: 0 }, { name: 'forward', ticks: 360, lean: 1 },
  { name: 'backward', ticks: 360, lean: -1 }, { name: 'neutral-return', ticks: 240, lean: 0 }];
const inputs: InputFrame[] = phases.flatMap(phase => Array.from({ length: phase.ticks }, () =>
  ({ throttle: 0, brake: 0, lean: phase.lean, hop: false, restart: false })));
const track = getTrack('b1-first-ride'); assert(track);
const compiled = compileTrack(track), seed = 138717428, hz = 120;
const sha = (value: string | Buffer) => crypto.createHash('sha256').update(value).digest('hex');
const sources = ['harness/rider-rebuild/gameplay-lean-physics-coast02.ts', 'src/physics/index.ts',
  'src/physics/v2/bike.ts', 'src/physics/v2/tuning.ts', 'src/physics/v2/rider.ts',
  'src/physics/v2/engine.ts', 'src/physics/v2/tyre.ts', 'src/physics/collision.ts',
  'src/physics/tuning.ts', 'src/physics/dmath.ts', 'src/core/rng.ts', 'src/core/hash.ts',
  'src/core/riderGeometry.ts', 'src/render/frame.ts', 'src/tracks/compile.ts',
  'src/tracks/courses/beginner.ts', 'src/tracks/author.ts', 'src/tracks/geometry.ts', 'src/tracks/kinds.ts'];
const sourcePins = sources.map(name => ({ path: name, sha256: sha(fs.readFileSync(path.join(ROOT, name))) }));
type Range = { minimum: number; maximum: number; excursion: number };
function run(bike: BikeClass) {
  const world = createBikePhysics(hz), builder = new FrameBuilder(), trajectory = crypto.createHash('sha256');
  world.loadTrack(compiled, seed, { bike });
  const endpoints = new Map([[0, 'initial'], [240, 'neutral'], [600, 'forward'], [960, 'backward'], [1200, 'neutral-return']]);
  const samples: unknown[] = [], ranges: Record<string, Range> = {}, poses = new Set<string>();
  const faults: { tick: number; reason: string }[] = [];
  let faultedTicks = 0, finite = true, allBodyAndDrawnPresent = true, finalHash = '';
  for (let tick = 0; tick <= inputs.length; tick++) {
    if (tick) world.step(inputs[tick - 1]!);
    const state = world.getState(), frame = builder.build(state, 1), body = state.riderBody, drawn = body?.drawn;
    finalHash = hashPhysicsState(state);
    if (state.faulted) { faultedTicks++; if (faults.length < 16) faults.push({ tick, reason: state.faulted }); }
    allBodyAndDrawnPresent &&= !!body && !!drawn && frame.riderBody.present && frame.riderBody.drawn.present;
    const values = { comWorldX: body?.pos.x ?? NaN, comWorldY: body?.pos.y ?? NaN,
      comChassisX: frame.riderBody.relX, comChassisY: frame.riderBody.relY,
      drawnHipX: drawn?.hips.x ?? NaN, drawnHipY: drawn?.hips.y ?? NaN,
      torsoRadians: drawn?.torso ?? NaN, effectiveLean: state.rider.lean,
      bikeX: state.bike.pos.x, bikeY: state.bike.pos.y };
    for (const [name, value] of Object.entries(values)) {
      finite &&= Number.isFinite(value);
      const range = ranges[name] ??= { minimum: value, maximum: value, excursion: 0 };
      range.minimum = Math.min(range.minimum, value); range.maximum = Math.max(range.maximum, value);
      range.excursion = range.maximum - range.minimum;
    }
    if (drawn) poses.add(drawn.pose);
    trajectory.update(JSON.stringify({ tick, physicsHash: finalHash, riderBody: body, frameBody: frame.riderBody }));
    if (endpoints.has(tick)) samples.push({ name: endpoints.get(tick), tick, timeSeconds: state.time,
      commandedLean: tick ? inputs[tick - 1]!.lean : 0, physicsHash: finalHash,
      faulted: state.faulted, finished: state.finished, finishTime: state.finishTime,
      bike: state.bike, rider: state.rider, riderBody: body, renderFrameBody: structuredClone(frame.riderBody) });
  }
  return { bike, steppedTicks: inputs.length, faultedTicks, firstFaults: faults, finite,
    allBodyAndDrawnPresent, poseIdsObserved: [...poses], ranges, samples, finalHash,
    physicsAndDerivedPoseTrajectorySHA256: trajectory.digest('hex') };
}

const started = performance.now();
const results = (['rookie', 'pro'] as const).map(bike => {
  const first = run(bike), repeat = run(bike);
  return { ...first, repeatTrajectoryByteIdentical: first.physicsAndDerivedPoseTrajectorySHA256 === repeat.physicsAndDerivedPoseTrajectorySHA256,
    repeatFinalHash: repeat.finalHash, comAndDrawnPoseVary: first.ranges.comChassisX!.excursion > 0.01
      && first.ranges.drawnHipY!.excursion > 0.01 && first.ranges.torsoRadians!.excursion > 0.01 };
});
assert(sourcePins.every(pin => sha(fs.readFileSync(path.join(ROOT, pin.path))) === pin.sha256), 'Source changed during check');
const passed = results.every(row => row.faultedTicks === 0 && row.finite && row.allBodyAndDrawnPresent
  && row.repeatTrajectoryByteIdentical && row.comAndDrawnPoseVary);
const report = { accepted: false, status: passed ? 'HELD_GAMEPLAY_PHYSICS_PREFLIGHT_PASS_RENDER_PENDING' : 'HELD_GAMEPLAY_PHYSICS_PREFLIGHT_FAILED',
  method: 'Actual createBikePhysics default v2; compiled registered track; direct120Hz steps; actual FrameBuilder alpha1 view. Two fresh deterministic runs per bike.',
  trackId: track.id, seed, physicsHz: hz, phases, constantInput: { throttle: 0, brake: 0, hop: false, restart: false },
  inputSHA256: sha(JSON.stringify(inputs)), compiledTrackSHA256: sha(JSON.stringify(compiled)),
  sourcePins, results, wallSeconds: (performance.now() - started) / 1000,
  limits: ['Physics-only, no GPU/Blender/browser/selected mesh load. No rendered/native75/art or contact acceptance.',
    'Direct physics preflight does not establish complete browser Game/render equivalence; actual captured gameplay remains required.',
    'Observed derived pose variation does not establish equilibrium profile extrema, garment fit or seating quality.'] };
fs.mkdirSync(path.dirname(out), { recursive: true });
fs.writeFileSync(out, JSON.stringify(report, null, 2) + '\n', { flag: 'wx' });
console.log(JSON.stringify({ out, status: report.status, wallSeconds: report.wallSeconds,
  results: results.map(({ bike, faultedTicks, repeatTrajectoryByteIdentical, comAndDrawnPoseVary, ranges }) =>
    ({ bike, faultedTicks, repeatTrajectoryByteIdentical, comAndDrawnPoseVary, ranges })) }));
if (!passed) process.exitCode = 1;
