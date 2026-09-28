import { chromium } from 'playwright';
import { execFileSync } from 'node:child_process';
import fs from 'node:fs/promises';
import path from 'node:path';
import sharp from 'sharp';

// Load the exact pre-harbor commit through Vite so both captures receive the
// same camera, GLB, viewport, rendering stack and input. Temporary sources are
// removed after capture and never become part of the standalone prototype.
const root=path.resolve('prototypes/world-map-b');
const out=path.resolve('docs/evidence/world-map-b');
const legacyJs=path.join(root,'__harbor-before.js');
const legacyHtml=path.join(root,'__harbor-before.html');
const legacyGlb=path.join(root,'assets','__baseline-terrain.glb');
const angles=[['front',.01],['three-quarter',-.68],['reverse',2.88]];
await fs.mkdir(out,{recursive:true});
const old=execFileSync('git',['show','3255b375:prototypes/world-map-b/main.js'],{encoding:'utf8'});
const oldTerrain=execFileSync('git',['show','3255b375:prototypes/world-map-b/assets/sculpted-terrain.glb'],{maxBuffer:16*1024*1024});
const html=await fs.readFile(path.join(root,'index.html'),'utf8');
await fs.writeFile(legacyJs,old.replace('./assets/sculpted-terrain.glb','./assets/__baseline-terrain.glb'));
await fs.writeFile(legacyGlb,oldTerrain);
await fs.writeFile(legacyHtml,html.replace('src="./main.js"','src="./__harbor-before.js"'));
let browser;
const results=[];
try{
 browser=await chromium.launch({headless:true,args:['--mute-audio','--use-gl=angle','--use-angle=swiftshader']});
 for(const [label,url] of [['before','/__harbor-before.html?art=1'],['after','/?art=1']]){
  const context=await browser.newContext({viewport:{width:844,height:390},deviceScaleFactor:1});
  const page=await context.newPage(),errors=[];
  page.on('pageerror',e=>errors.push(String(e)));
  const started=performance.now();
  await page.goto('http://127.0.0.1:5187'+url,{waitUntil:'networkidle'});
  await page.waitForFunction(()=>globalThis.__mapB?.getState().terrainReady&&globalThis.__mapB?.getState().towers===12,{timeout:30000});
  const readyMs=Math.round(performance.now()-started);
  for(const [name,azimuth] of angles){
   await page.evaluate(a=>globalThis.__mapB.setView(a,1.01,20),azimuth);
   await page.waitForTimeout(950);
   await page.screenshot({path:path.join(out,`harbor-${label}-${name}.png`)});
  }
  results.push({label,readyMs,errors,views:angles.map(([name])=>name)});
  await context.close();
 }
 // Pair frames after identical actual pointer moves, waiting for each camera
 // to reach the same angle. Independent browser video clocks cannot be stacked
 // reliably because GLB load and SwiftShader frame times differ.
 const pairContexts=await Promise.all([0,1].map(()=>browser.newContext({viewport:{width:844,height:390},deviceScaleFactor:1})));
 const pairPages=await Promise.all(pairContexts.map(c=>c.newPage()));
 const pairErrors=[[],[]];
 pairPages.forEach((page,i)=>page.on('pageerror',e=>pairErrors[i].push(String(e))));
 await Promise.all(pairPages.map((page,i)=>page.goto('http://127.0.0.1:5187'+(i?'/':'/__harbor-before.html'),{waitUntil:'networkidle'})));
 await Promise.all(pairPages.map(page=>page.waitForFunction(()=>globalThis.__mapB?.getState().terrainReady&&globalThis.__mapB?.getState().towers===12,{timeout:30000})));
 await Promise.all(pairPages.map(async page=>{await page.mouse.move(650,200);await page.mouse.down();}));
 const frames=path.join(out,'__harbor-matched-frames');
 await fs.mkdir(frames,{recursive:true});
 let maxAzimuthDelta=0;
 try{
  for(let i=0;i<=36;i++){
   if(i)await Promise.all(pairPages.map(page=>page.mouse.move(650-i*15,200+Math.sin(i/4)*8)));
   const expected=.01+i*.09;
   await Promise.all(pairPages.map(page=>page.waitForFunction(a=>Math.abs(globalThis.__mapB.getState().azimuth-a)<.012,expected,{timeout:6000})));
   const azimuths=await Promise.all(pairPages.map(page=>page.evaluate(()=>globalThis.__mapB.getState().azimuth)));
   maxAzimuthDelta=Math.max(maxAzimuthDelta,Math.abs(azimuths[0]-azimuths[1]));
   const [left,right]=await Promise.all(pairPages.map(page=>page.screenshot()));
   await sharp({create:{width:1688,height:390,channels:3,background:'#181614'}})
    .composite([{input:left,left:0,top:0},{input:right,left:844,top:0}])
    .png().toFile(path.join(frames,`frame-${String(i).padStart(3,'0')}.png`));
  }
  await Promise.all(pairPages.map(page=>page.mouse.up()));
  execFileSync('ffmpeg',['-y','-loglevel','error','-framerate','6','-i',path.join(frames,'frame-%03d.png'),
   '-an','-c:v','libx264','-crf','22','-pix_fmt','yuv420p',path.join(out,'harbor-before-after-orbit.mp4')]);
 }finally{
  await Promise.all(pairContexts.map(c=>c.close()));
  await fs.rm(frames,{recursive:true,force:true});
 }
 results.push({label:'matched-played-orbit',frames:37,maxAzimuthDelta,errors:pairErrors.flat(),video:'harbor-before-after-orbit.mp4'});
 // One genuinely played orbit and a full tower click pass at the phone ratio.
 const context=await browser.newContext({viewport:{width:844,height:390},deviceScaleFactor:1,recordVideo:{dir:out,size:{width:844,height:390}}});
 const page=await context.newPage(),errors=[];
 page.on('pageerror',e=>errors.push(String(e)));
 await page.goto('http://127.0.0.1:5187/',{waitUntil:'networkidle'});
 await page.waitForFunction(()=>globalThis.__mapB?.getState().terrainReady&&globalThis.__mapB?.getState().towers===12,{timeout:30000});
 await page.waitForTimeout(600);
 await page.mouse.move(650,200);await page.mouse.down();
 for(let i=0;i<105;i++){
  await page.mouse.move(650-i*5.1,200+Math.sin(i/14)*9);
  await page.waitForTimeout(32);
 }
 await page.mouse.up();
 await page.waitForTimeout(500);
 await page.evaluate(()=>globalThis.__mapB.resetView());
 await page.waitForTimeout(900);
 const selected=[];
 for(let i=0;i<12;i++){
  const p=await page.evaluate(i=>globalThis.__mapB.stageScreenPosition(i),i);
  await page.mouse.click(p.x,p.y);
  const actual=await page.evaluate(()=>globalThis.__mapB.getState().selected);
  selected.push(actual);
  if(actual!==i+1)throw new Error(`tower ${i+1} selected ${actual}`);
  await page.locator('#card-close').click();
  await page.waitForTimeout(430);
 }
 const video=await page.video().path();
 await context.close();
 await fs.rename(video,path.join(out,'harbor-after-interaction.webm'));
 results.push({label:'played-after',errors,selected,video:'harbor-after-interaction.webm'});
 const rows=[];
 for(const [name] of angles){
  const left=await fs.readFile(path.join(out,`harbor-before-${name}.png`));
  const right=await fs.readFile(path.join(out,`harbor-after-${name}.png`));
  rows.push(await sharp({create:{width:1688,height:390,channels:3,background:'#181614'}})
   .composite([{input:left,left:0,top:0},{input:right,left:844,top:0}]).jpeg({quality:88}).toBuffer());
 }
 await sharp({create:{width:1688,height:1170,channels:3,background:'#181614'}})
  .composite(rows.map((input,i)=>({input,left:0,top:i*390}))).jpeg({quality:89})
  .toFile(path.join(out,'harbor-before-after.jpg'));
 await fs.writeFile(path.join(out,'harbor-pass.json'),JSON.stringify({viewport:'844x390',silent:true,baselineCommit:'3255b375',angles,results},null,2));
 if(results.some(r=>r.errors?.length||r.inputs?.some(input=>input.errors.length)))throw new Error(JSON.stringify(results));
 console.log(JSON.stringify(results));
}finally{
 if(browser)await browser.close();
 await fs.rm(legacyJs,{force:true});
 await fs.rm(legacyHtml,{force:true});
 await fs.rm(legacyGlb,{force:true});
}
