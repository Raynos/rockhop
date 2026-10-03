/** Full held-out trajectory metrics, including unsupported reach rather than hiding it. */
import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import crypto from 'node:crypto';
const [folder, outFile] = process.argv.slice(2); assert(outFile && !fs.existsSync(outFile));
const sha = b => crypto.createHash('sha256').update(b).digest('hex');
const reportBytes = fs.readFileSync(path.join(folder, 'report.json')), report = JSON.parse(reportBytes);
assert.equal(report.cases.length, 8); assert.deepEqual(report.errors, []);
const results = [], traces = new Map();
for (const c of report.cases) {
  const bytes = fs.readFileSync(path.join(folder, c.id, 'tick-trace.ndjson')); assert.equal(sha(bytes), c.everyInputTraceSHA256);
  const rows = bytes.toString().trim().split('\n').map(l => JSON.parse(l)); assert.equal(rows.length, c.everyInputTickCount); traces.set(c.id, rows);
  const surfaces = rows.flatMap(t => t.arch.sides.map(s => ({ ...s, inputTick: t.inputTick })));
  const maxima = Object.fromEntries(['centerToMarkerM', 'centerToPegM', 'markerToPegM', 'pegToActualFiniteArchM'].map(key => {
    const worst = surfaces.reduce((a, b) => a[key] >= b[key] ? a : b); return [key, { maximumM: worst[key], side: worst.side, inputTick: worst.inputTick }];
  }));
  results.push({ id: c.id, fixtureId: c.fixtureId, inputTicks: rows.length, actualArchMeasurements: surfaces.length, maxima,
    actualFiniteArchOver1MmCount: surfaces.filter(s => s.pegToActualFiniteArchM > .001).length,
    actualCentroidOver1MmCount: surfaces.filter(s => s.centerToPegM > .001).length,
    maximumSampledLegStretchRatio: Math.max(...c.samples.flatMap(s => s.debug.legStretch)), maximumSampledGripErrorM: Math.max(...c.samples.flatMap(s => s.debug.gripErr)),
    maximumSourcePositionResidualM: c.init.actualArch.maximumSourcePositionResidualM, maximumSourceWeightError: c.init.actualArch.maximumSourceWeightError,
    poseInjection: c.samples.some(s => s.poseInjection), physicalPoseEveryTick: rows.every(t => t.physicalPose), sampledInputTicks: c.samples.map(s => s.inputTick) });
}
for (const fixture of new Set(report.cases.map(c => c.fixtureId))) {
  const off = traces.get(fixture + '-off'), on = traces.get(fixture + '-on'); assert(off && on && off.length === on.length);
  const fields = t => [t.inputTick, t.stateHash, t.tick, t.phase, t.runTime, t.finishTime, t.physicalPose];
  for (let i = 0; i < off.length; i++) assert.deepEqual(fields(off[i]), fields(on[i]));
}
const proof = { status: 'UNACCEPTED_CONSTRUCTED09_HELDOUT_TRAJECTORIES_AUDITED', reportSHA256: sha(reportBytes), candidateSHA256: report.candidate.sha256,
  totalActualInputTicks: results.reduce((sum, r) => sum + r.inputTicks, 0), everyOffOnPhysicsFieldsExact: true, results,
  limits: ['Metrics include entire trajectory from spawn; the orbit films show19 sampled frames in each named transition window.',
    'Existing peg upper-surface reference point and proposed seven-triangle arch only. No full peg solid/collision/load-bearing or current wedge art acceptance.',
    'Four held-out actual riding fixtures; arbitrary independent toe/ankle articulation, rear landing, crash/restart and physical phone remain unqualified.',
    'Shared desktop CPU readback remains quantized; no mobile/GPU/performance promotion. Root alone judges moving art.'] };
fs.writeFileSync(outFile, JSON.stringify(proof, null, 2) + '\n'); console.log(JSON.stringify({ totalActualInputTicks: proof.totalActualInputTicks, results }));
