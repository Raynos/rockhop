import { test } from 'node:test';
import assert from 'node:assert/strict';
import { buildBattery } from './motion-battery.mjs';
await test('all cases replay the exact same command path backwards', () => {
  const b = buildBattery();
  for (const c of b.cases) {
    const f = b.frames.slice(c.start, c.end + 1);
    assert.deepEqual(f.filter(x => x.phase === 'forward').map(x => x.command).reverse(), f.filter(x => x.phase === 'reverse').map(x => x.command));
    assert.equal(f[0].command.rootTranslationNativeM.reduce((a, x) => a + Math.abs(x), 0), 0);
  }
  assert.deepEqual(b.frames[0].command.rotations, []);
  assert.equal(b.cases.length, 14);
});
await test('A/T/neutral directions are anatomical, and bad sample rates rejected', () => {
  const b = buildBattery();
  assert.deepEqual(b.cases.find(x => x.name === 'T').target.armDirections, { L: [0, -1, 0], R: [0, 1, 0] });
  assert.deepEqual(b.cases.find(x => x.name === 'neutral').target.armDirections.L, [0, 0, -1]);
  assert.throws(() => buildBattery({ hz: 0 }));
  assert.throws(() => buildBattery({ transitionS: 0 }));
  assert.throws(() => buildBattery({ transitionS: .001 }), /at least one sample interval/);
});
