/** Silent 852×392 played clip around an Alpine skill gate. */
import fs from 'node:fs';
import path from 'node:path';
import { preview } from 'vite';
import { createSim } from '../lib/sim';
import { launchBrowser } from '../lib/browser';
import { encodeMp4, contactSheet } from '../lib/ffmpeg';
import { HookClient, openGame } from '../lib/hook';
import { decodeJSON, expandFrames } from '../../src/core/replay';
import type { InputFrame } from '../../src/core/types';
import { getTrack } from '../../src/tracks';

const id=process.argv[2]??'a1-sawdust',bike=process.argv[3]==='pro'?'pro':'rookie',go=process.argv[4]==='go';
const specs={
  'a1-sawdust':{start:284,skillEnd:352,faultMin:300,rookie:'docs/evidence/alpine-retarget/a1-rookie-skilled.rec.json',pro:'docs/evidence/alpine-retarget/a1-pro-skilled.rec.json'},
  'a2-log-jam':{start:30,skillEnd:78,faultMin:40,rookie:'harness/inputs/a2-log-jam/bot-3.json',pro:'docs/evidence/alpine-retarget/a2-log-jam-pro-bot.rec.json'},
  'a3-timberline':{start:240,skillEnd:293,faultMin:230,rookie:'docs/evidence/alpine-retarget/a3-timberline-rookie-bot.rec.json',pro:'docs/evidence/alpine-retarget/a3-timberline-pro-bot.rec.json'},
} as const;
if(!(id in specs))throw new Error(`not Alpine: ${id}`);
const spec=specs[id as keyof typeof specs],recFile=spec[bike];
const rec=decodeJSON(fs.readFileSync(recFile,'utf8'));
const inputs:InputFrame[]=go?Array.from({length:100*120},()=>({throttle:1,brake:0,lean:0,hop:false,restart:false})):expandFrames(rec);
const track=getTrack(id)!;
const sim=await createSim(id,rec.header.seed,120,{bike});
let startTick=-1,endTick=-1;
for(let tick=0;tick<inputs.length;tick++){
  const beforeX=sim.state().bike.pos.x;
  const events=sim.step(inputs[tick]!);
  if(startTick<0&&beforeX>=spec.start)startTick=tick+1;
  if(go&&beforeX>spec.faultMin&&events.some(e=>e.type==='fault')){endTick=tick+1+96;break;}
  if(!go&&endTick<0&&beforeX>=spec.skillEnd){endTick=tick+1;break;}
}
if(startTick<0||endTick<0)throw new Error(`${id} ${bike} ${go?'GO':'skill'} misses gate: ${startTick}/${endTick}`);
startTick=Math.max(0,startTick-120);endTick=Math.min(inputs.length,endTick+24);
const fps=20,ticksPerFrame=120/fps;
startTick=Math.floor(startTick/ticksPerFrame)*ticksPerFrame;
endTick=Math.ceil(endTick/ticksPerFrame)*ticksPerFrame;
const expected=await createSim(id,rec.header.seed,120,{bike});
for(const frame of inputs.slice(0,endTick))expected.step(frame);
const expectedHash=expected.hash();
const outDir=new URL(`../../docs/evidence/alpine-retarget/clips/${id}-${bike}-${go?'go':'skilled'}/`,import.meta.url);
fs.mkdirSync(outDir,{recursive:true});
const framesDir=path.join(outDir.pathname,'frames');fs.rmSync(framesDir,{recursive:true,force:true});fs.mkdirSync(framesDir,{recursive:true});
// Static QA snapshot: concurrent builders can edit source without Vite HMR
// reloading the played run. Built separately with qa-vite.config.ts.
const server=await preview({root:process.cwd(),configFile:'harness/alpine-retarget/qa-vite.config.ts',preview:{host:'127.0.0.1',port:0}});
const url=server.resolvedUrls?.local[0];if(!url)throw new Error('QA preview has no local URL');
const browser=await launchBrowser({width:852,height:392});
try{
  const page=browser.page;await openGame(page,url);
  const hook=new HookClient(page);await hook.setBike(bike);
  if(!(await hook.loadTrack(track.id,rec.header.seed)))throw new Error('track load failed');
  await page.evaluate(()=>window.__rockhop!.skipCountdown());await hook.resize(852,392);await hook.setQuality('low');
  for(let tick=0;tick<startTick;tick+=600){
    const chunk=inputs.slice(tick,Math.min(startTick,tick+600));
    await page.evaluate((batch)=>{const h=window.__rockhop!;for(const f of batch){h.setInput(f);h.step(1);}},chunk);
  }
  const pictures=[];let cameraBoxViolations=0,maxAbsRoll=0;
  for(let tick=startTick,index=0;tick<endTick;tick+=ticksPerFrame,index++){
    const chunk=inputs.slice(tick,tick+ticksPerFrame);
    const info=await page.evaluate((batch)=>{
      const h=window.__rockhop!;for(const f of batch){h.setInput(f);h.step(1);}h.render();
      return {x:h.getState().bike.pos.x,camera:h.camera(),phase:h.phase()};
    },chunk);
    const c=info.camera;maxAbsRoll=Math.max(maxAbsRoll,Math.abs(c.roll??0));
    if(info.phase==='riding'&&(c.bikeScreenX<0.2||c.bikeScreenX>0.8||c.bikeScreenY<0.2||c.bikeScreenY>0.8))cameraBoxViolations++;
    const pic=path.join(framesDir,`frame-${String(index).padStart(5,'0')}.png`);
    await page.screenshot({path:pic,type:'png',animations:'disabled',caret:'hide'});pictures.push(pic);
    if(index%25===0)process.stdout.write(`${id} ${bike} ${go?'GO':'skill'} frame=${index} x=${info.x.toFixed(1)}\n`);
  }
  const mp4=path.join(outDir.pathname,'clip.mp4');
  await encodeMp4({fps,pattern:path.join(framesDir,'frame-%05d.png'),out:mp4,crf:22,preset:'fast'});
  await contactSheet({frames:pictures,out:path.join(outDir.pathname,'sheet.jpg'),cols:4,rows:2,tileWidth:426});
  const browserHash=await hook.hashState();
  if(browserHash!==expectedHash)throw new Error(`${id} ${bike} clip browser/node mismatch ${browserHash} vs ${expectedHash}`);
  fs.writeFileSync(path.join(outDir.pathname,'clip.json'),JSON.stringify({id,bike,input:go?'held GO':'skilled recording',source:go?'constant GO':recFile,captureBuild:'non-shipping frozen QA build; production bundle-budget plugin excluded',width:852,height:392,fps,startTick,endTick,frames:pictures.length,seconds:pictures.length/fps,nodeHashAtWindowEnd:expectedHash,browserHashAtWindowEnd:browserHash,cameraBoxViolations,maxAbsRoll},null,2)+'\n');
  process.stdout.write(`${mp4} ${pictures.length} frames\n`);
}finally{fs.rmSync(framesDir,{recursive:true,force:true});await browser.close();await new Promise<void>((resolve,reject)=>server.httpServer.close(err=>err?reject(err):resolve()));}
