import fs from 'node:fs';
import {decodeJSON,expandFrames} from '../../src/core/replay';
import {createSimFor} from '../../harness/lib/sim';
const rec=decodeJSON(fs.readFileSync('docs/evidence/course-remaster/pro-envelope/d3-pro-upper.replay.json','utf8'));
for(const variant of ['clean','held-go']) {
 const sim=await createSimFor(rec); const frames=expandFrames(rec); const rows=[]; let lastBand=-1;
 for(let tick=0;tick<2400;tick++) { const frame=variant==='clean'?frames[tick]:{throttle:1,lean:0,brake:0,restart:false}; if(!frame)break;const events=sim.step(frame);const s=sim.state();const band=Math.floor(s.bike.pos.x/2);
 if(band!==lastBand||events.some(e=>e.type==='fault')) {rows.push({tick:tick+1,time:sim.runTime(),x:s.bike.pos.x,y:s.bike.pos.y,vx:s.bike.vel.x,pitch:s.bike.angle*180/Math.PI,rear:s.wheels.rear.grounded,front:s.wheels.front.grounded,input:frame,events});lastBand=band;}
 if(events.some(e=>e.type==='fault')||s.bike.pos.x>180)break;
 }
 console.log(JSON.stringify({variant,trackOpening:sim.track.obstacles.filter(o=>o.pos.x<180),rows,hash:sim.hash()}));
}
