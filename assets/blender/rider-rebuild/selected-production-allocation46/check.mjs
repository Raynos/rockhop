import test from 'node:test';
import assert from 'node:assert/strict';
import { targetOutcome } from './construct.mjs';
import { captureFrame } from './census.mjs';
import { summarize } from './budget.mjs';

test('above8000 remains an exact-count unaccepted candidate without scene allocation', () => {
  for (const count of [8000, 8001, 610934]) {
    const row = targetOutcome(count);
    assert.equal(row.targetTriangles, count);
    assert.equal(row.simplificationTargetTriangles, 8000);
    assert.equal(row.simplificationTargetReached, count <= 8000);
    assert.equal(row.status, 'UNACCEPTED_SCENE_BUDGET_PENDING');
    assert.equal(row.sceneBudgetPassed, false);
    assert.equal(row.allocationPassed, false);
  }
});

function fixture() {
  const root = { name: 'selected-rider' }, boot = { name: 'boot', parent: root };
  const terrain = { name: 'terrain' };
  const renderer = { info: { render: { triangles: 0 } }, renderBufferDirect(...args) {
    this.info.render.triangles += args[2].testDrawTriangles;
  } };
  const render = { debug: { renderer, rider: { root } } };
  const draw = (object, triangles) => renderer.renderBufferDirect(null, null,
    { testDrawTriangles: triangles, index: { count: triangles * 3 } }, null, object, null);
  return { render, renderer, boot, terrain, draw };
}

test('complete draw census includes repeat passes and counter resets; restores function', () => {
  const f = fixture(), original = f.renderer.renderBufferDirect;
  const frame = captureFrame(f.render, () => {
    f.draw(f.boot, 9000); f.draw(f.terrain, 480000);
    f.renderer.info.render.triangles = 0;
    f.draw(f.boot, 9000); // Actual second pass, not assumed one-pass geometry.
  }, { caseId: 'test:rookie', tick: 0 });
  assert.equal(f.renderer.renderBufferDirect, original);
  assert.equal(frame.completeSceneDrawTriangles, 498000);
  assert.equal(frame.riderDrawTriangles, 18000);
  const report = summarize({ schemaVersion: 1, completeSceneTriangleBudget: 500000,
    requiredCases: ['test:rookie'], frames: [frame] });
  assert.equal(report.status, 'SAMPLED_SCENES_WITHIN_BUDGET_UNACCEPTED');
  assert.equal(report.perBootTriangleAllocation, null);
  frame.drawRows[1].triangles += 3000; frame.completeSceneDrawTriangles += 3000; frame.nonRiderDrawTriangles += 3000;
  assert.equal(summarize({ schemaVersion: 1, completeSceneTriangleBudget: 500000,
    requiredCases: ['test:rookie'], frames: [frame] }).status, 'REJECTED_SAMPLED_COMPLETE_SCENE_TRIANGLE_BUDGET');
});

test('missing scene samples award no allocation; skipped and failed draws restore wrapper', () => {
  const f = fixture(), original = f.renderer.renderBufferDirect;
  assert.throws(() => captureFrame(f.render, () => {}, {}), /No actual rider draw/);
  assert.equal(f.renderer.renderBufferDirect, original);
  assert.throws(() => captureFrame(f.render, () => { throw Error('draw failure'); }, {}), /draw failure/);
  assert.equal(f.renderer.renderBufferDirect, original);
  const report = summarize({ schemaVersion: 1, completeSceneTriangleBudget: 500000,
    requiredCases: ['garage:rookie'], frames: [] });
  assert.equal(report.status, 'MISSING_COMPLETE_SCENE_MEASUREMENTS_NO_ALLOCATION');
});

test('above-target real topology retains every locked vertex/edge and component', async () => {
  const { topology, compactCandidate } = await import('../selected-production-constructor37/construct.mjs');
  const count = 8001, n = count * 3;
  const positions = new Float32Array(n * 3), triangles = Uint32Array.from({ length: n }, (_, i) => i);
  for (let f = 0; f < count; f++) {
    positions.set([f * 2, 0, 0, f * 2 + 1, 0, 0, f * 2, 1, 0], f * 9);
  }
  const a = { positions, triangles, names: ['DEF-foot.L'], fields: new Float32Array(n).fill(1),
    materials: new Int32Array(count), loopIds: Int32Array.from(triangles),
    cornerNormals: new Float32Array(n * 3), uv: [] };
  const protectedTopology = topology(a);
  assert.equal(Math.ceil(protectedTopology.report.lockedVertices / 3), 8001);
  const candidate = compactCandidate(a, protectedTopology, triangles);
  assert.equal(candidate.triangles.length / 3, 8001);
  assert.equal(targetOutcome(candidate.triangles.length / 3).status, 'UNACCEPTED_SCENE_BUDGET_PENDING');
  assert.throws(() => compactCandidate(a, protectedTopology, triangles.subarray(3)), /Locked source vertex removed/);
});
