/** Silent headless event-loop review controls; not character acceptance. */
import assert from 'node:assert/strict';
import {readFile,writeFile} from 'node:fs/promises';
import {webkit} from 'playwright';
const [out,url]=process.argv.slice(2);assert(out&&url);
const hosted=process.argv.includes('--auth-stdin');
const auth:unknown=hosted?JSON.parse(await readFile('/dev/stdin','utf8')):null;
if(hosted)assert(auth&&typeof auth==='object'&&'token'in auth&&typeof auth.token==='string'&&auth.token.length>0);
const browser=await webkit.launch({headless:true});const rows=[];
const events=[['Maximum forward lean',29/12,42/12],['Saddle crossing',174/12,199/12],['Maximum back lean',420/12,433/12],['Landing and recovery',440/12,453/12]] as const;
try {
 for(const width of [390,1200]) {
  const page=await browser.newPage({viewport:{width,height:844}});const errors:string[]=[];
  if(hosted)await page.route(new URL(url).origin+'/**',route=>route.continue({headers:{...route.request().headers(),'OAI-Sites-Authorization':'Bearer '+(auth as {token:string}).token}}));
  page.on('pageerror',e=>errors.push(e.message));await page.goto(url,{waitUntil:'networkidle'});
  assert(await page.evaluate(()=>navigator.webdriver));
  assert.equal(await page.locator('video').count(),29);
  const groups=page.getByRole('group',{name:'Loop riding review moments'});assert.equal(await groups.count(),2);
  for(let index=0;index<2;index++) {
   const group=groups.nth(index),card=group.locator('..'),video=card.locator('video');
   for(const [label,start,end]of events) {
    await group.getByRole('button',{name:label,exact:true}).click();
    await page.waitForFunction(({index,label})=>{
     const v=[...document.querySelectorAll<HTMLVideoElement>('#structural-gate video')].filter(v=>/physical157/.test(v.getAttribute('src')??''))[index];
     return v?.dataset.reviewEvent===label&&!v.paused&&Number(v.dataset.reviewLoops)>0;
    },{index,label},{timeout:15000});
    const rec=await video.evaluate(v=>{const x=v as HTMLVideoElement;return {event:x.dataset.reviewEvent,start:Number(x.dataset.reviewStart),end:Number(x.dataset.reviewEnd),loops:Number(x.dataset.reviewLoops),time:x.currentTime,muted:x.muted,error:x.error?.message??null,source:x.getAttribute('src')};});
    assert.equal(rec.event,label);assert.equal(rec.start,start);assert.equal(rec.end,end);assert(rec.loops>0&&rec.muted&&!rec.error);assert(rec.time>=start-.05&&rec.time<=end+.35);
    rows.push({width,view:index,...rec});await video.evaluate(v=>(v as HTMLVideoElement).pause());
   }
   await group.getByRole('button',{name:'Full clip',exact:true}).click();
   await page.waitForFunction(index=>{const v=[...document.querySelectorAll<HTMLVideoElement>('#structural-gate video')].filter(v=>/physical157/.test(v.getAttribute('src')??''))[index];return v?.dataset.reviewEvent==='Full clip'&&!v.dataset.reviewStart&&!v.paused;},index);
   await group.getByRole('button',{name:'Maximum forward lean',exact:true}).focus();await page.keyboard.press('Enter');
   await page.waitForFunction(index=>{const v=[...document.querySelectorAll<HTMLVideoElement>('#structural-gate video')].filter(v=>/physical157/.test(v.getAttribute('src')??''))[index];return v?.dataset.reviewEvent==='Maximum forward lean'&&!v.paused;},index);
   await video.evaluate(v=>{(v as HTMLVideoElement).currentTime=10;});
   await page.waitForFunction(index=>{const v=[...document.querySelectorAll<HTMLVideoElement>('#structural-gate video')].filter(v=>/physical157/.test(v.getAttribute('src')??''))[index];return v?.dataset.reviewEvent==='Full clip'&&!v.dataset.reviewStart;},index);
   await video.evaluate(v=>(v as HTMLVideoElement).pause());
  }
  assert.deepEqual(errors,[]);assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
  await page.screenshot({path:out+`/events-${width}.png`});await page.close();
 }
}finally{await browser.close();}
await writeFile(out+'/events-check.json',JSON.stringify({status:hosted?'HOSTED_SILENT_LOOP_CONTROLS_PASS':'LOCAL_SILENT_LOOP_CONTROLS_PASS',rows,keyboardAndNativeScrub:'Both views/both widths passed',videosPreserved:29,limits:hosted?'Authenticated headless WebKit playback at two widths only; not human access, physical iOS, mobile performance or character/contact acceptance.':'Local WebKit two widths only; not hosted playback, physical iOS or character/contact acceptance.'},null,2)+'\n');
console.log(JSON.stringify({windows:rows.length,widths:[390,1200],errors:0}));
