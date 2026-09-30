/** Parent-only opt-in build recipe. Nothing builds when imported. */
import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import { spawnSync } from 'node:child_process';
import { home, project, common, sha, verifySnapshot } from './prepare.mjs';
const phase = process.argv[2];
if (phase !== 'before' && phase !== 'after') throw new Error('Usage: node build.mjs before|after (parent after GPU lane release)');
if(fs.existsSync(path.join(home,'out',phase,'build.json'))) throw new Error('Refusing to replace an existing frozen phase build; use a new comparison snapshot');
const manifest = verifySnapshot();
// Canonical /private/tmp IDs matter: normal release/retired plugins compare exact paths.
const scratch = fs.realpathSync(fs.mkdtempSync(path.join(os.tmpdir(), `rockhop-s1-landing-sightline-v1-${phase}-`)));
// /tmp is outside Git: normal config git lookups fall back to the pinned SHA.
fs.cpSync(common, scratch, { recursive: true, filter: source => path.basename(source) !== 'node_modules' });
fs.symlinkSync(path.join(project, 'node_modules'), path.join(scratch, 'node_modules'), 'dir');
const overrideFiles = phase === 'after' ? Object.fromEntries(manifest.overrides.map(entry => [entry.file,
  fs.readFileSync(path.join(home, 'out/after', entry.file), 'utf8')])) : {};
const config = `import base from './vite.config';
import {defineConfig,mergeConfig,type Plugin} from 'vite';
import path from 'node:path';
const replacements:Record<string,string>=${JSON.stringify(overrideFiles)};
const trial:Plugin={name:'s1-landing-sightline-v1:two-source-overrides',enforce:'pre',
  load(id){const relative=path.relative(process.cwd(),id.split('?')[0]!).split(path.sep).join('/');return replacements[relative]??null;},
  generateBundle:{order:'post',handler(_options,bundle){const version=bundle['version.json'];if(version?.type==='asset')version.source=${JSON.stringify(JSON.stringify({ sha: manifest.head, build: manifest.head.slice(0, 7), time: manifest.capturedUTC }))};}}
};
export default defineConfig(mergeConfig(base,{define:{__BUILD_ID__:${JSON.stringify(JSON.stringify(manifest.head.slice(0, 7)))},__BUILD_TIME__:${JSON.stringify(JSON.stringify(manifest.capturedUTC.slice(0, 16).replace('T', ' ') + 'Z'))}},plugins:[trial]}));
`;
fs.writeFileSync(path.join(scratch, 'trial.config.mts'), config);
const result = spawnSync(process.execPath, [path.join(project, 'node_modules/vite/bin/vite.js'), 'build', '--config', 'trial.config.mts'], {
  cwd: scratch, encoding: 'utf8', maxBuffer: 16 * 1024 * 1024,
  env: { ...process.env, VERCEL_GIT_COMMIT_SHA: manifest.head, VITE_STORE: '0', VITE_STORE_DEBUG: '0' },
});
const dest = path.join(home, 'out', phase); fs.mkdirSync(dest, { recursive: true });
fs.writeFileSync(path.join(dest, 'build.log'), `${result.stdout ?? ''}\n${result.stderr ?? ''}`);
const generated = ['src/boot/plan.generated.ts', 'src/render/hero/models.generated.ts'].map(file => ({file,sha256:sha(fs.readFileSync(path.join(scratch,file)))}));
const report = { schema: 1, phase, status: result.status, scratch, sourceHEAD: manifest.head,
  snapshotManifestSHA256: sha(fs.readFileSync(path.join(home,'snapshot-manifest.json'))),
  prebuildAppSHA256: manifest.appSHA256, bankSHA256: manifest.bankSHA256,
  privateConfigSHA256: sha(config), overrides: phase === 'after' ? manifest.overrides : [], generated,
  budget: { playerGzipBytes: 700 * 1024, inlineRawBytes: 8 * 1024, normalGates: true },
  entry: null, indexSHA256: null, catalogSHA256: null, version: null,
  measuredPlayerGzipBytes: Number(`${result.stdout ?? ''}\n${result.stderr ?? ''}`.match(/bundle budget:[^\n]*\((\d+) B\)/)?.[1] ?? 0) || null };
if (result.status === 0) {
  const dist = path.join(scratch,'dist');
  const html = fs.readFileSync(path.join(dist,'index.html'),'utf8');
  const entry = html.match(/data-entry="([^"]+)"/)?.[1];
  if (!entry) throw new Error('Built loader is missing its data-entry');
  Object.assign(report, {entry,indexSHA256:sha(fs.readFileSync(path.join(dist,entry))),
    catalogSHA256:sha(fs.readFileSync(path.join(dist,'model-catalog.json'))),
    version:JSON.parse(fs.readFileSync(path.join(dist,'version.json'),'utf8'))});
  fs.cpSync(dist,path.join(dest,'dist'),{recursive:true});
  const other = path.join(home,'out',phase==='before'?'after':'before','build.json');
  if(fs.existsSync(other)) {
    const pair=JSON.parse(fs.readFileSync(other,'utf8'));
    if(pair.status===0&&(pair.catalogSHA256!==report.catalogSHA256||JSON.stringify(pair.generated)!==JSON.stringify(report.generated))) throw new Error('Paired model catalog/generated source differs');
  }
}
fs.writeFileSync(path.join(dest,'build.json'),JSON.stringify(report,null,2)+'\n');
console.info(JSON.stringify(report,null,2));
if(result.status!==0) process.exitCode=result.status??1;
