/** Format/cadence/parity fixture data only. No browser, model or fake film. */
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
import {cadence,decodeProof,comparePresentation,parseFrameHashes,requestCoverage} from './garage60-proof.mjs';
import {filePin} from './garage60-capture.mjs';
import {installGarage60Recorder} from './garage60-recorder.mjs';
const fixture=(fps=60,count=121)=>({streams:[{codec_type:'video',codec_name:'h264',pix_fmt:'yuv420p',width:1280,height:720,avg_frame_rate:'60/1'}],
  frames:Array.from({length:count},(_,i)=>({media_type:'video',best_effort_timestamp_time:(i/fps).toFixed(6)}))});
const hashes=count=>Array.from({length:count},(_,i)=>i.toString(16).padStart(32,'0'));
void test('Real decoded PTS/count define cadence;25fps marked60 cannot pass',()=> {
  const sixty=decodeProof(fixture(),hashes(121));assert(sixty.nominal60CadenceObserved);assert(Math.abs(sixty.observedFPS-60)<1e-10);
  const slow=decodeProof(fixture(25),hashes(121));assert.equal(slow.observedFPS,25);assert.equal(slow.nominal60CadenceObserved,false);
  assert.throws(()=>cadence([0,0,.1]),/Non-increasing/);
});
void test('Dropped frame fails nominal60 even with average near60',()=> {
  const data=fixture(60,1201);data.frames.splice(100,1);
  const proof=decodeProof(data,hashes(data.frames.length));assert(!proof.nominal60CadenceObserved);
  assert(proof.intervalSeconds.maximum>.03);
});
void test('Silent video format and exact decoded digest count are mandatory',()=> {
  const data=fixture();data.streams.push({codec_type:'audio'});
  assert.throws(()=>decodeProof(data,hashes(121)),/Silent/);
  assert.throws(()=>decodeProof(fixture(),hashes(120)),/Every decoded/);
  assert.deepEqual(parseFrameHashes('#format: frame checksums\n0, 0, 0, 1, 20, '+hashes(1)[0]+'\n'),hashes(1));
});
void test('Lossless presentation preserves frames, normalized timing and pixels',()=> {
  const a=decodeProof(fixture(),hashes(121)),b=structuredClone(a);
  b.timestamps=b.timestamps.map(t=>t+10);
  assert(comparePresentation(a,b,hashes(121),hashes(121)).decodedPixelsExact);
  const requests=a.timestamps.map(t=>t*1000);
  assert(requestCoverage(a,requests).completeRequestSpanObserved);
  assert(!requestCoverage(a,requests.concat([2033,2050,2067])).completeRequestSpanObserved);
  const bad=structuredClone(b);bad.timestamps[30]+=.01;
  assert.throws(()=>comparePresentation(a,bad,hashes(121),hashes(121)),/presentation times/);
  assert.throws(()=>comparePresentation(a,{...b,frames:120},hashes(121),hashes(121)),/duplicated/);
  const pixels=hashes(121);pixels[10]='f'.repeat(32);
  assert.throws(()=>comparePresentation(a,b,hashes(121),pixels),/decoded pixels/);
});
void test('Identical repeated pictures remain measurable as frozen footage',()=> {
  const row=decodeProof(fixture(),Array(121).fill('f'.repeat(32)));
  assert.equal(row.uniqueDecodedFrames,1);assert(row.distinctFraction<.01);
});
void test('File/URL source identities agree without browser or source mutation',()=> {
  const dir=fs.mkdtempSync(path.join(os.tmpdir(),'rockhop-garage60-pin-'));
  try {const file=path.join(dir,'receipt.json');fs.writeFileSync(file,'unaccepted fixture\n');
    assert.deepEqual(filePin(file),filePin(pathToFileURL(file)));}
  finally {fs.rmSync(dir,{recursive:true,force:true});}
});

void test('Exact recorder scheduler retains near60 renders with jitter and samples120 without30Hz collapse',()=> {
  const start=1234.25,duration=20000;
  for(const realFPS of [30,59.4,60,60.1,120]) {
    for(const jitter of [0,.4]) {
      const scheduler=installGarage60Recorder({fps:60,schedulerTestOnlyStart:start});
      const observations=[],requests=[],slots=[];
      for(let i=0;i<=Math.floor(duration*realFPS/1000);i++) {
        const at=start+i*1000/realFPS+(i===0?0:jitter*Math.sin(i*1.37));
        observations.push(at);const slot=scheduler(at);
        if(slot!==null) {requests.push(at);slots.push(slot);}
      }
      assert(slots.every((slot,i)=>i===0||slot>slots[i-1]));
      assert(requests.every(at=>observations.includes(at)),'No manufactured capture timestamp');
      const expected=Math.min(observations.length,duration*60/1000+1);
      // Jitter can put two near60 samples in the same nearest slot; retaining
      // only one is explicit, occasional, and its real timing stays in proof.
      assert(requests.length>=expected*.98 && requests.length<=expected+1,`Collapsed${realFPS}Hz sample count`);
      if(jitter===0&&realFPS<=60)assert.equal(requests.length,observations.length);
      if(realFPS===30||realFPS===60)assert.equal(requests.length,observations.length);
      const rate=cadence(requests,.001).observedFPS;
      assert(Math.abs(rate-Math.min(realFPS,60))<1,`Collapsed${realFPS}Hz to${rate}`);
      if(realFPS===30)assert(rate<31,'Real30Hz cannot be reported as60Hz');
    }
  }
  const late=installGarage60Recorder({fps:60,schedulerTestOnlyStart:start});
  assert.equal(late(start),0);assert.equal(late(start),null);
  assert.equal(late(start+1000),60);assert.equal(late(start+1000),null);
  assert.equal(late(start+1000+1000/60),61); // No60-request catch-up loop.
});
