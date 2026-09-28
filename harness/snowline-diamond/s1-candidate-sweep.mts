/** Compare the same two-window station-jump inputs across passive-safe S1 decks. */
import fs from 'node:fs';
import { decodeJSON, expandFrames, quantizeInput } from '../../src/core/replay';
import type { InputFrame } from '../../src/core/types';
import { RunRules } from '../lib/rules';
import { resolvePhysicsFactory } from '../lib/sim';
import { compileTrack } from '../../src/tracks';
import { S1 } from '../../src/tracks/rockhop/snowline';

const cases:[number,number,number][]=[[282,12,4.6],[283,10,4.6],[283,12,4.6],[284,10,4.6],[284,12,4.6],[285,8,4.6],[285,10,4.6],
  [286,8,4.6],[286,10,4.6],[287,6,4.6],[287,8,4.6],[287,10,4.6],[288,8,4.6],[288,10,4.6],[289,6,4.6],[289,8,4.6]];
const opts:{name:string,frame:InputFrame|null}[]=[{name:'source',frame:null}];
for(const throttle of [0,.5,1])for(const lean of [-1,-.5,0,.5,1])opts.push({name:`t${throttle}l${lean}`,frame:quantizeInput({throttle,lean})});
const recs=['rookie','pro'].map(bike=>{
  const file=`docs/evidence/snowline-retarget/s1-lift-line-${bike}-skill3.rec.json`;
  const rec=decodeJSON(fs.readFileSync(file,'utf8'));
  return {bike,rec,frames:expandFrames(rec)};
});
const factory=(await resolvePhysicsFactory()).factory;
const baseObstacles=S1.obstacles.filter(o=>o.kind!=='open-platform');
const rows=[];
for(const [x,len,y] of cases){
  const track={...S1,obstacles:[...baseObstacles,{kind:'open-platform' as const,pos:{x,y:0},params:{length:len,height:y,thickness:.18,surface:'snow' as const}}],diamondGoal:{id:'probe',platformObstacleIndex:baseObstacles.length,x:x+len*.55,minRearY:y+.2}};
  const compiled=compileTrack(track),byBike=[];
  for(const {bike,rec,frames} of recs){
    const world=factory(rec.header.physicsHz);world.loadTrack(compiled,rec.header.seed,{bike:bike as 'rookie'|'pro'});world.drainEvents();
    const rules=new RunRules(world,rec.header.physicsHz,track);rules.go();rules.drainEvents();
    let idx=0;while(idx<frames.length&&world.getState().bike.pos.x<260){rules.tick(frames[idx]!);rules.drainEvents();idx++}
    const start=idx,root={physics:world.snapshot(),counters:rules.counters()};
    let proof=0,proofAlive=0,lowerAlive=0,baseline=null;
    for(const pre of opts)for(const flight of opts){
      world.restore(root.physics);world.drainEvents();rules.restoreCounters(root.counters);idx=start;
      while(idx<frames.length&&world.getState().bike.pos.x<315&&!rules.faults()&&rules.phase()==='riding'){
        const xx=world.getState().bike.pos.x;
        const frame=xx<267?(pre.frame??frames[idx]!):xx<295?(flight.frame??frames[idx]!):frames[idx]!;
        rules.tick(frame);rules.drainEvents();idx++;
      }
      const p=rules.counters().diamondRouteCrossed===true,alive=rules.faults()===0&&world.getState().bike.pos.x>=315;
      if(p)proof++;if(p&&alive)proofAlive++;if(!p&&alive)lowerAlive++;
      if(pre.name==='source'&&flight.name==='source')baseline={proof:p,alive};
    }
    byBike.push({bike,proof,proofAlive,lowerAlive,baseline});
  }
  rows.push({x,len,y,byBike});
}
fs.writeFileSync('docs/evidence/snowline-diamond/s1-candidate-sweep.json',`${JSON.stringify(rows,null,2)}\n`);
console.log(JSON.stringify(rows,null,2));
