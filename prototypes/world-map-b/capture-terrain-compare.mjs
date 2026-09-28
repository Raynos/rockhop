import { chromium } from 'playwright';
import fs from 'node:fs/promises';
import path from 'node:path';

// The same actual pointer drag and tower click is played against both terrain
// implementations. No camera frames or scenery are substituted with stills.
const output=path.resolve('docs/evidence/world-map-b');
const browser=await chromium.launch({headless:true,args:['--mute-audio','--use-gl=angle','--use-angle=swiftshader']});
const results=[];
for(const [mode,suffix] of [['before','?proceduralTerrain=1'],['after','']]){
 const context=await browser.newContext({viewport:{width:844,height:390},deviceScaleFactor:1,recordVideo:{dir:output,size:{width:844,height:390}}});
 const start=performance.now(),page=await context.newPage(),errors=[];
 page.on('pageerror',e=>errors.push(String(e)));
 await page.goto(`http://127.0.0.1:5187/${suffix}`,{waitUntil:'networkidle'});
 await page.waitForFunction(()=>globalThis.__mapB?.getState().terrainReady&&globalThis.__mapB?.getState().towers===12,{timeout:30000});
 await page.waitForTimeout(650);
 const inputStartMs=performance.now()-start;
 await page.screenshot({path:path.join(output,`terrain-${mode}-mobile.png`)});
 await page.mouse.move(560,190);await page.mouse.down();
 for(let i=0;i<=38;i++){await page.mouse.move(560-i*7.3,190+i*.25);await page.waitForTimeout(34);}
 await page.waitForTimeout(450);
 for(let i=0;i<=52;i++){await page.mouse.move(283+i*7.3,199-i*.2);await page.waitForTimeout(34);}
 await page.mouse.up();await page.waitForTimeout(500);
 await page.evaluate(()=>globalThis.__mapB.resetView());await page.waitForTimeout(800);
 const pos=await page.evaluate(()=>globalThis.__mapB.stageScreenPosition(7));await page.mouse.click(pos.x,pos.y);
 await page.waitForFunction(()=>globalThis.__mapB.getState().selected===8,{timeout:5000});
 await page.waitForTimeout(1200);
 await page.screenshot({path:path.join(output,`terrain-${mode}-selected-mobile.png`)});
 const state=await page.evaluate(()=>globalThis.__mapB.getState());
 const videoPath=await page.video().path();await context.close();
 await fs.rename(videoPath,path.join(output,`terrain-${mode}.webm`));
 results.push({mode,source:state.terrainSource,inputStartMs:Math.round(inputStartMs),elapsedMs:Math.round(performance.now()-start),errors,selected:state.selected});
 if(errors.length)throw new Error(`${mode}: ${errors.join('; ')}`);
}
await browser.close();
await fs.writeFile(path.join(output,'terrain-comparison.json'),JSON.stringify(results,null,2));
console.log(JSON.stringify(results));
