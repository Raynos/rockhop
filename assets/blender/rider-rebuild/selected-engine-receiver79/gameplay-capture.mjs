/** Parent guarded Metal invocation; exact existing1200-input capture/replay. */
import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import { ROOT,CAPTURE,hash,gateContract,authority,ownedOutput } from './gameplay-source.mjs';
const arg=name=>process.argv.find(v=>v.startsWith(`--${name}=`))?.slice(name.length+3);
const source=arg('source'),contractPath=arg('contract'),receiptPath=arg('export-receipt');
assert(source&&contractPath&&receiptPath&&arg('out'));
assert.equal(arg('backend'),'metal');assert.equal(arg('camera-yaw'),'0');
assert(['rookie','pro'].includes(arg('bike')));ownedOutput(arg('out'));
const report=await authority(receiptPath),contract=JSON.parse(await fs.readFile(contractPath));
assert.equal(path.resolve(source),path.resolve(ROOT,report.glb.path));
gateContract(contract,report,await hash(source),true);
assert.equal(contract.gameplayLeanReview.selectedSource.path,path.resolve(source));
const capture=path.join(ROOT,CAPTURE.path);assert.equal(await hash(capture),CAPTURE.sha256);
// Preserve every input, selected-asset response witness,120Hz step, silent URL,
// headless Metal check and actual physical-pose/no-stage assertion in the source.
const child=spawn(process.execPath,[capture,...process.argv.slice(2).filter(v=>!v.startsWith('--export-receipt='))],
  {cwd:ROOT,stdio:'inherit',env:{...process.env,TRIALS_BROWSER_BACKEND:'metal'}});
await new Promise((resolve,reject)=>{child.once('error',reject);child.once('exit',(code,signal)=>{
  process.exitCode=code??1;if(signal) console.error(`Capture child stopped: ${signal}`);resolve();});});
