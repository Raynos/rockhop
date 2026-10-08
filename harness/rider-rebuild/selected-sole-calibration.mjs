/** Freeze measured rigid selected soles against both actual bike peg sources. */
import fs from 'node:fs';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
const arg = key => process.argv.find(value => value.startsWith(`--${key}=`))?.slice(key.length + 3);
const sha = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
const inputs = ['rookie', 'pro'].map(key => {
  const file = arg(key); assert(file, `Missing --${key}`);
  const bytes = fs.readFileSync(file), report = JSON.parse(bytes);
  return { key, file, sha256: sha(bytes), report };
});
const first = inputs[0].report, driver = { selectedSoleInFoot: {}, selectedPegSurfaceBike: {} };
assert(arg('out') && !fs.existsSync(arg('out')), 'Fresh calibration output required');
assert.equal(sha(fs.readFileSync(first.source.path)), first.source.sha256);
for (const { report } of inputs) {
  assert.deepEqual(report.source, first.source); assert.deepEqual(report.contract, first.contract);
  assert.equal(sha(fs.readFileSync(report.bike.path)), report.bike.sha256);
  assert.equal(report.boots.length, 2);
  for (const row of report.boots) {
    assert(row.sampledSupportNormalsOpposition > .99);
    assert(row.supportPointSource.fields.every(fields => fields.length === 1
      && fields[0][0] === `DEF-foot.${row.side === 'left' ? 'L' : 'R'}` && fields[0][1] === 1));
    for (const [key, value] of [['selectedSoleInFoot', row.selectedSoleInFoot],
      ['selectedPegSurfaceBike', row.finitePegPoint.point]]) {
      if (driver[key][row.side]) assert.deepEqual(driver[key][row.side], value, 'Bike support frames differ; require per-bike consumption');
      driver[key][row.side] = value;
    }
  }
}
fs.writeFileSync(arg('out'), JSON.stringify({ accepted: false, sourceSHA256: first.source.sha256,
  driver, bikes: inputs.map(({ report }) => report.bike),
  evidence: inputs.map(({ key, file, sha256 }) => ({ bike: key, path: file, sha256 })),
  limits: 'Measured rigid outer-sole witness and finite peg points only; whole moving contacts and art remain unaccepted.' }, null, 2) + '\n');
