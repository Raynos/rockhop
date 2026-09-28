/** Test S1 shelf placements against passive GO and the already proven controlled inputs. */
import fs from 'node:fs';
import { decodeJSON, expandFrames, quantizeInput } from '../../src/core/replay';
import { RunRules } from '../lib/rules';
import { resolvePhysicsFactory } from '../lib/sim';
import { compileTrack } from '../../src/tracks';
import { S1 } from '../../src/tracks/rockhop/snowline';

const candidates:[number,number,number][]=[[283,12,4.6],[284,10,4.6],[285,10,4.6],[286,8,4.6],[287,4,4.6],[287,8,4.6],[288,10,4.6],[289,4,4.2],
  [284,10,4.8],[285,10,4.8],[286,8,4.8],[287,8,4.8],[288,8,4.8],[289,6,4.8],[290,6,4.8],[291,6,4.8]];
const factory=(await resolvePhysicsFactory()).factory;
const go=quantizeInput({throttle:1});
const baseObstacles=S1.obstacles.filter(o=>o.kind!=='open-platform');
const recs=['rookie','pro'].map(bike=>{
  const file=`docs/evidence/snowline-diamond/s1-lift-line-${bike}.rec.json`;
  const rec=decodeJSON(fs.readFileSync(file,'utf8'));
  return {bike,rec,frames:expandFrames(rec)};
});
for(const [x,len,y] of candidates){
  const track={...S1,obstacles:[...baseObstacles,{kind:'open-platform' as const,pos:{x,y:0},params:{length:len,height:y,thickness:.18,surface:'snow' as const}}],diamondGoal:{id:'probe',platformObstacleIndex:baseObstacles.length,x:x+len*.55,minRearY:y+.2}};
  let compiled;
  try{compiled=compileTrack(track)}catch(e){console.log(JSON.stringify({x,len,y,error:(e as Error).message}));continue}
  const rows=[];
  for(const {bike,rec,frames} of recs){
    for(const mode of ['passive','skilled']){
      const world=factory(rec.header.physicsHz);world.loadTrack(compiled,rec.header.seed,{bike:bike as 'rookie'|'pro'});world.drainEvents();
      const rules=new RunRules(world,rec.header.physicsHz,track);rules.go();rules.drainEvents();
      let ticks=0,maxX=0;
      const limit=mode==='passive'?72000:frames.length;
      for(let i=0;i<limit;i++){rules.tick(mode==='passive'?go:frames[i]!);rules.drainEvents();ticks++;maxX=Math.max(maxX,world.getState().bike.pos.x);if(mode==='passive'&&rules.phase()==='finished')break}
      rows.push({bike,mode,phase:rules.phase(),faults:rules.faults(),proof:rules.counters().diamondRouteCrossed===true,ticks,maxX});
    }
  }
  console.log(JSON.stringify({x,len,y,rows}));
}
