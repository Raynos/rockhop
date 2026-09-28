import fs from 'node:fs/promises';
import path from 'node:path';
import { chromium } from 'playwright';

// Repeatable, silent phone-landscape review of the real interactive scene.
const out=path.resolve(process.env.ATLAS_OUT??'docs/evidence/world-map-c/fidelity-pass/after');
const url=process.env.ATLAS_URL??'http://127.0.0.1:5178/';
await fs.mkdir(out,{recursive:true});
const browser=await chromium.launch({headless:true,args:['--mute-audio','--use-gl=angle','--use-angle=swiftshader']});
const context=await browser.newContext({viewport:{width:852,height:393},deviceScaleFactor:2,recordVideo:{dir:out,size:{width:852,height:393}}});
const page=await context.newPage();
const captureStart=Date.now();
const errors=[];
page.on('pageerror',error=>errors.push(error.message));
await page.goto(url,{waitUntil:'networkidle'});
await page.waitForFunction(()=>!!globalThis.__atlas && globalThis.__atlas.renderer.info.render.triangles>0);
await page.waitForTimeout(700);

const angles=[
 ['front',[2.5,20,32]],
 ['three-quarter',[-20,20,25]],
 ['reverse',[2.5,20,-32]],
];
for(const [name,position] of angles){
 await page.evaluate(pos=>{
   const {camera,controls}=globalThis.__atlas;
   camera.position.set(pos[0],pos[1],pos[2]);controls.target.set(0,0,0);controls.update();
 },position);
 await page.waitForTimeout(180);
 await page.screenshot({path:path.join(out,`${name}.png`)});
}

// Play a full rotation using pointer input. The video captures moving mesh and
// occlusion, not a posed sequence of camera stills.
await page.evaluate(()=>{
 const {camera,controls}=globalThis.__atlas;
 camera.position.set(2.5,20,32);controls.target.set(0,0,0);controls.update();
});
await page.mouse.move(690,190);
const orbitStart=Date.now();
await page.mouse.down();
for(let i=0;i<=160;i++){
 await page.mouse.move(690-455*i/160,190+12*Math.sin(i/160*Math.PI*2),{steps:1});
 await page.waitForTimeout(35);
}
await page.mouse.up();
const orbitEnd=Date.now();
await page.waitForTimeout(800);

// Project actual 3D hit meshes, then test selection through real pointer taps.
for(const index of [7,11]){
 await page.evaluate(()=>{
   const {camera,controls}=globalThis.__atlas;
   camera.position.set(2.5,20,32);controls.target.set(0,0,0);controls.update();
 });
 await page.waitForTimeout(200);
 const point=await page.evaluate(i=>{
   const {camera,stages}=globalThis.__atlas;
   const world=stages[i].hit.getWorldPosition(camera.position.clone());
   world.project(camera);
   return {x:(world.x+1)*426,y:(1-world.y)*196.5};
 },index);
 await page.mouse.click(point.x,point.y);
 await page.waitForTimeout(800);
 const title=await page.locator('#selection-title').textContent();
 if(!title?.startsWith(String(index+1).padStart(2,'0')))throw new Error(`stage ${index+1} tap selected ${title}`);
 await page.screenshot({path:path.join(out,`focus-${String(index+1).padStart(2,'0')}.png`)});
 await page.locator('#overview').click();
 await page.waitForTimeout(800);
}
const stats=await page.evaluate(()=>({fps:globalThis.__atlas.fps,drawCalls:globalThis.__atlas.renderer.info.render.calls,triangles:globalThis.__atlas.renderer.info.render.triangles,viewport:[globalThis.innerWidth,globalThis.innerHeight],dpr:globalThis.devicePixelRatio}));
const video=await page.video().path();
await context.close();
await fs.rename(video,path.join(out,'orbit-and-taps.webm'));
await fs.writeFile(path.join(out,'measurements.json'),JSON.stringify({stats,errors,selected:['08','12'],orbit:{startSeconds:(orbitStart-captureStart)/1000,endSeconds:(orbitEnd-captureStart)/1000},angles:angles.map(([name,position])=>({name,position}))},null,2)+'\n');
await browser.close();
if(errors.length)throw new Error(errors.join('\n'));
console.log(JSON.stringify({out,stats,errors}));
