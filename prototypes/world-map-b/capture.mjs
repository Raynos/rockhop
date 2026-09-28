import { chromium } from 'playwright';
import fs from 'node:fs/promises';
import path from 'node:path';

const output=path.resolve('docs/evidence/world-map-b');
await fs.mkdir(output,{recursive:true});
const browser=await chromium.launch({headless:true,args:['--mute-audio','--use-gl=angle','--use-angle=swiftshader']});
const context=await browser.newContext({viewport:{width:1280,height:588},deviceScaleFactor:1,recordVideo:{dir:output,size:{width:1280,height:588}}});
const page=await context.newPage();
const errors=[];
page.on('pageerror',e=>errors.push(String(e)));
const start=performance.now();
await page.goto('http://127.0.0.1:5187/',{waitUntil:'networkidle'});
await page.waitForFunction(()=>window.__mapB?.getState().towers===12&&window.__mapB?.getState().terrainReady,{timeout:30000});
const readyMs=Math.round(performance.now()-start);
await page.waitForTimeout(900);
await page.screenshot({path:path.join(output,'front-landscape.png')});
await page.mouse.move(680,280);await page.mouse.down();
for(let i=0;i<36;i++){await page.mouse.move(680+i*6,280+i*.75);await page.waitForTimeout(25);}
await page.mouse.up();await page.waitForTimeout(850);
await page.screenshot({path:path.join(output,'rotated-landscape.png')});
const stage=await page.evaluate(()=>window.__mapB.stageScreenPosition(7));
await page.mouse.click(stage.x,stage.y);
await page.waitForFunction(()=>window.__mapB.getState().selected===8,{timeout:5000});
await page.waitForTimeout(400);
await page.screenshot({path:path.join(output,'selected-stage.png')});
for(let i=0;i<5;i++){await page.evaluate(()=>window.__mapB.rotateBy(Math.PI/7));await page.waitForTimeout(300);}
await page.waitForTimeout(450);
const state=await page.evaluate(()=>window.__mapB.getState());
const videoPath=await page.video().path();
await context.close();
const mobile=await browser.newContext({viewport:{width:844,height:390},deviceScaleFactor:1});
const mobilePage=await mobile.newPage();await mobilePage.goto('http://127.0.0.1:5187/',{waitUntil:'networkidle'});
await mobilePage.waitForFunction(()=>window.__mapB?.getState().towers===12&&window.__mapB?.getState().terrainReady);await mobilePage.waitForTimeout(450);
await mobilePage.screenshot({path:path.join(output,'mobile-landscape.png')});
const mobileSelections=[];
for(let i=0;i<12;i++){
  const position=await mobilePage.evaluate(i=>window.__mapB.stageScreenPosition(i),i);
  await mobilePage.mouse.click(position.x,position.y);
  const selected=await mobilePage.evaluate(()=>window.__mapB.getState().selected);
  mobileSelections.push(selected);
  if(selected!==i+1)throw new Error(`Mobile tower ${i+1} selected ${selected}`);
  if(i===7){await mobilePage.waitForTimeout(800);await mobilePage.screenshot({path:path.join(output,'mobile-selected.png')});}
  await mobilePage.locator('#card-close').click();
  await mobilePage.waitForTimeout(500);
}
await mobile.close();
const portrait=await browser.newContext({viewport:{width:390,height:844},deviceScaleFactor:1});
const portraitPage=await portrait.newPage();await portraitPage.goto('http://127.0.0.1:5187/',{waitUntil:'networkidle'});
await portraitPage.screenshot({path:path.join(output,'portrait-rotate.png')});await portrait.close();await browser.close();
await fs.rename(videoPath,path.join(output,'rotation-select.webm'));
await fs.writeFile(path.join(output,'capture.json'),JSON.stringify({readyMs,durationMs:Math.round(performance.now()-start),state,errors,viewport:'1280x588 DPR1',mobileViewport:'844x390 DPR1',mobileSelections,silent:true,clickedActualTower:true,source:'standalone Three.js scene with Blender-authored UV/material terrain GLB'},null,2));
if(errors.length){console.error(errors);process.exitCode=1;}else console.log(JSON.stringify({output,durationMs:Math.round(performance.now()-start),state}));
