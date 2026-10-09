/** Fresh boot/first-Garage and normal-clock silent phone-viewport candidate diagnosis. */
import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import { preview } from 'vite';
import { webkit } from 'playwright';
import { register } from 'tsx/esm/api';
import { pathToFileURL } from 'node:url';
import { summarizeLoader } from './loader-summary.mjs';
const arg = (key, fallback) => process.argv.find(value => value.startsWith(`--${key}=`))?.slice(key.length + 3) ?? fallback;
const input = path.resolve(arg('build', 'dist')), out = path.resolve(arg('out'));
const expected = JSON.parse(await fs.readFile(path.resolve(arg('expected'))));
for (const key of ['sourceSHA256', 'metadataSHA256', 'gripProfileSHA256']) assert(/^[a-f0-9]{64}$/.test(expected[key]), `Expected ${key} required`);
const backend = arg('backend', 'webkit'), seconds = Number(arg('seconds', '20'));
assert(['webkit', 'metal'].includes(backend)); assert(seconds >= 10 && seconds <= 30);
const sha = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
await fs.mkdir(path.dirname(out), {recursive: true});
await fs.mkdir(out, {recursive: false});
const build = path.join(out, 'frozen-build'); await fs.cp(input, build, {recursive: true});
const manifest = JSON.parse(await fs.readFile(path.join(build, 'rider-remaster-source.json')));
assert.equal(manifest.sha256, expected.sourceSHA256, 'Frozen source manifest identity');
assert.equal(manifest.contractSHA256, expected.metadataSHA256, 'Frozen raw contract identity');
const report = {expected, status: 'UNACCEPTED_RUNTIME_DIAGNOSIS', accepted: false, backend, buildVersion: JSON.parse(await fs.readFile(path.join(build, 'version.json'))), selectedSource: manifest,
 recipeSHA256: sha(await fs.readFile(new URL(import.meta.url))), errors: [], navigations: [], requests: [], requestFailures: [], responses: [], scenarios: [],
 method: 'Normal production App RAF and physics clock. Trusted Garage outfit clicks and held ArrowUp/ArrowLeft keys. App public flow API launches C1 and quits, bypassing the world-map GPU transfer only. No manual ticks, replay, quality/cap/camera/pose overrides.',
 limits: ['Mac hardware with phone viewport/touch/DPR is not physical iPhone hardware.', 'CPU submissions and RAF differ from GPU completion. Timer queries sampled asynchronously only when extension exists.', 'Lifecycle and warm performance measured in one fresh normal page. No physical-phone crash claim from absence on Mac.']};
function lifecycle() {
 const events = [], started = performance.timeOrigin;
 sessionStorage.setItem('rockhop.performance02.documentCount', String(Number(sessionStorage.getItem('rockhop.performance02.documentCount') ?? 0) + 1));
 const log = (kind, detail) => events.push({atMs: performance.now(), kind, detail});
 globalThis.window.__phoneLifecycle = {events, timeOrigin: started, documentCount: Number(sessionStorage.getItem('rockhop.performance02.documentCount'))};
 globalThis.window.addEventListener('webglcontextlost', event => log('context-lost', event.statusMessage), true);
 globalThis.window.addEventListener('webglcontextrestored', () => log('context-restored'), true);
 globalThis.window.addEventListener('pageshow', event => log('pageshow', {persisted: event.persisted}));
 globalThis.navigator.serviceWorker?.addEventListener('controllerchange', () => log('sw-controllerchange', globalThis.navigator.serviceWorker.controller?.scriptURL));
 let last = '';
 const observer = new globalThis.MutationObserver(() => {
  const loader = globalThis.document.querySelector('#loader'), text = loader?.textContent?.trim().replace(/\s+/g, ' ').slice(0, 1000) ?? 'REMOVED';
  const detail = {present: !!loader, text, download: loader?.dataset.download ?? null, setup: loader?.dataset.setup ?? null, done: loader?.dataset.done ?? null, step: loader?.querySelector('li.on')?.dataset.key ?? null, setupLine: loader?.querySelector('.gauge.su .line')?.textContent ?? null, downloadLine: loader?.querySelector('.gauge.dl .line')?.textContent ?? null};
  const signature = JSON.stringify(detail);
  if (signature !== last) {last = signature; log('loader', detail);}
 });
 observer.observe(globalThis.document, {childList: true, subtree: true, characterData: true, attributes: true, attributeFilter: ['hidden', 'style', 'class', 'data-download', 'data-setup', 'data-done']});
}
function installMeter() {
 const owner = globalThis.window.__render, renderer = owner.renderer, gl = renderer.getContext();
 const ext = gl.getExtension('EXT_disjoint_timer_query_webgl2');
 const data = {rows: [], raf: [], gpu: [], disjoint: 0}; let active = true, rafId, frame = 0;
 const pending = [], wrappedRiders = new Map();
 const renderOriginal = owner.render, postOriginal = owner.debug.post.render;
 let riderMs = 0, postMs = 0, resetCount = 0;
 owner.debug.post.render = function(...args) { const start = performance.now(); try {return postOriginal.apply(this, args);} finally {postMs += performance.now() - start;} };
 owner.render = function(...args) {
  const rider = owner.debug.rider;
  if (!wrappedRiders.has(rider)) {
   const original = rider.update;
   const wrapped = function(...args) {const start = performance.now(), before = this.debug?.fullResetCount ?? 0; try {return original.apply(this, args);} finally {riderMs += performance.now() - start; resetCount += (this.debug?.fullResetCount ?? before) - before;}};
   rider.update = wrapped; wrappedRiders.set(rider, {original, wrapped});
  }
  const before = renderer.info.render.frame, start = performance.now(); riderMs = postMs = resetCount = 0;
  let query;
  if (ext && frame++ % 30 === 0 && !gl.getQuery(ext.TIME_ELAPSED_EXT, gl.CURRENT_QUERY)) {query = gl.createQuery(); gl.beginQuery(ext.TIME_ELAPSED_EXT, query);}
  let result; try {result = renderOriginal.apply(this, args);} finally {
   if (query) {gl.endQuery(ext.TIME_ELAPSED_EXT); pending.push(query);}
   for (let i = pending.length - 1; i >= 0; i--) if (gl.getQueryParameter(pending[i], gl.QUERY_RESULT_AVAILABLE)) {
    if (!gl.getParameter(ext.GPU_DISJOINT_EXT)) data.gpu.push(gl.getQueryParameter(pending[i], gl.QUERY_RESULT) / 1e6); else data.disjoint++;
    gl.deleteQuery(pending.splice(i, 1)[0]);
   }
   const end = performance.now(), submitted = renderer.info.render.frame > before;
   data.rows.push({atMs: end, cpuMs: end - start, riderMs, postMs, resetCount, submitted,
    calls: renderer.info.render.calls, triangles: renderer.info.render.triangles, phase: globalThis.window.__rockhop.phase(), tick: globalThis.window.__rockhop.frame(), meter: globalThis.document.querySelector('.fpsmeter')?.textContent});
  }
  return result;
 };
 function raf(now) {if (!active) return; data.raf.push(now); rafId = globalThis.requestAnimationFrame(raf);} rafId = globalThis.requestAnimationFrame(raf);
 globalThis.window.__phoneMeter = {startMs: performance.now(), extension: !!ext, reset() {data.rows.length = data.raf.length = data.gpu.length = 0; data.disjoint = 0; this.startMs = performance.now();}, result() {return {...data, startMs: this.startMs, endMs: performance.now(), extension: !!ext};}, stop() {active = false; globalThis.cancelAnimationFrame(rafId); owner.render = renderOriginal; owner.debug.post.render = postOriginal; for (const [rider, record] of wrappedRiders) if (rider.update === record.wrapped) rider.update = record.original; for (const query of pending) gl.deleteQuery(query);}};
}
const pct = values => {const sorted = [...values].sort((a,b) => a-b); return {p50: sorted[Math.floor(sorted.length*.5)] ?? null, p95: sorted[Math.floor(sorted.length*.95)] ?? null, max: sorted.at(-1) ?? null};};
let server, browser, context, page;
try {
 server = await preview({configFile: false, root: process.cwd(), build: {outDir: build}, preview: {host: '127.0.0.1', port: 0}, logLevel: 'warn'});
 if (backend === 'webkit') browser = await webkit.launch({headless: true});
 else {register(); const {launchBrowser} = await import(pathToFileURL(path.resolve('harness/lib/browser.ts')).href); process.env.TRIALS_BROWSER_BACKEND = 'metal'; const launched = await launchBrowser({width: 844, height: 390}); browser = launched.browser; report.browserProbe = launched.probe; await launched.context.close();}
 context = await browser.newContext({viewport: {width: 844, height: 390}, deviceScaleFactor: 3, isMobile: true, hasTouch: true});
 await context.addInitScript(() => {localStorage.setItem('rockhop.onboarded', '1'); localStorage.setItem('rockhop.riderOutfit', 'street-remastered'); localStorage.setItem('rockhop.economy.v1', JSON.stringify({version: 1, wallet: 0, medals: {}, proOwned: true, equipped: 'rookie'}));});
 await context.addInitScript(lifecycle);
 page = await context.newPage(); page.setDefaultTimeout(120000);
 page.on('pageerror', error => report.errors.push(error.message));
 page.on('framenavigated', frame => {if (frame === page.mainFrame()) report.navigations.push({atMs: performance.now(), url: frame.url()});});
 page.on('requestfailed', request => report.requestFailures.push({url: request.url(), error: request.failure()?.errorText}));
 page.on('response', response => report.responses.push({url: response.url(), status: response.status(), fromServiceWorker: response.fromServiceWorker()}));
 page.on('request', request => report.requests.push({atMs: performance.now(), url: request.url(), type: request.resourceType()}));
 await page.goto(server.resolvedUrls.local[0] + '?audio=0&perf=1');
 await page.waitForSelector('.menu-screen.live .menu-item[data-id=garage]');
 report.firstGarageBefore = await page.evaluate(() => ({lifecycle: globalThis.window.__phoneLifecycle, info: globalThis.window.__rockhop.info(), stats: globalThis.window.__rockhop.stats(), webdriver: globalThis.navigator.webdriver}));
 assert(report.firstGarageBefore.webdriver, 'Silent automation requires navigator.webdriver');
 const firstGarageStart = performance.now();
 await page.locator('.menu-screen.live .menu-item[data-id=garage]').click(); await page.waitForSelector('.garage-screen.live');
 await page.evaluate(() => globalThis.window.__render.whenReady());
 report.boot = await page.evaluate(() => ({lifecycle: globalThis.window.__phoneLifecycle, info: globalThis.window.__rockhop.info(), renderDetails: globalThis.window.__render.debugInfo({selectedTextures: true}), userAgent: globalThis.navigator.userAgent, viewport: [globalThis.innerWidth, globalThis.innerHeight], DPR: globalThis.devicePixelRatio, coarse: globalThis.matchMedia('(pointer: coarse)').matches, renderer: globalThis.window.__rockhop.stats(), phase: globalThis.window.__rockhop.phase()}));
 report.firstGarage = {readyMs: performance.now() - firstGarageStart, timeOriginUnchanged: report.firstGarageBefore.lifecycle.timeOrigin === report.boot.lifecycle.timeOrigin, documentCount: report.boot.lifecycle.documentCount, phase: report.boot.phase, navigations: report.navigations.length};
 await page.evaluate(installMeter);
 for (const outfit of ['street-mustard', 'street-remastered']) {
  if (!(await page.locator('.garage-screen.live').count())) {await page.evaluate(() => globalThis.window.__rockhop.app.quit()); await page.locator('.menu-screen.live .menu-item[data-id=garage]').click();}
  const requests0 = report.requests.length, timeOrigin = await page.evaluate(() => performance.timeOrigin), choiceStart = performance.now();
  await page.locator(`button[data-outfit=${outfit}]`).click(); await page.locator(`button[data-outfit=${outfit}][aria-pressed=true]`).waitFor(); await page.evaluate(() => globalThis.window.__render.whenReady());
  const choiceMs = performance.now() - choiceStart;
  for (const mode of ['garage', 'c1-ride']) {
   if (mode === 'c1-ride') {await page.evaluate(() => globalThis.window.__rockhop.app.play('c1-low-tide')); await page.waitForFunction(() => globalThis.window.__rockhop.phase() === 'riding'); await page.keyboard.down('ArrowUp');}
   await page.waitForTimeout(1500); await page.evaluate(() => globalThis.window.__phoneMeter.reset());
   const before = await page.evaluate(() => ({info: globalThis.window.__rockhop.info(), renderDetails: globalThis.window.__render.debugInfo({selectedTextures: true}), state: globalThis.window.__rockhop.getState(), source: globalThis.window.__render.debug.rider.debug.candidate ?? null, lifecycle: globalThis.window.__phoneLifecycle.events.length}));
   await page.waitForTimeout(seconds * 1000);
   const measured = await page.evaluate(() => ({meter: globalThis.window.__phoneMeter.result(), info: globalThis.window.__rockhop.info(), renderDetails: globalThis.window.__render.debugInfo({selectedTextures: true}), state: globalThis.window.__rockhop.getState(), lifecycle: globalThis.window.__phoneLifecycle, timeOrigin: performance.timeOrigin, stats: globalThis.window.__rockhop.stats()}));
   if (outfit === 'street-remastered') {
    measured.nativeSkeleton = await page.evaluate(() => {
     const bones = new Set(), roots = new Set();
     globalThis.window.__render.debug.rider.root.traverse(object => {
      if (!object.isSkinnedMesh) return; roots.add(object.skeleton);
      for (const bone of object.skeleton.bones) bones.add(bone.name);
     });
     return {jointCount: bones.size, skeletonCount: roots.size, jointNames: [...bones].sort()};
    });
    assert.equal(measured.nativeSkeleton.jointCount, expected.nativeJointCount ?? 75, 'Actual native skeleton count');
    assert.equal(measured.renderDetails.riderSourceSHA256, expected.sourceSHA256, 'Actual drawn selected source');
    assert.equal(measured.renderDetails.riderNativeMetadataSHA256, expected.metadataSHA256, 'Actual drawn metadata');
    assert.equal(measured.renderDetails.riderGripProfileSHA256, expected.gripProfileSHA256, 'Actual drawn fitted grip');
    assert(measured.renderDetails.selectedTextures?.textureCount > 0, 'Actual material texture receipt missing');
    assert.equal(measured.renderDetails.selectedTextures.unavailableTextures, 0, 'Selected material payload unavailable');
    assert.equal(measured.renderDetails.selectedTextures.incompleteTextures, 0, 'Selected mip payload incomplete');
   }
   const rows = measured.meter.rows, submitted = rows.filter(row => row.submitted), duration = (measured.meter.endMs-measured.meter.startMs)/1000;
   const summary = {outfit, mode, choiceMs, timeOriginUnchanged: measured.timeOrigin === timeOrigin, duration, appRenderCalls: rows.length, submittedFrames: submitted.length, submittedFPS: submitted.length/duration, appRenderFPS: rows.length/duration, observedRAFFPS: measured.meter.raf.length/duration,
    cpuMs: pct(rows.map(row => row.cpuMs)), riderMs: pct(submitted.map(row => row.riderMs)), postMs: pct(submitted.map(row => row.postMs)), resetsPerSubmittedFrame: pct(submitted.map(row => row.resetCount)), calls: pct(submitted.map(row => row.calls)), triangles: pct(submitted.map(row => row.triangles)), gpuMs: pct(measured.meter.gpu), gpuTimerSupported: measured.meter.extension, gpuDisjointQueries: measured.meter.disjoint, before, after: measured.info, renderDetailsBefore: before.renderDetails, renderDetailsAfter: measured.renderDetails, statsAfter: measured.stats, nativeSkeleton: measured.nativeSkeleton ?? null, startState: before.state, endState: measured.state, lifecycle: measured.lifecycle.events.slice(before.lifecycle), requestsSinceChoice: report.requests.slice(requests0)};
   report.scenarios.push(summary); await fs.writeFile(path.join(out, `${outfit}-${mode}.json`), JSON.stringify(measured, null, 2)); await page.screenshot({path: path.join(out, `${outfit}-${mode}.png`)});
   await fs.writeFile(path.join(out, 'report.partial.json'), JSON.stringify(report, null, 2)); console.log(JSON.stringify({outfit, mode, submittedFPS: summary.submittedFPS, riderMs: summary.riderMs, resets: summary.resetsPerSubmittedFrame, gpuMs: summary.gpuMs, triangles: summary.triangles}));
   if (mode === 'c1-ride') await page.keyboard.up('ArrowUp');
  }
 }
 await page.evaluate(() => globalThis.window.__phoneMeter.stop());
 report.finalLifecycle = await page.evaluate(() => globalThis.window.__phoneLifecycle);
 report.loader = summarizeLoader(report.finalLifecycle.events);
 assert(report.loader.finished && report.loader.removed && !report.loader.reinserted, 'Loader did not finish once');
 assert.equal(report.loader.regressions.length, 0, 'Loader percentage regressed');
 report.lifecycleChecks = {singleDocument: report.navigations.length === 1 && report.finalLifecycle.documentCount === 1, timeOriginUnchanged: report.firstGarageBefore.lifecycle.timeOrigin === report.finalLifecycle.timeOrigin, contextLost: report.finalLifecycle.events.filter(row => row.kind === 'context-lost').length, contextRestored: report.finalLifecycle.events.filter(row => row.kind === 'context-restored').length, selectedSourceFetches: report.requests.filter(row => row.url === manifest.url).length, errors: report.errors.length, requestFailures: report.requestFailures.length, audioNull: report.boot.info.modules.audio === 'null' && report.scenarios.every(row => row.after.modules.audio === 'null')};
 assert(report.lifecycleChecks.singleDocument && report.lifecycleChecks.timeOriginUnchanged, 'Unexpected reload/timeOrigin change');
 assert(report.lifecycleChecks.contextLost === 0 && report.lifecycleChecks.contextRestored === 0, 'Unexpected rendering context loss');
 assert(report.lifecycleChecks.selectedSourceFetches === 1, 'Candidate should fetch once through boot/Garage/outfit/C1');
 assert(report.lifecycleChecks.errors === 0 && report.lifecycleChecks.requestFailures === 0 && report.lifecycleChecks.audioNull, 'Page or silent-automation regression');
 report.status = 'COMPLETE_RUNTIME_DIAGNOSIS_NOT_PHONE_ACCEPTANCE';
 report.textureLimit = 'Literal Three texture format/type and retained typed-array mip payloads; not measured GPU allocation. Mac results never qualify physical iPhone FPS.';
} catch (error) {report.failure = error.stack; try {report.failurePage = await page?.evaluate(() => ({lifecycle: globalThis.window.__phoneLifecycle, loader: globalThis.document.querySelector('#loader')?.textContent, info: globalThis.window.__rockhop?.info()}));} catch { /* A terminated page cannot provide a failure snapshot. */ } throw error;}
finally {await fs.writeFile(path.join(out, 'report.json'), JSON.stringify(report, null, 2)); await context?.close(); await browser?.close(); server?.httpServer.close();}
