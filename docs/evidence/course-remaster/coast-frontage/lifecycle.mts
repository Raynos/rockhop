/** Frozen runtime failure/late-load proof; instrumentation exists only in the headless page. */
import { writeFileSync,readFileSync,mkdirSync } from 'node:fs';
import path from 'node:path';
import { createHash } from 'node:crypto';
import { preview } from 'vite';
import { launchBrowser } from '../../../../harness/lib/browser';
import { openGame } from '../../../../harness/lib/hook';
import { frozenSource } from '../../../../assets/blender/course-kits/alpine-trees/frozen-source.mts';
import type * as THREE from 'three';
interface RuntimeProof { fallbacks: THREE.Group[]; owners: THREE.Group[]; geometryDisposals: number; textureDisposals: number }

const [distDir,output]=process.argv.slice(2);
if(!distDir||!output||process.env.TRIALS_BROWSER_BACKEND!=='metal')throw Error('Require Metal and <frozen-dist> <output.json>');
const sha=JSON.parse(readFileSync(path.join(distDir,'version.json'),'utf8')).sha as string;
const entryPath=readFileSync(path.join(distDir,'index.html'),'utf8').match(/data-entry="([^"]+)"/)![1]!;
const index=createHash('sha256').update(readFileSync(path.join(distDir,entryPath))).digest('hex');
const previewServer=await preview({root:process.cwd(),configFile:path.resolve('vite.config.ts'),logLevel:'warn',build:{outDir:path.resolve(distDir)},preview:{host:'127.0.0.1',port:0}});
const url=previewServer.resolvedUrls!.local[0]!;
mkdirSync(path.dirname(output),{recursive:true});
const source=await frozenSource(url,sha,index);
const entry=await fetch(source.indexUrl).then(r=>r.text());
const threePath=entry.match(/\.\/three-[\w-]+\.js/)?.[0];
if(!threePath) throw new Error('Cannot locate frozen Three module');
const threeURL=new URL(threePath,source.indexUrl).href;
const results=[];
for(const mode of ['missing-map','late-switch']) {
  const browser=await launchBrowser({width:852,height:392});
  try {
    const page=browser.page,errors:string[]=[],warnings:string[]=[],requests:string[]=[],release:Array<()=>void>=[];
    let holding=true;
    page.on('pageerror',e=>errors.push(e.message));
    page.on('console',m=>{if(m.type()==='warning'||m.type()==='error') warnings.push(m.text());});
    await openGame(page,url);
    await page.evaluate(async moduleURL=>{
      const mod=await import(moduleURL);
      const object=Object.values(mod).find(v=>typeof v==='function'&&Object.hasOwn(v.prototype,'getObjectByName')) as {prototype:THREE.Object3D};
      const geometry=Object.values(mod).find(v=>typeof v==='function'&&Object.hasOwn(v.prototype,'setAttribute')) as {prototype:THREE.BufferGeometry};
      const texture=Object.values(mod).find(v=>typeof v==='function'&&Object.hasOwn(v.prototype,'transformUv')) as {prototype:THREE.Texture};
      const proof:RuntimeProof={fallbacks:[],owners:[],geometryDisposals:0,textureDisposals:0};
      (window as unknown as {__coastProof:RuntimeProof}).__coastProof=proof;
      const add=object.prototype.add;
      object.prototype.add=function(...items:THREE.Object3D[]) {
        for(const item of items) {
          if(item.name==='c1-original-harbor-fallback') proof.fallbacks.push(item as THREE.Group);
          if(item.name==='course-owned-assets') proof.owners.push(item as THREE.Group);
        }
        return add.apply(this,items);
      };
      const disposeGeometry=geometry.prototype.dispose,disposeTexture=texture.prototype.dispose;
      geometry.prototype.dispose=function(){proof.geometryDisposals++;return disposeGeometry.call(this);};
      texture.prototype.dispose=function(){proof.textureDisposals++;return disposeTexture.call(this);};
    },threeURL);
    await page.route(/\/models\/.*(?:frontage-albedo[^/]*\.webp|coast-frontage[^/]*\.glb)$/,
      async route=>{
        const request=route.request().url();
        if(mode==='missing-map'&&!request.endsWith('.webp')) return route.continue();
        if(mode==='late-switch'&&!request.endsWith('.glb')) return route.continue();
        requests.push(request);
        if(mode==='missing-map') return route.abort('failed');
        if(!holding) return route.continue();
        await new Promise<void>(resolve=>release.push(resolve));
        await route.continue();
      });
    await page.evaluate(()=>{const h=window.__rockhop!;h.setQuality('low');void h.loadTrack('c1-low-tide',341352973);});
    if(mode==='late-switch') {
      for(let i=0;i<100&&!requests.length;i++) await page.waitForTimeout(50);
      if(!requests.length) throw new Error('No Coast GLB request held');
      await page.evaluate(()=>{void window.__rockhop!.loadTrack('d1-dust-devil',1);});
    }
    await page.waitForFunction(()=>window.__rockhop!.info().render.entering===false,undefined,{timeout:30000});
    const snapshot=()=>page.evaluate(()=>{
      window.__rockhop!.render(false);
      const p=(window as unknown as {__coastProof:RuntimeProof}).__coastProof;
      return {info:window.__rockhop!.info(),stats:window.__rockhop!.stats(),
        fallbacks:p.fallbacks.map(g=>({visible:g.visible,attached:!!g.parent,children:g.children.length,counts:g.children.map(m=>({name:m.name,count:(m as THREE.InstancedMesh).count}))})),
        owners:p.owners.map(g=>({attached:!!g.parent,children:g.children.length})),
        geometryDisposals:p.geometryDisposals,textureDisposals:p.textureDisposals};
    });
    const before=await snapshot();
    if(mode==='late-switch') {
      holding=false;for(const done of release) done();
      await page.waitForFunction(()=> (window as unknown as {__coastProof:RuntimeProof}).__coastProof.geometryDisposals>0);
      await page.waitForTimeout(2500);
    }
    const after=await snapshot();
    const render=after.info.render as {courseAssetsMounted?:number};
    const pass=errors.length===0&&requests.length>0&&(mode==='missing-map'
      ?render.courseAssetsMounted===1&&after.fallbacks.at(-1)?.visible&&after.fallbacks.at(-1)!.children>0
      :after.info.trackId==='d1-dust-devil'&&render.courseAssetsMounted===0&&after.owners.every(o=>o.children===0)&&after.geometryDisposals>before.geometryDisposals&&after.stats.texturesMB<=before.stats.texturesMB+.01);
    results.push({mode,pass,requests,errors,warnings,before,after});
    console.log(mode,pass,requests.length,render.courseAssetsMounted);
  } finally {await browser.close();}
}
const report={source,afterSource:await frozenSource(url,sha,index),backend:'metal',results};
writeFileSync(output,JSON.stringify(report,null,2)+'\n');
await new Promise<void>((resolve,reject)=>previewServer.httpServer.close(error=>error?reject(error):resolve()));
if(results.some(r=>!r.pass)) process.exitCode=1;
