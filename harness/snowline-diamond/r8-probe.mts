/** Exact R8 angular recovery clock and psi band on one recording, with violating x/tick windows. */
import fs from 'node:fs';
import { decodeJSON, expandFrames } from '../../src/core/replay';
import { createSimFor } from '../lib/sim';
import type { BikePhysicsWorldV2 } from '../../src/physics/v2/bike';

const file=process.argv[2]??'docs/evidence/snowline-diamond/s3-whiteout-rookie.rec.json';
const rec=decodeJSON(fs.readFileSync(file,'utf8'));
const sim=await createSimFor(rec);
const w=sim.world as BikePhysicsWorldV2 & {F:Float64Array};
const HZ=rec.header.physicsHz,DT=1/HZ,G=9.81,DEMAND_W=6,RECOVER_TICKS=60,BAND_PSI=.35;
const demandG=w.tuning.rider.Fmax/(w.tuning.rider.mass*G),demandA=w.tuning.rider.tauMax/w.tuning.rider.inertia;
const initial=sim.state(),ic=Math.cos(initial.bike.angle),isn=Math.sin(initial.bike.angle);
let ptx=initial.bike.pos.x+w.F[6]!*ic-w.F[7]!*isn;
let pty=initial.bike.pos.y+w.F[6]!*isn+w.F[7]!*ic;
let pta=initial.bike.angle+w.F[8]!;
const vhx:number[]=Array(DEMAND_W+1).fill(0),vhy:number[]=Array(DEMAND_W+1).fill(0),vha:number[]=Array(DEMAND_W+1).fill(0),capFrac:number[]=Array(DEMAND_W).fill(1);
let lastOver=-1e9,tick=0;
const violations=[];const over=[];
for(const f of expandFrames(rec)){
  const events=sim.step(f);tick++;
  const s=sim.state(),ph=sim.phase();
  if(ph!=='riding'||!s.riderBody){
    ptx=Number.NaN;pta=Number.NaN;vhx.length=0;vhy.length=0;vha.length=0;capFrac.length=0;lastOver=-1e9;continue;
  }
  let reason='';
  if(events.some(e=>e.type==='land')||w.debug().rider.hold.seatJ>2*w.tuning.rider.mass*G*DT){lastOver=tick;reason='land-or-seat';}
  const c=Math.cos(s.bike.angle),sn=Math.sin(s.bike.angle);
  const tx=w.F[6]!,ty=w.F[7]!,tpsi=w.F[8]!;
  const twx=s.bike.pos.x+tx*c-ty*sn,twy=s.bike.pos.y+tx*sn+ty*c,twa=s.bike.angle+tpsi;
  if(Number.isNaN(ptx)){
    vhx.push(...Array(DEMAND_W+1).fill(0));vhy.push(...Array(DEMAND_W+1).fill(0));vha.push(...Array(DEMAND_W+1).fill(0));capFrac.push(...Array(DEMAND_W).fill(1));lastOver=tick;
  }
  capFrac.push(w.debug().rider.legFrac);if(capFrac.length>DEMAND_W)capFrac.shift();
  if(!Number.isNaN(ptx)){
    vhx.push((twx-ptx)/DT);vhy.push((twy-pty)/DT);vha.push((twa-pta)/DT);
    if(vhx.length>DEMAND_W+1){vhx.shift();vhy.shift();vha.shift()}
    if(vhx.length===DEMAND_W+1){
      const demand=Math.hypot((vhx[DEMAND_W]!-vhx[0]!)/(DEMAND_W*DT),(vhy[DEMAND_W]!-vhy[0]!)/(DEMAND_W*DT)+G)/G;
      const demandAng=Math.abs((vha[DEMAND_W]!-vha[0]!)/(DEMAND_W*DT));
      if(demand>demandG*capFrac.reduce((a,b)=>a+b,0)/capFrac.length||demandAng>demandA){lastOver=tick;over.push({tick,x:s.bike.pos.x,demand,demandAng});reason='over-demand';}
    }
  }
  ptx=twx;pty=twy;pta=twa;
  const rel=s.riderBody.angle-s.bike.angle,psiErr=Math.abs(rel-tpsi),since=tick-lastOver;
  if(since>=RECOVER_TICKS&&psiErr>BAND_PSI)violations.push({tick,x:s.bike.pos.x,psiErr,since,lastOver,angle:s.bike.angle,lean:f.lean,throttle:f.throttle,reason});
}
const segments=[];
for(const v of violations){const prev=segments[segments.length-1];if(prev&&v.tick===prev.end+1){prev.end=v.tick;prev.x1=v.x;prev.maxPsi=Math.max(prev.maxPsi,v.psiErr)}else segments.push({start:v.tick,end:v.tick,x0:v.x,x1:v.x,maxPsi:v.psiErr})}
console.log(JSON.stringify({file,phase:sim.phase(),faults:sim.faults(),finishS:sim.state().finishTime,badTicks:violations.length,segments,firstViolations:violations.slice(0,20),lastOver:over.slice(-15)},null,2));
