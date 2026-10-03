/** Pin the reused input fixture; this measures no new candidate. */
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';

const root = process.cwd();
const evidence = 'docs/evidence/hero-remaster/user-agent3-qa-2026-10-03';
const fixturePath = 'docs/evidence/hero-remaster/rider-contact-diagnostic-2026-10-03/aligned01/engine-fixture.json';
const manifestPath = 'docs/evidence/hero-remaster/anatomical-foundation-2026-10-03/control01/export-manifest.json';
const pin = file => {
  const bytes = fs.readFileSync(file);
  return { path: path.relative(root, path.resolve(file)), bytes: bytes.length,
    sha256: crypto.createHash('sha256').update(bytes).digest('hex') };
};
const fixture = JSON.parse(fs.readFileSync(fixturePath));
const baseline = JSON.parse(fs.readFileSync(manifestPath));
const bike = pin('public/models/bike-rookie.glb');
assert.equal(bike.sha256, fixture.bikeSHA256);
const control = pin(baseline.file);
assert.equal(control.sha256, baseline.sha256);
assert.equal(baseline.namedRuntime19.length, 19);
const report = {
  schemaVersion: 1, status: 'PREPARED_NO_CANDIDATE_ACCEPTANCE',
  recordedAtUTC: new Date().toISOString(),
  repositorySHA: execFileSync('git', ['rev-parse', 'HEAD'], { encoding: 'utf8' }).trim(),
  ownAttribution: execFileSync('node', ['.githooks/resolve-attribution.mjs'], { encoding: 'utf8' }).trim(),
  suppliedContext: { filesystem: 'unrestricted / danger-full-access', network: 'enabled', approval: 'never' },
  pins: { fixture: pin(fixturePath), baselineManifest: pin(manifestPath), bike, control },
  bikeFrameWorldColumnMajor: fixture.fixture.bikeFrameWorld,
  historicalBikeContactMarksWorldM: fixture.bikeRuntimeContactMarks,
  baselineCoordinateContract: baseline.coordinateContract,
  baselineSkinJointOrders: baseline.inverseBinds,
  baselineActionOffPoses: Object.keys(baseline.actionOffPoses),
  gates: Object.fromEntries(['M0', 'M1', 'M2', 'M3', 'M4', 'M5'].map(g => [g, 'OPEN'])),
  limits: [
    'Historical fixture reused; no current candidate or runtime capture measured.',
    'Socket marks do not establish palm, sole or saddle surface support.',
    'Native/conditioned/export vertex correspondence and time-matched samples pending Agent 1.',
    'Finite time samples cannot certify continuous parity.',
    'Root alone judges appearance, likeness and gates; physical iOS and stranger observations absent.',
  ],
};
fs.mkdirSync(evidence, { recursive: true });
fs.writeFileSync(path.join(evidence, 'intake.json'), JSON.stringify(report, null, 2) + '\n');
console.log(JSON.stringify({ status: report.status, pins: report.pins, gates: report.gates }));
