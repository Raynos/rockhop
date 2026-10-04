/** Bounded silent actual-Game weight observation; no new cosmetic capture. */
/* oxlint-disable eslint/no-undef, typescript/no-extraneous-class -- headless globals and AudioContext trap. */
import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import { preview } from 'vite';
import { webkit } from 'playwright';
import { decodeJSON, expandFrames } from '../../../src/core/replay.ts';
import { readGlbChunks } from './metadata.mjs';
import { acc } from './fidelity-utils.mjs';

const [buildArg, candidateFile, contractFile, fixtureFile, outArg] = process.argv.slice(2);
assert(outArg && !fs.existsSync(outArg)); const build = path.resolve(buildArg), out = path.resolve(outArg);
const sha = b => crypto.createHash('sha256').update(b).digest('hex');
const sourceBytes = fs.readFileSync(candidateFile), contractBytes = fs.readFileSync(contractFile), contract = JSON.parse(contractBytes);
assert.equal(sha(sourceBytes), '6042207a828883322df0ff5305eefb33fd3ecb26b0ed8fa5a13642e84b3317ad');
assert.equal(contract.status, 'UNACCEPTED_FAITHFUL_SOURCE14_EXPORT_INSTALLED_ENGINE_ONLY_CONSUMES_PRIMARY_FOUR_WEIGHTS');
const glb = readGlbChunks(sourceBytes), attrs = glb.json.meshes[0].primitives[0].attributes;
const primary = acc(glb, attrs.WEIGHTS_0), secondary = acc(glb, attrs.WEIGHTS_1);
contract.sourceWeights = primary.map((row, i) => [...row, ...secondary[i]]);
fs.mkdirSync(out, { recursive: true }); fs.mkdirSync(path.join(build, 'agent3-garment'), { recursive: true });
fs.writeFileSync(path.join(build, 'agent3-garment/source14.glb'), sourceBytes);
const fixtures = JSON.parse(fs.readFileSync(fixtureFile)), fixture = fixtures.cases.find(c => c.id === 'rookie-maximum-backward-lean');
const recordingBytes = fs.readFileSync(path.join(path.dirname(fixtureFile), fixture.recording));
assert.equal(sha(recordingBytes), fixture.sourceSHA256); const recording = decodeJSON(recordingBytes.toString()), inputs = expandFrames(recording).slice(0, 703);
assert.equal(inputs.length, 703);
const manifest = JSON.parse(fs.readFileSync(path.join(build, 'hero-review.json')));
assert.equal(manifest.models.find(m => m.logical === 'models/rider-street-mustard.glb').sha256, '3ffd591d6872513646cab2384f8fe6b21f828ab57bdb5842cc1659fcd32face2');
const report = { status: 'UNACCEPTED_SOURCE14_ACTUAL_GAME_NUMERICAL_WEIGHT_DIAGNOSIS', candidateSHA256: sha(sourceBytes),
  exportAuditSHA256: sha(contractBytes), buildManifestSHA256: sha(fs.readFileSync(path.join(build, 'hero-review.json'))),
  fixtureId: fixture.id, recordingSHA256: sha(recordingBytes), inputTicks: inputs.length,
  codeSHA256: sha(fs.readFileSync(new URL(import.meta.url))), runtimeSHA256: sha(fs.readFileSync(new URL('garment-engine-runtime.mjs', import.meta.url))),
  bundledRuntimeSHA256: sha(fs.readFileSync(path.join(build, 'agent3-garment/observer.js'))), errors: [], runs: [],
  limits: ['No new movie or cosmetic capture: root rejected source14/native59 appearance and deformation.',
    'Reuses qualified source37 JSON-only hand/foot marker derivative of source09 to admit actual body posing; no source38 leg-offset wrapper or new contact/geometry construction.',
    'Actual original Game and51body skeleton drive unchanged source14; eight-slot calculation is numerical reference only, never rendered or installed.',
    'This diagnoses existing influence consumption, not a weight/geometry/shader rewrite or collision response.',
    'No contact-count equivalence to a visible tear; known native garment and separate jeans failures remain independent.',
    'Single recorded riding window, not arbitrary pose safety, candidate/mobile acceptance or publication.'] };
const server = await preview({ configFile: false, root: process.cwd(), build: { outDir: build }, preview: { host: '127.0.0.1', port: 0 }, logLevel: 'warn' });
const browser = await webkit.launch({ headless: true });
try {
  for (const runName of ['first', 'repeat']) {
    const context = await browser.newContext({ viewport: { width: 960, height: 640 } });
    await context.addInitScript(() => { localStorage.setItem('rockhop.onboarded', '1'); window.__agent3AudioCount = 0;
      for (const name of ['AudioContext', 'webkitAudioContext']) window[name] = class { constructor() { window.__agent3AudioCount++; throw new Error('Silent numeric skin QA'); } }; });
    const page = await context.newPage(); page.on('pageerror', e => report.errors.push(e.message));
    await page.goto(server.resolvedUrls.local[0] + '?harness=1&audio=0&sw=0&outfit=street-mustard&physics=v2&hz=120');
    await page.waitForFunction(() => window.__rockhop?.ready, null, { timeout: 120000 });
    const init = await page.evaluate(async ({ header, contract }) => {
      const t = window.__rockhop, r = window.__render; t.setBike(header.bike); await r.whenReady();
      await t.loadTrack(header.trackId, header.seed); t.setQuality('high'); await r.whenReady(); t.skipCountdown(); t.render(true);
      const module = await import('/agent3-garment/observer.js');
      const observer = await module.installGarmentObserver(r.debug, '/agent3-garment/source14.glb', contract);
      window.__agent3GarmentObserver = observer;
      return { contract: observer.contract, initial: observer.sample(), webdriver: navigator.webdriver, audioContexts: window.__agent3AudioCount };
    }, { header: recording.header, contract });
    assert(init.webdriver && init.audioContexts === 0); const rows = [], traces = [];
    for (let start = 0; start < inputs.length; start += 20) {
      const result = await page.evaluate(({ input, start }) => {
        const t = window.__rockhop, r = window.__render, rows = [], traces = [];
        for (let i = 0; i < input.length; i++) {
          t.setInput(input[i]); t.step(1); t.render(true); if (!r.debug.rider.debug.physicalPose) throw new Error('Real rider body pose missing');
          rows.push({ inputTick: start + i + 1, ...window.__agent3GarmentObserver.sample() });
          traces.push({ inputTick: start + i + 1, stateHash: t.hashState(), tick: t.getState().tick, phase: t.phase(), runTime: t.runTime(), finishTime: t.getState().finishTime, physicalPose: r.debug.rider.debug.physicalPose });
        }
        return { rows, traces, audioContexts: window.__agent3AudioCount };
      }, { input: inputs.slice(start, start + 20), start });
      assert.equal(result.audioContexts, 0); rows.push(...result.rows); traces.push(...result.traces);
    }
    const raw = Buffer.from(rows.map(x => JSON.stringify(x)).join('\n') + '\n'), trace = Buffer.from(traces.map(x => JSON.stringify(x)).join('\n') + '\n');
    fs.writeFileSync(path.join(out, runName + '.weights.ndjson'), raw); fs.writeFileSync(path.join(out, runName + '.physics.ndjson'), trace);
    const worst = rows.reduce((a, b) => b.maximumOmittedWeightDisplacementM > a.maximumOmittedWeightDisplacementM ? b : a);
    report.runs.push({ name: runName, init, rows: rows.length, all703RowsSHA256: sha(raw), physicsSHA256: sha(trace),
      maximumManual4ResidualM: Math.max(...rows.map(r => r.manual4ResidualM)),
      maximumOmittedWeightDisplacementM: worst.maximumOmittedWeightDisplacementM, worstTick: worst.inputTick, witness: worst.witness,
      rowsAbove1mm: rows.filter(r => r.maximumOmittedWeightDisplacementM > .001).length });
    console.log(JSON.stringify({ runName, maximumOmittedWeightDisplacementM: worst.maximumOmittedWeightDisplacementM, worstTick: worst.inputTick }));
    await context.close();
  }
  assert.equal(report.runs[0].all703RowsSHA256, report.runs[1].all703RowsSHA256);
  assert.equal(report.runs[0].physicsSHA256, report.runs[1].physicsSHA256); assert.deepEqual(report.errors, []);
  report.all703NumericalRowsRepeatExact = true;
} catch (e) { report.failure = String(e); process.exitCode = 1; }
finally { fs.writeFileSync(path.join(out, 'report.json'), JSON.stringify(report, null, 2) + '\n');
  await browser.close(); await new Promise(resolve => server.httpServer.close(resolve)); }
