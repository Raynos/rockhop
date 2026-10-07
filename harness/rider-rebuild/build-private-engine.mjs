/** Reuse the actual private real-game build recipe with one isolated Vite plugin.
 * node harness/rider-rebuild/build-private-engine.mjs --source=FILE --contract=FILE --out=DIR
 */
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { spawnSync } from 'node:child_process';

const arg = name => process.argv.find(value => value.startsWith(`--${name}=`))?.slice(name.length + 3);
const sha = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
const root = process.cwd(), source = path.resolve(arg('source') ?? ''), contract = path.resolve(arg('contract') ?? ''), out = path.resolve(arg('out') ?? '');
for (const name of ['source', 'contract', 'out']) if (!arg(name)) throw new Error(`Missing --${name}`);
if (out === root || out === path.join(root, 'public') || fs.existsSync(path.join(out, 'hero-review.json'))) throw new Error('Use a fresh private output directory');
const sourceBytes = fs.readFileSync(source), metadataBytes = fs.readFileSync(contract);
const metadata = { ...JSON.parse(metadataBytes), sourceSHA256: sha(sourceBytes), metadataSHA256: sha(metadataBytes) };
if (arg('garage-clip')) metadata.driver.garageClip = arg('garage-clip');
if (arg('near-similarity')) metadata.driver.nearSimilarityTolerance = Number(arg('near-similarity'));
const originalPath = path.join(root, 'harness/hero-remaster/build.mts'), original = fs.readFileSync(originalPath, 'utf8');
const pluginPath = path.join(root, 'harness/rider-rebuild/private-engine-plugin.mjs');
const replacements = [
  ["'../../src/boot/model-catalog'", JSON.stringify(path.join(root, 'src/boot/model-catalog.ts'))],
  ["'./new-rider-private-adapter.mjs'", JSON.stringify(path.join(root, 'harness/hero-remaster/new-rider-private-adapter.mjs'))],
  ["'./new-rider-hip-corrective.mjs'", JSON.stringify(path.join(root, 'harness/hero-remaster/new-rider-hip-corrective.mjs'))],
  ['plugins: [adapterPlugin, plugin]', `plugins: [privateEnginePlugin(${JSON.stringify(metadata)}), adapterPlugin, plugin]`],
];
let generated = `import { privateEnginePlugin } from ${JSON.stringify(pluginPath)};\n` + original;
for (const [before, after] of replacements) {
  if (generated.split(before).length !== 2) throw new Error(`Actual build recipe changed at ${before}`);
  generated = generated.replace(before, after);
}
fs.mkdirSync(out, { recursive: true });
const mapping = Object.fromEntries(fs.readdirSync(path.join(root, 'public/models')).filter(name => /^rider.*\.glb$/.test(name)).map(name => [`models/${name}`, source]));
if (!Object.keys(mapping).length) throw new Error('No actual rider model slots');
const driverPath = path.join(out, '.private-build-driver.mts'), mappingPath = path.join(out, '.private-models.json');
fs.writeFileSync(driverPath, generated); fs.writeFileSync(mappingPath, JSON.stringify(mapping, null, 2));
fs.writeFileSync(path.join(out, 'rider-rebuild-inputs.json'), JSON.stringify({
  releaseBuild: false, source, contract, sourceSHA256: sha(sourceBytes), metadataSHA256: sha(metadataBytes),
  actualBuildRecipe: { path: originalPath, sha256: sha(original) },
  adapter: ['private-rider.mjs', 'private-engine-plugin.mjs', 'new-humanoid-contract.mjs'].map(name => {
    const file = path.join(root, 'harness/rider-rebuild', name); return { path: file, sha256: sha(fs.readFileSync(file)) };
  }), modelSlots: Object.keys(mapping),
}, null, 2));
const result = spawnSync(process.execPath, ['--import', 'tsx', driverPath, `--out=${out}`, `--models=${mappingPath}`], { cwd: root, stdio: 'inherit' });
if (result.error) throw result.error;
if (result.status !== 0) throw new Error(`Private actual-game build failed: ${result.status}`);
if (sha(fs.readFileSync(source)) !== sha(sourceBytes) || sha(fs.readFileSync(contract)) !== sha(metadataBytes)) throw new Error('Source/metadata changed during build');
console.log(JSON.stringify({ out, sourceSHA256: sha(sourceBytes), metadataSHA256: sha(metadataBytes), actualGame: true, normalAssetsChanged: false }));
