/** Complete finite head/head and body/head checks for pinned native snapshots. */
import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import fs from 'node:fs';
import path from 'node:path';
import zlib from 'node:zlib';
import { checkPair } from './geometry-check.mjs';

const [directory, output] = process.argv.slice(2);
assert(directory && output && !fs.existsSync(output), 'Supply native intake and new report');
const sha = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
const reportPath = path.join(directory, 'report.json');
const input = JSON.parse(fs.readFileSync(reportPath, 'utf8'));
const records = [];
for (const pin of input.samples) {
  const bytes = fs.readFileSync(path.join(directory, pin.path));
  assert.equal(sha(bytes), pin.sha256);
  const sample = JSON.parse(zlib.gunzipSync(bytes));
  const row = { index: sample.index, case: sample.case, phase: sample.phase, fields: {} };
  for (const kind of ['full', 'four']) {
    const head = sample.parts.head[kind], body = sample.parts.body[kind];
    assert(head && body, 'Both complete evaluated parts are required');
    row.fields[kind] = {
      'head/head': checkPair(head, head, true),
      'body/head': checkPair(body, head),
    };
  }
  records.push(row);
  process.stdout.write(`BODY06_CONTACT_SAMPLE ${sample.index}\n`);
}
fs.writeFileSync(output, `${JSON.stringify({
  status: 'UNACCEPTED_COMPLETE_FINITE_HEADSELF_BODYHEAD_CONTACT_DIAGNOSTIC',
  nativeReportSHA256: sha(fs.readFileSync(reportPath)), sourcePins: input.sourcePins,
  recipeSHA256: sha(fs.readFileSync(new URL(import.meta.url))),
  classifierSHA256: sha(fs.readFileSync(new URL('./geometry-check.mjs', import.meta.url))),
  triangleContactSHA256: sha(fs.readFileSync(new URL('../hero-remaster/user-agent3-2026-10-03/triangle-contacts.mjs', import.meta.url))),
  records,
  limits: [
    'Complete evaluated triangles at ten declared poses, with unchanged proper classifier and 1e-9 m epsilon.',
    'Shared native vertex IDs excluded only for head self; no positional alias or source corner exclusions.',
    'Degenerate surfaces remain unqualified and their IDs retained; no finite zero contacts becomes a continuous certificate.',
    'No signed penetration depth, grounded support, whole wearer, clothing, GPU, played-art or device acceptance.',
  ],
}, null, 2)}\n`);
