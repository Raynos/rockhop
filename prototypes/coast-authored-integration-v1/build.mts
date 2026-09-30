/** Frozen actual-game baseline/candidate pair with one immutable model bank.
 * No runtime selector or public/models replacement. Use from repository root:
 * pnpm exec tsx prototypes/coast-authored-integration-v1/build.mts /tmp/PAIR
 */
import fs from 'node:fs';
import path from 'node:path';
import { execFileSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { build, type Plugin } from 'vite';
import { readModelCatalog, readModelResources } from '../../src/boot/model-catalog';

const root = process.cwd();
const out = path.resolve(process.argv[2] ?? 'harness/out/coast-authored-pair');
const runtimePatch = path.resolve(process.argv[3] ?? 'prototypes/coast-authored-integration-v1/runtime.patch');
if (fs.existsSync(out)) throw Error('Use a fresh pair output directory');
const snapshot = path.join(out, '.inputs');
fs.mkdirSync(snapshot, {recursive:true});
fs.cpSync(path.join(root,'public/models'),path.join(snapshot,'models'),{recursive:true});
fs.cpSync(path.join(root,'prototypes/coast-authored-integration-v1/public/models'),path.join(snapshot,'models'),{recursive:true});
const biomePath = path.join(root,'src/render/world/biomeKit.ts');
const liveBiome = fs.readFileSync(biomePath,'utf8');
const baselineRevision = process.argv[4] ?? 'bdf002fa';
const before = execFileSync('git',['show',`${baselineRevision}:src/render/world/biomeKit.ts`],{cwd:root,encoding:'utf8'});
const privateBiome = path.join(snapshot,'src/render/world/biomeKit.ts');
fs.mkdirSync(path.dirname(privateBiome),{recursive:true});fs.writeFileSync(privateBiome,before);
execFileSync('git',['apply',runtimePatch],{cwd:snapshot});
const after = fs.readFileSync(privateBiome,'utf8');
const assets = readModelCatalog(snapshot), resources = readModelResources(snapshot);
const table = (bank: typeof assets) => Object.fromEntries(bank.map(a=>[a.logical,{url:a.url,bytes:a.bytes.length,sha256:a.sha256}]));
const generated = `export const MODEL_ASSETS = ${JSON.stringify(table(assets))} as const;\nexport const MODEL_RESOURCES = ${JSON.stringify(table(resources))} as const;\n`;
const sha=(s:Buffer|string)=>createHash('sha256').update(s).digest('hex');
const catalog = {models:assets.map(a=>({...table([a])[a.logical],logical:a.logical})),resources:resources.map(a=>({...table([a])[a.logical],logical:a.logical}))};
for (const [phase,source] of [['before',before],['after',after]] as const) {
  const plugin:Plugin={
    name:`rockhop:private-coast-${phase}`,enforce:'pre',
    load(id) {
      if(id===biomePath)return source;
      if(id===path.join(root,'src/render/hero/models.generated.ts'))return generated;
      return null;
    },
    generateBundle(_options,bundle) {
      for(const a of [...assets,...resources]) if(!bundle[a.url]) this.emitFile({type:'asset',fileName:a.url,source:a.bytes});
      const current=bundle['model-catalog.json'];if(!current||current.type!=='asset')throw Error('Missing emitted model catalog');
      current.source=JSON.stringify(catalog,null,2)+'\n';

    },
  };
  const phaseOut=path.join(out,phase);
  await build({root,configFile:path.join(root,'vite.config.ts'),logLevel:'warn',plugins:[plugin],build:{outDir:phaseOut,emptyOutDir:false}});
  fs.writeFileSync(path.join(phaseOut,'coast-review.json'),JSON.stringify({phase,releaseBuild:false,biomeSourceSHA256:sha(source),modelBank:catalog,limits:'Private visual/performance review. Prototype model files are emitted but not added to the production offline pack.'},null,2)+'\n');
  for(const a of [...assets,...resources])if(sha(fs.readFileSync(path.join(phaseOut,a.url)))!==a.sha256)throw Error(`Changed emitted input ${a.logical}`);
  if(fs.readFileSync(biomePath,'utf8')!==liveBiome)throw Error('Production biome hook changed during private review build');
  console.log(JSON.stringify({phase,out:phaseOut,models:assets.length,resources:resources.length}));
}
fs.writeFileSync(path.join(out,'pair.json'),JSON.stringify({matchedModels:true,matchedResources:true,beforeBiomeSHA256:sha(before),afterBiomeSHA256:sha(after),catalog},null,2)+'\n');
