import fs from 'node:fs/promises';
import path from 'node:path';
import { chromium } from 'playwright';

// Silent, reproducible headless review. The video contains a dragged orbit and
// actual pointer taps on all twelve 3D flag hit meshes.
const out=path.resolve(process.env.ATLAS_OUT??'docs/evidence/world-map-c/polish-round');
const url=process.env.ATLAS_URL??'http://127.0.0.1:5178/';
await fs.mkdir(out,{recursive:true});
const browser=await chromium.launch({headless:true,args:['--mute-audio','--use-gl=angle','--use-angle=swiftshader']});
const context=await browser.newContext({viewport:{width:852,height:393},deviceScaleFactor:2,recordVideo:{dir:out,size:{width:852,height:393}}});
const page=await context.newPage();
const errors=[];
page.on('pageerror',error=>errors.push(error.message));
await page.goto(url,{waitUntil:'networkidle'});
await page.waitForFunction(()=>!!globalThis.__atlas&&globalThis.__atlas.renderer.info.render.triangles>0);
const angles=[['front',[2.5,20,32]],['three-quarter',[-20,20,25]],['reverse',[2.5,20,-32]]];
const angleStats=[];
for(const [name,pos] of angles){
 await page.evaluate(pos=>{
   const {camera,controls}=globalThis.__atlas;
   camera.position.set(pos[0],pos[1],pos[2]);controls.target.set(0,0,0);controls.update();
   globalThis.document.documentElement.classList.add('art-mode');
 },pos);
 await page.waitForTimeout(250);
 await page.screenshot({path:path.join(out,`${name}.png`)});
 angleStats.push(await page.evaluate(name=>({name,fps:globalThis.__atlas.fps,drawCalls:globalThis.__atlas.renderer.info.render.calls,triangles:globalThis.__atlas.renderer.info.render.triangles}),name));
}
await page.evaluate(()=>{
 globalThis.document.documentElement.classList.remove('art-mode');
 const {controls}=globalThis.__atlas;
 controls.reset();controls.update();
});
await page.mouse.move(690,190);
await page.mouse.down();
for(let i=0;i<=140;i++){
 await page.mouse.move(690-455*i/140,190+12*Math.sin(i/140*Math.PI*2),{steps:1});
 await page.waitForTimeout(27);
}
await page.mouse.up();
await page.waitForTimeout(750);
const taps=[];
for(let i=0;i<12;i++){
 await page.evaluate(()=>{
   globalThis.document.documentElement.classList.remove('focused');
   const {controls}=globalThis.__atlas;
   controls.reset();controls.update();
 });
 const point=await page.evaluate(i=>{
   const {camera,stages}=globalThis.__atlas;
   const world=stages[i].hit.getWorldPosition(camera.position.clone());world.project(camera);
   return {x:(world.x+1)*globalThis.innerWidth/2,y:(1-world.y)*globalThis.innerHeight/2};
 },i);
 await page.mouse.click(point.x,point.y);
 await page.waitForTimeout(760);
 const actual=await page.locator('#selection-title').textContent();
 const expected=String(i+1).padStart(2,'0');
 taps.push({stage:expected,selected:actual,point});
 if(!actual?.startsWith(expected))throw new Error(`tower ${expected} selected ${actual}`);
}
const stats=await page.evaluate(()=>({fps:globalThis.__atlas.fps,drawCalls:globalThis.__atlas.renderer.info.render.calls,triangles:globalThis.__atlas.renderer.info.render.triangles,viewport:[globalThis.innerWidth,globalThis.innerHeight],dpr:globalThis.devicePixelRatio}));
const video=await page.video().path();
await context.close();
await fs.rename(video,path.join(out,'played-orbit-and-12-taps.webm'));

const portrait=await browser.newPage({viewport:{width:393,height:852},deviceScaleFactor:2});
await portrait.goto(url,{waitUntil:'networkidle'});
await portrait.screenshot({path:path.join(out,'portrait-rotate.png')});
const rotateVisible=await portrait.locator('#rotate').isVisible();
await portrait.close();
await fs.writeFile(path.join(out,'measurements.json'),JSON.stringify({stats,angleStats,errors,taps,rotateVisible,angles:angles.map(([name,position])=>({name,position}))},null,2)+'\n');
await browser.close();
if(errors.length||!rotateVisible)throw new Error(`page errors: ${errors.join('; ')}; rotateVisible=${rotateVisible}`);
console.log(JSON.stringify({out,stats,angleStats,taps:taps.length,rotateVisible,errors}));
