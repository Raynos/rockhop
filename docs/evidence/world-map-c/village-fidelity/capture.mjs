/* Silent full C-island orbit in headless WebKit. Plays Menu → Play, drags the
   camera with pointer input, then selects every tower by a real touch tap. */
import fs from 'node:fs';
import path from 'node:path';
import { webkit } from 'playwright';

const url=process.argv[2]||'http://127.0.0.1:5194/?map3d=1&sw=0&audio=0';
const output=path.resolve(process.argv[3]||'docs/evidence/world-map-c/village-fidelity/final');
const record=!process.argv.includes('--no-video');
fs.mkdirSync(output,{recursive:true});
const browser=await webkit.launch({headless:true});
const context=await browser.newContext({
 viewport:{width:852,height:393},deviceScaleFactor:2,isMobile:true,hasTouch:true,
 ...(record?{recordVideo:{dir:output,size:{width:852,height:393}}}:{})
});
await context.addInitScript(()=>localStorage.setItem('rockhop.onboarded','1'));
const page=await context.newPage(),video=record?page.video():null,errors=[];
page.on('pageerror',error=>errors.push(error.message));
page.on('console',message=>{if(message.type()==='error')errors.push(message.text());});
const samples=[],selections=[];
try{
 await page.goto(url);
 await page.waitForSelector('.menu-screen.live',{timeout:120000});
 await page.locator('.menu-screen.live .menu-item[data-id=play]').click();
 await page.waitForFunction(()=>document.querySelector('.wm3d-host')?.dataset.ready==='1'&&!!window.__rockhopMap3d,null,{timeout:60000});
 await page.evaluate(()=>{
   const gaps=[];let last=0;
   function tick(now){if(last)gaps.push(now-last);last=now;requestAnimationFrame(tick);}
   requestAnimationFrame(tick);window.__mapPerfIntervals=gaps;
 });
 async function sample(name){
   const data=await page.evaluate(()=>({stats:window.__rockhopMap3d.stats(),intervals:window.__mapPerfIntervals.splice(0)}));
   const times=data.intervals.filter(value=>value>0).sort((a,b)=>a-b);
   const percentile=p=>times.length?Math.round(times[Math.floor((times.length-1)*p)]*10)/10:null;
   samples.push({name,stats:data.stats,frames:times.length,medianMs:percentile(.5),p95Ms:percentile(.95)});
   if(record)await page.screenshot({path:path.join(output,`${name}.png`)});
 }
 await page.waitForTimeout(3000);await sample('front');
 await page.mouse.move(650,181);await page.mouse.down();
 for(let step=1;step<=48;step++){
   await page.mouse.move(650-step*7.5,181,{steps:1});
   if(step===12)await sample('three-quarter');
   if(step===36)await sample('reverse');
   await page.waitForTimeout(32);
 }
 await page.mouse.up();await page.waitForTimeout(1200);await sample('settled');
 for(let target=0;target<12;target++){
   const from=target===0?1:target-1;
   await page.evaluate(index=>window.__rockhopMap3d.selectStage(index,true),from);
   await page.waitForTimeout(850);
   const point=await page.evaluate(index=>window.__rockhopMap3d.towerScreenPoint(index),target);
   if(point)await page.touchscreen.tap(point.x,point.y);
   await page.waitForTimeout(100);
   selections.push(await page.evaluate(({from,target,point})=>({from,target,point,selected:window.__rockhopMap3d.stats().selected,track:document.querySelector('.wm3d-detail')?.dataset.track}),{from,target,point}));
 }
 const report={url,viewport:'852x393',dpr:2,engine:'Playwright WebKit',samples,selections,errors,
   pass:errors.length===0&&selections.length===12&&selections.every(entry=>entry.point&&entry.selected===entry.target)};
 fs.writeFileSync(path.join(output,'report.json'),JSON.stringify(report,null,2));
 console.log(JSON.stringify({pass:report.pass,drawCalls:samples.map(s=>s.stats.drawCalls),triangles:samples.map(s=>s.stats.triangles),selections:selections.length,errors}));
 if(!report.pass)process.exitCode=1;
}finally{
 await context.close();
 if(video){const source=await video.path();fs.renameSync(source,path.join(output,'played-orbit.webm'));}
 await browser.close();
}
