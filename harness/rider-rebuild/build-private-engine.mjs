/** Reuse the actual private real-game build recipe with one isolated Vite plugin.
 * node harness/rider-rebuild/build-private-engine.mjs --source=FILE --contract=FILE --out=DIR [--comparison]
 * Comparison preserves original outfits and adds one selected full-asset review choice.
 */
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { spawnSync } from 'node:child_process';
import { comparisonRider, comparisonModelMapping, comparisonSnapshotSource } from './private-engine-plugin.mjs';

const arg = name => process.argv.find(value => value.startsWith(`--${name}=`))?.slice(name.length + 3);
const sha = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
const comparison = process.argv.includes('--comparison');
const root = process.cwd(), source = path.resolve(arg('source') ?? ''), contract = path.resolve(arg('contract') ?? ''), out = path.resolve(arg('out') ?? '');
for (const name of ['source', 'contract', 'out']) if (!arg(name)) throw new Error(`Missing --${name}`);
if (out === root || out === path.join(root, 'public') || fs.existsSync(path.join(out, 'hero-review.json'))) throw new Error('Use a fresh private output directory');
const sourceBytes = fs.readFileSync(source), metadataBytes = fs.readFileSync(contract);
const metadata = { ...JSON.parse(metadataBytes), sourceSHA256: sha(sourceBytes), metadataSHA256: sha(metadataBytes) };
const sourceTriangles = comparison ? (() => {
  const document = JSON.parse(sourceBytes.subarray(20, 20 + sourceBytes.readUInt32LE(12)));
  return document.meshes.flatMap(mesh => mesh.primitives).reduce((sum, primitive) => sum + ((primitive.mode ?? 4) === 4
    ? document.accessors[primitive.indices ?? primitive.attributes.POSITION].count / 3 : 0), 0);
})() : null;
const calibrationPath = arg('pose-calibration') ? path.resolve(arg('pose-calibration')) : null;
const calibration = calibrationPath ? JSON.parse(fs.readFileSync(calibrationPath, 'utf8')) : null;
if (calibration) {
  if (calibration.sourceSHA256 !== sha(sourceBytes)) throw new Error('Pose calibration source changed');
  for (const bike of calibration.bikes ?? []) {
    if (sha(fs.readFileSync(path.resolve(root, bike.path))) !== bike.sha256) throw new Error('Selected sole bike source changed');
  }
  Object.assign(metadata.driver, calibration.driver);
}
const mapping = comparison ? comparisonModelMapping(source)
  : Object.fromEntries(fs.readdirSync(path.join(root, 'public/models')).filter(name => /^rider.*\.glb$/.test(name)).map(name => [`models/${name}`, source]));
if (!Object.keys(mapping).length) throw new Error('No actual rider model slots');
const canonicalLogical = comparison ? comparisonRider.full : 'models/rider-street-mustard.glb';
if (!Object.hasOwn(mapping, canonicalLogical)) throw new Error('Missing canonical selected rider model slot');
// Runtime mass calibration consumes five native head/tail correspondences only.
// Full 75-joint names/roles/parents remain captured and checked on the loaded rig;
// do not ship unused native 4x4 matrices inside private player JavaScript.
const first = value => Array.isArray(value) ? value[0] : value;
const endpointIds = [first(metadata.specification.roles.head), ...['left', 'right'].flatMap(side => {
  const suffix = side === 'left' ? 'Left' : 'Right';
  return [first(metadata.specification.roles['toe' + suffix] ?? metadata.specification.roles['foot' + suffix]),
    metadata.specification.hands[side].digits.middle.at(-1)];
})];
const endpointNames = new Set(endpointIds.map(id => metadata.specification.jointNames[id]));
const runtimeMetadata = { sourceSHA256: metadata.sourceSHA256, metadataSHA256: metadata.metadataSHA256,
  selectedRiderSource: { modelSlots: Object.keys(mapping), canonicalLogical, sourceSHA256: metadata.sourceSHA256,
    texturePolicy: 'preserve-authored-images' },
  specification: metadata.specification, driver: metadata.driver,
  nativeRest: { frame: metadata.nativeRest.frame, bones: metadata.nativeRest.bones.filter(row => endpointNames.has(row.name))
    .map(({ name, head, tail }) => ({ name, head, tail })) } };
if (comparison) runtimeMetadata.comparison = true;
if (arg('garage-clip')) runtimeMetadata.previewClip = arg('garage-clip');
if (arg('near-similarity')) metadata.driver.nearSimilarityTolerance = Number(arg('near-similarity'));
const originalPath = path.join(root, 'harness/hero-remaster/build.mts'), original = fs.readFileSync(originalPath, 'utf8');
const pluginPath = path.join(root, 'harness/rider-rebuild/private-engine-plugin.mjs');
const replacements = [
  ["'../../src/boot/model-catalog'", JSON.stringify(path.join(root, 'src/boot/model-catalog.ts'))],
  ["'./new-rider-private-adapter.mjs'", JSON.stringify(path.join(root, 'harness/hero-remaster/new-rider-private-adapter.mjs'))],
  ["'./new-rider-hip-corrective.mjs'", JSON.stringify(path.join(root, 'harness/hero-remaster/new-rider-hip-corrective.mjs'))],
  ['plugins: [adapterPlugin, plugin]', `plugins: [privateEnginePlugin(${JSON.stringify(runtimeMetadata)}), adapterPlugin, plugin]`],
];
let generated = `import { privateEnginePlugin } from ${JSON.stringify(pluginPath)};\n` + original;
for (const [before, after] of replacements) {
  if (generated.split(before).length !== 2) throw new Error(`Actual build recipe changed at ${before}`);
  generated = generated.replace(before, after);
}
if (comparison) generated = comparisonSnapshotSource(generated);
fs.mkdirSync(out, { recursive: true });
const driverPath = path.join(out, '.private-build-driver.mts'), mappingPath = path.join(out, '.private-models.json');
fs.writeFileSync(driverPath, generated); fs.writeFileSync(mappingPath, JSON.stringify(mapping, null, 2));
fs.writeFileSync(path.join(out, 'rider-rebuild-inputs.json'), JSON.stringify({
  releaseBuild: false, source, contract, sourceSHA256: sha(sourceBytes), metadataSHA256: sha(metadataBytes),
  comparison: comparison ? { ...comparisonRider, sourceBytes: sourceBytes.length, sourceTriangles, lodAliasesFull: true,
    limits: 'High-resolution selected full asset for both detail slots; phone memory, performance and art unaccepted. Original five riders/bytes/drivers retained.' } : null,
  actualBuildRecipe: { path: originalPath, sha256: sha(original) },
  runtimeMetadataSHA256: sha(JSON.stringify(runtimeMetadata)),
  selectedRiderSource: runtimeMetadata.selectedRiderSource,
  poseCalibration: calibrationPath ? { path: calibrationPath, sha256: sha(fs.readFileSync(calibrationPath)), driver: calibration.driver } : null,
  adapter: ['private-rider.mjs', 'private-engine-plugin.mjs', 'new-humanoid-contract.mjs', 'anthropometric-inverse.mjs'].map(name => {
    const file = path.join(root, 'harness/rider-rebuild', name); return { path: file, sha256: sha(fs.readFileSync(file)) };
  }), modelSlots: Object.keys(mapping),
}, null, 2));
const result = spawnSync(process.execPath, ['--import', 'tsx', driverPath, `--out=${out}`, `--models=${mappingPath}`], { cwd: root, stdio: 'inherit' });
if (result.error) throw result.error;
if (result.status !== 0) throw new Error(`Private actual-game build failed: ${result.status}`);
if (sha(fs.readFileSync(source)) !== sha(sourceBytes) || sha(fs.readFileSync(contract)) !== sha(metadataBytes)) throw new Error('Source/metadata changed during build');
console.log(JSON.stringify({ out, sourceSHA256: sha(sourceBytes), metadataSHA256: sha(metadataBytes), actualGame: true, normalAssetsChanged: false }));
