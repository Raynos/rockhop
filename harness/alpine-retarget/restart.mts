/** One-tick browser restart after each Alpine course's held-GO skill-gate fault. */
import { writeFileSync } from 'node:fs';
import { createSim } from '../lib/sim';
import { recordingHeader } from '../lib/recording';
import { launchBrowser } from '../lib/browser';
import { HookClient, openGame } from '../lib/hook';
import { startServer } from '../lib/server';
import { InputRecorder } from '../../src/core/replay';
import { getTrack } from '../../src/tracks';

const cases=[['a1-sawdust',300],['a2-log-jam',40],['a3-timberline',230]] as const;
const GO={throttle:1,brake:0,lean:0,hop:false,restart:false} as const;
const server=await startServer({dev:true}),browser=await launchBrowser({width:852,height:392}),rows=[];
try{
  await openGame(browser.page,server.url);
  const hook=new HookClient(browser.page);
  for(const [id,threshold] of cases)for(const bike of ['rookie','pro'] as const){
    const track=getTrack(id)!;
    const sim=await createSim(id,track.seed,120,{bike});
    const recorder=new InputRecorder(recordingHeader(sim,`Alpine ${id} ${bike} held-GO gate fault then one-tick restart`));
    let faultTick=-1,faultX=0,cp=-1;
    for(let tick=0;tick<600*120;tick++){
      const s=sim.state(),x=s.bike.pos.x;recorder.push(GO);
      if(sim.step(GO).some(e=>e.type==='fault')&&x>threshold){faultTick=tick+1;faultX=x;cp=s.checkpoint;break;}
    }
    if(faultTick<0)throw new Error(`${id} ${bike} missing gate fault`);
    const before=sim.faults(),restart={...GO,restart:true};recorder.push(restart);sim.step(restart);
    const json=JSON.stringify({magic:'TRIN',...recorder.toRecording()})+'\n';
    writeFileSync(new URL(`../../docs/evidence/alpine-retarget/${id}-${bike}-restart.rec.json`,import.meta.url),json);
    const browserRun=await hook.runRecording(json),browserPhase=await browser.page.evaluate(()=>window.__rockhop!.phase());
    const row={id,bike,faultTick,faultX:+faultX.toFixed(2),restartTick:faultTick+1,checkpoint:cp,
      nodePhase:sim.phase(),browserPhase,nodeCheckpoint:sim.state().checkpoint,browserCheckpoint:browserRun.state.checkpoint,
      nodeBikeX:sim.state().bike.pos.x,browserBikeX:browserRun.state.bike.pos.x,
      faultsBefore:before,faultsAfter:sim.faults(),hash:sim.hash(),browserHash:browserRun.hash,
      exact:sim.phase()==='riding'&&browserPhase==='riding'&&sim.hash()===browserRun.hash&&sim.faults()===before&&sim.state().checkpoint===cp};
    rows.push(row);process.stdout.write(`${JSON.stringify(row)}\n`);if(!row.exact)throw new Error(`${id} ${bike} restart differs`);
  }
}finally{await browser.close();await server.close();}
writeFileSync(new URL('../../docs/evidence/alpine-retarget/restart-verify.json',import.meta.url),JSON.stringify(rows,null,2)+'\n');
