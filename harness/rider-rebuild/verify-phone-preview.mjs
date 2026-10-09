/** Remote source/transition gate only; no video, screenshots, art or FPS judgment.
 * node harness/rider-rebuild/verify-phone-preview.mjs --build=DIR --url-file=PRIVATE --out=FRESH
 * Run only under the parent's serialized browser/memory guard.
 */
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import { webkit, devices } from 'playwright';

const sha = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
const originals = ['street-mustard', 'street-openface', 'race-bluewhite', 'street-charcoal', 'race-charcoalyellow'];
const oldId = 'street-mustard', selectedId = 'street-remastered';

// Count actual renderer submissions, caching only mesh references/bone counts.
// Native joint lists and author metadata are read once after each choice is ready.
function installWitness({ aliases }) {
  const owner = globalThis.window.__render, original = owner.render, cache = new WeakMap();
  const state = { expected: null, frames: 0, invalidFrames: 0, lastLogical: null, examples: [] };
  const inspect = (full = true) => {
    const rider = owner.debug.rider;
    if (!rider?.source?.scene || !rider.scene) {
      const empty = { logical: null, actualLogical: null, sourceUUID: null, instanceUUID: null,
        selectedMarker: false, visibleSkins: 0 };
      return full ? { ...empty, skeletonBones: 0, boundNativeJoints: null, jointIds: null,
        sourceSHA256: null, authorMeshRoles: null, stageClip: null } : empty;
    }
    if (!cache.has(rider)) {
      const skins = [], bones = new Set();
      rider.scene.traverse(node => {
        if (node.isSkinnedMesh) { skins.push(node); node.skeleton.bones.forEach(bone => bones.add(bone.uuid)); }
      });
      cache.set(rider, { skins, bones: bones.size });
    }
    const parts = cache.get(rider), actual = rider?.source ? owner.heroDocUrl.get(rider.source) : null;
    const visible = mesh => {
      for (let node = mesh; node; node = node.parent) {
        if (!node.visible) return false;
        if (node === owner.scene) return mesh.geometry.attributes.position.count > 0;
      }
      return false;
    };
    const row = { logical: aliases[actual] ?? actual, actualLogical: actual,
      sourceUUID: rider?.source?.scene?.uuid ?? null, instanceUUID: rider?.root?.uuid ?? null,
      selectedMarker: rider?.source?.scene?.userData?.privateSelectedRider === true,
      visibleSkins: parts?.skins.filter(visible).length ?? 0 };
    return full ? { ...row, skeletonBones: parts?.bones ?? 0, boundNativeJoints: rider?.binding?.byId?.size ?? null,
      jointIds: rider?.binding ? [...rider.binding.byId.keys()].sort((a, b) => a < b ? -1 : a > b ? 1 : 0) : null,
      sourceSHA256: rider?.debug?.candidate?.sourceSHA256 ?? null,
      authorMeshRoles: rider?.debug?.candidate?.authorMeshRoles ?? null, stageClip: rider?.debug?.stageClip ?? null } : row;
  };
  function wrapped(...args) {
    const before = owner.renderer.info.render.frame, result = original.apply(this, args);
    if (owner.renderer.info.render.frame > before) {
      const row = inspect(false); state.lastLogical = row.logical;
      if (state.expected) {
        state.frames++;
        if (row.logical !== state.expected || row.sourceUUID !== state.sourceUUID
          || row.instanceUUID !== state.instanceUUID || !row.sourceUUID || !row.instanceUUID || !row.visibleSkins) {
          state.invalidFrames++;
          if (state.examples.length < 3) state.examples.push(row);
        }
      }
    }
    return result;
  }
  owner.render = wrapped;
  globalThis.window.__phonePreviewWitness = { inspect, state,
    begin(expected) { const row = inspect(false); Object.assign(state, { expected, sourceUUID: row.sourceUUID,
      instanceUUID: row.instanceUUID, frames: 0, invalidFrames: 0, examples: [] }); },
    stop() { if (owner.render === wrapped) owner.render = original; return state; } };
}

async function main() {
  const arg = name => process.argv.find(value => value.startsWith(`--${name}=`))?.slice(name.length + 3);
  for (const key of ['build', 'url-file', 'out']) assert(arg(key), `Missing --${key}`);
  const build = path.resolve(arg('build')), out = path.resolve(arg('out'));
  assert(!fs.existsSync(out), 'Use a fresh verification output');
  const entry = new URL(fs.readFileSync(arg('url-file'), 'utf8').trim());
  assert(entry.protocol === 'https:' && entry.hostname.endsWith('.vercel.app') && !entry.username && !entry.password,
    'An isolated HTTPS Vercel preview is required');
  const safeKeys = new Set(['x-vercel-set-bypass-cookie', 'audio', 'sw', 'audible']);
  const secrets = [...entry.searchParams].filter(([key, value]) => value && !safeKeys.has(key)).map(([, value]) => value)
    .flatMap(value => [value, encodeURIComponent(value)]);
  const sanitize = value => {
    let safe = String(value);
    for (const secret of secrets) safe = safe.replaceAll(secret, '[redacted]');
    return safe.replace(/https?:\/\/[^\s"'<>]+/g, url => {
      try { const parsed = new URL(url); return parsed.origin + parsed.pathname; } catch { return '[redacted URL]'; }
    });
  };
  entry.searchParams.delete('audible'); entry.searchParams.set('audio', '0'); entry.searchParams.set('sw', '0');
  const inputs = JSON.parse(fs.readFileSync(path.join(build, 'rider-rebuild-inputs.json')));
  const catalog = JSON.parse(fs.readFileSync(path.join(build, 'model-catalog.json')));
  const measurements = JSON.parse(fs.readFileSync(path.join(build, 'rider-comparison-js.json')));
  const contractBytes = fs.readFileSync(inputs.contract), contract = JSON.parse(contractBytes);
  const assets = new Map(catalog.models.map(row => [row.logical, row]));
  const oldAsset = assets.get(`models/rider-${oldId}.glb`), selected = assets.get(`models/rider-${selectedId}.glb`);
  const lod = assets.get(`models/rider-${selectedId}-lod.glb`);
  assert.equal(inputs.releaseBuild, false); assert.equal(inputs.comparison?.id, selectedId);
  assert.equal(inputs.metadataSHA256, sha(contractBytes));
  assert(oldAsset && selected && lod); assert.notEqual(oldAsset.sha256, selected.sha256);
  assert.equal(selected.sha256, inputs.sourceSHA256); assert.equal(selected.sha256, contract.glbSHA256);
  assert.equal(selected.sha256, lod.sha256); assert.equal(selected.url, lod.url); assert.equal(selected.bytes, lod.bytes);
  assert.equal(Object.keys(contract.specification.jointNames).length, 75);
  const report = { accepted: false, sourceTransitionGatePassed: false, phase: 'initialized',
    deployment: { origin: entry.origin, access: 'Scoped share access; private URL and cookies omitted' },
    device: { engine: 'webkit', viewport: { width: 932, height: 430 }, dpr: 2, isMobile: true, hasTouch: true, physicalPhone: false },
    recorder: false, screenshots: false, audio: 'audio=0; silent webdriver', selected, originalMustard: oldAsset,
    contractSHA256: sha(contractBytes), recipeSHA256: sha(fs.readFileSync(new URL(import.meta.url))),
    toolbar: { requestHeader: 'x-vercel-skip-toolbar: 1',
      source: 'https://vercel.com/docs/vercel-toolbar/managing-toolbar',
      limit: 'Skips injected toolbar for automation; other CORS/loading failures remain diagnostic targets.' },
    controls: [], choices: [], errors: [], errorCount: 0, omittedErrorCount: 0,
    network: [], omittedNetworkEvents: 0,
    limits: ['Source identity and actual submitted-frame transition gate only.',
      'No movie, moving-art, performance, physical-phone, or device-memory acceptance.',
      'Remote model response bodies are not copied or independently hashed; runtime source identity is checked against the local emitted catalog.'] };
  fs.mkdirSync(out, { recursive: true });
  const save = phase => {
    report.phase = phase;
    const text = JSON.stringify(report, (_key, value) => typeof value === 'string' ? sanitize(value) : value, 2) + '\n';
    fs.writeFileSync(path.join(out, 'report.next.json'), text);
    fs.renameSync(path.join(out, 'report.next.json'), path.join(out, 'report.json'));
  };
  const recordError = message => {
    const safe = sanitize(message).slice(0, 2000), prior = report.errors.find(row => row.message === safe);
    report.errorCount++;
    if (prior) { prior.count++; prior.lastPhase = report.phase; }
    else if (report.errors.length < 12) report.errors.push({ message: safe, count: 1, firstPhase: report.phase, lastPhase: report.phase });
    else report.omittedErrorCount++;
    if (!prior || (prior.count & (prior.count - 1)) === 0) save(report.phase);
  };
  const targets = new Map([['/' + selected.url, 'selected-glb'],
    ['/' + measurements.reviewChunk, 'selected-review-js'], ['/model-catalog.json', 'model-catalog']]);
  const tracked = new WeakMap();
  const identify = request => {
    if (tracked.has(request)) return tracked.get(request);
    const url = new URL(request.url()), from = request.redirectedFrom();
    const asset = targets.get(url.pathname) ?? (from ? identify(from)?.asset : null)
      ?? (request.resourceType() === 'script' ? 'other-script' : null);
    const row = asset ? { asset } : null; tracked.set(request, row); return row;
  };
  const location = (value, base = entry.origin) => {
    try { const url = new URL(value, base); return { origin: url.origin, path: sanitize(url.pathname).slice(0, 600) }; }
    catch { return { origin: null, path: '[invalid URL]' }; }
  };
  const networkKeys = new Map();
  const recordNetwork = (kind, request, details = {}) => {
    const meta = identify(request);
    if (!meta && kind !== 'requestfailed') return;
    const row = { kind, asset: meta?.asset ?? 'other-failure', phase: report.phase,
      ...location(request.url()), resourceType: request.resourceType(), ...details };
    const key = JSON.stringify(row), prior = networkKeys.get(key);
    if (prior) prior.count++;
    else if (report.network.length < 64) { const item = { ...row, count: 1 }; report.network.push(item); networkKeys.set(key, item); }
    else report.omittedNetworkEvents++;
    save(report.phase);
  };
  let browser, context, page;
  save('before-browser-launch');
  try {
    browser = await webkit.launch({ headless: true });
    context = await browser.newContext({ viewport: report.device.viewport, screen: report.device.viewport,
      deviceScaleFactor: 2, userAgent: devices['iPhone 14 Pro Max landscape'].userAgent, isMobile: true, hasTouch: true,
      extraHTTPHeaders: { 'x-vercel-skip-toolbar': '1' } });
    await context.addInitScript(() => {
      localStorage.setItem('rockhop.onboarded', '1'); localStorage.setItem('rockhop.riderOutfit', 'street-mustard');
      localStorage.setItem('rockhop.economy.v1', JSON.stringify({ version: 1, wallet: 0, medals: {}, proOwned: true, equipped: 'rookie' }));
    });
    page = await context.newPage(); page.setDefaultTimeout(180000);
    page.on('pageerror', error => recordError(error.message));
    page.on('request', request => recordNetwork('request', request));
    page.on('requestfinished', request => recordNetwork('requestfinished', request));
    page.on('requestfailed', request => recordNetwork('requestfailed', request,
      { failure: sanitize(request.failure()?.errorText ?? 'unknown failure').slice(0, 600) }));
    page.on('response', response => {
      if (!identify(response.request())) return;
      const headers = response.headers();
      recordNetwork('response', response.request(), { status: response.status(),
        contentType: headers['content-type'] ?? null, contentLength: headers['content-length'] ?? null,
        allowOrigin: sanitize(headers['access-control-allow-origin'] ?? '').slice(0, 600),
        resourcePolicy: headers['cross-origin-resource-policy'] ?? null,
        redirectTarget: headers.location ? location(headers.location, response.url()) : null });
    });
    save('before-boot-load'); await page.goto(entry.href, { timeout: 180000 });
    assert.equal(await page.evaluate(() => navigator.webdriver), true, 'Silent automation mode required');
    save('before-garage-load'); await page.locator('.menu-screen.live .menu-item[data-id=garage]').tap();
    await page.waitForSelector('.garage-screen.live'); await page.locator('button[data-bike=rookie]').tap();
    await page.evaluate(() => globalThis.window.__render.whenReady());
    await page.evaluate(installWitness, { aliases: { [lod.logical]: selected.logical } });
    report.surface = await page.evaluate(() => ({ deviceClass: globalThis.window.__render.debugInfo().deviceClass,
      width: globalThis.innerWidth, height: globalThis.innerHeight, horizontalOverflow: globalThis.document.documentElement.scrollWidth > globalThis.innerWidth }));
    assert.equal(report.surface.deviceClass, 'phone'); assert.equal(report.surface.horizontalOverflow, false);
    report.controls = await page.locator('button[data-outfit]').evaluateAll(buttons => buttons.map(button => {
      const r = button.getBoundingClientRect(), hit = globalThis.document.elementFromPoint(r.x + r.width / 2, r.y + r.height / 2);
      return { id: button.dataset.outfit, text: button.textContent.replace(/\s+/g, ' ').trim(), width: r.width, height: r.height,
        withinViewport: r.x >= 0 && r.y >= 0 && r.right <= globalThis.innerWidth && r.bottom <= globalThis.innerHeight,
        reachable: hit === button || button.contains(hit), disabled: button.disabled };
    }));
    assert.deepEqual(report.controls.map(row => row.id).sort((a, b) => a < b ? -1 : a > b ? 1 : 0), [...originals, selectedId].sort((a, b) => a < b ? -1 : a > b ? 1 : 0));
    assert.match(report.controls.find(row => row.id === selectedId).text, /Mustard.*Remastered/);
    for (const button of report.controls) assert(button.withinViewport && button.reachable && !button.disabled
      && button.width >= 44 && button.height >= 44, `Reachable 44px phone target: ${button.id}`);
    for (const [index, id] of [oldId, selectedId, oldId, selectedId].entries()) {
      const expected = id === selectedId ? selected : oldAsset, phase = `choice-${index + 1}-${id}`;
      await page.evaluate(() => globalThis.window.__phonePreviewWitness.begin(null));
      save(phase + '-before-load');
      await page.locator(`button[data-outfit=${id}]`).tap();
      await page.locator(`button[data-outfit=${id}][aria-pressed=true]`).waitFor();
      await page.evaluate(() => globalThis.window.__render.whenReady());
      await page.waitForFunction(logical => globalThis.window.__phonePreviewWitness.state.lastLogical === logical,
        expected.logical, { polling: 100, timeout: 180000 });
      const identity = await page.evaluate(() => globalThis.window.__phonePreviewWitness.inspect());
      assert.equal(identity.logical, expected.logical); assert(identity.sourceUUID && identity.instanceUUID && identity.visibleSkins > 0);
      if (id === selectedId) {
        assert.equal(identity.selectedMarker, true); assert.equal(identity.boundNativeJoints, 75); assert.equal(identity.skeletonBones, 75);
        assert.equal(identity.sourceSHA256, selected.sha256); assert.equal(identity.stageClip, 'Riding IK/breathing');
        assert.deepEqual(identity.jointIds, Object.keys(contract.specification.jointNames).sort((a, b) => a < b ? -1 : a > b ? 1 : 0));
        assert.deepEqual(identity.authorMeshRoles, contract.specification.meshNames);
      } else {
        assert.equal(identity.selectedMarker, false); assert.equal(identity.boundNativeJoints, null); assert(identity.skeletonBones > 0);
      }
      const prior = report.choices.find(row => row.id === id);
      if (prior) {
        assert.equal(identity.sourceUUID, prior.identity.sourceUUID, 'Parsed source stays resident');
        assert.equal(identity.instanceUUID, prior.identity.instanceUUID, 'Pooled instance stays resident');
      } else if (report.choices.length) {
        assert.notEqual(identity.sourceUUID, report.choices[0].identity.sourceUUID, 'Sixth rider uses its separate source');
      }
      const choice = { id, visit: prior ? 2 : 1, identity, submitted: null }; report.choices.push(choice);
      save(phase + '-ready');
      await page.evaluate(logical => globalThis.window.__phonePreviewWitness.begin(logical), expected.logical);
      await page.waitForTimeout(2000);
      choice.submitted = await page.evaluate(() => ({ ...globalThis.window.__phonePreviewWitness.state }));
      assert(choice.submitted.frames > 0, 'Actual render submissions required'); assert.equal(choice.submitted.invalidFrames, 0);
      save(phase + '-submitted');
    }
    assert.equal(report.errorCount, 0); report.sourceTransitionGatePassed = true; save('source-transition-gate-passed');
  } catch (error) {
    report.failure = sanitize(error.stack ?? error.message).slice(0, 4000); process.exitCode = 1; save(report.phase + '-failed');
  } finally {
    try { if (page) await page.evaluate(() => globalThis.window.__phonePreviewWitness?.stop()); } catch { /* Page termination can make the final read-only witness unavailable. */ }
    try { await context?.close(); await browser?.close(); } catch (error) { report.cleanupError = sanitize(error.message).slice(0, 2000); process.exitCode = 1; }
    save(report.phase);
    console.log(JSON.stringify({ out, phase: report.phase, choices: report.choices.length,
      sourceTransitionGatePassed: report.sourceTransitionGatePassed, errors: report.errorCount }));
  }
}

// Setup failures must not let an invalid private URL escape through Node's stack.
main().catch(() => { console.error('Preview verifier setup failed before the gate; private URL omitted.'); process.exitCode = 1; });
