/** Silent WebKit phone-layout comparison of original Mustard and sixth selected outfit.
 * node deployed-garage-review.mjs --build=DIR --source=GLB --contract=JSON --out=FRESH_DIR
 * Optional --url-file=FILE verifies the normal deployed HTTPS game.
 * Headless silent harness; this is not physical-device or final art acceptance.
 */
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { preview } from 'vite';
import { webkit, devices } from 'playwright';
import { installGarageCaptureMeter } from './garage-capture-meter.mjs';

const arg = (name, fallback = '') => process.argv.find(v => v.startsWith(`--${name}=`))?.slice(name.length + 3) ?? fallback;
for (const key of ['build', 'source', 'contract', 'out']) assert(arg(key), `Missing --${key}`);
const build = path.resolve(arg('build')), source = path.resolve(arg('source'));
const contractPath = path.resolve(arg('contract')), out = path.resolve(arg('out'));
const bike = arg('bike', 'rookie'), dpr = Number(arg('dpr', '3')), orbitSeconds = Number(arg('orbit-seconds', '18'));
const userAgent = devices['iPhone 14 Pro Max landscape'].userAgent;
assert(['rookie', 'pro'].includes(bike));
assert(Number.isFinite(dpr) && dpr >= 1 && dpr <= 3);
assert(Number.isFinite(orbitSeconds) && orbitSeconds >= 16 && orbitSeconds <= 60);
assert(!fs.existsSync(out), 'Use a fresh comparison output');
const sha = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
const streamSHA = async file => {
  const digest = crypto.createHash('sha256');
  for await (const chunk of fs.createReadStream(file)) digest.update(chunk);
  return digest.digest('hex');
};
const contractBytes = fs.readFileSync(contractPath), contract = JSON.parse(contractBytes);
const catalog = JSON.parse(fs.readFileSync(path.join(build, 'model-catalog.json')));
const selectedManifest = JSON.parse(fs.readFileSync(path.join(build, 'rider-remaster-source.json')));
catalog.models.push(...['models/rider-street-remastered.glb','models/rider-street-remastered-lod.glb'].map(logical => ({logical,...selectedManifest})));
const inputs = { source, metadataSHA256:selectedManifest.contractSHA256, sourceSHA256:selectedManifest.sha256 };
const originalIds = ['street-mustard', 'street-openface', 'race-bluewhite', 'street-charcoal', 'race-charcoalyellow'];
const oldId = 'street-mustard', newId = 'street-remastered';
assert.equal(selectedManifest.optional, true); assert.equal(selectedManifest.lodAliasesFull, true);
assert.equal(path.resolve(inputs.source), source); assert.equal(inputs.metadataSHA256, sha(contractBytes));
const assets = Object.fromEntries(catalog.models.map(row => [row.logical, row]));
const oldAsset = assets[`models/rider-${oldId}.glb`], newAsset = assets[`models/rider-${newId}.glb`];
assert(oldAsset && newAsset); assert.notEqual(oldAsset.sha256, newAsset.sha256);
const selectedLod = assets[`models/rider-${newId}-lod.glb`];
assert.equal(selectedLod?.sha256, newAsset.sha256); assert.equal(selectedLod.url, newAsset.url);
assert.equal(newAsset.sha256, contract.glbSHA256); assert.equal(newAsset.sha256, inputs.sourceSHA256);
assert.equal(newAsset.bytes, fs.statSync(source).size);
assert.equal(await streamSHA(source), newAsset.sha256, 'Actual selected input stream hash');
const originals = [];
for (const id of originalIds) for (const suffix of ['', '-lod']) {
  const logical = `models/rider-${id}${suffix}.glb`, row = assets[logical];
  assert(row, `Original outfit source retained: ${logical}`);
  assert.equal(await streamSHA(path.join('public', logical)), row.sha256, `Original bytes unchanged: ${logical}`);
  originals.push({ logical, sha256: row.sha256, bytes: row.bytes });
}
const garageSource = fs.readFileSync('src/ui/garage.ts');
const yawMatch = garageSource.toString().match(/yawPerPx:\s*\(2 \* Math.PI\) \/ ([\d.]+)/);
assert(yawMatch); const fullTurnPixels = Number(yawMatch[1]);
assert(Number.isFinite(fullTurnPixels) && fullTurnPixels > 0 && fullTurnPixels < 850);
fs.mkdirSync(out, { recursive: true });
const report = { accepted: false, build, source: { path: source, sha256: newAsset.sha256, bytes: newAsset.bytes },
  contract: { path: contractPath, sha256: sha(contractBytes) }, bike,
  device: { engine: 'webkit', viewport: { width: 932, height: 430 }, dpr, userAgent, isMobile: true, hasTouch: true, physicalPhone: false },
  originals, selectedSlot: newAsset, originalMustardSlot: oldAsset, choices: [], requests: [], errors: [],
  recipeSHA256: sha(fs.readFileSync(new URL(import.meta.url))),
  meterRecipeSHA256: sha(fs.readFileSync(new URL('./garage-capture-meter.mjs', import.meta.url))),
  audio: 'silent webdriver; audio=0',
  limits: ['WebKit mobile-layout proxy, not physical iPhone GPU/memory/device acceptance.',
    'Source SHA is streamed locally and tied to build catalog/runtime source identity; browser response bodies are never copied or independently rehashed.',
    'Submitted-frame source/visibility guards detect missing/generic rider submissions; pixel appearance and complete moving art require parent movie judgment.'] };
let phase = 'boot';
const remoteFile = arg('url-file');
const server = remoteFile ? null : await preview({ configFile: false, root: process.cwd(), build: { outDir: build },
  preview: { host: '127.0.0.1', port: 0 }, logLevel: 'warn' });
const entryURL = new URL(remoteFile ? fs.readFileSync(remoteFile, 'utf8').trim() : server.resolvedUrls.local[0]);
if (remoteFile) assert(entryURL.protocol === 'https:' && entryURL.hostname.endsWith('.vercel.app'), 'Normal HTTPS game required');
entryURL.searchParams.set('audio', '0'); entryURL.searchParams.set('sw', '0');
report.deployment = remoteFile ? { origin: entryURL.origin, access: 'Public normal game; no share token' } : null;
const publicBase = entryURL.origin + '/';
const browser = await webkit.launch({ headless: true });
const context = await browser.newContext({ viewport: report.device.viewport, screen: report.device.viewport,
  deviceScaleFactor: dpr, userAgent, isMobile: true, hasTouch: true,
  recordVideo: { dir: out, size: report.device.viewport } });
await context.addInitScript(() => {
  localStorage.setItem('rockhop.onboarded', '1');
  localStorage.setItem('rockhop.riderOutfit', 'street-mustard');
  localStorage.setItem('rockhop.economy.v1', JSON.stringify({ version: 1, wallet: 0, medals: {}, proOwned: true, equipped: 'rookie' }));
});
const page = await context.newPage(), requests = new WeakMap(), pendingHeaders = [];
page.setDefaultTimeout(120000);
page.on('pageerror', error => report.errors.push(error.message));
page.on('request', request => {
  if (new URL(request.url()).pathname.endsWith('.glb')) requests.set(request, { phase, at: performance.now() });
});
page.on('response', response => {
  const request = response.request(), started = requests.get(request);
  if (!started) return;
  pendingHeaders.push((async () => {
    const headers = await response.allHeaders();
    const row = catalog.models.find(asset => new URL(asset.url, publicBase).href === response.url());
    report.requests.push({ phase: started.phase, url: response.url(), status: response.status(),
      logical: row?.logical ?? null, catalogSHA256: row?.sha256 ?? null,
      contentLength: headers['content-length'] === undefined ? null : Number(headers['content-length']), responseHeaderWallMs: performance.now() - started.at });
  })());
});

// Cheap post-render presence witness. It reads scene identities/counts once per
// instance, never skin coordinates, indices, textures or whole geometry buffers.
function installComparisonMonitor({ logicals, aliases }) {
  const owner = window.__render, original = owner.render, cache = new WeakMap();
  const state = { frames: 0, invalidFrames: 0, examples: [], lastLogical: null };
  const details = rider => {
    if (!rider?.source?.scene || !rider.scene) return null;
    if (!cache.has(rider)) {
      const skins = [], bones = new Set();
      rider.scene.traverse(node => {
        if (node.isSkinnedMesh) { skins.push(node); for (const bone of node.skeleton.bones) bones.add(bone.uuid); }
      });
      cache.set(rider, { skins, bones: bones.size });
    }
    return cache.get(rider);
  };
  const inScene = node => { for (let p = node; p; p = p.parent) if (p === owner.scene) return true; return false; };
  const visible = node => { for (let p = node; p; p = p.parent) if (!p.visible) return false; return true; };
  const inspect = () => {
    const rider = owner.debug.rider, part = details(rider);
    const actualLogical = rider?.source ? owner.heroDocUrl.get(rider.source) : null;
    const logical = aliases[actualLogical] ?? actualLogical;
    return { logical, actualLogical, sourceUUID: rider?.source?.scene?.uuid ?? null, instanceUUID: rider?.root?.uuid ?? null,
      selectedMarker: rider?.source?.scene?.userData?.selectedRemaster === true,
      boundNativeJoints: rider?.binding?.byId?.size ?? null, skeletonBones: part?.bones ?? 0,
      visibleSkins: part?.skins.filter(mesh => visible(mesh) && inScene(mesh) && mesh.geometry.attributes.position.count > 0).length ?? 0,
      sourceSHA256: rider?.debug?.candidate?.sourceSHA256 ?? null,
      authorMeshRoles: rider?.debug?.candidate?.authorMeshRoles ?? null,
      jointIds: rider?.binding ? [...rider.binding.byId.keys()].sort() : null,
      stageClip: rider?.debug?.stageClip ?? null, rootName: rider?.root?.name ?? null };
  };
  function wrapped(...args) {
    const before = owner.renderer.info.render.frame;
    const result = original.apply(this, args);
    if (owner.renderer.info.render.frame > before) {
      const row = inspect(); state.frames++; state.lastLogical = row.logical;
      if (!logicals.includes(row.logical) || row.visibleSkins === 0) {
        state.invalidFrames++;
        if (state.examples.length < 12) state.examples.push({ frame: state.frames, ...row });
      }
    }
    return result;
  }
  owner.render = wrapped;
  window.__garageComparison = { inspect, state, stop() { if (owner.render === wrapped) owner.render = original; return state; } };
}

async function orbit() {
  const box = await page.locator('.garage-stage').boundingBox(); assert(box);
  const x = box.x + fullTurnPixels + 40, y = box.y + box.height * .55;
  assert(x < 932 && x - fullTurnPixels >= 0, 'Full pointer turn stays inside phone viewport');
  assert(await page.evaluate(({ x, y }) => !!document.elementFromPoint(x, y)?.closest('.garage-stage'), { x, y }), 'Orbit starts on actual stage');
  await page.mouse.move(x, y); await page.mouse.down();
  const start = performance.now(); let progress = 0, moves = 0, maximumStepPx = 0;
  while (progress < 1) {
    const previous = progress; progress = Math.min(1, (performance.now() - start) / (orbitSeconds * 1000));
    await page.mouse.move(x - fullTurnPixels * progress, y);
    moves++; maximumStepPx = Math.max(maximumStepPx, (progress - previous) * fullTurnPixels);
    if (progress < 1) await page.waitForTimeout(16);
  }
  await page.waitForTimeout(100); await page.mouse.up();
  return { requestedSeconds: orbitSeconds, wallSeconds: (performance.now() - start) / 1000,
    pointerDegrees: 360, fullTurnPixels, moves, maximumStepPx,
    pointer: 'Trusted WebKit mouse drag in mobile layout; actual touch taps select outfits. No pose/camera-clock injection.' };
}
try {
  const bootAt = performance.now();
  await page.goto(entryURL.href);
  await page.locator('.menu-screen.live .menu-item[data-id=garage]').tap();
  await page.waitForSelector('.garage-screen.live');
  await page.locator(`button[data-bike=${bike}]`).tap();
  await page.evaluate(() => window.__render.whenReady());
  report.bootToGarageReadyMs = performance.now() - bootAt;
  report.meter = await page.evaluate(installGarageCaptureMeter);
  // The full/LOD selected slots deliberately share one parsed full document.
  // heroDocUrl can retain either alias after concurrent cache resolution.
  await page.evaluate(installComparisonMonitor, { logicals: [oldAsset.logical, newAsset.logical],
    aliases: { [selectedLod.logical]: newAsset.logical } });
  const controls = await page.locator('button[data-outfit]').evaluateAll(buttons => buttons.map(button => {
    const r = button.getBoundingClientRect(), hit = document.elementFromPoint(r.x + r.width / 2, r.y + r.height / 2);
    return { id: button.dataset.outfit, text: button.textContent.replace(/\s+/g, ' ').trim(),
      width: r.width, height: r.height, x: r.x, y: r.y,
      withinViewport: r.x >= 0 && r.y >= 0 && r.right <= innerWidth && r.bottom <= innerHeight,
      centerReachable: hit === button || button.contains(hit), disabled: button.disabled };
  }));
  report.controls = controls;
  assert.deepEqual(controls.map(row => row.id).sort(), [...originalIds, newId].sort(), 'Five original choices plus sixth selected');
  assert.match(controls.find(row => row.id === newId).text, /Mustard.*Remastered/);
  for (const button of controls) assert(button.withinViewport && button.centerReachable && !button.disabled
    && button.width >= 44 && button.height >= 44, `Reachable phone touch target: ${button.id}`);
  for (const [index, id] of [oldId, newId, oldId, newId].entries()) {
    phase = `choice-${index + 1}-${id}`;
    const expectedAsset = id === newId ? newAsset : oldAsset, at = performance.now();
    await page.locator(`button[data-outfit=${id}]`).tap();
    await page.locator(`button[data-outfit=${id}][aria-pressed=true]`).waitFor({ timeout: 180000 });
    await page.evaluate(() => window.__render.whenReady());
    await page.waitForFunction(logical => window.__garageComparison.state.lastLogical === logical,
      expectedAsset.logical, { polling: 100, timeout: 180000 });
    const readyMs = performance.now() - at;
    const identity = await page.evaluate(() => window.__garageComparison.inspect());
    const surface = await page.evaluate(() => {
      const d = window.__render.debugInfo(), canvas = document.querySelector('canvas').getBoundingClientRect();
      return { deviceClass: d.deviceClass, profile: d.profile, rendererDpr: d.dpr,
        canvasW: d.canvasW, canvasH: d.canvasH, canvasRect: { x: canvas.x, y: canvas.y, width: canvas.width, height: canvas.height },
        viewport: { width: innerWidth, height: innerHeight }, horizontalOverflow: document.documentElement.scrollWidth > innerWidth };
    });
    assert.equal(surface.deviceClass, 'phone', 'Actual game uses phone renderer profile');
    assert.equal(surface.horizontalOverflow, false, 'Phone Garage has no horizontal overflow');
    assert.equal(identity.logical, expectedAsset.logical); assert(identity.visibleSkins > 0 && identity.skeletonBones > 0);
    if (id === newId) {
      assert.equal(identity.selectedMarker, true); assert.equal(identity.boundNativeJoints, 75); assert.equal(identity.skeletonBones, 75);
      assert.equal(identity.sourceSHA256, newAsset.sha256);
      assert.deepEqual(identity.jointIds, Object.keys(contract.specification.jointNames).sort());
      assert.deepEqual(identity.authorMeshRoles, contract.specification.meshNames);
      assert.equal(identity.stageClip, 'Riding IK/breathing', 'Comparison default is on-bike riding solver');
    } else { assert.equal(identity.selectedMarker, false); assert.equal(identity.boundNativeJoints, null); }
    const previous = report.choices.find(row => row.id === id);
    if (previous) {
      assert.equal(identity.sourceUUID, previous.identity.sourceUUID, 'Parsed outfit source stays resident');
      assert.equal(identity.instanceUUID, previous.identity.instanceUUID, 'Pooled outfit instance stays resident');
      assert.equal(identity.skeletonBones, previous.identity.skeletonBones, 'Original actual skeleton count preserved');
    }
    const still = `${phase}-front.png`;
    await page.screenshot({ path: path.join(out, still) });
    await page.evaluate(() => window.__garageCaptureMeter.reset());
    const motion = await orbit();
    const performanceStats = await page.evaluate(() => window.__garageCaptureMeter.read());
    assert(performanceStats.rendered.frames > 0, 'Actual rendered Garage frames required');
    report.choices.push({ id, visit: previous ? 2 : 1, readyMs, identity, surface,
      catalogSHA256: expectedAsset.sha256, frontStill: still, movie: 'deployed-garage-comparison.mp4', motion, performance: performanceStats });
  }
  await Promise.all(pendingHeaders);
  report.presence = await page.evaluate(() => window.__garageComparison.state);
  assert.equal(report.presence.invalidFrames, 0, 'No missing/generic/blank-geometry rider submissions');
  assert.deepEqual(report.errors, []);
  const selectedRequests = report.requests.filter(row => row.catalogSHA256 === newAsset.sha256);
  assert.equal(selectedRequests.length, 1, 'New full/LOD alias fetches actual selected source once');
  assert.equal(selectedRequests[0].phase, `choice-2-${newId}`);
  assert.equal(selectedRequests[0].status, 200);
  if (selectedRequests[0].contentLength !== null) assert.equal(selectedRequests[0].contentLength, newAsset.bytes);
  report.browserByteWitness = selectedRequests[0].contentLength === null
    ? 'Response has no Content-Length; browser byte count unmeasured. Independently verified public source/catalog SHA retained.'
    : 'Response Content-Length matches independently verified source size.';
  for (const choice of report.choices) {
    const rows = report.requests.filter(row => row.phase === `choice-${report.choices.indexOf(choice) + 1}-${choice.id}`);
    choice.network = { modelRequests: rows.length, responsesWithoutSize: rows.filter(row => row.contentLength === null).length, modelResponseBytes: rows.reduce((sum, row) => sum + (row.contentLength ?? 0), 0) };
    if (choice.visit === 2) assert.equal(rows.length, 0, 'Resident comparison repeats request no model files');
  }
  report.resourceTiming = await page.evaluate(() => performance.getEntriesByType('resource')
    .filter(row => row.name.includes('.glb')).map(row => ({ url: row.name, durationMs: row.duration,
      transferSize: row.transferSize, encodedBodySize: row.encodedBodySize, decodedBodySize: row.decodedBodySize })));
} catch (error) { report.failure = String(error.stack).replaceAll(entryURL.href, publicBase); process.exitCode = 1; }
finally {
  try {
    report.presence = await page.evaluate(() => window.__garageComparison?.stop() ?? null);
    report.finalMeter = await page.evaluate(() => window.__garageCaptureMeter?.stop() ?? null);
  } catch (error) { report.finalReadError = error.message; }
  const video = page.video(); await context.close(); await browser.close();
  const raw = await video.path(), movie = path.join(out, 'deployed-garage-comparison.mp4');
  const encoded = spawnSync('ffmpeg', ['-v', 'error', '-y', '-threads', '2', '-i', raw, '-an', '-c:v', 'libx264', '-threads', '2',
    '-crf', '18', '-pix_fmt', 'yuv420p', '-fps_mode', 'passthrough', movie], { encoding: 'utf8' });
  const probe = file => {
    const result = spawnSync('ffprobe', ['-v', 'error', '-select_streams', 'v:0', '-show_entries',
      'stream=codec_name,r_frame_rate,avg_frame_rate,nb_frames,duration:format=duration', '-of', 'json', file], { encoding: 'utf8' });
    return { exitCode: result.status, metadata: result.status === 0 ? JSON.parse(result.stdout) : null, stderr: result.stderr };
  };
  report.video = { movie: 'deployed-garage-comparison.mp4', exitCode: encoded.status, stderr: encoded.stderr,
    raw: probe(raw), encoded: probe(movie), meaning: 'One canonical movie retains all four choices; stream rates are separate from actual render/RAF FPS. No interpolation.' };
  if (encoded.status !== 0 || report.video.encoded.exitCode !== 0) process.exitCode = 1;
  if (server) await new Promise(resolve => server.httpServer.close(resolve));
  fs.writeFileSync(path.join(out, 'report.json'), JSON.stringify(report, null, 2) + '\n');
  console.log(JSON.stringify({ out, choices: report.choices.length, failure: report.failure, errors: report.errors }));
}
