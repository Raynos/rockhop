/**
 * Freeze one matched normal-app D1 before/after pair outside the repository.
 * `prepare` is CPU/filesystem only. `build` is for the parent after this handoff.
 *
 * pnpm exec tsx prototypes/quarry-authored-integration-v1/prepare.mts prepare /tmp/rockhop-quarry-d1-PAIR
 * pnpm exec tsx prototypes/quarry-authored-integration-v1/prepare.mts build   /tmp/rockhop-quarry-d1-PAIR
 */
import fs from 'node:fs';
import path from 'node:path';
import { createHash } from 'node:crypto';
import { execFileSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { readModelCatalog, readModelResources } from '../../src/boot/model-catalog';

const root = fs.realpathSync(process.cwd());
const here = path.dirname(fileURLToPath(import.meta.url));
const mode = process.argv[2];
const requestedOut = path.resolve(process.argv[3] ?? '');
if (!['prepare', 'build'].includes(mode ?? '') || !process.argv[3]) throw Error('Use prepare|build /tmp/FRESH-QUARRY-PAIR');
if (requestedOut === root || requestedOut.startsWith(root + path.sep)) throw Error('Pair output must be outside the repository');
if (mode === 'prepare' && fs.existsSync(requestedOut)) throw Error(`Use a fresh output directory: ${requestedOut}`);
if (mode === 'build' && !fs.existsSync(requestedOut)) throw Error(`Missing frozen pair: ${requestedOut}`);
// Vite compares plugin IDs with c.root; on macOS /tmp is an alias for /private/tmp.
// Resolve the physical path before any phase is created so the build sees one identity.
if (mode === 'prepare') fs.mkdirSync(requestedOut, { recursive: true });
const out = fs.realpathSync(requestedOut);
if (out === root || out.startsWith(root + path.sep)) throw Error('Resolved pair output is inside the repository');
const patch = path.join(here, 'runtime.patch');
const patchSha256 = 'edaabe71a9612e14f3f86062de5b07f7aad540cd9db50d347ecc0531c687cbf7';
const historicalV5PatchSha256 = '59780237282bd27f7ac488074766ed226f61a5123a9a405b1ec0833aa6a26cbc';
const historicalV5Head = '17115c8ee8baa7b38acebcb51a250d20c75579cc';
const delivery = path.join(root, 'assets/blender/course-kits/quarry-standard/delivery');
const input = path.join(out, '.inputs');
const sources = ['src', 'public', 'assets/worldmap', 'harness/lib'];
const rootFiles = ['index.html', 'vite.config.ts', 'vitest.config.ts', 'tsconfig.json', 'package.json', 'harness/gate/device-rows.ts'];
const sha = (value: Buffer | string): string => createHash('sha256').update(value).digest('hex');
const fingerprint = (rows: Record<string, string>): string => sha(JSON.stringify(Object.entries(rows).sort(([a], [b]) => a.localeCompare(b))));
if (sha(fs.readFileSync(patch)) !== patchSha256) throw Error('Private patch bytes changed; review and update the pinned patch hash');

function fileHashes(base: string): Record<string, string> {
  const rows: Record<string, string> = {};
  const visit = (relative: string): void => {
    const absolute = path.join(base, relative);
    for (const entry of fs.readdirSync(absolute, { withFileTypes: true }).sort((a, b) => a.name.localeCompare(b.name))) {
      const next = path.join(relative, entry.name);
      if (entry.isDirectory()) visit(next);
      else if (entry.isFile()) rows[next.split(path.sep).join('/')] = sha(fs.readFileSync(path.join(base, next)));
      else throw Error(`Unsupported snapshot entry: ${next}`);
    }
  };
  for (const relative of sources) visit(relative);
  for (const relative of rootFiles) rows[relative] = sha(fs.readFileSync(path.join(base, relative)));
  return rows;
}

function modelTable(base: string): { models: { logical: string; url: string; bytes: number; sha256: string }[]; resources: { logical: string; url: string; bytes: number; sha256: string }[] } {
  const publicRoot = path.join(base, 'public');
  const row = (item: { logical: string; url: string; bytes: Buffer; sha256: string }) => ({ logical: item.logical, url: item.url, bytes: item.bytes.length, sha256: item.sha256 });
  return { models: readModelCatalog(publicRoot).map(row), resources: readModelResources(publicRoot).map(row) };
}

function linkModules(phase: string): void {
  fs.symlinkSync(path.join(root, 'node_modules'), path.join(out, phase, 'node_modules'), 'dir');
}
const privateName = (name: string): string => name.replace(/-lod-packed\.glb$/, '-packed-lod.glb');

if (mode === 'prepare') {
  const beforeCopy = fileHashes(root);
  const head = execFileSync('git', ['rev-parse', 'HEAD'], { cwd: root, encoding: 'utf8' }).trim();
  fs.mkdirSync(input, { recursive: true });
  for (const relative of sources) fs.cpSync(path.join(root, relative), path.join(input, relative), { recursive: true });
  for (const relative of rootFiles) {
    fs.mkdirSync(path.dirname(path.join(input, relative)), { recursive: true });
    fs.copyFileSync(path.join(root, relative), path.join(input, relative));
  }
  const afterCopy = fileHashes(root);
  if (fingerprint(beforeCopy) !== fingerprint(afterCopy) || fingerprint(beforeCopy) !== fingerprint(fileHashes(input))) {
    throw Error('Source/public changed during freeze; discard this pair and retry when writers are quiet');
  }

  const delivered = JSON.parse(fs.readFileSync(path.join(delivery, 'manifest.json'), 'utf8')) as { assets: { file: string; bytes: number; sha256: string }[] };
  if (delivered.assets.length !== 8) throw Error('Quarry delivery is not the full four-machine full/LOD bank');
  const candidateDir = path.join(input, 'public/models/course-kits/quarry-standard');
  fs.mkdirSync(candidateDir, { recursive: true });
  for (const asset of delivered.assets) {
    if (!/^quarry-(drill|crusher|haul|gantry)(-lod)?-packed\.glb$/.test(asset.file)) throw Error(`Unexpected quarry asset ${asset.file}`);
    const bytes = fs.readFileSync(path.join(delivery, asset.file));
    if (bytes.length !== asset.bytes || sha(bytes) !== asset.sha256) throw Error(`Quarry delivery mismatch: ${asset.file}`);
    fs.writeFileSync(path.join(candidateDir, privateName(asset.file)), bytes);
  }
  const bank = modelTable(input);
  for (const phase of ['before', 'after']) {
    fs.cpSync(input, path.join(out, phase), { recursive: true });
    linkModules(phase);
  }
  execFileSync('git', ['apply', '--unidiff-zero', patch], { cwd: path.join(out, 'after'), stdio: 'pipe' });
  const beforePhase = fileHashes(path.join(out, 'before'));
  const afterPhase = fileHashes(path.join(out, 'after'));
  const changed = Object.keys(beforePhase).filter(key => beforePhase[key] !== afterPhase[key]);
  if (JSON.stringify(changed.sort()) !== JSON.stringify(['src/render/world/biomeKit.ts', 'src/render/world/zones/quarryStandard.ts'])) throw Error(`Unexpected source diff: ${changed.join(', ')}`);
  if (JSON.stringify(bank) !== JSON.stringify(modelTable(path.join(out, 'before'))) ||
      JSON.stringify(bank) !== JSON.stringify(modelTable(path.join(out, 'after')))) throw Error('Before/after model or map bank differs');
  const report = {
    status: 'frozen-source-only-unbuilt', head, preparedAt: new Date().toISOString(),
    patchSha256: sha(fs.readFileSync(patch)), currentSourceSha256: fingerprint(beforeCopy),
    frozenSourceSha256: fingerprint(fileHashes(input)),
    beforeBiomeSha256: beforePhase['src/render/world/biomeKit.ts'],
    afterBiomeSha256: afterPhase['src/render/world/biomeKit.ts'],
    changedSourceFiles: changed, modelBank: bank,
    deliveredAssets: delivered.assets.map(a => ({ sourceFile: a.file, privateLogicalName: privateName(a.file), bytes: a.bytes, sha256: a.sha256 })),
    inputHashes: fileHashes(input),
    beforeSourceHashes: beforePhase,
    afterSourceHashes: afterPhase,
    sourceRoot: root,
    warning: 'No build, GPU, replay, moving art or phone qualification; root must build and review.',
  };
  fs.writeFileSync(path.join(out, 'pair.json'), JSON.stringify(report, null, 2) + '\n');
  console.log(JSON.stringify({ out, status: report.status, changed, models: bank.models.length, resources: bank.resources.length }));
} else {
  const reportPath = path.join(out, 'pair.json');
  const report = JSON.parse(fs.readFileSync(reportPath, 'utf8')) as { head: string; patchSha256: string; inputHashes: Record<string, string>; beforeSourceHashes: Record<string, string>; afterSourceHashes: Record<string, string>; modelBank: ReturnType<typeof modelTable>; changedSourceFiles: string[] };
  if (report.patchSha256 !== patchSha256 &&
      !(report.patchSha256 === historicalV5PatchSha256 && report.head === historicalV5Head)) {
    throw Error('Frozen pair does not match this reviewed patch or the exact historical v5 source');
  }
  const expectedBefore = { ...report.inputHashes };
  for (const asset of JSON.parse(fs.readFileSync(path.join(delivery, 'manifest.json'), 'utf8')).assets as { file: string; sha256: string }[]) {
    const relative = `public/models/course-kits/quarry-standard/${privateName(asset.file)}`;
    expectedBefore[relative] = asset.sha256;
  }
  if (fingerprint(fileHashes(path.join(out, 'before'))) !== fingerprint(expectedBefore)) throw Error('Frozen before source changed');
  if (fingerprint(fileHashes(path.join(out, 'before'))) !== fingerprint(report.beforeSourceHashes) ||
      fingerprint(fileHashes(path.join(out, 'after'))) !== fingerprint(report.afterSourceHashes)) throw Error('Frozen phase source changed');
  if (JSON.stringify(modelTable(path.join(out, 'before'))) !== JSON.stringify(report.modelBank) ||
      JSON.stringify(modelTable(path.join(out, 'after'))) !== JSON.stringify(report.modelBank)) throw Error('Frozen model/map bank changed');
  const vite = path.join(root, 'node_modules/.bin/vite');
  for (const phase of ['before', 'after']) {
    const phaseRoot = path.join(out, phase);
    const dist = path.join(phaseRoot, 'dist');
    if (fs.existsSync(dist)) throw Error(`Refusing to rebuild nonfresh phase ${dist}`);
    execFileSync(vite, ['build'], { cwd: phaseRoot, stdio: 'inherit', env: { ...process.env, VERCEL_GIT_COMMIT_SHA: report.head } });
    const catalog = JSON.parse(fs.readFileSync(path.join(dist, 'model-catalog.json'), 'utf8')) as ReturnType<typeof modelTable>;
    if (JSON.stringify(catalog) !== JSON.stringify(report.modelBank)) throw Error(`${phase} emitted a changed catalog`);
    const postHashes = fileHashes(phaseRoot);
    const entries = fs.readdirSync(path.join(dist, 'assets')).filter(name => /^index-.+\.js$/.test(name));
    const entry = entries.map(name => ({ name, bytes: fs.statSync(path.join(dist, 'assets', name)).size,
      sha256: sha(fs.readFileSync(path.join(dist, 'assets', name))) }));
    const generated = Object.fromEntries(['src/boot/plan.generated.ts', 'src/render/hero/models.generated.ts']
      .map(name => [name, postHashes[name]]));
    fs.writeFileSync(path.join(out, `${phase}-build.json`), JSON.stringify({ phase, dist, entry,
      catalogSha256: sha(fs.readFileSync(path.join(dist, 'model-catalog.json'))),
      postBuildSourceSha256: fingerprint(postHashes), generated, sourceHashes: postHashes }, null, 2) + '\n');
  }
  console.log(JSON.stringify({ out, status: 'built-private-pair; visual/ride approval pending' }));
}
