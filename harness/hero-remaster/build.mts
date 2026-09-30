/** Build a private real-game hero review with immutable candidate model URLs.
 * No public/models replacement and no experimental player-facing selector.
 * tsx harness/hero-remaster/build.mts --out=DIR [--models=logical-to-file.json]
 */
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { build, type Plugin } from 'vite';
import { readModelCatalog, type ModelAsset } from '../../src/boot/model-catalog';

const arg = (name: string, fallback = '') => process.argv.find(a => a.startsWith(`--${name}=`))?.slice(name.length + 3) ?? fallback;
const root = process.cwd();
const out = path.resolve(arg('out', 'harness/out/hero-remaster/baseline-build'));
const mappingFile = arg('models');
const mapping: Record<string, string> = mappingFile ? JSON.parse(fs.readFileSync(mappingFile, 'utf8')) : {};
const sourceRoot = path.join(out, '.inputs');
fs.mkdirSync(path.join(sourceRoot, 'models'), { recursive: true });
fs.cpSync(path.join(root, 'public/models'), path.join(sourceRoot, 'models'), { recursive: true });
for (const entry of fs.readdirSync(path.join(root, 'public/models'))) {
  if (!entry.endsWith('.glb')) continue;
  const logical = `models/${entry}`;
  fs.copyFileSync(path.resolve(mapping[logical] ?? path.join(root, 'public', logical)), path.join(sourceRoot, logical));
}
for (const logical of Object.keys(mapping)) {
  if (!/^models\/[a-z0-9-]+\.glb$/.test(logical)) throw new Error(`invalid logical model ${logical}`);
  if (!fs.existsSync(path.join(sourceRoot, logical))) throw new Error(`unknown logical model ${logical}`);
}
const assets = readModelCatalog(sourceRoot);
const values = Object.fromEntries(assets.map(a => [a.logical, { url: a.url, bytes: a.bytes.length, sha256: a.sha256 }]));
const changed = assets.filter(a => mapping[a.logical]);
const manifest = {
  kind: 'private actual-game hero review',
  mapping,
  releaseBuild: false,
  models: assets.map(a => ({ logical: a.logical, url: a.url, bytes: a.bytes.length, sha256: a.sha256 })),
};
const plugin: Plugin = {
  name: 'rockhop:private-hero-review',
  enforce: 'post',
  transform(code, id) {
    if (id.endsWith('/src/render/hero/models.generated.ts')) {
      // Preserve other generated exports (including authored-course resources)
      // as the shared catalog grows; replace only the model snapshot table.
      const first = code.indexOf('export const MODEL_ASSETS =');
      if (first < 0) throw new Error('missing generated model table');
      const next = code.indexOf('export const ', first + 1);
      return { code: code.slice(0, first) + `export const MODEL_ASSETS = ${JSON.stringify(values)};\n` + (next < 0 ? '' : code.slice(next)), map: null };
    }
    if (id.endsWith('/src/boot/plan.generated.ts')) {
      for (const a of changed) code = code.replace(new RegExp(`(${JSON.stringify(a.logical)}\\s*:\\s*)\\d+`), `$1${a.bytes.length}`);
      return { code, map: null };
    }
    return null;
  },
  generateBundle(_options, bundle) {
    for (const a of assets) {
      if (!bundle[a.url]) this.emitFile({ type: 'asset', fileName: a.url, source: a.bytes });
    }
    const catalog = bundle['model-catalog.json'];
    if (!catalog || catalog.type !== 'asset') throw new Error('missing model catalog');
    const existing = JSON.parse(typeof catalog.source === 'string' ? catalog.source : Buffer.from(catalog.source).toString('utf8'));
    catalog.source = JSON.stringify({ ...existing, models: manifest.models }, null, 2) + '\n';
    this.emitFile({ type: 'asset', fileName: 'hero-review.json', source: JSON.stringify(manifest, null, 2) + '\n' });
  },
};
await build({ root, configFile: path.join(root, 'vite.config.ts'), logLevel: 'warn', plugins: [plugin], build: { outDir: out, emptyOutDir: false } });
// The published manifest is truthful about the exact candidate bytes/URLs.
for (const a of assets) {
  const actual = fs.readFileSync(path.join(out, a.url));
  if (crypto.createHash('sha256').update(actual).digest('hex') !== a.sha256) throw new Error(`review hash mismatch ${a.logical}`);
}
fs.writeFileSync(path.join(out, 'hero-review.json'), JSON.stringify(manifest, null, 2) + '\n');
console.log(JSON.stringify({ out, replaced: changed.map(a => a.logical), models: assets.length }));

export type { ModelAsset };
