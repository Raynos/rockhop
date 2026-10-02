/** Play the matched encoded film silently; no subjective quality certificate. */
import assert from 'node:assert/strict';
import {readFile,writeFile}from'node:fs/promises';
import {createHash}from'node:crypto';
import {createServer}from'node:http';
import {webkit}from'playwright';
const[file,out]=process.argv.slice(2);assert(file&&out);
const bytes=await readFile(file),hash=createHash('sha256').update(bytes).digest('hex');
const server=createServer((req,res)=>{
 if(req.url==='/movie.mp4'){res.writeHead(200,{'Content-Type':'video/mp4','Content-Length':bytes.length});res.end(bytes);return;}
 res.writeHead(200,{'Content-Type':'text/html'});res.end('<video muted playsinline controls src="/movie.mp4"></video>');
});await new Promise<void>(r=>server.listen(0,'127.0.0.1',r));
const address=server.address();assert(address&&typeof address==='object');
const browser=await webkit.launch({headless:true});const page=await browser.newPage();const errors:string[]=[];page.on('pageerror',e=>errors.push(e.message));
try{
 await page.goto(`http://127.0.0.1:${address.port}`);assert(await page.evaluate(()=>navigator.webdriver));
 // Raw browser code avoids tsx keepNames helpers inside a serialized closure.
 await page.evaluate("(async()=>{const v=document.querySelector('video');v.muted=true;v.dataset.presented='0';const count=()=>{v.dataset.presented=String(Number(v.dataset.presented)+1);if(!v.ended)v.requestVideoFrameCallback(count);};v.requestVideoFrameCallback(count);await v.play();})()");
 await page.waitForFunction(()=>document.querySelector('video')!.ended,null,{timeout:20000});
 const video=await page.evaluate(()=>{const v=document.querySelector('video')!;return{ended:v.ended,muted:v.muted,duration:v.duration,currentTime:v.currentTime,presentedCallbacks:Number(v.dataset.presented),error:v.error?.message??null};});
 assert(video.ended&&video.muted&&video.presentedCallbacks>0&&!video.error);assert.deepEqual(errors,[]);
 await writeFile(out,JSON.stringify({status:'MATCHED_FILM_SILENT_PLAYBACK_TO_END_ONLY',file,SHA256:hash,bytes:bytes.length,video,errors,limits:'Local headless decoder playback only; not all-frame subjective inspection, anatomy/cloth/basic-pose or device acceptance.'},null,2)+'\n');console.log(JSON.stringify({playedToEnd:video.ended,seconds:video.duration,muted:video.muted}));
}finally{await page.close();await browser.close();await new Promise<void>((r,j)=>server.close(e=>e?j(e):r()));}
