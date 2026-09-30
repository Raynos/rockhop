/** Parent-only sequential silent headless captures; never builds or imports live app source. */
import fs from 'node:fs';
import path from 'node:path';
import http from 'node:http';
import { spawn } from 'node:child_process';
import { home, project, common, sha, verifySnapshot } from './prepare.mjs';
const [phase, which] = process.argv.slice(2);
if (!['before','after'].includes(phase) || (which && !['a2-full','a2-log','a3-full','a3-beam','a3-fault'].includes(which))) throw new Error('Usage: TRIALS_BROWSER_BACKEND=metal node capture.mjs before|after [a2-full|a2-log|a3-full|a3-beam|a3-fault]');
if(process.env.TRIALS_BROWSER_BACKEND!=='metal') throw new Error('Matched capture requires the parent-owned Metal lane');
const manifest=verifySnapshot();
const output=path.join(home,'out',phase),dist=path.join(output,'dist');
const build=JSON.parse(fs.readFileSync(path.join(output,'build.json'),'utf8'));
if(build.status!==0||build.prebuildAppSHA256!==manifest.appSHA256||build.bankSHA256!==manifest.bankSHA256) throw new Error('Successful build of the pinned inputs required');
const html=fs.readFileSync(path.join(dist,'index.html'),'utf8'),entry=html.match(/data-entry="([^"]+)"/)?.[1];
if(entry!==build.entry||sha(fs.readFileSync(path.join(dist,entry)))!==build.indexSHA256) throw new Error('Built entry fingerprint changed');
const catalogBytes=fs.readFileSync(path.join(dist,'model-catalog.json'));
if(sha(catalogBytes)!==build.catalogSHA256) throw new Error('Built model catalog changed');
const catalog=JSON.parse(catalogBytes.toString());
for(const asset of [...catalog.models,...catalog.resources]) if(sha(fs.readFileSync(path.join(dist,asset.url)))!==asset.sha256) throw new Error(`Built model/resource bytes changed: ${asset.logical}`);
const mime={'.js':'text/javascript','.json':'application/json','.html':'text/html','.css':'text/css','.wasm':'application/wasm','.webp':'image/webp','.png':'image/png','.jpg':'image/jpeg','.woff2':'font/woff2','.glb':'model/gltf-binary'};
const server=http.createServer((req,res)=>{
  try {
    const pathname=decodeURIComponent(new URL(req.url??'/','http://localhost').pathname);
    const file=path.resolve(dist,`.${pathname==='/'?'/index.html':pathname}`);
    if(!file.startsWith(dist+path.sep)||!fs.existsSync(file)||!fs.statSync(file).isFile()) {res.statusCode=404;res.end();return;}
    res.setHeader('Cross-Origin-Opener-Policy','same-origin');res.setHeader('Cross-Origin-Embedder-Policy','require-corp');
    res.setHeader('Cache-Control','no-store');res.setHeader('Content-Type',mime[path.extname(file)]??'application/octet-stream');
    res.end(fs.readFileSync(file));
  } catch(error) {res.statusCode=500;res.end(String(error));}
});
await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
try {
  const address=server.address();if(!address||typeof address==='string') throw new Error('Missing frozen server address');
  const env={...process.env,A1_CAPTURE_URL:`http://127.0.0.1:${address.port}/`,A1_CAPTURE_SHA:manifest.head,A1_CAPTURE_INDEX_SHA:build.indexSHA256,A1_EXPECT_MOUNT:phase==='after'?'1':'0'};
  const runner='prototypes/alpine-forest-rollout-v1/runner.mts';
  const bytes=fs.readFileSync(path.join(home,'runner.mts'));
  fs.mkdirSync(path.dirname(path.join(common,runner)),{recursive:true});
  fs.writeFileSync(path.join(common,runner),bytes);
  fs.writeFileSync(path.join(output,'capture-harness.json'),JSON.stringify({file:runner,sha256:sha(bytes),usesFrozenHarnessLibraries:true},null,2)+'\n');
  const args=[path.join(output,'captures'),...(which?[which]:[])];
  const status=await new Promise((resolve,reject)=>{
    const child=spawn(process.execPath,[path.join(project,'node_modules/tsx/dist/cli.mjs'),path.join(common,runner),...args],{cwd:common,env,stdio:'inherit'});
    child.once('error',reject);child.once('exit',code=>resolve(code??1));
  });
  if(status!==0) process.exitCode=Number(status);
} finally {await new Promise((resolve,reject)=>server.close(error=>error?reject(error):resolve()));}
