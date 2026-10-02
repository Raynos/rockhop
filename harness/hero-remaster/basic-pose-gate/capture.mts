/** Headless six-view exported motion evidence; canonical shared GPU lock required. */
import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import {spawnSync} from 'node:child_process';
import {createServer} from 'vite';
import {webkit} from 'playwright';
import type {PoseFixture} from './protocol';
const arg=(key:string)=>process.argv.find(a=>a.startsWith('--'+key+'='))?.slice(key.length+3);
const source=arg('source'),fixturePath=arg('fixture'),out=arg('out');assert(source&&fixturePath&&out);
assert(!fs.existsSync(out),'Freeze captures; fresh destination required');
const sha=(p:string)=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
const fixture:PoseFixture=JSON.parse(fs.readFileSync(fixturePath,'utf8'));
const sourceHash=sha(source),fixtureHash=sha(fixturePath);
fs.mkdirSync(path.join(out,'frames'),{recursive:true});
const report:{sourceSHA256:string;fixtureSHA256:string;fps:number;families:string[];frames:unknown[];errors:string[];loaded:string[];failure?:string;limits:string[]}={sourceSHA256:sourceHash,fixtureSHA256:fixtureHash,fps:fixture.fps,families:fixture.families,frames:[],errors:[],loaded:[],limits:['Authored studio stress fixture; not actual Garage/gameplay/Blender equivalence.','No continuous collision/contact/device acceptance.',`Stored ${fixture.fps}fps / ${fixture.families.length} families; finite samples, not continuous-time certification.`]};
const server=await createServer({configFile:false,root:process.cwd(),server:{host:'127.0.0.1',port:0},logLevel:'warn',plugins:[{name:'frozen-pose-fixture',configureServer(vite){vite.middlewares.use((req,res,next)=>{
 const file=req.url==='/fixture-source.glb'?source:req.url==='/pose-fixture.json'?fixturePath:null;
 if(req.url==='/fixture-source-meta.json') {
  res.setHeader('Content-Type','application/json');
  res.end(JSON.stringify({sourceSHA256:sourceHash}));return;
 }
 if(!file)return next();res.setHeader('Content-Type',file===source?'model/gltf-binary':'application/json');res.end(fs.readFileSync(file));
});}}]});
await server.listen();const browser=await webkit.launch({headless:true});
const page=await browser.newPage({viewport:{width:1440,height:960},deviceScaleFactor:1});
page.on('pageerror',e=>report.errors.push(e.message));
const responses:Promise<void>[]=[];
page.on('response',r=>{if(r.url().endsWith('/fixture-source.glb'))responses.push(r.body().then(b=>{assert.equal(r.status(),200);report.loaded.push(crypto.createHash('sha256').update(b).digest('hex'));}));});
try{
 await page.goto(server.resolvedUrls!.local[0]+'harness/hero-remaster/basic-pose-gate/studio.html');
 await page.waitForFunction(()=>window.__basicPoseGate?.ready,null,{timeout:120000});
 assert(await page.evaluate(()=>navigator.webdriver),'Headless automation required');
 assert.equal(await page.evaluate(()=>window.__basicPoseGate!.sourceSHA256),sourceHash,'Displayed candidate identity mismatch');
 for(let i=0;i<fixture.frames.length;i++){
  const rec=await page.evaluate(index=>window.__basicPoseGate!.render(index),i);
  assert.equal(rec.family,fixture.frames[i]!.family);assert.equal(rec.frame,fixture.frames[i]!.frame);
  assert(rec.matrixError<1e-8);report.frames.push(rec);
  await page.screenshot({path:path.join(out,'frames',`${String(i).padStart(4,'0')}.png`)});
 }
 await Promise.all(responses);assert(report.loaded.includes(sourceHash));assert.deepEqual(report.errors,[]);
 assert.equal(sha(source),sourceHash);assert.equal(sha(fixturePath),fixtureHash);
 const ff=spawnSync('ffmpeg',['-v','error','-y','-framerate',String(fixture.fps),'-i',path.join(out,'frames/%04d.png'),'-c:v','libx264','-threads','2','-crf','19','-pix_fmt','yuv420p','-an','-movflags','+faststart',path.join(out,'basic-poses.mp4')],{encoding:'utf8'});assert.equal(ff.status,0,ff.stderr);
}catch(e){report.failure=e instanceof Error?e.message:String(e);process.exitCode=1;}
finally{await page.close();await browser.close();await server.close();fs.writeFileSync(path.join(out,'report.json'),JSON.stringify(report)+'\n');console.log(JSON.stringify({frames:report.frames.length,failure:report.failure,errors:report.errors}));}
