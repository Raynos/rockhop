/** Compare the same 256 two-window inputs on each S3 deck candidate. */
import fs from 'node:fs';
import { decodeJSON, expandFrames, quantizeInput } from '../../src/core/replay';
import type { InputFrame } from '../../src/core/types';
import { RunRules } from '../lib/rules';
import { resolvePhysicsFactory } from '../lib/sim';
import { compileTrack } from '../../src/tracks';
import { S3 } from '../../src/tracks/rockhop/snowline';

const opts:{name:string,frame:InputFrame|null}[]=[{name:'source',frame:null}];
for(const throttle of [0,.5,1])for(const lean of [-1,-.5,0,.5,1])opts.push({name:`t${throttle}l${lean}`,frame:quantizeInput({throttle,lean})});
const recs=['rookie','pro'].map(bike=>{
  const file=bike==='rookie'?'harness/inputs/s3-whiteout/bot-3.json':`docs/evidence/snowline-retarget/s3-whiteout-${bike}-skill3.rec.json`;
  const rec=decodeJSON(fs.readFileSync(file,'utf8'));
  return {bike,rec,frames:expandFrames(rec)};
});
const factory=(await resolvePhysicsFactory()).factory;
const baseObstacles=S3.obstacles.filter(o=>o.kind!=='open-platform');
const rows=[];
const cases:[number,number,number][]=[];
for(let x=139;x<=144;x++)for(const len of [8,12])for(const y of [2.5,2.7,2.9,3.1,3.3,3.5,3.7])cases.push([x,len,y]);
for(const [x,len,y] of cases){
  const track={...S3,obstacles:[...baseObstacles,{kind:'open-platform' as const,pos:{x,y:0},params:{length:len,height:y,thickness:.18,surface:'snow' as const}}],diamondGoal:{id:'probe',platformObstacleIndex:baseObstacles.length,x:x+len*.55,minRearY:y+.2}};
  const compiled=compileTrack(track),byBike=[];
  for(const {bike,rec,frames} of recs){
    const world=factory(rec.header.physicsHz);world.loadTrack(compiled,rec.header.seed,{bike:bike as 'rookie'|'pro'});world.drainEvents();
    const rules=new RunRules(world,rec.header.physicsHz,track);rules.go();rules.drainEvents();
    let idx=0;while(idx<frames.length&&world.getState().bike.pos.x<125){rules.tick(frames[idx]!);rules.drainEvents();idx++}
    const start=idx,root={physics:world.snapshot(),counters:rules.counters()};
    let proof=0,proofAlive=0,lowerAlive=0,baseline=null;
    for(const pre of opts)for(const flight of opts){
      world.restore(root.physics);world.drainEvents();rules.restoreCounters(root.counters);idx=start;
      while(idx<frames.length&&world.getState().bike.pos.x<160&&!rules.faults()&&rules.phase()==='riding'){
        const xx=world.getState().bike.pos.x;
        const frame=xx<132?(pre.frame??frames[idx]!):xx<152?(flight.frame??frames[idx]!):frames[idx]!;
        rules.tick(frame);rules.drainEvents();idx++;
      }
      const p=rules.counters().diamondRouteCrossed===true,alive=rules.faults()===0&&world.getState().bike.pos.x>=160;
      if(p)proof++;if(p&&alive)proofAlive++;if(!p&&alive)lowerAlive++;
      if(pre.name==='source'&&flight.name==='source')baseline={proof:p,alive};
    }
    byBike.push({bike,proof,proofAlive,lowerAlive,baseline});
  }
  rows.push({x,len,y,byBike});
}
fs.writeFileSync('docs/evidence/snowline-diamond/s3-candidate-sweep.json',`${JSON.stringify(rows,null,2)}\n`);
console.log(JSON.stringify({tested:rows.length,promising:rows.filter(r=>r.byBike[1]!.proofAlive>r.byBike[0]!.proofAlive&&r.byBike[1]!.proofAlive>=3&&r.byBike[0]!.lowerAlive>0).sort((a,b)=>(b.byBike[1]!.proofAlive-b.byBike[0]!.proofAlive)-(a.byBike[1]!.proofAlive-a.byBike[0]!.proofAlive)).slice(0,20),bestPro:rows.sort((a,b)=>b.byBike[1]!.proofAlive-a.byBike[1]!.proofAlive).slice(0,10)},null,2));
