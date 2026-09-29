/** Clean-source store shell check: real C-island tower -> Ride -> map -> Menu, on web Metal and iOS WKWebView. */
import fs from 'node:fs';
import path from 'node:path';
import { REPO_ROOT } from '../lib/paths';
import { runIos } from './ios';
import { buildMode, buildSource, EVIDENCE_DIR, stamp, type PlatformRun } from './lib';
import { runWeb } from './web';

if (buildMode() !== 'debug') throw new Error('build a clean debug store shell first: node scripts/store-build.mjs debug --ios');
const arm = { front: { map: true, mapRide: true } };
const runs: PlatformRun[] = [];
for (const platform of ['web', 'ios'] as const) {
  console.info(`native map flow: ${platform} …`);
  const run = platform === 'web' ? await runWeb({ arm, width: 852, height: 393 }) : await runIos({ arm, record: true, tag: 'map-flow' });
  runs.push(run);
  console.info(`native map flow: ${platform} ${run.ok ? 'completed' : 'FAILED'} in ${run.wallS} s`);
}

const report = {
  source: buildSource(),
  at: new Date().toISOString(),
  runs: runs.map((run) => {
    const open = run.messages['map-open'];
    const ride = run.messages['map-ride'];
    const returned = run.messages['map-return'];
    const exit = run.messages['map-exit'];
    const pass = run.ok && !!open && !!ride && !!returned && !!exit &&
      open['mapCanvases'] === 1 && open['gameContextLost'] === true && open['audioContexts'] === 0 &&
      ride['trackId'] === 'c1-low-tide' && ride['mapCanvases'] === 0 && ride['gameContextLost'] === false && ride['audioContexts'] === 0 &&
      returned['mapCanvases'] === 1 && returned['gameContextLost'] === true &&
      exit['mapCanvases'] === 0 && exit['gameContextLost'] === false && exit['audioContexts'] === 0;
    return { platform: run.platform, device: run.device, wallS: run.wallS, pass, open, ride, returned, exit,
      error: run.messages['error'] ?? null, notes: run.notes, clip: run.clip ? path.relative(REPO_ROOT, run.clip) : null };
  }),
};
const out = path.join(EVIDENCE_DIR, `map-flow-${stamp()}`);
fs.mkdirSync(out, { recursive: true });
for (const run of runs) {
  if (!run.clip) continue;
  fs.copyFileSync(run.clip, path.join(out, `${run.platform}-clip.mp4`));
  const sheet = path.join(path.dirname(run.clip), 'sheet.jpg');
  if (fs.existsSync(sheet)) fs.copyFileSync(sheet, path.join(out, `${run.platform}-sheet.jpg`));
}
fs.writeFileSync(path.join(out, 'report.json'), `${JSON.stringify(report, null, 2)}\n`);
console.info(`evidence: ${path.relative(REPO_ROOT, out)}`);
for (const run of report.runs) console.info(`${run.pass ? 'PASS' : 'FAIL'} ${run.platform} map -> C1 -> map -> Menu${run.error ? `: ${JSON.stringify(run.error)}` : ''}`);
if (report.runs.some((run) => !run.pass)) process.exitCode = 1;
