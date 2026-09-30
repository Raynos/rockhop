/** Private immutable S1–S3 comparison. No public asset or runtime hook mutation. */
import fs from 'node:fs';
import path from 'node:path';
import { createHash } from 'node:crypto';
import { execFileSync } from 'node:child_process';
import { build } from 'vite';

const repo = process.cwd();
const requestedOutput = path.resolve(process.argv[2] ?? 'harness/out/snowline-standard-v2');
if (fs.existsSync(requestedOutput)) throw new Error('Use a fresh output directory');
fs.mkdirSync(requestedOutput,{recursive:true});
// Rollup canonicalizes macOS /tmp. Config exact-ID transforms must match it.
const output = fs.realpathSync(requestedOutput);
const revision = execFileSync('git', ['rev-parse', 'HEAD'], {encoding:'utf8'}).trim();
const frozen = path.join(output, '.inputs');
fs.mkdirSync(frozen, {recursive:true});
for (const directory of ['src', 'public', 'assets/worldmap']) fs.cpSync(path.join(repo,directory),path.join(frozen,directory),{recursive:true});
for (const file of ['index.html','vite.config.ts','tsconfig.json','package.json']) fs.copyFileSync(path.join(repo,file),path.join(frozen,file));
fs.symlinkSync(path.join(repo,'node_modules'),path.join(frozen,'node_modules'),'dir');
const bank = path.join(frozen,'public/models/course-kits/snowline-standard');
fs.mkdirSync(bank,{recursive:true});
for (const [input, name] of [['snowline-standard-packed.glb','snowline-standard.glb'],['snowline-standard-lod-packed.glb','snowline-standard-lod.glb']]) {
  fs.copyFileSync(path.join(repo,'harness/fixtures/snowline-standard',input!),path.join(bank,name!));
}
const sha = (bytes:Buffer|string):string => createHash('sha256').update(bytes).digest('hex');
const hashTree = (directory:string):Record<string,string> => {
  const entries:Record<string,string>={};
  const walk = (current:string):void => {
    for(const entry of fs.readdirSync(current,{withFileTypes:true}).sort((a,b)=>a.name.localeCompare(b.name,'en'))) {
      const file=path.join(current,entry.name);
      if(entry.isDirectory())walk(file);else if(entry.isFile())entries[path.relative(directory,file)]=sha(fs.readFileSync(file));
    }
  };
  walk(directory);return entries;
};
const beforeSource = hashTree(path.join(frozen,'src'));
const modelSources = hashTree(path.join(frozen,'public/models'));
for (const phase of ['before','after'] as const) {
  const sourceRoot=path.join(output,`${phase}-source`);
  fs.mkdirSync(sourceRoot,{recursive:true});
  for(const directory of ['src','public','assets/worldmap'])fs.cpSync(path.join(frozen,directory),path.join(sourceRoot,directory),{recursive:true});
  for(const file of ['index.html','vite.config.ts','tsconfig.json','package.json'])fs.copyFileSync(path.join(frozen,file),path.join(sourceRoot,file));
  fs.symlinkSync(path.join(repo,'node_modules'),path.join(sourceRoot,'node_modules'),'dir');
  if(phase==='after') {
    const file=path.join(sourceRoot,'src/render/world/biomeKit.ts');
    let source=fs.readFileSync(file,'utf8');
    const importAnchor="import { buildZoneKit, isZone, zoneGround } from './zones/zoneKit';";
    if(!source.includes(importAnchor))throw new Error('ZoneKit import anchor changed');
    source=source.replace(importAnchor,importAnchor+"\nimport { loadSnowlineStandard, snapshotSnowlineAnchors, SNOWLINE_AUTHORED_BATCHES } from './zones/snowlineStandard';");
    const mountAnchor='      meshes.push(...zk.meshes);';
    if(source.split(mountAnchor).length!==2)throw new Error('ZoneKit finalization anchor is ambiguous');
    const patch=fs.readFileSync(path.join(repo,'prototypes/snowline-standard-v1/biomeKit.patch'),'utf8');
    const block=patch.split('\n').filter(line=>line.startsWith('+')&&!line.startsWith('+++')&&!line.includes('import { loadSnowlineStandard')).map(line=>line.slice(1)).join('\n');
    source=source.replace(mountAnchor,block+'\n'+mountAnchor);
    fs.writeFileSync(file,source);
  }
  const sourceHashes=hashTree(path.join(sourceRoot,'src'));
  const changed=Object.keys(beforeSource).filter(file=>beforeSource[file]!==sourceHashes[file]);
  if(phase==='after'&&(changed.length!==1||changed[0]!=='render/world/biomeKit.ts'))throw new Error(`Unexpected source changes: ${changed}`);
  if(JSON.stringify(hashTree(path.join(sourceRoot,'public/models')))!==JSON.stringify(modelSources))throw new Error('Model sources changed between phases');
  const outDir=path.join(output,phase);
  // No nested git checkout: use the frozen revision fallback while compiling
  // from this temporary source directory, never the changing main stamp.
  const previousSha=process.env.VERCEL_GIT_COMMIT_SHA;
  process.env.VERCEL_GIT_COMMIT_SHA=revision;process.chdir(sourceRoot);
  try { await build({root:sourceRoot,configFile:path.join(sourceRoot,'vite.config.ts'),logLevel:'warn',build:{outDir}}); }
  finally { process.chdir(repo);if(previousSha===undefined)delete process.env.VERCEL_GIT_COMMIT_SHA;else process.env.VERCEL_GIT_COMMIT_SHA=previousSha; }
  const html=fs.readFileSync(path.join(outDir,'index.html'),'utf8');
  const entry=/src="([^"]*assets\/index-[^"]+\.js)"/.exec(html)?.[1];
  if(!entry)throw new Error('Missing built app entry');
  const entrySHA256=sha(fs.readFileSync(path.resolve(outDir,entry)));
  const compiledSourceHashes=hashTree(path.join(sourceRoot,'src'));
  const catalog=JSON.parse(fs.readFileSync(path.join(outDir,'model-catalog.json'),'utf8'));
  fs.writeFileSync(path.join(outDir,'snowline-review.json'),JSON.stringify({phase,revision,sourceHashes,compiledSourceHashes,entry,entrySHA256,modelSources,catalog,limits:'Private source/model snapshot, not a release build or accepted course. Same assets exist in both phases; baseline does not decode the candidate.'},null,2)+'\n');
  console.log(JSON.stringify({phase,outDir,changed}));
}
const catalogs=['before','after'].map(phase=>JSON.parse(fs.readFileSync(path.join(output,phase,'model-catalog.json'),'utf8')));
if(JSON.stringify(catalogs[0])!==JSON.stringify(catalogs[1]))throw new Error('Emitted model/resource catalogs differ');
fs.writeFileSync(path.join(output,'pair.json'),JSON.stringify({revision,matchedModelResources:true,beforeSource,modelSources,intendedChanges:['src/render/world/biomeKit.ts'],limits:'Candidate source only. Full moving/fault/lifecycle/performance/device judgement remains required.'},null,2)+'\n');
