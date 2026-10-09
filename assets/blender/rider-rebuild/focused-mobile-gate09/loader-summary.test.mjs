import assert from 'node:assert/strict';
import test from 'node:test';
import { summarizeLoader } from './loader-summary.mjs';
const sample = (atMs, download, setup, rest = {}) => ({ atMs, kind: 'loader', detail: {
  present: true, download: String(download), setup: String(setup), done: '0', step: 'heroModels',
  setupLine: 'hero', downloadLine: 'bytes', ...rest,
} });
test('measures continuous30% dwell across real byte/detail updates', () => {
  const r = summarizeLoader([sample(0, 0, 0), sample(20, 30, 30),
    sample(120, 30, 30, { downloadLine: 'more bytes' }), sample(320, 60, 50),
    sample(420, 100, 100, { done: '1' }), sample(720, 100, 100, { present: false })]);
  assert.equal(r.setup.longest30Ms, 300);
  assert.equal(r.download.longest30Ms, 300);
  assert.equal(r.removedAtMs, 720);
  assert(r.finished && r.removed && !r.reinserted);
  assert.deepEqual(r.regressions, []);
});
test('exposes counter regression and reload-like loader reinsertion', () => {
  const r = summarizeLoader([sample(0, 30, 30), sample(100, 20, 40),
    sample(200, 100, 100, { done: '1' }), sample(300, 100, 100, { present: false }), sample(400, 0, 0)]);
  assert(r.reinserted);
  assert.deepEqual(r.regressions, [{ atMs: 100, field: 'download', before: 30, after: 20 }]);
});
