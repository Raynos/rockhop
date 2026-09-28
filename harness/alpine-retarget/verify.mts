/** Browser/Node equality for one skilled recording per Alpine course and bike. */
import { readFileSync, writeFileSync } from 'node:fs';
import { createSim } from '../lib/sim';
import { launchBrowser } from '../lib/browser';
import { HookClient, openGame } from '../lib/hook';
import { startServer } from '../lib/server';
import { decodeJSON, iterateFrames } from '../../src/core/replay';

const records=[
  ['a1-sawdust','rookie','docs/evidence/alpine-retarget/a1-rookie-skilled.rec.json'],
  ['a1-sawdust','pro','docs/evidence/alpine-retarget/a1-pro-skilled.rec.json'],
  ['a2-log-jam','rookie','harness/inputs/a2-log-jam/bot-3.json'],
  ['a2-log-jam','pro','docs/evidence/alpine-retarget/a2-log-jam-pro-bot.rec.json'],
  ['a3-timberline','rookie','docs/evidence/alpine-retarget/a3-timberline-rookie-bot.rec.json'],
  ['a3-timberline','pro','docs/evidence/alpine-retarget/a3-timberline-pro-bot.rec.json'],
] as const;
const server=await startServer({dev:true}),browser=await launchBrowser({width:852,height:392}),rows=[];
try{
  await openGame(browser.page,server.url);
  const hook=new HookClient(browser.page);
  for(const [id,bike,file] of records){
    const json=readFileSync(file,'utf8'),rec=decodeJSON(json);
    const sim=await createSim(id,rec.header.seed,rec.header.physicsHz,{bike});
    let tick=0,finishTick:number|null=null;
    for(const frame of iterateFrames(rec)){tick++;if(sim.step(frame).some(e=>e.type==='finish'))finishTick=tick;}
    const browserRun=await hook.runRecording(json);
    const browserTime=await hook.finishTime();
    const browserFinishTick=browserTime===null?null:Math.round(browserTime*120);
    const row={id,bike,source:file,finishTick,browserFinishTick,hash:sim.hash(),browserHash:browserRun.hash,
      faults:sim.faults(),exact:finishTick===browserFinishTick&&sim.hash()===browserRun.hash};
    rows.push(row);process.stdout.write(`${JSON.stringify(row)}\n`);
    if(!row.exact)throw new Error(`${id} ${bike} browser differs`);
  }
}finally{await browser.close();await server.close();}
writeFileSync(new URL('../../docs/evidence/alpine-retarget/browser-verify.json',import.meta.url),JSON.stringify(rows,null,2)+'\n');
