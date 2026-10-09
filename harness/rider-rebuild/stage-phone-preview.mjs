/** Stage an existing private Garage comparison as static Vercel Build Output v3.
 * node harness/rider-rebuild/stage-phone-preview.mjs --build=DIR --out=FRESH_IGNORED_DIR
 * Then, from OUT: vercel deploy --prebuilt --yes (preview target; never --prod).
 * No build, browser, auth access, network request, or deployment happens here.
 */
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';
import { Transform } from 'node:stream';
import { pipeline } from 'node:stream/promises';

const repo = path.resolve(fileURLToPath(new URL('../..', import.meta.url)));
const originalIds = ['street-mustard', 'street-openface', 'race-bluewhite', 'street-charcoal', 'race-charcoalyellow'];
const selectedSlots = ['models/rider-street-remastered.glb', 'models/rider-street-remastered-lod.glb'];
const roots = ['index.html', 'load-manifest.json', 'model-catalog.json', 'version.json', 'sw.js', 'offline.html', 'manifest.webmanifest'];
const privateNames = /^(?:hero-review\.json|rider-rebuild-inputs\.json|auth\.json|credentials(?:\..*)?|session(?:s|data)?(?:\..*)?)$/i;
const json = file => JSON.parse(fs.readFileSync(file, 'utf8'));
const sha = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
const within = (parent, child) => child === parent || child.startsWith(parent + path.sep);

function publicPath(value) {
  assert.equal(typeof value, 'string', 'Asset URL must be a string');
  const relative = value.replace(/^\.\//, '');
  // URL controls are intentionally rejected before constructing public file paths.
  // oxlint-disable-next-line eslint/no-control-regex
  assert(relative && !relative.includes('\\') && !/[?#%\x00-\x1f]/.test(relative), `Unsafe asset URL: ${value}`);
  assert(!path.posix.isAbsolute(relative) && relative.split('/').every(part => part && part !== '..'
    && !part.startsWith('.') && !privateNames.test(part)), `Private or unsafe asset URL: ${value}`);
  assert(!/\.(?:map|source\.json|mts|ts|tsx)$/.test(relative), `Source file is not a public output: ${value}`);
  assert(roots.includes(relative) || /^(?:assets|models|fonts|art|audio|bench)\//.test(relative)
    || relative === 'rider-comparison-js.json', `Unexpected public output: ${value}`);
  return relative;
}

function regularFile(root, relative) {
  let file = root;
  const parts = relative.split('/');
  for (let i = 0; i < parts.length; i++) {
    file = path.join(file, parts[i]);
    const stat = fs.lstatSync(file);
    assert(!stat.isSymbolicLink(), `Symlink is not a build output: ${relative}`);
    assert(i === parts.length - 1 ? stat.isFile() : stat.isDirectory(), `Not a regular build file: ${relative}`);
  }
  return file;
}

async function hashFile(file) {
  const digest = crypto.createHash('sha256');
  for await (const chunk of fs.createReadStream(file)) digest.update(chunk);
  return digest.digest('hex');
}

// The current repository uses only literal paths and terminal /(.*) sources.
// Fail if that recipe changes rather than silently weakening a header rule.
function headerRoutes(config) {
  return (config.headers ?? []).map(rule => {
    assert(!rule.has && !rule.missing, 'Conditional Vercel headers need an explicit adapter');
    const wildcard = rule.source.endsWith('/(.*)');
    const literal = wildcard ? rule.source.slice(0, -5) : rule.source;
    assert(/^\/[a-zA-Z0-9/_.-]*$/.test(literal) || literal === '', `Unsupported header source: ${rule.source}`);
    const escaped = literal.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    return { src: '^' + escaped + (wildcard ? '/(.*)' : '') + '$',
      headers: Object.fromEntries(rule.headers.map(({ key, value }) => [key, value])), continue: true };
  });
}

export async function stagePhonePreview({ build, out, root = repo }) {
  build = path.resolve(build); out = path.resolve(out); root = path.resolve(root);
  assert(fs.lstatSync(build).isDirectory() && !fs.lstatSync(build).isSymbolicLink(), 'Build must be a real directory');
  assert(!fs.existsSync(out), 'Use a fresh ignored staging directory');
  assert(!within(build, out) && !within(out, build), 'Staging must be separate from the input build');
  assert(!within(path.join(root, 'public'), out) && !within(path.join(root, '.vercel'), out), 'Keep staging outside public and repository Vercel output');
  const inputsFile = regularFile(build, 'rider-rebuild-inputs.json');
  const inputs = json(inputsFile), review = json(regularFile(build, 'hero-review.json'));
  const catalog = json(regularFile(build, 'model-catalog.json'));
  const loads = json(regularFile(build, 'load-manifest.json'));
  const measurements = json(regularFile(build, 'rider-comparison-js.json'));
  assert.equal(inputs.releaseBuild, false); assert.equal(review.releaseBuild, false);
  assert.equal(measurements.releaseBuild, false);
  assert.equal(measurements.measurement, 'Final emitted files; PWA worker cost reported separately.',
    'Comparison budget must measure final emitted files');
  assert.equal(measurements.normalPlayerLimitGzipBytes, 701 * 1024, 'Normal player budget must remain unchanged');
  assert(Number.isFinite(measurements.normalPlayerGzipBytes) && measurements.normalPlayerGzipBytes >= 0
    && measurements.normalPlayerGzipBytes <= measurements.normalPlayerLimitGzipBytes,
  'Final emitted normal player JavaScript exceeds the unchanged budget');
  assert.equal(inputs.comparison?.id, 'street-remastered');
  assert.equal(inputs.comparison.label, 'Mustard · Remastered');
  assert.equal(inputs.comparison.lodAliasesFull, true);
  assert.deepEqual(inputs.modelSlots, selectedSlots);
  assert.deepEqual(Object.keys(review.mapping).sort((a, b) => a < b ? -1 : a > b ? 1 : 0), [...selectedSlots].sort((a, b) => a < b ? -1 : a > b ? 1 : 0));
  assert.equal(inputs.selectedRiderSource?.canonicalLogical, selectedSlots[0]);
  assert.deepEqual(inputs.selectedRiderSource.modelSlots, selectedSlots);
  assert.equal(inputs.selectedRiderSource.texturePolicy, 'preserve-authored-images');
  assert.equal(inputs.selectedRiderSource.sourceSHA256, inputs.sourceSHA256);
  assert(/^[a-f0-9]{64}$/.test(inputs.sourceSHA256), 'Invalid selected source hash');
  assert.equal(new Set(catalog.models.map(row => row.logical)).size, catalog.models.length, 'Duplicate catalog model');
  const models = new Map(catalog.models.map(row => [row.logical, row]));
  const selected = models.get(selectedSlots[0]), lod = models.get(selectedSlots[1]);
  assert(selected && lod, 'Missing sixth rider full/LOD slots');
  assert.equal(selected.url, lod.url); assert.equal(selected.sha256, lod.sha256); assert.equal(selected.bytes, lod.bytes);
  assert.equal(selected.sha256, inputs.sourceSHA256); assert.equal(selected.bytes, inputs.comparison.sourceBytes);
  for (const logical of selectedSlots) assert.deepEqual(review.models.find(row => row.logical === logical), models.get(logical));
  assert.equal(catalog.models.filter(row => row.sha256 === selected.sha256).length, 2, 'Selected source appears only in its full/LOD slots');
  const originalModels = originalIds.flatMap(id => ['', '-lod'].map(suffix => `models/rider-${id}${suffix}.glb`));
  for (const logical of [...originalModels, ...['rookie', 'pro'].flatMap(id => ['', '-lod'].map(suffix => `models/bike-${id}${suffix}.glb`))]) {
    const row = models.get(logical); assert(row, `Missing original hero: ${logical}`);
    assert.equal(await hashFile(regularFile(path.join(root, 'public'), logical)), row.sha256, `Original hero bytes changed: ${logical}`);
  }
  assert.notEqual(models.get(originalModels[0]).sha256, selected.sha256, 'Selected source cannot replace original Mustard');
  const expected = new Map();
  const add = (value, bytes, digest) => {
    const relative = publicPath(value), prior = expected.get(relative) ?? {};
    if (bytes !== undefined) {
      assert(Number.isSafeInteger(bytes) && bytes >= 0, `Invalid byte count: ${relative}`);
      assert(prior.bytes === undefined || prior.bytes === bytes, `Conflicting byte counts: ${relative}`);
    }
    if (digest !== undefined) {
      assert(/^[a-f0-9]{64}$/.test(digest), `Invalid asset hash: ${relative}`);
      assert(!prior.sha256 || prior.sha256 === digest, `Conflicting hashes: ${relative}`);
    }
    expected.set(relative, { bytes: bytes ?? prior.bytes, sha256: digest ?? prior.sha256 });
  };
  // The existing recipe includes duplicate art rows with historical estimates,
  // and final HTML/version injection can change JS after this manifest hook.
  // Retain the emitted manifest exactly; catalog sizes/hashes remain strict.
  for (const row of loads.items) add(row.path, undefined, row.sha256);
  for (const row of [...catalog.models, ...(catalog.resources ?? [])]) add(row.url, row.bytes, row.sha256);
  // Recorded audio and the on-device bench input are copied public assets,
  // fetched dynamically by the game rather than listed in load-manifest.json.
  const copiedPublic = (directory, prefix) => {
    if (!fs.existsSync(directory)) return;
    for (const entry of fs.readdirSync(directory, { withFileTypes: true })) {
      const relative = prefix + '/' + entry.name;
      if (entry.isDirectory()) copiedPublic(path.join(directory, entry.name), relative);
      else if (prefix.startsWith('audio') ? /\.(?:mp3|m4a|ogg|wav|txt)$/.test(entry.name) : entry.name.endsWith('.json')) {
        regularFile(path.join(root, 'public'), relative); add(relative);
      }
    }
  };
  for (const directory of ['audio', 'bench']) copiedPublic(path.join(root, 'public', directory), directory);
  for (const relative of roots) if (fs.existsSync(path.join(build, relative))) add(relative);
  for (const relative of ['index.html', 'load-manifest.json', 'model-catalog.json', 'rider-comparison-js.json']) assert(expected.has(relative), `Missing runtime output: ${relative}`);
  add(measurements.reviewChunk, undefined, measurements.reviewChunkSHA256);
  assert.equal(loads.items.filter(row => publicPath(row.path) === selected.url).length, 1, 'Selected source must be loaded once');
  const config = { version: 3, routes: [...headerRoutes(json(path.join(root, 'vercel.json'))), { handle: 'filesystem' }] };
  const linkage = json(path.join(root, '.vercel/project.json'));
  const project = { projectId: linkage.projectId, orgId: linkage.orgId, projectName: linkage.projectName };
  assert(/^prj_[a-zA-Z0-9]+$/.test(project.projectId) && /^(?:team|user)_[a-zA-Z0-9]+$/.test(project.orgId), 'Missing public project linkage');
  assert(typeof project.projectName === 'string' && project.projectName.length > 0);
  const staticDir = path.join(out, '.vercel/output/static'), files = [];
  fs.mkdirSync(staticDir, { recursive: true });
  // All large assets are copied and hashed sequentially with bounded buffers.
  // Text inspection rejects local machine receipts without reading GLBs as text.
  for (const [relative, declared] of [...expected].sort(([a], [b]) => a.localeCompare(b))) {
    const source = regularFile(build, relative), destination = path.join(staticDir, relative);
    const before = fs.statSync(source), digest = crypto.createHash('sha256');
    if (declared.bytes !== undefined) assert.equal(before.size, declared.bytes, `Build byte count mismatch: ${relative}`);
    let bytes = 0, tail = '';
    const text = /\.(?:html|js|css|json|webmanifest|svg|txt)$/.test(relative);
    fs.mkdirSync(path.dirname(destination), { recursive: true });
    await pipeline(fs.createReadStream(source), new Transform({ transform(chunk, _encoding, callback) {
      try {
        bytes += chunk.length; digest.update(chunk);
        if (text) {
          const sample = tail + chunk.toString('utf8');
          assert(!/(?:\/(?:Users|home)\/[^/\s"']+\/|\/private\/var\/|file:\/\/[^\s"'`<>]+)/.test(sample), `Local machine path in public text: ${relative}`);
          tail = sample.slice(-512);
        }
        callback(null, chunk);
      } catch (error) { callback(error); }
    } }), fs.createWriteStream(destination, { flags: 'wx' }));
    const actual = digest.digest('hex'), after = fs.statSync(source);
    assert.equal(bytes, before.size); assert.equal(after.size, before.size); assert.equal(after.mtimeMs, before.mtimeMs);
    if (declared.sha256) assert.equal(actual, declared.sha256, `Build hash mismatch: ${relative}`);
    assert.equal(await hashFile(destination), actual, `Staged bytes changed: ${relative}`);
    files.push({ path: relative, bytes, sha256: actual });
  }
  assert.equal(files.filter(row => row.sha256 === selected.sha256).length, 1, 'Stage contains exactly one selected GLB');
  const write = (relative, value) => fs.writeFileSync(path.join(out, relative), JSON.stringify(value, null, 2) + '\n', { flag: 'wx' });
  write('.vercel/output/config.json', config);
  // CLI 59.11.2 reads this target and rejects accidental --prod prebuilt upload.
  write('.vercel/output/builds.json', { target: 'preview', builds: [] });
  write('.vercel/project.json', project);
  const staged = new Map(files.map(row => [row.path, row]));
  const manifestByteDifferences = loads.items.flatMap(row => {
    const actual = staged.get(publicPath(row.path)).bytes;
    return row.bytes === actual ? [] : [{ path: publicPath(row.path), declaredBytes: row.bytes, actualBytes: actual }];
  });
  const receipt = { releaseBuild: false, accepted: false, target: 'preview', staticOnly: true,
    comparison: inputs.comparison, selected: { url: selected.url, bytes: selected.bytes, sha256: selected.sha256 },
    originalHeroesVerified: originalModels.length + 4, recipeSHA256: sha(fs.readFileSync(fileURLToPath(import.meta.url))),
    inputReceiptSHA256: await hashFile(inputsFile), configSHA256: await hashFile(path.join(out, '.vercel/output/config.json')),
    fileCount: files.length, bytes: files.reduce((sum, row) => sum + row.bytes, 0), files, manifestByteDifferences,
    excluded: ['.inputs/', '.private*', 'hero-review.json', 'rider-rebuild-inputs.json', 'source maps and provenance sidecars'],
    deployCommand: 'vercel deploy --prebuilt --yes' };
  write('staging-receipt.json', receipt);
  return receipt;
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const arg = name => process.argv.find(value => value.startsWith(`--${name}=`))?.slice(name.length + 3);
  for (const key of ['build', 'out']) assert(arg(key), `Missing --${key}`);
  const ignored = spawnSync('git', ['check-ignore', '--quiet', '--no-index', '--', path.resolve(arg('out'))], { cwd: repo });
  assert.equal(ignored.status, 0, 'Staging output must be ignored by Git');
  const receipt = await stagePhonePreview({ build: arg('build'), out: arg('out') });
  console.log(JSON.stringify({ out: path.resolve(arg('out')), target: receipt.target, fileCount: receipt.fileCount,
    bytes: receipt.bytes, selected: receipt.selected, configSHA256: receipt.configSHA256 }));
}
