/** No per-boot allocation is inferred from an old player or incomplete scene. */
import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../../../..');
const hash = value => crypto.createHash('sha256').update(value).digest('hex');
export function summarize(input) {
  assert.equal(input.schemaVersion, 1);
  assert.equal(input.completeSceneTriangleBudget, 500000);
  assert(Array.isArray(input.requiredCases) && input.requiredCases.length > 0);
  assert.equal(new Set(input.requiredCases).size, input.requiredCases.length);
  const frames = input.frames ?? [];
  const missingCases = input.requiredCases.filter(id => !frames.some(row => row.caseId === id));
  const measured = frames.map(row => {
    assert(input.requiredCases.includes(row.caseId), 'Unregistered scene case');
    assert(row.drawRows?.length > 0 && row.drawRows.some(draw => draw.rider && draw.triangles > 0));
    for (const draw of row.drawRows) assert(Number.isSafeInteger(draw.triangles) && draw.triangles >= 0);
    const complete = row.drawRows.reduce((n, draw) => n + draw.triangles, 0);
    const rider = row.drawRows.filter(draw => draw.rider).reduce((n, draw) => n + draw.triangles, 0);
    assert.equal(row.completeSceneDrawTriangles, complete);
    assert.equal(row.riderDrawTriangles, rider);
    assert.equal(row.nonRiderDrawTriangles, complete - rider);
    return { caseId: row.caseId, tick: row.tick, completeSceneDrawTriangles: complete,
      nonRiderDrawTriangles: complete - rider, riderDrawTriangles: rider,
      availableTotalRiderDrawTriangles: 500000 - (complete - rider),
      triangleBudgetPassed: complete <= 500000 };
  });
  return { schemaVersion: 1, acceptedArt: false,
    status: missingCases.length ? 'MISSING_COMPLETE_SCENE_MEASUREMENTS_NO_ALLOCATION'
      : measured.every(row => row.triangleBudgetPassed) ? 'SAMPLED_SCENES_WITHIN_BUDGET_UNACCEPTED'
      : 'REJECTED_SAMPLED_COMPLETE_SCENE_TRIANGLE_BUDGET',
    completeSceneTriangleBudget: 500000, perBootTriangleAllocation: null, missingCases, measured,
    maximumMeasuredCompleteSceneDrawTriangles: measured.length ? Math.max(...measured.map(row => row.completeSceneDrawTriangles)) : null,
    limits: ['No exact8000 gate. Available total rider DRAW triangles are shared by all rider parts and every render pass; never divide them into an invented boot cap.',
      'Measurements apply only to their exact pinned full scene/candidate and sampled frame. Complete both-bike/course/pose/camera/streaming coverage remains required.',
      'Unchanged source identity, every original1mm/detail/orientation/skin/FOUR/support/fold/contact gate, selected atlas bake, moving review,96MiB,16msP95,heap and devices remain required.'] };
}
if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  assert.equal(process.argv.length, 4, 'Usage: node budget.mjs INTAKE_JSON NEW_REPORT_JSON');
  const raw = fs.readFileSync(process.argv[2]); const input = JSON.parse(raw);
  for (const row of Object.values(input.pins ?? {})) {
    const file = path.resolve(ROOT, row.path); const relative = path.relative(ROOT, file);
    assert(relative && !relative.startsWith('..') && !path.isAbsolute(relative));
    assert.equal(hash(fs.readFileSync(file)), row.sha256, `Changed pin: ${row.path}`);
  }
  const report = { ...summarize(input), intakeSHA256: hash(raw) };
  fs.writeFileSync(process.argv[3], JSON.stringify(report, null, 2)+'\n', { flag: 'wx' });
  console.log(JSON.stringify({ status: report.status, missingCases: report.missingCases.length, perBootTriangleAllocation: null }));
  if (report.status !== 'SAMPLED_SCENES_WITHIN_BUDGET_UNACCEPTED') process.exitCode = 2;
}
