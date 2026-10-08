/** Read-only replay and sampled joint-continuity evidence; no acceptance thresholds. */
import fs from 'node:fs';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import { isDeepStrictEqual } from 'node:util';

const arg = (name, fallback) => process.argv.find(value => value.startsWith(`--${name}=`))?.slice(name.length + 3) ?? fallback;
const base = 'harness/out/rider-rebuild/selected-complete-engine01/';
const paths = { baseline: arg('baseline', base + 'ride03-pro-side/report.json'), current: arg('current', base + 'ride04-pro-coupled/report.json') };
const sha = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
const reports = {}, pins = {};
for (const [name, path] of Object.entries(paths)) {
  const bytes = fs.readFileSync(path); reports[name] = JSON.parse(bytes); pins[name] = { path, sha256: sha(bytes), bytes: bytes.length };
  assert.equal(reports[name].samples.length, 192, `${name}: complete 192-sample report required`);
  assert.deepEqual(reports[name].errors, []);
}
const { baseline, current } = reports;
assert.equal(current.bikeSelection.effective, baseline.bikeSelection.effective, 'Same bike required');
assert.deepEqual(current.selectedRiderSource, baseline.selectedRiderSource, 'Same selected source/contract required');
const supported = sample => sample.debug.physicalPose === true && sample.state.faulted === null;
const vector = (value, n) => Array.isArray(value) && value.length === n && value.every(Number.isFinite);
const distance = (a, b) => Math.hypot(...a.map((value, axis) => value - b[axis]));
const angle = (a, b) => {
  if (a.every((value, axis) => value === b[axis])) return 0;
  const denominator = Math.hypot(...a) * Math.hypot(...b); assert(denominator > 0, 'Nonzero quaternion required');
  return 2 * Math.acos(Math.min(1, Math.abs(a.reduce((sum, value, axis) => sum + value * b[axis], 0) / denominator)));
};
const statistics = values => {
  if (!values.length) return null;
  const sorted = [...values].sort((a, b) => a - b), at = fraction => sorted[Math.ceil((sorted.length - 1) * fraction)];
  return { min: sorted[0], median: at(0.5), p95: at(0.95), max: sorted.at(-1) };
};
const result = { accepted: false, pins, analyzerSHA256: sha(fs.readFileSync(new URL(import.meta.url))),
  selectedRiderSource: current.selectedRiderSource, bike: current.bikeSelection.effective,
  replay: { comparedSamples: 192, hashMismatches: [], stateMismatches: [], tickMismatches: [], inputMismatches: [] },
  phases: {}, continuity: { measuredPairs: 0, transitions: [], pairs: [], joints: {} },
  limits: ['Supported iff physicalPose=true and faulted=null; released contact values are stale and excluded.',
    'Only adjacent supported samples with advancing simulation ticks enter continuity metrics; resets and phase changes are disclosed.',
    'World-position deltas include bike locomotion and rotation. Local quaternion angles use normalized absolute dot products.',
    '12 fps witnesses cannot rule out higher-frequency jitter or establish acceptable joint speeds; no inferred temporal pass.',
    'Solver elapsedMs measures the reported final pose solve, not total frame/GPU time. No geometry, surface-contact or art acceptance.'] };
for (let index = 0; index < 192; index++) {
  const a = baseline.samples[index], b = current.samples[index];
  if (a.hash !== b.hash) result.replay.hashMismatches.push(index);
  if (!isDeepStrictEqual(a.state, b.state)) result.replay.stateMismatches.push(index);
  if (a.tick !== b.tick) result.replay.tickMismatches.push(index);
  if (!isDeepStrictEqual(a.input, b.input)) result.replay.inputMismatches.push(index);
}
result.replay.allPhysicalWitnessesExact = ['hashMismatches', 'stateMismatches', 'tickMismatches', 'inputMismatches'].every(key => !result.replay[key].length);
for (const [name, report] of Object.entries(reports)) {
  const rows = report.samples, active = rows.map((sample, index) => ({ sample, index })).filter(({ sample }) => supported(sample));
  const worst = key => active.reduce((best, row) => Math.max(...row.sample.debug[key]) > Math.max(...best.sample.debug[key]) ? row : best);
  const location = row => ({ index: row.index, mediaTimeS: row.index / report.fps, simulationTimeS: row.sample.state.time, tick: row.sample.tick });
  const hand = worst('gripErr'), sole = worst('soleErr');
  result.phases[name] = { samples: rows.length, supported: active.length, releasedOrCrash: rows.length - active.length,
    allBoneFinite: rows.every(sample => sample.debug.allBoneFinite),
    supportedOver1cm: active.filter(({ sample }) => Math.max(...sample.debug.gripErr, ...sample.debug.soleErr) > 0.01).map(location),
    maximumHandGap: { metres: Math.max(...hand.sample.debug.gripErr), ...location(hand) },
    maximumSoleGap: { metres: Math.max(...sole.sample.debug.soleErr), ...location(sole) },
    maximumXYCOMResidualM: Math.max(...active.map(({ sample }) => sample.debug.comResidual)),
    maximumAbsLateralResidualM: active.every(({ sample }) => Number.isFinite(sample.debug.anthropometry.lateralResidualM))
      ? Math.max(...active.map(({ sample }) => Math.abs(sample.debug.anthropometry.lateralResidualM))) : null,
    finalPoseSolveElapsedMs: statistics(active.map(({ sample }) => sample.debug.anthropometry.elapsedMs)),
    chosenFlexRadians: statistics(active.map(({ sample }) => sample.debug.anthropometry.spineFlexRadians)) };
}
const identities = Object.keys(current.samples[0].debug.candidate.jointNames).sort();
assert.equal(identities.length, 75);
for (const sample of current.samples) {
  assert.deepEqual(sample.jointPose.map(joint => joint.id).sort(), identities, 'All 75 actual joints required per sample');
  for (const joint of sample.jointPose) {
    assert(vector(joint.localQuaternion, 4) && vector(joint.worldPosition, 3), `Finite pose required: ${joint.id}`);
  }
}
for (let index = 1; index < current.samples.length; index++) {
  const before = current.samples[index - 1], after = current.samples[index];
  const phaseBefore = supported(before), phaseAfter = supported(after), reset = after.tick <= before.tick;
  if (phaseBefore !== phaseAfter || reset) result.continuity.transitions.push({ before: index - 1, after: index,
    supportedBefore: phaseBefore, supportedAfter: phaseAfter, tickReset: reset,
    tickBefore: before.tick, tickAfter: after.tick, faultedBefore: before.state.faulted, faultedAfter: after.state.faulted });
  if (!phaseBefore || !phaseAfter || reset) continue;
  const previous = new Map(before.jointPose.map(joint => [joint.id, joint]));
  const pair = { before: index - 1, after: index, mediaTimeS: index / current.fps,
    simulationTimeS: after.state.time, tickDelta: after.tick - before.tick,
    maximumLocalAngleRadians: { value: -1, id: null }, maximumWorldDeltaM: { value: -1, id: null } };
  for (const joint of after.jointPose) {
    const prior = previous.get(joint.id), rotation = angle(prior.localQuaternion, joint.localQuaternion), translation = distance(prior.worldPosition, joint.worldPosition);
    const stats = result.continuity.joints[joint.id] ??= { pairs: 0, maximumLocalAngleRadians: 0, maximumLocalAngleAfterIndex: null,
      maximumWorldDeltaM: 0, maximumWorldDeltaAfterIndex: null };
    stats.pairs++;
    if (rotation > stats.maximumLocalAngleRadians) { stats.maximumLocalAngleRadians = rotation; stats.maximumLocalAngleAfterIndex = index; }
    if (translation > stats.maximumWorldDeltaM) { stats.maximumWorldDeltaM = translation; stats.maximumWorldDeltaAfterIndex = index; }
    if (rotation > pair.maximumLocalAngleRadians.value) pair.maximumLocalAngleRadians = { value: rotation, id: joint.id };
    if (translation > pair.maximumWorldDeltaM.value) pair.maximumWorldDeltaM = { value: translation, id: joint.id };
  }
  result.continuity.pairs.push(pair);
}
result.continuity.measuredPairs = result.continuity.pairs.length;
result.continuity.maximumLocalAngleRadians = statistics(result.continuity.pairs.map(pair => pair.maximumLocalAngleRadians.value));
result.continuity.maximumWorldDeltaM = statistics(result.continuity.pairs.map(pair => pair.maximumWorldDeltaM.value));
const output = arg('out');
if (output) { assert(!fs.existsSync(output), 'Fresh analysis output required'); fs.writeFileSync(output, JSON.stringify(result, null, 2) + '\n'); }
console.log(JSON.stringify({ replay: result.replay, phases: result.phases, continuity: {
  measuredPairs: result.continuity.measuredPairs, transitions: result.continuity.transitions,
  maximumLocalAngleRadians: result.continuity.maximumLocalAngleRadians, maximumWorldDeltaM: result.continuity.maximumWorldDeltaM } }));
