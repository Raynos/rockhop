/** Current clean Pro approach followed by over-leaned launch, one fault and checkpoint retry. */
import fs from 'node:fs';
import {decodeJSON,expandFrames,InputRecorder,encodeJSON,quantizeInput} from '../../src/core/replay';
import {createSimFor} from '../../harness/lib/sim';
const rec=decodeJSON(fs.readFileSync('docs/evidence/course-remaster/pro-envelope/s1-pro-upper.replay.json','utf8'));
const sim=await createSimFor(rec);const recorder=new InputRecorder({...rec.header,routeProof:undefined,note:'Current Pro clean prefix to x245, then GO plus full back lean until first fault, auto retry and resumed control; diagnostic only'});
for(const frame of expandFrames(rec)) {if(sim.state().bike.pos.x>=245)break;recorder.push(frame);sim.step(frame);}
const prefix={tick:sim.totalTicks(),x:sim.state().bike.pos.x};let fault:unknown=null;
const go=quantizeInput({throttle:1,lean:-1,brake:0});
for(let i=0;i<1500;i++){recorder.push(go);const events=sim.step(go);if(events.some(e=>e.type==='fault')){fault={tick:sim.totalTicks(),x:sim.state().bike.pos.x,y:sim.state().bike.pos.y,events};break;}}
if(!fault)throw new Error('Over-leaned candidate did not fault');
const recover=quantizeInput({throttle:1,lean:0,brake:0});
for(let i=0;i<180;i++){recorder.push(recover);sim.step(recover);}
fs.writeFileSync('prototypes/s1-landing-sightline-v1/s1-held-go-retry.json',encodeJSON(recorder.toRecording())+'\n');
fs.writeFileSync('prototypes/s1-landing-sightline-v1/fault-proof.json',JSON.stringify({prefix,fault,tail:{tick:sim.totalTicks(),phase:sim.phase(),x:sim.state().bike.pos.x,faults:sim.faults(),hash:sim.hash()}},null,2)+'\n');
console.log({prefix,fault,phase:sim.phase(),hash:sim.hash()});
