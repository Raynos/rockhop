/** Silent played evidence validation; decoding is never an art acceptance. */
/* oxlint-disable eslint/no-undef -- Playwright browser globals. */
import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import http from 'node:http';
import { webkit } from 'playwright';
const folder=path.resolve(process.argv[2]);
const playedTimeS=Number(process.argv[3]??1.9);assert(Number.isFinite(playedTimeS)&&playedTimeS>=0);
const source=JSON.parse(fs.readFileSync(path.join(folder,'surface-witnesses.json')));
const server=http.createServer((req,res)=>{
  const name=path.basename(req.url.slice(1));
  if(!source.delivery.some(d=>path.basename(d.path)===name)){res.writeHead(404);res.end();return;}
  const bytes=fs.readFileSync(path.join(folder,name));
  res.writeHead(200,{'Content-Type':'video/mp4','Content-Length':bytes.length});res.end(bytes);
});
await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
const browser=await webkit.launch({headless:true});
const page=await browser.newPage({viewport:{width:1920,height:1280}});
const errors=[];page.on('pageerror',e=>errors.push(e.message));
const results=[];
try {
  for(const delivery of source.delivery){
    const name=path.basename(delivery.path),bytes=fs.readFileSync(path.join(folder,name));
    assert.equal(crypto.createHash('sha256').update(bytes).digest('hex'),delivery.sha256);
    await page.setContent('<video id="film" muted playsinline style="width:100%;display:block"></video>');
    await page.evaluate(async url=>{
      const v=document.querySelector('#film'); v.muted=true;v.src=url; await v.play();
    },`http://127.0.0.1:${server.address().port}/${name}`);
    await page.waitForFunction(time=>document.querySelector('#film').currentTime>=time,playedTimeS);
    await page.screenshot({path:path.join(folder,name.replace('.mp4','.played.png'))});
    await page.waitForFunction(()=>document.querySelector('#film').ended,null,{timeout:15000});
    const result=await page.evaluate(()=>{const v=document.querySelector('#film');return{ended:v.ended,duration:v.duration,currentTime:v.currentTime,muted:v.muted,webdriver:navigator.webdriver,width:v.videoWidth,height:v.videoHeight,decodedFrames:v.getVideoPlaybackQuality().totalVideoFrames,error:v.error?.message??null};});
    assert(result.ended&&result.muted&&result.webdriver&&!result.error&&result.decodedFrames>0);
    results.push({name,sha256:delivery.sha256,...result});
    console.log(JSON.stringify({played:name,...result}));
  }
  assert.deepEqual(errors,[]);
} finally {
  fs.writeFileSync(path.join(folder,'playback-qa.json'),JSON.stringify({status:'PLAYED_UNACCEPTED',results,errors,limits:['Headless silent decode verifies delivery, not fit, art or mobile acceptance.']},null,2)+'\n');
  await page.close();await browser.close();await new Promise(resolve=>server.close(resolve));
}
console.log(JSON.stringify(results));
