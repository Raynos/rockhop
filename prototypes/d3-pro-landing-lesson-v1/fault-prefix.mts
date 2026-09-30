/** Current Pro held GO first fault then neutral input through checkpoint retry. */
import fs from 'node:fs';
import {decodeJSON,InputRecorder,encodeJSON,quantizeInput} from '../../src/core/replay';
import {createSimFor} from '../../harness/lib/sim';
const rec=decodeJSON(fs.readFileSync('docs/evidence/course-remaster/pro-envelope/d3-pro-upper.replay.json','utf8'));
const sim=await createSimFor(rec);const recorder=new InputRecorder({...rec.header,routeProof:undefined,note:'Current Pro held GO until first ore-cart landing fault; neutral input through checkpoint retry, then resumed GO. Diagnostic only'});
let fault:unknown=null;const go=quantizeInput({throttle:1,lean:0,brake:0});
for(let i=0;i<1800;i++){recorder.push(go);const events=sim.step(go);if(events.some(e=>e.type==='fault')){fault={tick:sim.totalTicks(),time:sim.runTime(),x:sim.state().bike.pos.x,y:sim.state().bike.pos.y,events};break;}}
if(!fault)throw new Error('Current passive Pro did not fault');
const neutral=quantizeInput({throttle:0,lean:0,brake:0});
for(let i=0;i<150;i++){recorder.push(neutral);sim.step(neutral);}
for(let i=0;i<90;i++){recorder.push(go);sim.step(go);}
fs.writeFileSync('prototypes/d3-pro-landing-lesson-v1/d3-held-go-retry.json',encodeJSON(recorder.toRecording())+'\n');
fs.writeFileSync('prototypes/d3-pro-landing-lesson-v1/fault-proof.json',JSON.stringify({fault,tail:{tick:sim.totalTicks(),phase:sim.phase(),x:sim.state().bike.pos.x,faults:sim.faults(),hash:sim.hash()}},null,2)+'\n');console.log({fault,phase:sim.phase(),hash:sim.hash()});
