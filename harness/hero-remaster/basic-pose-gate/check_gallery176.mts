/** Actual matched review film playback; no character acceptance. */
import assert from 'node:assert/strict';
import {readFile,writeFile}from'node:fs/promises';
import {createHash}from'node:crypto';
import {webkit}from'playwright';
const[out,url]=process.argv.slice(2);assert(out&&url);
const hosted=process.argv.includes('--auth-stdin');
const auth=hosted?JSON.parse(await readFile('/dev/stdin','utf8'))as{token:string}:null;
if(hosted)assert(auth&&typeof auth.token==='string'&&auth.token.length>0);
const browser=await webkit.launch({headless:true});const rows=[];
try{
 for(const width of[390,1200]){
  const page=await browser.newPage({viewport:{width,height:844}}),errors:string[]=[];
  if(auth)await page.route(new URL(url).origin+'/**',r=>r.continue({headers:{...r.request().headers(),'OAI-Sites-Authorization':'Bearer '+auth.token}}));
  // The library can keep metadata/range requests open; the requested movie's
  // complete hash and playback establish readiness without global network idle.
  page.on('pageerror',e=>errors.push(e.message));await page.goto(url,{waitUntil:'domcontentloaded'});
  assert(await page.evaluate(()=>navigator.webdriver));assert.equal(await page.locator('video').count(),30);
  const card=page.locator('#sleeve-rebuild173'),video=card.locator('video');
  assert.match(await card.innerText(),/still rejected/);assert.equal(await video.getAttribute('src'),'media/sleeve-rebuild173-matched-side-gray.mp4');
  // Raw serialization avoids tsx helper injection into the browser closure.
  const bytes=await page.evaluate("(async()=>{const v=document.querySelector('#sleeve-rebuild173 video');return Array.from(new Uint8Array(await(await fetch(v.getAttribute('src'))).arrayBuffer()));})()")as number[];
  const hash=createHash('sha256').update(Buffer.from(bytes)).digest('hex');assert.equal(hash,'633f4f35eefdc08de9e82cfe47afdf043cec4533d6e58fed07b877a964988970');assert.equal(bytes.length,144949);
  await video.scrollIntoViewIfNeeded();
  await page.evaluate("(async()=>{const v=document.querySelector('#sleeve-rebuild173 video');if(!v.loop||!v.muted||!v.playsInline)throw Error('Missing silent inline loop policy');v.loop=false;v.dataset.presented='0';const count=()=>{v.dataset.presented=String(Number(v.dataset.presented)+1);if(!v.ended)v.requestVideoFrameCallback(count);};v.requestVideoFrameCallback(count);await v.play();})()");
  await page.waitForFunction(()=>document.querySelector<HTMLVideoElement>('#sleeve-rebuild173 video')!.ended,null,{timeout:20000});
  const played=await video.evaluate(v=>{const x=v as HTMLVideoElement;return{ended:x.ended,muted:x.muted,duration:x.duration,presentedCallbacks:Number(x.dataset.presented),error:x.error?.message??null};});
  assert(played.ended&&played.muted&&played.presentedCallbacks>0&&!played.error);assert(Math.abs(played.duration-386/48)<.03);assert.deepEqual(errors,[]);
  assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
  await page.screenshot({path:out+`/matched-${width}.png`});rows.push({width,SHA256:hash,bytes:bytes.length,...played,errors});await page.close();
 }
}finally{await browser.close();}
await writeFile(out+'/matched-check.json',JSON.stringify({status:hosted?'HOSTED_MATCHED_FILM_PLAYBACK_PASS':'LOCAL_MATCHED_FILM_PLAYBACK_PASS',rows,videos:30,limits:'Decoder playback at two headless WebKit widths only; not human access, physical iOS, character appearance, full pose or contact acceptance.'},null,2)+'\n');
console.log(JSON.stringify({widths:rows.map(r=>r.width),playedToEnd:true,errors:0}));
