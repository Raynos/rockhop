/** Parent-owned A1 matched motion against immutable built outputs, silent Metal only. */
import { preview } from 'vite';
import path from 'node:path';
import { readFileSync } from 'node:fs';
import { createHash } from 'node:crypto';
const [distDir, outDir, only] = process.argv.slice(2);
if (!distDir || !outDir || process.env.TRIALS_BROWSER_BACKEND !== 'metal') throw Error('Requires Metal <frozen-dist> <out-dir> [case]');
const html=readFileSync(path.join(distDir,'index.html'),'utf8');
const entry=html.match(/data-entry="([^"]+)"/)![1]!;
const version=JSON.parse(readFileSync(path.join(distDir,'version.json'),'utf8')) as {sha:string};
const server=await preview({root:process.cwd(),configFile:path.resolve('vite.config.ts'),logLevel:'warn',build:{outDir:path.resolve(distDir)},preview:{host:'127.0.0.1',port:0}});
try {
  process.env.A1_CAPTURE_URL=server.resolvedUrls!.local[0]!;
  process.env.A1_CAPTURE_SHA=version.sha;
  process.env.A1_CAPTURE_INDEX_SHA=createHash('sha256').update(readFileSync(path.join(distDir,entry))).digest('hex');
  process.env.A1_EXPECT_MOUNT='1';
  process.argv=[process.argv[0]!, process.argv[1]!, outDir, ...(only?[only]:[])];
  await import(new URL('../../../../assets/blender/course-kits/alpine-trees/a1-frozen-capture.mts',import.meta.url).href);
} finally { await new Promise<void>((resolve,reject)=>server.httpServer.close(error=>error?reject(error):resolve())); }
