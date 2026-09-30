/** Bounded R3 Rookie timing probe. No renderer, fixtures or physics mutation. */
import os from 'node:os';
import { performance } from 'node:perf_hooks';
import { quantizeInput } from '../../src/core/replay';
import type { InputFrame } from '../../src/core/types';
import { createBikePhysicsV2 } from '../../src/physics/v2/bike';
import { makeTrack } from '../../src/physics/testTracks';

const blocks = Math.min(1200, Math.max(1, Number(process.env.ROCKHOP_CPU_BLOCKS ?? 200)));
const w = createBikePhysicsV2(120);
w.loadTrack(makeTrack({ finishX: 1e9 }), 1, { bike: 'rookie' });
for (let i = 0; i < 60; i++) w.step(quantizeInput({}));
const script = (i: number): InputFrame => quantizeInput({
  throttle: 0.6 + 0.3 * Math.sin(i / 90),
  lean: 0.4 * Math.sin(i / 200),
  brake: i % 500 < 30 ? 0.5 : 0,
});
for (let i = 0; i < 2000; i++) w.step(script(i));

const wall: number[] = [];
const cpu: number[] = [];
const loadBefore = os.loadavg();
const usageBefore = process.resourceUsage();
const start = performance.now();
let restarts = 0;
for (let k = 0; k < blocks; k++) {
  const t0 = performance.now();
  const c0 = process.threadCpuUsage();
  for (let i = 0; i < 100; i++) w.step(script(k * 100 + i));
  const c = process.threadCpuUsage(c0);
  wall.push(((performance.now() - t0) * 1000) / 100);
  cpu.push((c.user + c.system) / 100);
  if (w.getState().faulted) { w.step(quantizeInput({ restart: true })); restarts++; }
}
const usageAfter = process.resourceUsage();
const p = (values: number[], percentile: number): number => [...values].sort((a, b) => a - b)[Math.floor(values.length * percentile)]!;
console.log(JSON.stringify({
  kind: 'r3-rookie-warmed-cpu', blocks, ticks: blocks * 100, restarts,
  wallUsPerTick: { p10: p(wall, 0.1), p50: p(wall, 0.5), p95: p(wall, 0.95), max: Math.max(...wall) },
  mainThreadCpuUsPerTick: { p10: p(cpu, 0.1), p50: p(cpu, 0.5), p95: p(cpu, 0.95), max: Math.max(...cpu) },
  totalWallMs: performance.now() - start,
  loadBefore, loadAfter: os.loadavg(),
  resourceDelta: {
    voluntaryContextSwitches: usageAfter.voluntaryContextSwitches - usageBefore.voluntaryContextSwitches,
    involuntaryContextSwitches: usageAfter.involuntaryContextSwitches - usageBefore.involuntaryContextSwitches,
  },
}));
