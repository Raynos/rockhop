/** Cheap deterministic receipt→driver overlay; no GLB decode, posing or search. */
import fs from 'node:fs';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import { Matrix4, Quaternion } from 'three';

const base = 'assets/blender/rider-rebuild/selected-ankle-contact02/';
const input = JSON.parse(fs.readFileSync(base + 'calibration-inputs.json'));
const sha = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
const read = row => { const bytes = fs.readFileSync(row.path); assert.equal(sha(bytes), row.sha256, row.path); return bytes; };
const fixture = JSON.parse(read(input.fixture)), previous = JSON.parse(read(input.previous));
read(input.controller);
assert.equal(fixture.inputs.source.sha256, previous.sourceSHA256);
assert.deepEqual(fixture.inputs.calibration, input.previous);
assert.deepEqual(fixture.inputs.dependencies.find(row => row.path === input.controller.path), input.controller);
const output = structuredClone(previous), pro = fixture.bikes.find(row => row.bike === 'pro');
assert(pro && fixture.bikes.length === 2);
const fields = ['soleInFoot', 'contactPointBike', 'soleFrameBike'];
for (const row of fixture.bikes) {
  const source = fixture.inputs.bikes.find(bike => bike.name === row.bike);
  assert(previous.bikes.some(bike => bike.path === source.path && bike.sha256 === source.sha256));
  for (const side of ['left', 'right']) {
    const actual = row.sides.find(item => item.side === side).proposed;
    const reference = pro.sides.find(item => item.side === side).proposed;
    for (const key of fields) assert.deepEqual(actual[key], reference[key], `${row.bike}.${side}.${key}`);
  }
}
output.driver.soleQuaternionBike = {};
for (const row of pro.sides) {
  const source = row.proposed;
  output.driver.selectedSoleInFoot[row.side] = [...source.soleInFoot];
  output.driver.selectedPegSurfaceBike[row.side] = [...source.contactPointBike];
  output.driver.soleQuaternionBike[row.side] = new Quaternion().setFromRotationMatrix(new Matrix4().fromArray(source.soleFrameBike)).normalize().toArray();
}
assert.equal(output.driver.maxSpineFlexRadians, previous.driver.maxSpineFlexRadians);
assert.deepEqual(Object.keys(output.driver).sort(), [...Object.keys(previous.driver), 'soleQuaternionBike'].sort());
output.accepted = false;
output.limits = 'One source-derived static ankle/finite-peg candidate. Actual fixed-length sole gaps remain 1.396/3.330 mm at Pro sample28; new bearing normal opposition 0.8486/0.9654 is point/edge support, not qualified moving contact. Full both-bike replay, ankle range, whole surfaces and selected art remain unaccepted; no player promotion.';
output.calibration.previousSoleCalibration = previous.calibration.soleCalibration;
output.calibration.soleCalibration = input.fixture;
output.calibration.qualification = 'SOURCE_DERIVED_ANKLE_CONTACT_CANDIDATE_MOVING_CONTACT_AND_ART_UNACCEPTED';
output.calibration.rationale = 'The actual fixture rotates the source foot/frame/normal about the anatomical ankle by the single measured sole-normal/peg-normal pitch, then settles actual rigid sole triangles against actual finite peg triangles. Copy those exact proposed contact frames; do not copy unreachable inverse ankle positions or claim zero gap. The previous torso envelope and existing three-candidate COM solver remain unchanged.';
output.calibration.driverBindings = [...previous.calibration.driverBindings, 'soleQuaternionBike'];
output.calibration.generation = { ...input, recipe: { path: base + 'generate-calibration.mjs', sha256: sha(fs.readFileSync(new URL(import.meta.url))) },
  derivation: 'selectedSoleInFoot=pro.sides.proposed.soleInFoot; selectedPegSurfaceBike=contactPointBike; soleQuaternionBike=normalized quaternion from soleFrameBike, matching existing controller extraction.',
  bothBikeProposedContactRowsByteIdentical: true,
  fixedFixtureSample: fixture.sample,
  fixtureResiduals: { soleErrM: pro.realized.soleErrM, legDemand: pro.realized.legDemand,
    inverseXYResidualM: pro.realized.inverseXY.residualM, residualXYZM: pro.realized.residualXYZM },
  nextJudgment: 'Actual full Rookie and Pro recorded replays through unchanged three-candidate solver; moving contact and selected appearance judged by parent.' };
const path = base + 'engine05-contact-calibration03.json';
fs.writeFileSync(path, JSON.stringify(output, null, 2) + '\n');
console.log(JSON.stringify({ path, sha256: sha(fs.readFileSync(path)), accepted: false,
  maxSpineFlexRadians: output.driver.maxSpineFlexRadians, bothBikeProposedContactRowsByteIdentical: true }));
