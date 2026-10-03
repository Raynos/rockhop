/** Audit every observed actual arch surface; marker agreement alone is insufficient. */
import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import crypto from 'node:crypto';
const [folder, outFile] = process.argv.slice(2); assert(outFile && !fs.existsSync(outFile));
const sha = b => crypto.createHash('sha256').update(b).digest('hex');
const reportBytes = fs.readFileSync(path.join(folder, 'report.json')), report = JSON.parse(reportBytes);
assert.equal(report.cases.length, 3); assert.deepEqual(report.errors, []);
const traces = report.cases.map(c => {
  const bytes = fs.readFileSync(path.join(folder, c.id, 'tick-trace.ndjson'));
  assert.equal(sha(bytes), c.everyInputTraceSHA256);
  const rows = bytes.toString().trim().split('\n').map(l => JSON.parse(l)); assert.equal(rows.length, 703); return rows;
});
const physical = t => [t.inputTick, t.stateHash, t.tick, t.phase, t.runTime, t.finishTime, t.physicalPose];
for (let i = 0; i < 703; i++) {
  assert.deepEqual(physical(traces[0][i]), physical(traces[1][i]));
  assert.deepEqual(physical(traces[1][i]), physical(traces[2][i]));
  assert.deepEqual(traces[1][i].arch.sides, traces[2][i].arch.sides);
}
const quantile = (values, q) => { const sorted = values.slice().sort((a, b) => a - b); return sorted[Math.floor((sorted.length - 1) * q)]; };
const summaries = report.cases.map((c, index) => {
  const values = traces[index].flatMap(t => t.arch.sides.map(s => ({ ...s, inputTick: t.inputTick })));
  const maxima = Object.fromEntries(['centerToMarkerM', 'centerToPegM', 'markerToPegM', 'pegToActualFiniteArchM'].map(key => {
    const worst = values.reduce((a, b) => a[key] >= b[key] ? a : b); return [key, { maximumM: worst[key], side: worst.side, inputTick: worst.inputTick }];
  }));
  const times = traces[index].map(t => t.arch.readbackCpuMs);
  assert(times.every(t => Number.isFinite(t) && t >= 0));
  assert(values.every(s => s.actualAreaM2 > 0 && s.triangles.length === 7));
  const legLengths = c.samples.flatMap(s => s.boneLengths.flatMap(b => [b.thigh, b.shin]));
  assert(legLengths.every(l => l > 0 && Number.isFinite(l)));
  return { id: c.id, everyInputTicks: 703, archMeasurements: values.length, maxima, readbackCpuP50Ms: quantile(times, .5), readbackCpuP95Ms: quantile(times, .95),
    measuredLegLengthRangeM: [Math.min(...legLengths), Math.max(...legLengths)], actualSourceContract: c.init.actualArch,
    finalControlCalls: c.samples.at(-1).controlCalls, maximumGripDebugErrorM: Math.max(...c.samples.flatMap(s => s.debug.gripErr)), maximumLegStretchRatio: Math.max(...c.samples.flatMap(s => s.debug.legStretch)) };
});
assert.equal(summaries[0].finalControlCalls, 0); assert(summaries[1].finalControlCalls >= 1406);
assert.equal(summaries[1].finalControlCalls, summaries[2].finalControlCalls);
const proof = { status: 'UNACCEPTED_ACTUAL_CONSTRUCTED_ARCH_OFFSET_MEASURED', reportSHA256: sha(reportBytes), sourceSHA256: report.candidate.sha256,
  everyPhysicsTraceFieldsExact: true, onRepeatEveryActualArchSurfaceByteExact: true, comparedInputTicks: 2109, summaries,
  limits: ['Actual normalized skinned seven-triangle arch is measured, but geometric arch/load-bearing semantics and current wedge shape remain unaccepted.',
    'Partial703 tick riding window; not attempts-to-clear/restart/finish gate. Independent production Game replay is separate.',
    'CPU readback is shared desktop WebKit quantized diagnostic cost, not GPU/FPS/sustained physical phone acceptance.',
    'No source geometry/weights/bind/physics/pelvis modification or normal-player promotion. Root alone judges played art.'] };
fs.writeFileSync(outFile, JSON.stringify(proof, null, 2) + '\n'); console.log(JSON.stringify({ status: proof.status, summaries }));
