/** One normal-build two-lap resource qualification. No player edits or timing measurements. */
/* oxlint-disable typescript/no-explicit-any -- existing headless renderer inspection handles. */
import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import { createHash } from 'node:crypto';
import { execFileSync } from 'node:child_process';
import { preview } from 'vite';
import { launchBrowser } from '../../harness/lib/browser';
import { openGame } from '../../harness/lib/hook';
import { frozenSource } from '../../assets/blender/course-kits/alpine-trees/frozen-source.mts';
const output=path.resolve(process.argv[2]??'prototypes/alpine-surface-rollout-v1/churn-proof.json');
if(process.env.TRIALS_BROWSER_BACKEND!=='metal')throw Error('Require silent Metal headless backend');
const frozen=process.argv[3]?fs.realpathSync(process.argv[3]):fs.realpathSync(fs.mkdtempSync(path.join(os.tmpdir(),'rockhop-alpine-course-churn-')));
if(!process.argv[3])fs.cpSync(path.resolve('dist'),frozen,{recursive:true});
const hash=(file:string)=>createHash('sha256').update(fs.readFileSync(file)).digest('hex');
const html=fs.readFileSync(path.join(frozen,'index.html'),'utf8'),entry=html.match(/data-entry="([^"]+)"/)![1]!;
const player=fs.readFileSync(path.join(frozen,entry),'utf8'),version=JSON.parse(fs.readFileSync(path.join(frozen,'version.json'),'utf8'));
const selectors=player.split('["a1-sawdust","a2-log-jam","a3-timberline"].includes(track.def.id)').length-1;
if(selectors!==3||player.includes('alpine-original-forest-fallback'))throw Error('Normal accepted surface-only build required');
const server=await preview({configFile:false,build:{outDir:frozen},preview:{host:'127.0.0.1',port:0,headers:{'Cross-Origin-Opener-Policy':'same-origin','Cross-Origin-Embedder-Policy':'require-corp'}},logLevel:'warn'});
const url=server.resolvedUrls!.local[0]!,browser=await launchBrowser({width:852,height:392}),page=browser.page;
const report:any={kind:'normal-course-entry-resource-churn',frozen,source:null,sharedHEAD:execFileSync('git',['rev-parse','HEAD'],{encoding:'utf8'}).trim(),
  sharedDirtyStatus:execFileSync('git',['status','--porcelain=v1'],{encoding:'utf8'}),normalSurfaceSelectors:selectors,
  normalCatalogSHA256:hash(path.join(frozen,'model-catalog.json')),backend:'metal',quality:'low',viewport:{width:852,height:392},timingBenchmark:false,rows:[],errors:[],warnings:[]};
page.on('pageerror',error=>report.errors.push(error.message));
page.on('console',message=>{if(['warning','error'].includes(message.type()))report.warnings.push(message.text());});
try {
  report.source=await frozenSource(url,version.sha,hash(path.join(frozen,entry)));
  await openGame(page,url);
  // TSX name helper for serialized harness callbacks only; no game source or clock change.
  await page.evaluate('globalThis.__name=(fn)=>fn');
  await page.evaluate(async()=>{
    const w=window as any,h=w.__rockhop,r=w.__render;
    h.resize(852,392,1);h.setQuality('low');await r.whenReady();
    // String-only registries never retain old Three resources or course owners.
    w.__churn={maps:new Map(),geometries:new Map()};
  });
  const courses=['a1-sawdust','a2-log-jam','a3-timberline','c1-low-tide','d1-dust-devil','s1-lift-line'];
  for(let lap=1;lap<=2;lap++)for(const course of courses) {
    const row=await page.evaluate(async({lap,course})=>{
      const w=window as any,h=w.__rockhop,r=w.__render,p=w.__churn;
      if(!await h.loadTrack(course))throw Error(`Unknown course ${course}`);
      await r.whenReady();h.skipCountdown();
      for(let i=0;i<3;i++){h.render(false);await new Promise<void>(done=>requestAnimationFrame(()=>done()));}
      r.finish();
      const geometryIds=new Set<string>(),canvasIds=new Set<string>(),owners:any[]=[];
      const register=(registry:Map<string,any>,resource:any,kind:string)=>{
        if(registry.has(resource.uuid))return;
        const uuid=resource.uuid;registry.set(uuid,{uuid,course,lap,kind,disposed:false});
        resource.addEventListener('dispose',()=>{registry.get(uuid).disposed=true;});
      };
      for(const root of [r.world?.group,r.ribbons?.group])root?.traverse((object:any)=>{
        if(object.geometry){geometryIds.add(object.geometry.uuid);register(p.geometries,object.geometry,'course-geometry');}
        const surface=object.name==='terrain'||object.name==='zone:lake'||/^zonedeck:(top|face):alpine:/.test(object.name);
        if(!surface||!course.startsWith('a'))return;
        for(const material of Array.isArray(object.material)?object.material:[object.material])for(const key of ['map','normalMap']){
          const texture=material?.[key];if(!texture?.isCanvasTexture||material.name)continue;
          canvasIds.add(texture.uuid);register(p.maps,texture,`${object.name}:${key}`);
        }
      });
      r.debug.scene.traverse((object:any)=>{if(object.name==='course-owned-assets')owners.push({uuid:object.uuid,children:object.children.length});});
      const priorUndisposed=(registry:Map<string,any>,active:Set<string>)=>[...registry.values()].filter(record=>!record.disposed&&!active.has(record.uuid));
      const gpu=r.debug.renderer.info,info=h.info(),gl=r.debug.renderer.getContext(),ext=gl.getExtension('WEBGL_debug_renderer_info');
      return {lap,course,quality:info.quality,render:info.render,renderer:String(gl.getParameter(ext?ext.UNMASKED_RENDERER_WEBGL:gl.RENDERER)),
        gpu:{geometries:gpu.memory.geometries,textures:gpu.memory.textures,programs:gpu.programs.length},owners,
        courseGeometryCount:geometryIds.size,ownedAlpineCanvasCount:canvasIds.size,
        retiredCanvasUndisposed:priorUndisposed(p.maps,canvasIds),retiredGeometryUndisposed:priorUndisposed(p.geometries,geometryIds),
        disposedCanvas:[...p.maps.values()].filter(record=>record.disposed).length,
        disposedGeometry:[...p.geometries.values()].filter(record=>record.disposed).length};
    },{lap,course});
    report.rows.push(row);console.log(lap,course,JSON.stringify(row.gpu),row.ownedAlpineCanvasCount,row.retiredCanvasUndisposed.length,row.retiredGeometryUndisposed.length);
  }
  report.secondLap=report.rows.slice(6).map((row:any,index:number)=>{
    const first=report.rows[index];return {course:row.course,delta:Object.fromEntries(['geometries','textures','programs'].map(key=>[key,row.gpu[key]-first.gpu[key]])),
      oldCanvasClear:row.retiredCanvasUndisposed.length===0,oldGeometryClear:row.retiredGeometryUndisposed.length===0};
  });
  report.afterSource=await frozenSource(url,version.sha,hash(path.join(frozen,entry)));
  report.pass=report.errors.length===0&&report.rows.every((row:any)=>/Metal/.test(row.renderer)&&row.quality==='low'&&row.retiredCanvasUndisposed.length===0&&row.retiredGeometryUndisposed.length===0)
    &&report.secondLap.every((row:any)=>Object.values(row.delta).every(value=>Number(value)<=0));
} catch(error) {report.failure=error instanceof Error?error.message:String(error);report.pass=false;}
finally {
  await browser.close();await new Promise<void>(resolve=>server.httpServer.close(()=>resolve()));
  fs.mkdirSync(path.dirname(output),{recursive:true});fs.writeFileSync(output,JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({output,pass:report.pass,failure:report.failure,secondLap:report.secondLap}));
  if(!report.pass)process.exitCode=1;
}
