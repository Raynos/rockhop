import fs from 'node:fs';
import { execFileSync } from 'node:child_process';
import { decodeAny, expandFrames } from '../../../../../src/core/replay';
import { createSimFor } from '../../../../../harness/lib/sim';

const dir = 'docs/evidence/store-release/native/20260930-200644';
const native = JSON.parse(fs.readFileSync(`${dir}/gate.json`, 'utf8'));
const head = execFileSync('git', ['rev-parse', 'HEAD'], { encoding: 'utf8' }).trim();
const paths = ['src/core', 'src/physics', 'src/tracks', 'harness/lib/rules.ts', 'harness/lib/sim.ts', 'harness/inputs'];
if (fs.readFileSync('store/build/SOURCE', 'utf8').trim() !== native.source) throw new Error('Native bundle source no longer matches the retained run');
const changed = execFileSync('git', ['diff', '--name-only', native.source, '--', ...paths], { encoding: 'utf8' }).trim();
if (changed) throw new Error(`Node simulation changed since native export: ${changed}`);
const rows = [];
for (const reference of native.runs[0].result.clear) {
  const file = `store/build/web/${reference.file}`;
  const recording = decodeAny(fs.readFileSync(file, 'utf8'));
  const sim = await createSimFor(recording);
  sim.run(expandFrames(recording));
  const state = sim.state();
  const ft = state.finishTime;
  const hex = ft === null ? null : Buffer.from(new Float64Array([ft]).buffer).toString('hex');
  const node = { ticks: state.tick, finishTime: ft, finishTimeHex: hex, hash: sim.hash(), cleared: sim.phase() === 'finished', faults: sim.faults() };
  const compared = native.runs.map((run: any) => ({ platform: run.platform, actual: run.result.clear.find((r: any) => r.file === reference.file) }));
  const pass = node.cleared && node.faults === 0 && compared.every(({ actual }: any) => actual?.cleared && actual.ticks === node.ticks && actual.finishTimeHex === hex && actual.hash === node.hash);
  rows.push({ file: reference.file, trackId: recording.header.trackId, bike: recording.header.bike, node, compared, pass });
}
const report = { source: native.source, nodeInvocationHead: head, simulationDiff: changed, rows, pass: rows.length === 12 && rows.every((r) => r.pass) };
fs.writeFileSync(`${dir}/node-compare.json`, `${JSON.stringify(report, null, 2)}\n`);
console.log(`${rows.filter((r) => r.pass).length}/${rows.length} exact Node/web/iOS endpoints; source ${native.source}`);
if (!report.pass) process.exitCode = 1;
