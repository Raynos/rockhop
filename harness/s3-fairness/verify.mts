/** Node plus two fresh silent browser replays for the visual S3 medal split. */
import fs from 'node:fs';
import { decodeJSON, encodeJSON, expandFrames } from '../../src/core/replay';
import { medalFor } from '../../src/game/rules';
import { decodeSnapshot } from '../../src/game/hook';
import { createSimFor } from '../lib/sim';
import { launchBrowser } from '../lib/browser';
import { HookClient, openGame } from '../lib/hook';
import { startServer } from '../lib/server';

const cases=[
  {bike:'rookie',file:'harness/inputs/s3-whiteout/bot-3.json',proof:false,medal:'gold'},
  {bike:'pro',file:'harness/inputs/s3-whiteout/bot-3-pro.json',proof:true,medal:'platinum'},
];
const rows=[];
const server=await startServer({dev:true});
const browser=await launchBrowser({width:852,height:393});
try{
  for(const c of cases){
    const rec=decodeJSON(fs.readFileSync(c.file,'utf8'));
    const sim=await createSimFor(rec);sim.run(expandFrames(rec));
    const proof=sim.rules.counters().diamondRouteCrossed===true;
    const medal=medalFor(sim.runTime(),sim.faults(),sim.track.meta?.targetTimeS,sim.bike,proof);
    const browserRuns=[];
    for(let i=0;i<2;i++){
      const page=await browser.context.newPage();
      try{
        await openGame(page,server.url);
        const hook=new HookClient(page);
        const run=await hook.runRecording(encodeJSON(rec));
        const snap=decodeSnapshot(await page.evaluate(()=>window.__rockhop!.snapshot()));
        browserRuns.push({hash:run.hash,finishS:run.state.finishTime,
          proof:snap.counters?.diamondRouteCrossed===true,phase:snap.counters?.phase,
          faults:snap.counters?.faults});
      }finally{await page.close()}
    }
    const row={bike:c.bike,file:c.file,node:{phase:sim.phase(),finishS:sim.state().finishTime,
      faults:sim.faults(),hash:sim.hash(),proof,medal},browserRuns};
    rows.push(row);
    if(row.node.phase!=='finished'||row.node.faults!==0||proof!==c.proof||medal!==c.medal||
      browserRuns.some(r=>r.hash!==row.node.hash||r.finishS!==row.node.finishS||
        r.proof!==proof||r.phase!=='finished'||r.faults!==0))
      throw new Error(`${c.bike}: ${JSON.stringify(row)}`);
  }
}finally{await browser.close();await server.close()}
fs.writeFileSync('docs/evidence/s3-fairness/verify.json',JSON.stringify(rows,null,2)+'\n');
console.log(JSON.stringify(rows,null,2));
