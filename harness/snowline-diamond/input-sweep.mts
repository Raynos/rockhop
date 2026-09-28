/** Two-window controls around each route jump, sampled from each bike's clean measured approach. */
import fs from 'node:fs';
import { decodeJSON, expandFrames, quantizeInput } from '../../src/core/replay';
import type { InputFrame } from '../../src/core/types';
import { resolveParams } from '../../src/tracks/kinds';
import { createSimFor } from '../lib/sim';

const opts: {name:string,frame:InputFrame|null}[]=[{name:'source',frame:null}];
for(const throttle of [0,0.5,1])for(const lean of [-1,-0.5,0,0.5,1])
  opts.push({name:`t${throttle}l${lean}`,frame:quantizeInput({throttle,lean})});
const id=process.argv[2]==='S3'?'s3-whiteout':'s1-lift-line';
const w=id==='s1-lift-line'?{start:260,pre:267,flight:295,stop:315}:{start:125,pre:132,flight:152,stop:160};
const rows=[];
for(const bike of ['rookie','pro']){
  const file=id==='s3-whiteout'&&bike==='rookie'?'harness/inputs/s3-whiteout/bot-3.json':`docs/evidence/snowline-retarget/${id}-${bike}-skill3.rec.json`;
  const rec=decodeJSON(fs.readFileSync(file,'utf8'));
  const frames=expandFrames(rec);
  const sim=await createSimFor(rec);
  const deck=sim.track.obstacles[sim.track.diamondGoal!.platformObstacleIndex]!;
  const deckParams=resolveParams('open-platform',deck.params);
  const deckX=deck.pos.x,deckLength=deckParams.length,deckTop=deck.pos.y+deckParams.height;
  let idx=0;
  while(idx<frames.length && sim.state().bike.pos.x<w.start){sim.step(frames[idx]!);idx++;}
  if(sim.faults())throw new Error(`${bike} approach fault`);
  const root=sim.snap(), prefixX=sim.state().bike.pos.x, start=idx;
  const candidates=[];
  for(const pre of opts)for(const flight of opts){
    sim.restore(root);idx=start;
    let maxRearYOverDeck=-Infinity,deckRearContacts=0;
    while(idx<frames.length && sim.state().bike.pos.x<w.stop && !sim.faults() && sim.phase()==='riding'){
      const x=sim.state().bike.pos.x;
      const frame=x<w.pre ? (pre.frame??frames[idx]!) : x<w.flight ? (flight.frame??frames[idx]!) : frames[idx]!;
      sim.step(frame);idx++;
      const rear=sim.state().wheels.rear;
      if(rear.pos.x>=deckX&&rear.pos.x<=deckX+deckLength){
        maxRearYOverDeck=Math.max(maxRearYOverDeck,rear.pos.y);
        if(rear.grounded&&rear.pos.y>=deckTop+.25&&rear.pos.y<=deckTop+.5)deckRearContacts++;
      }
    }
    candidates.push({pre:pre.name,flight:flight.name,proof:sim.rules.counters().diamondRouteCrossed===true,
      alive:sim.faults()===0&&sim.state().bike.pos.x>=w.stop,x:sim.state().bike.pos.x,faults:sim.faults(),
      maxRearYOverDeck,deckRearContacts});
  }
  rows.push({bike,file,prefixX,total:candidates.length,proof:candidates.filter(c=>c.proof).length,
    proofAlive:candidates.filter(c=>c.proof&&c.alive).length,lowerAlive:candidates.filter(c=>!c.proof&&c.alive).length,
    baseline:candidates.find(c=>c.pre==='source'&&c.flight==='source'),
    upperSamples:candidates.filter(c=>c.proof&&c.alive).slice(0,8),
    lowerSamples:candidates.filter(c=>!c.proof&&c.alive).sort((a,b)=>a.deckRearContacts-b.deckRearContacts||a.maxRearYOverDeck-b.maxRearYOverDeck).slice(0,14)});
}
const out=`docs/evidence/snowline-diamond/${id}-input-sweep.json`;
fs.mkdirSync('docs/evidence/snowline-diamond',{recursive:true});
fs.writeFileSync(out,`${JSON.stringify(rows,null,2)}\n`);
console.log(JSON.stringify(rows,null,2));
