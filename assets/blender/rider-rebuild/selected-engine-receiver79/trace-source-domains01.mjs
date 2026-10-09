// Run only after the parent grants the serial CPU2 slot for this exact trace.
import {spawnSync} from 'node:child_process';
import {existsSync,readFileSync} from 'node:fs';
import {dirname,resolve} from 'node:path';
import {fileURLToPath} from 'node:url';

const here=dirname(fileURLToPath(import.meta.url));
const root=resolve(here,'../../../..');
const output=resolve(root,'harness/out/rider-rebuild/selected-engine-receiver79/source-domains01');
if(existsSync(output))throw new Error('Actual source-domains01 already exists; refuse replacement/retry');
const result=spawnSync('/opt/homebrew/bin/python3.13',[
  resolve(here,'source_walls.py'),'trace',resolve(here,'source47-inventory.json'),output,
],{cwd:root,stdio:'inherit',timeout:120000,killSignal:'SIGKILL',env:{...process.env,
  PYTHONPATH:resolve(root,'harness/out/rider-rebuild/selected-anatomical-hoodie-fit73/python'),
  OMP_NUM_THREADS:'2',OPENBLAS_NUM_THREADS:'2',MKL_NUM_THREADS:'2',
  VECLIB_MAXIMUM_THREADS:'2',NUMEXPR_NUM_THREADS:'2',PYTHONNOUSERSITE:'1',
}});
if(result.error)throw result.error;
if(result.status!==0)throw new Error(`Source trace failed: status=${result.status} signal=${result.signal}`);
const row=JSON.parse(readFileSync(resolve(output,'source-domain-report.json'),'utf8'));
console.log(JSON.stringify({status:row.status,faceCounts:row.faceCounts,
  actualClosureCutEdges:row.actualClosureCutEdges,opposingWallConflicts:row.opposingWallConflicts,
  actualClosurePaths:row.actualClosurePaths.length,sourceWallDomainsQualified:row.sourceWallDomainsQualified,
  report:resolve(output,'source-domain-report.json'),nativeExecuted:false,bakeExecuted:false}));
