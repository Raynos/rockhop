/** Independent finite surface diagnostics; missing partners never become zero contacts. */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import zlib from 'node:zlib';
import crypto from 'node:crypto';
import { pathToFileURL } from 'node:url';
import { triangleContact } from '../hero-remaster/user-agent3-2026-10-03/triangle-contacts.mjs';
const sub = (a, b) => a.map((x, i) => x - b[i]);
const dot = (a, b) => a.reduce((s, x, i) => s + x * b[i], 0);
const cross = (a, b) => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
const epsilon = 1e-9;
const overlaps = (a, b) => a.min.every((x, i) => x <= b.max[i] + epsilon && b.min[i] <= a.max[i] + epsilon);
function finiteRows(xyz, faces) {
  assert(xyz.length && faces.length && xyz.every(v => v.length === 3 && v.every(Number.isFinite)), 'Missing/nonfinite surface');
  const rows = [], degenerate = [];
  for (const [id, ids] of faces.entries()) {
    assert(ids.length === 3 && ids.every(i => Number.isInteger(i) && i >= 0 && i < xyz.length));
    const points = ids.map(i => xyz[i]), area2 = Math.hypot(...cross(sub(points[1], points[0]), sub(points[2], points[0])));
    if (area2 < 1e-14) { degenerate.push(id); continue; }
    rows.push({ id, ids, points, min: [0, 1, 2].map(k => Math.min(...points.map(p => p[k]))), max: [0, 1, 2].map(k => Math.max(...points.map(p => p[k]))) });
  }
  return { rows, degenerate };
}
function tree(rows) {
  const min = [0, 1, 2].map(k => rows.reduce((m, r) => Math.min(m, r.min[k]), Infinity));
  const max = [0, 1, 2].map(k => rows.reduce((m, r) => Math.max(m, r.max[k]), -Infinity));
  if (rows.length <= 12) return { min, max, rows };
  const axis = [0, 1, 2].reduce((a, b) => max[a] - min[a] >= max[b] - min[b] ? a : b);
  const sorted = rows.slice().sort((a, b) => a.min[axis] + a.max[axis] - b.min[axis] - b.max[axis]), half = Math.floor(sorted.length / 2);
  return { min, max, left: tree(sorted.slice(0, half)), right: tree(sorted.slice(half)) };
}
export function properTriangleCrossing(a, b) {
  function edgePassesTriangle(points, target) {
    const u = sub(target[1], target[0]), v = sub(target[2], target[0]), n = cross(u, v), size = Math.hypot(...n);
    const distances = points.map(p => dot(n, sub(p, target[0])) / size);
    for (let i = 0; i < 3; i++) {
      const j = (i + 1) % 3;
      if (!(distances[i] < -epsilon && distances[j] > epsilon || distances[i] > epsilon && distances[j] < -epsilon)) continue;
      const t = distances[i] / (distances[i] - distances[j]);
      const q = points[i].map((x, k) => x + t * (points[j][k] - x));
      const w = sub(q, target[0]), uu = dot(u, u), uv = dot(u, v), vv = dot(v, v), wu = dot(w, u), wv = dot(w, v), denom = uu * vv - uv * uv;
      const s = (wu * vv - wv * uv) / denom, r = (wv * uu - wu * uv) / denom;
      if (s > 1e-9 && r > 1e-9 && s + r < 1 - 1e-9) return true;
    }
    return false;
  }
  return edgePassesTriangle(a, b) || edgePassesTriangle(b, a);
}
export function checkPair(a, b, same = false) {
  const left = finiteRows(a.xyzWorld, a.faces), right = same ? left : finiteRows(b.xyzWorld, b.faces);
  let candidates = 0, contacts = 0, proper = 0;
  const witnesses = [], properWitnesses = [];
  if (right.rows.length) {
    const root = tree(right.rows);
    function query(row, node) {
      if (!overlaps(row, node)) return;
      if (!node.rows) { query(row, node.left); query(row, node.right); return; }
      for (const other of node.rows) {
        if (same && (other.id <= row.id || row.ids.some(id => other.ids.includes(id))) || !overlaps(row, other)) continue;
        candidates++;
        if (triangleContact(row.points, other.points, epsilon)) {
          contacts++;
          const strict = properTriangleCrossing(row.points, other.points); if (strict) proper++;
          if (strict && properWitnesses.length < 16) properWitnesses.push({ triangleA: row.id, triangleB: other.id, nativeVertexIDsA: row.ids, nativeVertexIDsB: other.ids, xyzWorldA: row.points, xyzWorldB: other.points });
          if (witnesses.length < 16) witnesses.push({ triangleA: row.id, triangleB: other.id, proper: strict });
        }
      }
    }
    for (const row of left.rows) query(row, root);
  }
  return { status: left.degenerate.length || right.degenerate.length ? 'DEGENERATE_SURFACE_UNQUALIFIED' : 'SAMPLED_FINITE_DIAGNOSTIC', candidates, finiteContacts: contacts, properCrossings: proper, witnesses, properWitnesses,
    degenerateA: left.degenerate, degenerateB: right.degenerate, epsilonM: epsilon, sharedVertexExclusion: same ? 'Same native derivative vertex identity only; no unrelated/coincident surface exclusion' : 'None' };
}
export function inspectSnapshot(snapshot) {
  assert(snapshot.parts.body && snapshot.parts.head, 'Body and separate head mandatory; missing target cannot pass');
  const report = { index: snapshot.index, case: snapshot.case, phase: snapshot.phase, fields: {} };
  const regions = Object.keys(snapshot.parts);
  for (const kind of ['full', 'four']) {
    const pairs = {};
    for (let i = 0; i < regions.length; i++) for (let j = i; j < regions.length; j++) {
      const a = snapshot.parts[regions[i]][kind], b = snapshot.parts[regions[j]][kind];
      assert(a && b, 'Every declared region requires full and four native evaluated data');
      pairs[`${regions[i]}/${regions[j]}`] = checkPair(a, b, i === j);
    }
    report.fields[kind] = pairs;
  }
  report.coverage = { status: 'UNMEASURED', reason: 'Requires declared semantic garment opening/body coverage samples and complete wearer; pair distances or absent wardrobe cannot prove enclosure.' };
  report.missingWardrobe = ['hoodie', 'jeans', 'gloves', 'boots'].filter(name => !snapshot.parts[name]);
  return report;
}
if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  const [directory, output] = process.argv.slice(2); assert(directory && output && !fs.existsSync(output), 'Usage geometry-check.mjs NATIVE_DIRECTORY NEW_REPORT.json');
  const input = JSON.parse(fs.readFileSync(path.join(directory, 'report.json'), 'utf8'));
  const sha = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
  const records = [];
  for (const pin of input.samples) {
    const bytes = fs.readFileSync(path.join(directory, pin.path)); assert.equal(sha(bytes), pin.sha256);
    records.push(inspectSnapshot(JSON.parse(zlib.gunzipSync(bytes)))); process.stdout.write(`CONTACT_SAMPLE ${records.at(-1).index}\n`);
  }
  fs.writeFileSync(output, JSON.stringify({ status: 'UNACCEPTED_FINITE_SURFACE_DIAGNOSTICS', sourcePins: input.sourcePins, nativeReportSHA256: sha(fs.readFileSync(path.join(directory, 'report.json'))), records,
    limits: ['Finite contacts and proper-crossing witnesses at sampled poses, no continuous-time or signed volume-depth certificate.', 'Proper classifier requires strict edge/plane crossing through triangle interior; coincident/edge-only/coplanar contacts remain finite-contact counts.', 'No clothing coverage, support, consumed collision, GPU, art or device acceptance.'] }, null, 2) + '\n');
}
