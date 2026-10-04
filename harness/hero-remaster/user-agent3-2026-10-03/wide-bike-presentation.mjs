/** One camera-only replacement of the frozen OFF/ON actual-engine control. */
/* oxlint-disable eslint/no-undef, typescript/no-extraneous-class -- headless page globals and silent audio trap. */
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { preview } from 'vite';
import { webkit } from 'playwright';
import { decodeJSON, expandFrames } from '../../../src/core/replay.ts';

const root = process.cwd(), base = path.join(root, 'harness/out/user-agent3-2026-10-03');
const build = path.join(base, 'constructed38-build'), out = path.join(base, 'presentation50');
assert(!fs.existsSync(out)); fs.mkdirSync(out);
const sha = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
const old = JSON.parse(fs.readFileSync(path.join(base, 'constructed38/report.json')));
const manifestBytes = fs.readFileSync(path.join(build, 'hero-review.json'));
const manifest = JSON.parse(manifestBytes);
const candidate = manifest.models.find(m => m.logical === 'models/rider-street-mustard.glb');
assert.equal(candidate.sha256, '3ffd591d6872513646cab2384f8fe6b21f828ab57bdb5842cc1659fcd32face2');
assert.equal(sha(fs.readFileSync(path.join(build, candidate.url))), candidate.sha256);
const fixturesFile = 'docs/evidence/hero-remaster/user-agent3-qa-2026-10-03/split-fixtures01-inputs/manifest.json';
const fixture = JSON.parse(fs.readFileSync(fixturesFile)).cases.find(c => c.id === 'rookie-maximum-backward-lean');
const recordingBytes = fs.readFileSync(path.join(path.dirname(fixturesFile), fixture.recording));
assert.equal(sha(recordingBytes), fixture.sourceSHA256);
const recording = decodeJSON(recordingBytes.toString()), inputs = expandFrames(recording).slice(0, 703);
assert.equal(inputs.length, 703);
const fps = 30, report = {
  status: 'UNACCEPTED_FROZEN_CAMERA_PRESENTATION_PENDING', sourceSHA256: candidate.sha256,
  buildManifestSHA256: sha(manifestBytes), recordingSHA256: sha(recordingBytes),
  captureSHA256: sha(fs.readFileSync(new URL(import.meta.url))),
  frozenRuntimeSHA256: sha(fs.readFileSync(path.join(build, 'agent3-constructed/solver.js'))),
  priorControlReportSHA256: sha(fs.readFileSync(path.join(base, 'constructed38/report.json'))),
  fps, viewport: [960, 720], cases: [], errors: [], loaded: [],
  limits: ['Existing rejected wedge boots and failed closed-solid seating are unchanged and unaccepted.',
    'First 703 input ticks play at original 120Hz physics speed, sampled every four ticks at30fps; final partial sample pads8.333333ms.',
    'Camera travel and front/side/rear holds explicitly pause at actual input703; no pose injection or geometry/material/rig/physics rewrite.',
    'Separate foot crops magnify the same paused pixels, not newly simulated contacts. No art, contact, phone or publication acceptance.']
};
const server = await preview({ configFile: false, root, build: { outDir: build }, preview: { host: '127.0.0.1', port: 0 }, logLevel: 'warn' });
const browser = await webkit.launch({ headless: true });
const context = await browser.newContext({ viewport: { width: 960, height: 720 } });
await context.addInitScript(() => {
  localStorage.setItem('rockhop.onboarded', '1'); window.__agent3AudioCount = 0;
  for (const name of ['AudioContext', 'webkitAudioContext']) window[name] = class { constructor() { window.__agent3AudioCount++; throw new Error('Silent presentation'); } };
});
const page = await context.newPage(), responses = [];
page.on('pageerror', e => report.errors.push(e.message));
page.on('response', r => { if (r.url().endsWith('.glb')) responses.push(r.body().then(b => report.loaded.push({ sha256: sha(b), status: r.status() }))); });
try {
  await page.goto(server.resolvedUrls.local[0] + '?harness=1&audio=0&sw=0&outfit=street-mustard&physics=v2&hz=120');
  await page.waitForFunction(() => window.__rockhop?.ready, null, { timeout: 120000 });
  await page.addStyleTag({ content: '#ui,#ui *,.hud,.touch-controls{visibility:hidden!important} #agent3-label{position:fixed;z-index:99999;color:white;background:#101820ed;padding:8px;font:14px monospace;white-space:pre;visibility:visible!important}' });
  for (const mode of ['off', 'on']) {
    await page.evaluate(() => { window.__agent3SoleControl?.restore(); window.__agent3SoleControl = null; });
    await page.evaluate(async header => {
      const t = window.__rockhop, r = window.__render;
      t.setBike(header.bike ?? 'rookie'); await r.whenReady(); await t.loadTrack(header.trackId, header.seed);
      t.setQuality('high'); await r.whenReady(); t.skipCountdown(); t.render(true);
    }, recording.header);
    await page.evaluate(async enabled => {
      const r = window.__render, d = r.debug, module = await import('/agent3-constructed/solver.js');
      window.__agent3SoleControl = module.installConstructedSoleTarget(d, enabled);
      window.__agent3Camera = settings => {
        const t = window.__rockhop, T = d.THREE;
        d.scene.updateMatrixWorld(true);
        d.rider.scene.traverse(o => { if (o.isSkinnedMesh) o.skeleton.update(); });
        let box = new T.Box3().setFromObject(d.bike.root, true);
        const center = box.getCenter(new T.Vector3());
        const foot = settings.foot ? d.rider.scene.getObjectByName('soleSocket' + settings.foot).getWorldPosition(new T.Vector3()) : null;
        r.setCameraOverride({ mode: 'orbit', yaw: settings.yaw, pitch: .12, dist: foot ? 3 : 8,
          x: (foot ?? center).x, y: (foot ?? center).y, screenX: .5, screenY: .54 });
        r.invalidate(); t.render(true);
        d.scene.updateMatrixWorld(true);
        box = new T.Box3().setFromObject(d.bike.root, true);
        const corners = [];
        for (const x of [box.min.x, box.max.x]) for (const y of [box.min.y, box.max.y]) for (const z of [box.min.z, box.max.z]) corners.push(new T.Vector3(x, y, z).project(d.rig.camera).toArray());
        const bounds = { minX: Math.min(...corners.map(p => p[0])), maxX: Math.max(...corners.map(p => p[0])), minY: Math.min(...corners.map(p => p[1])), maxY: Math.max(...corners.map(p => p[1])) };
        let clip = null;
        if (foot) {
          const p = foot.clone().project(d.rig.camera);
          clip = { x: Math.max(0, Math.min(576, Math.round((p.x + 1) * 480 - 192))), y: Math.max(0, Math.min(432, Math.round((1 - p.y) * 360 - 144))), width: 384, height: 288 };
        }
        let label = document.getElementById('agent3-label');
        if (!label) { label = document.createElement('div'); label.id = 'agent3-label'; document.body.append(label); }
        label.style.left = (clip ? clip.x + 4 : 10) + 'px'; label.style.top = (clip ? clip.y + 4 : 10) + 'px';
        label.style.fontSize = clip ? '8px' : '14px'; label.style.padding = clip ? '3px' : '8px';
        label.textContent = settings.label;
        const bones = d.rider.scene.getObjectByName('pelvis').parent;
        const matrices = []; bones.traverse(o => { if (o.isBone) matrices.push([o.name, ...o.matrixWorld.elements]); });
        return { bounds, clip, matrices, hash: t.hashState(), tick: t.getState().tick, runTime: t.runTime(), phase: t.phase(), audioContexts: window.__agent3AudioCount, webdriver: navigator.webdriver };
      };
    }, mode === 'on');
    const folder = path.join(out, mode); fs.mkdirSync(folder);
    const frames = [], samples = [], trace = []; let previous = 0;
    const capture = async (settings, copies = 1) => {
      const result = await page.evaluate(s => window.__agent3Camera(s), settings);
      assert(result.webdriver && result.audioContexts === 0 && result.phase === 'riding');
      if (!settings.foot) assert(result.bounds.minX > -.94 && result.bounds.maxX < .94 && result.bounds.minY > -.9 && result.bounds.maxY < .82, JSON.stringify(result.bounds));
      const file = path.join(folder, String(samples.length).padStart(4, '0') + '.png');
      await page.screenshot({ path: file, ...(result.clip ? { clip: result.clip } : {}) });
      frames.push(...Array(copies).fill(file)); samples.push({ ...settings, copies, ...result });
      return result;
    };
    for (let tick = 4; previous < 703; tick += 4) {
      const end = Math.min(tick, 703);
      const rows = await page.evaluate(chunk => {
        const t = window.__rockhop, r = window.__render;
        return chunk.map(input => { t.setInput(input); t.step(1); t.render(true); return { stateHash: t.hashState(), tick: t.getState().tick, phase: t.phase(), runTime: t.runTime(), finishTime: t.getState().finishTime, physicalPose: r.debug.rider.debug.physicalPose }; });
      }, inputs.slice(previous, end));
      rows.forEach((row, i) => { const oldRow = old.cases.find(c => c.id === mode).id; assert.equal(oldRow, mode); trace.push({ inputTick: previous + i + 1, ...row }); });
      previous = end;
      await capture({ yaw: 0, label: `UNACCEPTED CONTROL | ${mode.toUpperCase()}\nActual riding at 1x | input ${end}/703\nFull rider + bike | original recorded physics` });
      if (end % 120 === 0) console.log(JSON.stringify({ mode, ridingTick: end }));
    }
    const held = samples.at(-1), freeze = result => {
      assert.equal(result.hash, held.hash); assert.equal(result.tick, held.tick); assert.equal(result.runTime, held.runTime);
      assert.deepEqual(result.matrices, held.matrices);
    };
    const paused = (view, yaw) => ({ yaw, label: `UNACCEPTED CONTROL | ${mode.toUpperCase()}\nPAUSED actual input 703 | ${view}\nCamera inspection only | no contact acceptance` });
    freeze(await capture(paused('FRONT hold', Math.PI / 2), 90));
    for (const [start, end, title] of [[Math.PI / 2, 0, 'FRONT to SIDE'], [0, -Math.PI / 2, 'SIDE to REAR']]) {
      for (let i = 1; i <= 150; i++) {
        const u = i / 150, eased = u * u * (3 - 2 * u);
        freeze(await capture(paused(title + ' | slow 5s travel', start + (end - start) * eased)));
      }
      freeze(await capture(paused(end === 0 ? 'SIDE hold' : 'REAR hold', end), 90));
      console.log(JSON.stringify({ mode, cameraSection: title }));
    }
    for (const foot of ['L', 'R']) freeze(await capture({ ...paused(`${foot === 'L' ? 'LEFT' : 'RIGHT'} foot crop`, foot === 'L' ? 0 : Math.PI), foot,
      label: `UNACCEPTED ${mode.toUpperCase()} | PAUSED input703\n${foot === 'L' ? 'LEFT' : 'RIGHT'} foot crop | same rendered pose\nClosed-solid seating previously FAILED` }, 90));
    const prior = fs.readFileSync(path.join(base, 'constructed38', mode, 'tick-trace.ndjson')).toString().trim().split('\n').map(line => JSON.parse(line));
    for (let i = 0; i < 703; i++) for (const key of Object.keys(trace[i])) assert.deepEqual(trace[i][key], prior[i][key], `${mode} ${i} ${key}`);
    const lines = frames.map(file => `file '${file}'\nduration ${1 / fps}`).join('\n') + `\nfile '${frames.at(-1)}'\n`;
    const list = path.join(folder, 'frames.txt'); fs.writeFileSync(list, lines);
    const film = path.join(folder, 'played.mp4');
    const encoded = spawnSync('ffmpeg', ['-v', 'error', '-n', '-f', 'concat', '-safe', '0', '-i', list, '-vf', 'scale=960:720:flags=lanczos', '-r', String(fps), '-frames:v', String(frames.length), '-c:v', 'libx264', '-threads', '2', '-crf', '18', '-pix_fmt', 'yuv420p', '-an', '-movflags', '+faststart', film], { encoding: 'utf8' });
    assert.equal(encoded.status, 0, encoded.stderr);
    fs.writeFileSync(path.join(folder, 'tick-trace.ndjson'), trace.map(row => JSON.stringify(row)).join('\n') + '\n');
    report.cases.push({ mode, everyPhysicsTickMatchesPrior: true, inputTicks: trace.length, frames: frames.length, capturedImages: samples.length,
      traceSHA256: sha(fs.readFileSync(path.join(folder, 'tick-trace.ndjson'))), filmSHA256: sha(fs.readFileSync(film)), samples });
  }
  await Promise.all(responses); assert.deepEqual(report.errors, []);
  assert(report.loaded.some(r => r.status === 200 && r.sha256 === candidate.sha256));
  assert.equal(report.cases[0].frames, report.cases[1].frames);
  const film = path.join(out, 'wide-slow.mp4');
  const encoded = spawnSync('ffmpeg', ['-v', 'error', '-n', '-i', path.join(out, 'off/played.mp4'), '-i', path.join(out, 'on/played.mp4'), '-filter_complex', '[0:v][1:v]hstack=inputs=2[v]', '-map', '[v]', '-c:v', 'libx264', '-threads', '2', '-crf', '18', '-pix_fmt', 'yuv420p', '-an', '-movflags', '+faststart', film], { encoding: 'utf8' });
  assert.equal(encoded.status, 0, encoded.stderr);
  report.delivery = { path: film, sha256: sha(fs.readFileSync(film)), frames: report.cases[0].frames, fps, dimensions: [1920, 720] };
  report.status = 'UNACCEPTED_CAMERA_ONLY_REPLACEMENT_CAPTURED';
} catch (e) { report.failure = String(e); process.exitCode = 1; }
finally {
  fs.writeFileSync(path.join(out, 'report.json'), JSON.stringify(report, null, 2) + '\n');
  await context.close(); await browser.close(); await new Promise(resolve => server.httpServer.close(resolve));
  console.log(JSON.stringify({ status: report.status, cases: report.cases.length, failure: report.failure, delivery: report.delivery }));
}
