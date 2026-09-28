/** Silent headless replay of each qualified upper and lower Snowline recording. */
import fs from 'node:fs';
import path from 'node:path';
import { decodeJSON, encodeJSON, expandFrames } from '../../src/core/replay';
import { medalFor } from '../../src/game/rules';
import { decodeSnapshot } from '../../src/game/hook';
import { createSimFor } from '../lib/sim';
import { launchBrowser } from '../lib/browser';
import { HookClient, openGame } from '../lib/hook';
import { startServer } from '../lib/server';

const id=process.argv[2]==='S3'?'s3-whiteout':'s1-lift-line';
const outDir=path.resolve('docs/evidence/snowline-diamond');
const cases=['rookie','pro'].map(bike=>{
  const file=path.join(outDir,`${id}-${bike}.rec.json`);
  return {bike,file,rec:decodeJSON(fs.readFileSync(file,'utf8')),expectedProof:bike==='pro',expectedMedal:bike==='pro'?'platinum':'gold'};
});
const rows=[];
const server=await startServer({dev:true});
const browser=await launchBrowser({width:852,height:393});
try{
  for(const c of cases){
    const sim=await createSimFor(c.rec);sim.run(expandFrames(c.rec));
    const proof=sim.rules.counters().diamondRouteCrossed===true;
    const medal=medalFor(sim.runTime(),sim.faults(),sim.track.meta?.targetTimeS,sim.bike,proof);
    const browserRuns=[];
    for(let i=0;i<2;i++){
      const page=await browser.context.newPage();
      try{
        await openGame(page,server.url);
        const hook=new HookClient(page);
        const run=await hook.runRecording(encodeJSON(c.rec));
        const snap=decodeSnapshot(await page.evaluate(()=>window.__rockhop!.snapshot()));
        browserRuns.push({hash:run.hash,finishS:run.state.finishTime,proof:snap.counters?.diamondRouteCrossed===true,
          phase:snap.counters?.phase,faults:snap.counters?.faults});
      }finally{await page.close()}
    }
    const row={bike:c.bike,file:c.file,node:{phase:sim.phase(),finishS:sim.state().finishTime,runClockS:sim.runTime(),faults:sim.faults(),hash:sim.hash(),proof,medal},browserRuns};
    rows.push(row);
    if(sim.phase()!=='finished'||sim.faults()!==0||proof!==c.expectedProof||medal!==c.expectedMedal||
      browserRuns.some(r=>r.hash!==sim.hash()||r.finishS!==sim.state().finishTime||r.proof!==proof||r.phase!=='finished'||r.faults!==0))
      throw new Error(`${c.bike}: ${JSON.stringify(row)}`);
  }
}finally{await browser.close();await server.close()}
fs.writeFileSync(path.join(outDir,`${id}-verify.json`),`${JSON.stringify(rows,null,2)}\n`);
console.log(JSON.stringify(rows,null,2));
