/** Convert actually played physics-driven native75 samples; no pose generation.
 * node gameplay_convert02.mjs INPUT.json FRESH_OUT
 * INPUT pins selectedNative, selectedContract, recipes and reports.rookie/pro; every pin
 * is {path,sha256}. Parent runs after successful real held-input captures.
 */
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import { fileURLToPath } from 'node:url';
import { Matrix4, Quaternion, Vector3, PropertyBinding } from 'three';

const ROOT = fileURLToPath(new URL('../../../../', import.meta.url));
const C = new Matrix4().set(1, 0, 0, 0, 0, 0, 1, 0, 0, -1, 0, 0, 0, 0, 0, 1);
const LIMIT = .0001;
const hash = filename => {
  const h = crypto.createHash('sha256'), fd = fs.openSync(filename, 'r'), b = Buffer.alloc(1024 * 1024);
  try { let n; while ((n = fs.readSync(fd, b)) > 0) h.update(b.subarray(0, n)); } finally { fs.closeSync(fd); }
  return h.digest('hex');
};
const pin = filename => ({ path: path.relative(ROOT, filename), sha256: hash(filename) });
function pinned(row) {
  assert(row && /^[a-f0-9]{64}$/.test(row.sha256));
  const filename = path.resolve(ROOT, row.path); assert(filename.startsWith(ROOT));
  assert.equal(hash(filename), row.sha256, `Changed source ${row.path}`); return filename;
}
function matrix(values) {
  assert(values?.length === 16 && values.every(Number.isFinite));
  const m = new Matrix4().fromArray(values); assert(Math.abs(m.determinant()) > .5); return m;
}
export function affineBound(a, b) {
  const d = a.elements.map((v, i) => v - b.elements[i]);
  return 2 * Math.hypot(...[0, 1, 2, 4, 5, 6, 8, 9, 10].map(i => d[i])) + Math.hypot(...d.slice(12, 15));
}
const rows = m => Array.from({ length: 4 }, (_, r) => Array.from({ length: 4 }, (_, c) => m.elements[c * 4 + r]));

/** Two independent paths: captured world matrices and parent/local TRS. */
export function convertSample(sample, contract) {
  assert(sample.debug.physicalPose === true && sample.debug.stageClip === null && sample.debug.allBoneFinite);
  assert(sample.frame.riderBody.present);
  const crashStateMeasured = typeof sample.frame.crashed === 'boolean', ragdollStateMeasured = Array.isArray(sample.frame.ragdoll);
  if (crashStateMeasured) assert.equal(sample.frame.crashed, false);
  if (ragdollStateMeasured) assert.equal(sample.frame.ragdoll.length, 0);
  assert.equal(sample.joints.length, 75);
  const rest = contract.nativeRest.bones, names = rest.map(b => b.name), parent = new Map(rest.map(b => [b.name, b.parent]));
  const byName = new Map(sample.joints.map(j => {
    const name = contract.specification.jointNames[j.id]; assert(name && names.includes(name));
    assert.equal(j.name, PropertyBinding.sanitizeNodeName(name)); return [name, j];
  }));
  assert.equal(byName.size, 75);
  const skeleton = matrix(sample.skeletonWorld), inverse = skeleton.clone().invert(), cumulative = new Map(), native = [];
  let hierarchyBound = 0;
  function world(name) {
    if (!cumulative.has(name)) {
      const j = byName.get(name); assert(j);
      assert(j.position.length === 3 && j.quaternion.length === 4 && j.scale.length === 3);
      assert([...j.position, ...j.quaternion, ...j.scale].every(Number.isFinite));
      assert(Math.abs(Math.hypot(...j.quaternion) - 1) < 2e-5);
      const local = new Matrix4().compose(new Vector3().fromArray(j.position), new Quaternion().fromArray(j.quaternion), new Vector3().fromArray(j.scale));
      cumulative.set(name, (parent.get(name) ? world(parent.get(name)).clone() : skeleton.clone()).multiply(local));
    }
    return cumulative.get(name);
  }
  for (const name of names) {
    const actual = matrix(byName.get(name).worldMatrix), expected = world(name);
    hierarchyBound = Math.max(hierarchyBound, affineBound(actual, expected));
    native.push(rows(C.clone().invert().multiply(inverse).multiply(actual)));
  }
  assert(hierarchyBound < LIMIT, `Captured hierarchy differs ${hierarchyBound}`);
  const f = sample.frame, rb = f.riderBody, c = Math.cos(f.bikeAngle), s = Math.sin(f.bikeAngle);
  const bike = matrix(sample.bikeFrameWorld), requested = new Vector3(f.bikeX + rb.relX * c - rb.relY * s,
    f.bikeY + rb.relX * s + rb.relY * c, 0).applyMatrix4(bike.clone().invert());
  const debug = sample.debug.anthropometry; assert(debug?.requestedCOM?.length === 3);
  const comProvenanceErrorM = requested.distanceTo(new Vector3().fromArray(debug.requestedCOM));
  const relative = rb.relAngle + f.bikeAngle - Math.atan2(bike.elements[1], bike.elements[0]);
  const carrierAngle = 65 * Math.PI / 180 + Math.atan2(Math.sin(relative), Math.cos(relative));
  assert(comProvenanceErrorM < 1e-6 && Math.abs(carrierAngle - debug.carrierAngle) < 1e-6, 'Captured COM/torso must be actual physical authority');
  return { native, hierarchyBound, witness: { tick: sample.tick, timeSeconds: sample.timeSeconds,
    phase: sample.phase, input: sample.input, frame: sample.frame, bikeFrameWorld: sample.bikeFrameWorld,
    physicalPose: true, stageClip: null, shapeActivation: 0, crashStateMeasured, ragdollStateMeasured,
    requestedCOMBike: requested.toArray(), carrierAngleRadians: carrierAngle,
    comProvenanceErrorM, anthropometry: debug, gripErrorM: sample.debug.gripErr, soleErrorM: sample.debug.soleErr,
    observedPelvisNative: native[names.indexOf(contract.specification.roles.pelvis)].map(r => r[3]).slice(0, 3) } };
}

export function convertReport(report, contract) {
  assert(!report.failure && report.errors.length === 0 && report.played.faults.length === 0);
  assert.equal(report.status, 'UNACCEPTED_ACTUAL_GAMEPLAY_LEAN');
  assert.equal(report.source.diagnosticKind, 'actual-gameplay-lean');
  assert(report.loaded.some(r => r.sha256 === contract.glbSHA256));
  const samples = report.played.motionSamples; assert.equal(samples.length, 241);
  assert.equal(report.played.ticks, 1200);
  assert.deepEqual(report.phases.map(p => [p.name, p.ticks, p.lean]),
    [['neutral', 240, 0], ['forward', 360, 1], ['backward', 360, -1], ['neutral-return', 240, 0]]);
  const converted = samples.map((sample, i) => {
    assert.equal(sample.tick, i * 5); assert.equal(sample.timeSeconds, sample.tick / 120);
    return convertSample(sample, contract);
  });
  return { name: 'RiderGameplayLean' + report.bike[0].toUpperCase() + report.bike.slice(1), bike: report.bike,
    fps: 24, seconds: 10, frameRange: [1, 241], playback: 'ONCE', loop: false, shapeActivation: 0,
    sourceTicks: samples.map(s => s.tick), surfaceWitnessFrames: [1, 49, 121, 193, 241],
    phases: report.phases, physicsAuthority: 'actual rendered frame.riderBody COM and relative torso angle',
    endpointMeaning: 'Observed simulation endpoints; commanded lean extrema do not imply equilibrium/profile extrema.',
    hierarchyMaximumAffineBoundWithin2mM: Math.max(...converted.map(s => s.hierarchyBound)),
    physicsWitnesses: converted.map(s => s.witness), nativeWorldMatrices: converted.map(s => s.native) };
}

function main() {
  const [inputName, outputName] = process.argv.slice(2); assert(inputName && outputName);
  const inputPath = path.resolve(inputName), out = path.resolve(outputName), input = JSON.parse(fs.readFileSync(inputPath));
  assert(input.accepted === false && !fs.existsSync(out) && out.startsWith(path.join(ROOT, 'harness/out/rider-rebuild/selected-authoring-motion11/')));
  assert.deepEqual(Object.keys(input.recipes).sort(), ['commonBuild', 'controls', 'gameplayControls', 'gameplayConverter']);
  for (const source of Object.values(input.recipes)) pinned(source);
  assert.equal(pinned(input.recipes.gameplayConverter), fileURLToPath(import.meta.url));
  const contract = JSON.parse(fs.readFileSync(pinned(input.selectedContract))); pinned(input.selectedNative);
  assert.equal(contract.qualificationState, 'UNACCEPTED_GAMEPLAY_LEAN_REVIEW'); assert(!contract.previewClip);
  assert.deepEqual(Object.keys(input.reports).sort(), ['pro', 'rookie']);
  const actions = ['rookie', 'pro'].map(bike => {
    const report = JSON.parse(fs.readFileSync(pinned(input.reports[bike]))); assert.equal(report.bike, bike);
    assert.equal(report.source.contract.sha256, input.selectedContract.sha256);
    for (const p of contract.gameplayLeanReview.sourcePins) pinned(p);
    return convertReport(report, contract);
  });
  assert.equal(actions[0].name, 'RiderGameplayLeanRookie');
  assert.equal(actions[1].name, 'RiderGameplayLeanPro');
  fs.mkdirSync(out);
  const posePath = path.join(out, 'measured-gameplay-native-world.json');
  const document = { accepted: false, status: 'MEASURED_GAMEPLAY_NATIVE_POSES_UNACCEPTED', source: input,
    boneNames: contract.nativeRest.bones.map(b => b.name), nativeRest: contract.nativeRest,
    coordinateMeaning: 'Native world = inverse(C) * inverse(captured RiderSkeleton matrixWorld) * captured bone.matrixWorld; C maps native (X,-Y,Z) to glTF (X,Z,-Y). Matrices below row-major. No bike offset or pose fit.',
    actions, shapeActivation: 0, limits: ['Observed actual physics trajectory; no stage score or synthetic equilibrium substitution.',
      'Matrix conversion is not Blender replay, live control reconstruction, contact qualification, appearance approval or a gameplay driver replacement.'] };
  fs.writeFileSync(posePath, JSON.stringify(document) + '\n', { flag: 'wx' });
  const receipt = { ...document, input: pin(inputPath), recipe: pin(fileURLToPath(import.meta.url)), nativePoseJSON: pin(posePath),
    actions: actions.map(({ nativeWorldMatrices, ...record }) => record) };
  fs.writeFileSync(path.join(out, 'receipt.json'), JSON.stringify(receipt, null, 2) + '\n', { flag: 'wx' });
  console.log(JSON.stringify({ out, actions: actions.map(a => ({ name: a.name, frames: a.frameRange[1] })) }));
}
if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) main();
