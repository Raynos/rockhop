/** Independent scalar replay of captured actual matrices and production Game. */
import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import { Game } from '../../../src/game/game.ts';
import { createBikePhysicsV2 } from '../../../src/physics/v2/bike.ts';
import { decodeJSON, expandFrames } from '../../../src/core/replay.ts';
import { readGlbChunks } from './metadata.mjs';
import { acc } from './fidelity-utils.mjs';
const [packet, candidateFile, fixturesFile, outFile] = process.argv.slice(2);
assert(outFile && !fs.existsSync(outFile)); const sha = b => crypto.createHash('sha256').update(b).digest('hex');
const reportBytes = fs.readFileSync(path.join(packet, 'report.json')), report = JSON.parse(reportBytes), source = fs.readFileSync(candidateFile);
assert.equal(sha(source), report.candidateSHA256); assert(report.all703NumericalRowsRepeatExact && !report.failure);
const g = readGlbChunks(source), a = g.json.meshes[0].primitives[0].attributes;
const positions = acc(g, a.POSITION), indices = [acc(g, a.JOINTS_0), acc(g, a.JOINTS_1)], weights = [acc(g, a.WEIGHTS_0), acc(g, a.WEIGHTS_1)];
const f = JSON.parse(fs.readFileSync(fixturesFile)).cases.find(c => c.id === report.fixtureId);
const recordingBytes = fs.readFileSync(path.join(path.dirname(fixturesFile), f.recording));
assert.equal(sha(recordingBytes), report.recordingSHA256); const recording = decodeJSON(recordingBytes.toString()), input = expandFrames(recording);
const transform = (point, matrix) => [0, 1, 2].map(k => matrix[k] * point[0] + matrix[k + 4] * point[1] + matrix[k + 8] * point[2] + matrix[k + 12]);
const apply = (row, matrices, full) => {
  const result = [0, 0, 0], primarySum = weights[0][row].reduce((x, y) => x + y, 0); let total = 0;
  for (let set = 0; set < (full ? 2 : 1); set++) for (let k = 0; k < 4; k++) {
    const w = full ? weights[set][row][k] : Math.fround(weights[0][row][k] / primarySum);
    if (w <= 0) continue; total += w; const p = transform(positions[row], matrices[indices[set][row][k]]);
    for (let axis = 0; axis < 3; axis++) result[axis] += p[axis] * w;
  }
  return full ? result.map(x => x / total) : result;
};
const output = { status: 'UNACCEPTED_INSTALLED_FOUR_SLOT_POSED_ERROR_INDEPENDENTLY_REPRODUCED', reportSHA256: sha(reportBytes),
  sourceSHA256: sha(source), auditSHA256: sha(fs.readFileSync(new URL(import.meta.url))), runs: [],
  limits: ['All188secondary render rows measured for703actual riding ticks twice; independent scalar four/eight math matches captured CPU surfaces.',
    'Standard shader has the same four consumed slots, but GPU arithmetic/output is not directly read back. Eight-slot reference is numerical, never displayed.',
    'No new cosmetic movie, construction, weight/shader rewrite, collision response, phone or visual acceptance.',
    'Native body/self contacts and root rejection are independent; measured posed error does not identify a visible tear.'] };
for (const run of report.runs) {
  const raw = fs.readFileSync(path.join(packet, run.name + '.weights.ndjson')), trace = fs.readFileSync(path.join(packet, run.name + '.physics.ndjson'));
  assert.equal(sha(raw), run.all703RowsSHA256); assert.equal(sha(trace), run.physicsSHA256);
  const rows = raw.toString().trim().split('\n').map(JSON.parse), traces = trace.toString().trim().split('\n').map(JSON.parse);
  assert.equal(rows.length, 703); assert.equal(traces.length, rows.length);
  const game = new Game({ physics: createBikePhysicsV2(recording.header.physicsHz), physicsHz: recording.header.physicsHz,
    renderer: { setTrack() {}, onEvent() {}, setQuality() {}, setBikeClass() {} }, autoSkipCountdown: true, ghostEnabled: false });
  game.loadTrack(recording.header.trackId, recording.header.seed, recording.header.bike);
  let maximumActual4ResidualM = 0, maximumReference8ResidualM = 0, maximumOmittedWeightDisplacementM = 0;
  for (let i = 0; i < rows.length; i++) {
    const r = rows[i], t = traces[i]; game.setInput(input[i]); game.step(1);
    assert.equal(t.inputTick, i + 1); assert.equal(r.inputTick, i + 1); assert.equal(t.stateHash, game.hashState());
    assert.equal(t.tick, game.getState().tick); assert.equal(t.phase, game.phase()); assert.equal(t.runTime, game.runTime()); assert.equal(t.finishTime, game.getState().finishTime);
    assert.equal(r.matrices.length, 51 * 16); assert.equal(r.secondaryRows.length, 188);
    const matrices = Array.from({ length: 51 }, (_, j) => r.matrices.slice(j * 16, (j + 1) * 16));
    for (const m of matrices) assert(Math.abs(m[3]) + Math.abs(m[7]) + Math.abs(m[11]) + Math.abs(m[15] - 1) < 1e-12);
    let maximum = 0;
    for (let j = 0; j < r.secondaryRows.length; j++) {
      const row = r.secondaryRows[j], actual = r.observed.slice(j * 3, j * 3 + 3), expected = r.expected8.slice(j * 3, j * 3 + 3);
      const four = apply(row, matrices, false), eight = apply(row, matrices, true);
      maximumActual4ResidualM = Math.max(maximumActual4ResidualM, Math.hypot(...actual.map((x, k) => x - four[k])));
      maximumReference8ResidualM = Math.max(maximumReference8ResidualM, Math.hypot(...expected.map((x, k) => x - eight[k])));
      maximum = Math.max(maximum, Math.hypot(...four.map((x, k) => x - eight[k])));
    }
    assert(Math.abs(maximum - r.maximumOmittedWeightDisplacementM) < 2e-12);
    maximumOmittedWeightDisplacementM = Math.max(maximumOmittedWeightDisplacementM, maximum);
  }
  assert(maximumActual4ResidualM < 2e-12); assert(maximumReference8ResidualM < 2e-12);
  assert(Math.abs(maximumOmittedWeightDisplacementM - run.maximumOmittedWeightDisplacementM) < 2e-12);
  output.runs.push({ name: run.name, inputTicks: rows.length, checkedSecondaryRowPositions: rows.length * 188,
    maximumActual4ResidualM, maximumReference8ResidualM, maximumOmittedWeightDisplacementM,
    all703ProductionGamePhysicsExact: true, finalStateHash: game.hashState(), rawWeightSHA256: sha(raw), traceSHA256: sha(trace) });
}
fs.writeFileSync(outFile, JSON.stringify(output, null, 2) + '\n'); console.log(JSON.stringify(output.runs));
