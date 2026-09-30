/** Freeze one current application/model bank, then prepare an isolated C1 art A/B.
 *
 * From the repository root:
 *   pnpm exec tsx prototypes/coast-surface-frontage-v3/prepare-pair.mts /tmp/rockhop-coast-v3-pair
 *
 * This command prepares sources only. It never builds, edits src/public, or uses
 * the shared GPU lane. The parent may later build each private root with
 * `node_modules/.bin/vite build --config pair.config.ts` from that root.
 */
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { createHash } from 'node:crypto';
import { execFileSync } from 'node:child_process';

const repo = fs.realpathSync(path.resolve(import.meta.dirname, '../..'));
const requestedOutput = path.resolve(process.argv[2] ?? path.join(os.tmpdir(), 'rockhop-coast-v3-pair'));
const prototype = path.join(repo, 'prototypes/coast-surface-frontage-v3');
if (![os.tmpdir(), '/tmp', '/private/tmp'].some(temp => requestedOutput.startsWith(path.resolve(temp) + path.sep)))
  throw new Error(`Pair output must be under a temporary directory`);
if (fs.existsSync(requestedOutput)) throw new Error(`Use a new output directory: ${requestedOutput}`);
fs.mkdirSync(requestedOutput,{recursive:false});
// macOS resolves /tmp to /private/tmp. Vite and Rollup use the canonical ID,
// so every phase/config/load override must use that same physical root.
const output = fs.realpathSync(requestedOutput);
const sha = (bytes: Buffer | string): string => createHash('sha256').update(bytes).digest('hex');
const relativeFiles = (directory: string): string[] => {
  const found: string[] = [];
  const visit = (folder: string): void => {
    for (const item of fs.readdirSync(folder, { withFileTypes: true }).sort((a,b) => a.name.localeCompare(b.name))) {
      const full = path.join(folder, item.name);
      if (item.isDirectory()) visit(full);
      else if (item.isFile()) found.push(path.relative(directory, full).replaceAll(path.sep, '/'));
      else throw new Error(`Unsupported source entry: ${full}`);
    }
  };
  visit(directory);
  return found;
};
const inventory = (folder: string): Record<string,string> => Object.fromEntries(
  relativeFiles(folder).map(file => [file, sha(fs.readFileSync(path.join(folder,file)))]));
const same = (a: unknown, b: unknown): boolean => JSON.stringify(a) === JSON.stringify(b);
const copy = (from: string, into: string): void => fs.cpSync(from, into, {recursive:true, force:false, errorOnExist:true});
const staged: Record<string,string> = {
  'models/course-kits/coast-frontage/coast-frontage.glb': 'coast-frontage.glb',
  'models/course-kits/coast-frontage/coast-frontage-lod.glb': 'coast-frontage-lod.glb',
  ...Object.fromEntries(['coast','frontage'].flatMap(family => ['albedo','normal','arm'].map(channel =>
    [`models/course-kits/coast-frontage/${family}-${channel}.phone.webp`, `${family}-${channel}.phone.webp`]))),
};
for (const channel of ['albedo','normal','arm']) for (const surface of ['quay-top','quay-wall','tidal-ground'])
  staged[`models/course-kits/coast-ground/${surface}-${channel}.phone.webp`] = `${surface}-${channel}.phone.webp`;

const pinned = JSON.parse(fs.readFileSync(path.join(prototype,'source-pins.json'),'utf8')) as Record<string,string>;
for (const [file, digest] of Object.entries(pinned)) {
  const actual = sha(fs.readFileSync(path.join(repo,file)));
  if (actual !== digest) throw new Error(`Pinned integration source changed: ${file} ${actual} != ${digest}`);
}
const sourceBefore = inventory(path.join(repo,'src'));
const publicBefore = inventory(path.join(repo,'public'));
const worldmapBefore = inventory(path.join(repo,'assets/worldmap'));
const harnessLibBefore = inventory(path.join(repo,'harness/lib'));
const harnessTypeFile = 'harness/gate/device-rows.ts';
const harnessTypeSHA = sha(fs.readFileSync(path.join(repo,harnessTypeFile)));
const configFiles = ['index.html','vite.config.ts','package.json','tsconfig.json','vitest.config.ts'];
const configBefore = Object.fromEntries(configFiles.map(file => [file,sha(fs.readFileSync(path.join(repo,file)))]));
const head = execFileSync('git',['rev-parse','HEAD'],{cwd:repo,encoding:'utf8'}).trim();
const frozen = path.join(output,'.frozen');
fs.mkdirSync(frozen,{recursive:true});
copy(path.join(repo,'src'),path.join(frozen,'src'));
copy(path.join(repo,'public'),path.join(frozen,'public'));
copy(path.join(repo,'assets/worldmap'),path.join(frozen,'assets/worldmap'));
copy(path.join(repo,'harness/lib'),path.join(frozen,'harness/lib'));
fs.mkdirSync(path.join(frozen,'harness/gate'),{recursive:true});
fs.copyFileSync(path.join(repo,harnessTypeFile),path.join(frozen,harnessTypeFile));
for (const file of configFiles) fs.copyFileSync(path.join(repo,file),path.join(frozen,file));
if (!same(sourceBefore,inventory(path.join(repo,'src'))) || !same(publicBefore,inventory(path.join(repo,'public'))) ||
    !same(worldmapBefore,inventory(path.join(repo,'assets/worldmap'))) ||
    !same(harnessLibBefore,inventory(path.join(repo,'harness/lib'))) ||
    harnessTypeSHA!==sha(fs.readFileSync(path.join(repo,harnessTypeFile))) ||
    !same(configBefore,Object.fromEntries(configFiles.map(file => [file,sha(fs.readFileSync(path.join(repo,file)))]))))
  throw new Error('Live source/public changed during freeze; discard this output and prepare again');

// Stage the *same* asset super-bank into the one frozen input before phase split.
// The baseline still requests the accepted Coast bank; these extra catalog bytes
// are unused until the after source opts into them.
for (const [target,name] of Object.entries(staged)) {
  const from = target.includes('/coast-ground/')
    ? path.join(repo,'assets/blender/course-kits/coast-ground/delivery',name)
    : path.join(repo,'assets/blender/course-kits/coast-frontage/delivery',name);
  const into = path.join(frozen,'public',target);
  if (!fs.existsSync(from)) throw new Error(`Missing candidate asset: ${from}`);
  fs.mkdirSync(path.dirname(into),{recursive:true});
  fs.copyFileSync(from,into);
}
const bank = inventory(path.join(frozen,'public/models'));

const overrideFiles = Object.keys(pinned);
const makeConfig = (phase: 'before' | 'after'): string => `import fs from 'node:fs';\nimport path from 'node:path';\nimport { mergeConfig, type Plugin } from 'vite';\nimport base from './vite.config';\nconst files = new Set(${JSON.stringify(overrideFiles)}.map(file => path.resolve(file)));\nconst frozenSource: Plugin = {\n  name:'rockhop:coast-v3-frozen-${phase}', enforce:'pre',\n  load(id) { const file=path.resolve(id.split('?')[0]!); return files.has(file) ? fs.readFileSync(file,'utf8') : null; },\n};\nexport default mergeConfig(base, { plugins:[frozenSource] });\n`;
for (const phase of ['before','after'] as const) {
  const root = path.join(output,phase);
  copy(frozen,root);
  fs.symlinkSync(path.join(repo,'node_modules'),path.join(root,'node_modules'),'dir');
  fs.writeFileSync(path.join(root,'pair.config.ts'),makeConfig(phase));
  if (phase === 'after') execFileSync('git',['apply','--unidiff-zero',path.join(prototype,'runtime.patch')],{cwd:root,stdio:'pipe'});
  if (!same(bank,inventory(path.join(root,'public/models')))) throw new Error(`${phase} model bank drifted`);
}
const changed = Object.fromEntries(overrideFiles.map(file => [file,{
  before:sha(fs.readFileSync(path.join(output,'before',file))),
  after:sha(fs.readFileSync(path.join(output,'after',file))),
}]));
const provenance = {
  status:'prepared-source-only; no Vite build, browser replay or visual acceptance',
  head,
  patchSHA256:sha(fs.readFileSync(path.join(prototype,'runtime.patch'))),
  sourceInventorySHA256:sha(JSON.stringify(sourceBefore)),
  harnessLibraryInventorySHA256:sha(JSON.stringify(harnessLibBefore)),
  harnessTypeSHA256:harnessTypeSHA,
  publicInventorySHA256:sha(JSON.stringify(publicBefore)),
  worldmapInventorySHA256:sha(JSON.stringify(worldmapBefore)),
  frozenBankInventorySHA256:sha(JSON.stringify(bank)),
  frozenModelFiles:Object.keys(bank).length,
  stagedCandidateFiles:Object.fromEntries(Object.keys(staged).sort().map(file=>[file,bank[file.replace(/^models\//,'')]])),
  sourceOverrides:changed,
  budget:'Unmodified vite.config.ts enforces 700 KiB gzip player JS; an over-budget private build is a failed gate.',
};
fs.writeFileSync(path.join(output,'pair-inputs.json'),JSON.stringify(provenance,null,2)+'\n');
console.log(JSON.stringify({output,head,sourceFiles:Object.keys(sourceBefore).length,modelFiles:Object.keys(bank).length,
  bankSHA256:provenance.frozenBankInventorySHA256,sourceOverrides:changed},null,2));
