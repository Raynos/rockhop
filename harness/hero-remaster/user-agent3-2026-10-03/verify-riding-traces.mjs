/** Compare every captured browser input tick to an independent production Game. */
import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import { Game } from '../../../src/game/game.ts';
import { createBikePhysicsV2 } from '../../../src/physics/v2/bike.ts';
import { decodeJSON, expandFrames } from '../../../src/core/replay.ts';
const [packetArg,fixturesFile,outFile]=process.argv.slice(2);assert(outFile&&!fs.existsSync(outFile));
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');const packet=path.resolve(packetArg),receiptBytes=fs.readFileSync(path.join(packet,'engine-receipt.json')),receipt=JSON.parse(receiptBytes),fixtures=JSON.parse(fs.readFileSync(fixturesFile));
const results=[];let ticks=0;
for(const c of receipt.cases){const f=fixtures.cases.find(f=>f.id===c.id);assert(f);
  const recordingBytes=fs.readFileSync(path.join(path.dirname(fixturesFile),f.recording));assert.equal(sha(recordingBytes),c.recordingSHA256);
  const rec=decodeJSON(recordingBytes.toString()),inputs=expandFrames(rec),traceBytes=fs.readFileSync(path.join(packet,c.id+'.ndjson'));assert.equal(sha(traceBytes),c.everyTickTraceSHA256??c.everyInputTraceSHA256);
  const trace=traceBytes.toString().trim().split('\n').map(l=>JSON.parse(l));assert.equal(trace.length,c.everyTickCount??c.everyInputTickCount);
  const game=new Game({physics:createBikePhysicsV2(rec.header.physicsHz),physicsHz:rec.header.physicsHz,
    renderer:{setTrack(){},onEvent(){},setQuality(){},setBikeClass(){}},autoSkipCountdown:true,ghostEnabled:false});
  game.loadTrack(rec.header.trackId,rec.header.seed,rec.header.bike);
  for(let i=0;i<trace.length;i++){game.setInput(inputs[i]);game.step(1);const t=trace[i];
    assert.equal(t.inputTick,i+1);assert.equal(t.stateHash,game.hashState());assert.equal(t.tick,game.getState().tick);assert.equal(t.phase,game.phase());
    assert.equal(t.runTime,game.runTime());assert.equal(t.finishTime,game.getState().finishTime);ticks++;
  }
  results.push({id:c.id,ticks:trace.length,traceSHA256:sha(traceBytes),exactPhysicsPhaseClockFinishEveryTick:true,finalHash:game.hashState()});
}
const report={status:'REJECTED_WARDROBE_CONTROL_EVERY_TICK_PHYSICS_VERIFIED',candidateSHA256:receipt.candidate.sha256,receiptSHA256:sha(receiptBytes),ticks,results,
  codePins:Object.fromEntries(['src/game/game.ts','src/physics/v2/bike.ts','src/core/replay.ts','src/core/hash.ts'].map(f=>[f,sha(fs.readFileSync(f))])),checkCodeSHA256:sha(fs.readFileSync(new URL(import.meta.url))),
  limits:['Partial input windows end while riding; no new recorded clear, attempts-to-clear, restart or finish-time claim.',
    'Exact physics is a control. Human rejected hoodie, jeans and footwear fit; contact samples and numerical parity do not admit those assets.']};
fs.writeFileSync(outFile,JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({ticks,cases:results.length,status:report.status}));
