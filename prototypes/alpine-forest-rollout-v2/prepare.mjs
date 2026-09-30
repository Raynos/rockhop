/** CPU-only immutable snapshot. Never reads dotenv, credentials, sessions or caches. */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createHash } from 'node:crypto';
import { execFileSync } from 'node:child_process';
import { overrides } from './overrides.mjs';
export const home = path.dirname(fileURLToPath(import.meta.url));
export const project = path.resolve(home, '../..');
export const common = path.join(home, 'out/common');
export const sha = bytes => createHash('sha256').update(bytes).digest('hex');
export const manifestPath = path.join(home, 'snapshot-manifest.json');
const roots = ['src', 'public', 'api', 'scripts', 'harness'];
const extra = ['index.html', 'vite.config.ts', 'vitest.config.ts', 'package.json', 'pnpm-lock.yaml', 'tsconfig.json', 'tsconfig.harness.json', '.oxlintrc.json',
  'assets/worldmap/sky-alpine-a.webp',
  'assets/blender/course-kits/alpine-trees/rollout-fixture.ts',
  'assets/blender/course-kits/alpine-trees/a1-frozen-capture.mts', 'assets/blender/course-kits/alpine-trees/a1-full-ride-perf.mts',
  'assets/blender/course-kits/alpine-trees/frozen-source.mts', 'assets/blender/course-kits/alpine-trees/a1-held-go.rec.json',
  'docs/evidence/alpine-retarget/a1-sawdust-rookie-restart.rec.json',
  'docs/evidence/course-remaster/a3/loader-cab/capture.mts',
  'docs/evidence/alpine-retarget/a2-log-jam-rookie-restart.rec.json',
  'docs/evidence/alpine-retarget/a3-timberline-rookie-restart.rec.json',
  'docs/evidence/alpine-retarget/a3-timberline-rookie-bot.rec.json'];
function inputs(root) {
  const files = [];
  function walk(relative) {
    if (relative === 'harness/out' || /(^|\/)(node_modules|\.vite|__pycache__)$/.test(relative)) return;
    const absolute = path.join(root, relative), stat = fs.lstatSync(absolute);
    if (stat.isSymbolicLink()) throw new Error(`Snapshot refuses a symlink: ${relative}`);
    if (stat.isDirectory()) for (const child of fs.readdirSync(absolute).sort()) walk(`${relative}/${child}`);
    else if (stat.isFile() && !/\.(log|pyc)$/.test(relative)) files.push(relative);
  }
  for (const directory of roots) walk(directory);
  for (const file of extra) { if (!fs.statSync(path.join(root, file)).isFile()) throw new Error(`Missing input ${file}`); files.push(file); }
  return [...new Set(files)].sort().map(file => {
    const bytes = fs.readFileSync(path.join(root, file)); return { file, bytes: bytes.length, sha256: sha(bytes) };
  });
}
export function verifySnapshot({ shared = false } = {}) {
  const manifest = JSON.parse(fs.readFileSync(manifestPath, 'utf8'));
  for (const entry of manifest.files) {
    const bytes = fs.readFileSync(path.join(common, entry.file));
    if (bytes.length !== entry.bytes || sha(bytes) !== entry.sha256) throw new Error(`Frozen input changed: ${entry.file}`);
    if (shared && sha(fs.readFileSync(path.join(project, entry.file))) !== entry.sha256) throw new Error(`Shared input differs from pinned snapshot: ${entry.file}`);
  }
  if (shared && JSON.stringify(inputs(project)) !== JSON.stringify(manifest.files)) throw new Error('Shared file inventory changed');
  if (sha(fs.readFileSync(path.join(project, 'pnpm-lock.yaml'))) !== manifest.lockSHA256) throw new Error('Shared dependencies changed; restore the pinned lock/runtime before using the snapshot');
  for (const entry of manifest.dependencies) {
    if (sha(fs.readFileSync(entry.packageJson)) !== entry.sha256) throw new Error(`Installed dependency changed: ${entry.name}`);
  }
  for (const entry of manifest.overrides) if (sha(fs.readFileSync(path.join(home, 'out/after', entry.file))) !== entry.sha256) throw new Error(`Frozen override changed: ${entry.file}`);
  return manifest;
}
if (process.argv[1] === fileURLToPath(import.meta.url)) {
  const record = process.argv.includes('--record');
  const restore = process.argv.includes('--restore');
  if (restore) {
    if (record || fs.existsSync(common)) throw new Error('--restore requires a manifest and absent out/common; never overwrites a frozen snapshot');
    const manifest = JSON.parse(fs.readFileSync(manifestPath, 'utf8'));
    if (JSON.stringify(inputs(project)) !== JSON.stringify(manifest.files)) throw new Error('Shared input inventory/bytes differ from pinned manifest; cannot reconstruct the historical snapshot');
    for (const entry of manifest.files) {
      const dest = path.join(common, entry.file); fs.mkdirSync(path.dirname(dest), { recursive: true }); fs.copyFileSync(path.join(project, entry.file), dest);
    }
    const changed = overrides(Object.fromEntries(manifest.overrides.map(entry => [entry.file, fs.readFileSync(path.join(common, entry.file), 'utf8')])));
    for (const [file, text] of Object.entries(changed)) {
      const dest = path.join(home, 'out/after', file); fs.mkdirSync(path.dirname(dest), { recursive: true }); fs.writeFileSync(dest, text);
    }
    fs.symlinkSync(path.join(project, 'node_modules'), path.join(common, 'node_modules'), 'dir');
  }
  if (record) {
    if (fs.existsSync(manifestPath) || fs.existsSync(common)) throw new Error('Refusing to replace an existing frozen snapshot');
    const head = execFileSync('git', ['rev-parse', 'HEAD'], { cwd: project, encoding: 'utf8' }).trim();
    const files = inputs(project);
    for (const entry of files) {
      const dest = path.join(common, entry.file); fs.mkdirSync(path.dirname(dest), { recursive: true }); fs.copyFileSync(path.join(project, entry.file), dest);
    }
    if (JSON.stringify(files) !== JSON.stringify(inputs(project)) || head !== execFileSync('git', ['rev-parse', 'HEAD'], { cwd: project, encoding: 'utf8' }).trim()) throw new Error('Shared inputs moved during snapshot; discard this incomplete out/ and retry');
    const changed = overrides(Object.fromEntries(['src/render/world/biomeKit.ts'].map(file => [file, fs.readFileSync(path.join(common, file), 'utf8')])));
    const overrideRows = [];
    for (const [file, text] of Object.entries(changed)) {
      const dest = path.join(home, 'out/after', file); fs.mkdirSync(path.dirname(dest), { recursive: true }); fs.writeFileSync(dest, text);
      overrideRows.push({ file, bytes: Buffer.byteLength(text), sha256: sha(text) });
    }
    // A reviewable patch; builds never apply it to the shared checkout.
    const patch = Object.keys(changed).map(file => {
      try { return execFileSync('diff', ['-U', '0', '--label', `a/${file}`, '--label', `b/${file}`, path.join(common, file), path.join(home, 'out/after', file)], { encoding: 'utf8' }); }
      catch (error) { if (error.status !== 1) throw error; return String(error.stdout); }
    }).join('');
    fs.writeFileSync(path.join(home, 'runtime.patch'), patch);
    fs.symlinkSync(path.join(project, 'node_modules'), path.join(common, 'node_modules'), 'dir');
    const dependencyNames = ['three', '@types/three', 'vite', 'typescript', 'tsx', 'vitest', 'oxlint', 'playwright'];
    const dependencies = dependencyNames.map(name => {
      const packageJson = path.join(project, 'node_modules', name, 'package.json'), bytes = fs.readFileSync(packageJson);
      return { name, packageJson, version: JSON.parse(bytes.toString()).version, sha256: sha(bytes) };
    });
    const manifest = { schema: 1, status: 'source-only-unaccepted', capturedUTC: new Date().toISOString(), head,
      node: process.version, treeConfounder: execFileSync('git', ['status', '--porcelain=v1'], { cwd: project, encoding: 'utf8' }),
      lockSHA256: sha(fs.readFileSync(path.join(common, 'pnpm-lock.yaml'))),
      bankSHA256: sha(JSON.stringify(files.filter(entry => entry.file.startsWith('public/')))),
      appSHA256: sha(JSON.stringify(files.filter(entry => entry.file.startsWith('src/')))),
      files, overrides: overrideRows, dependencies };
    fs.writeFileSync(manifestPath, JSON.stringify(manifest, null, 2) + '\n');
  }
  const manifest = verifySnapshot({ shared: !record });
  console.info(JSON.stringify({ ready: true, head: manifest.head, appSHA256: manifest.appSHA256, bankSHA256: manifest.bankSHA256, files: manifest.files.length, phase: 'No builds or captures run' }, null, 2));
}
