/** Decode existing played evidence silently. No model/game/rig/render capture. */
/* oxlint-disable eslint/no-undef -- headless video element and automation. */
import fs from 'node:fs';
import path from 'node:path';
import http from 'node:http';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import { webkit } from 'playwright';
const out=path.dirname(new URL(import.meta.url).pathname),root=process.cwd();
const clips=[{id:'native529',path:'docs/evidence/hero-remaster/anatomical-foundation-2026-10-03/user-agent1/diagnostic02/review/native-full-vs-four.mp4',sha256:'0187bd98b52ea8535574a0635295a3b70414ca59e6c37e634e9419ce82a07307',frames:133},{id:'actual50',path:'docs/evidence/hero-remaster/user-agent3-qa-2026-10-03/presentation50/wide-slow.mp4',sha256:'9159958962bf6e4a78f415afa50d00c335749fb4652c549975af5a37b8df86f2',frames:926}];
const sha=x=>crypto.createHash('sha256').update(x).digest('hex');
const server=http.createServer((req,res)=>{const clip=clips.find(c=>req.url==='/'+c.id);if(!clip){res.writeHead(404);res.end();return;}const bytes=fs.readFileSync(path.join(root,clip.path));res.writeHead(200,{'Content-Type':'video/mp4','Content-Length':bytes.length});res.end(bytes);});
await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
const browser=await webkit.launch({headless:true}),page=await browser.newPage();
const errors=[],results=[];page.on('pageerror',e=>errors.push(e.message));
await page.addInitScript(()=>{window.__body53Audio=0;for(const key of ['AudioContext','webkitAudioContext'])window[key]=class{constructor(){window.__body53Audio++;throw new Error('Silent existing movie playback');}};});
await page.goto('about:blank');
try{for(const clip of clips){assert.equal(sha(fs.readFileSync(path.join(root,clip.path))),clip.sha256);await page.setContent('<video id="film" muted playsinline></video>');await page.evaluate(async url=>{const v=document.querySelector('#film');v.muted=true;v.src=url;await v.play();},`http://127.0.0.1:${server.address().port}/${clip.id}`);await page.waitForFunction(()=>document.querySelector('#film').ended,null,{timeout:45000});const row=await page.evaluate(()=>{const v=document.querySelector('#film');return{webdriver:navigator.webdriver,muted:v.muted,ended:v.ended,durationS:v.duration,decodedFrames:v.getVideoPlaybackQuality().totalVideoFrames,width:v.videoWidth,height:v.videoHeight,audioContexts:window.__body53Audio,error:v.error?.message??null};});assert(row.webdriver&&row.muted&&row.ended&&!row.error&&row.audioContexts===0&&row.decodedFrames===clip.frames,JSON.stringify(row));results.push({...clip,...row});console.log(JSON.stringify({id:clip.id,...row}));}assert.deepEqual(errors,[]);}finally{fs.writeFileSync(path.join(out,'playback.json'),JSON.stringify({status:'SILENT_EXISTING_PLAYED_CLIPS_UNACCEPTED',results,errors,limits:['Existing dressed footage conceals body shoulders/hips. Playback confirms continuity/decoding, not art acceptance. Actual50 film does not witness garment47 numeric frames. No new model or pose capture.']},null,2)+'\n');await page.close();await browser.close();await new Promise(resolve=>server.close(resolve));}
