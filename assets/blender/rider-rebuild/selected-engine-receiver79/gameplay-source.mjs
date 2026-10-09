/** Narrow topology admission; all frozen gameplay preparation remains exact. */
import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';

export const ROOT = fileURLToPath(new URL('../../../../',import.meta.url));
export const PREPARE = {path:'harness/rider-rebuild/prepare-gameplay-lean-review.mjs',
  sha256:'ffedb8e76e4b522e356d7208754bc33b5338d9d1c8e742d27a455561f6a9733c'};
export const CAPTURE = {path:'harness/rider-rebuild/gameplay-lean-review.mjs',
  sha256:'3b459d6ba99bb90e0bb4d500e4be6b301834bc3f54c96310daf7339c7dbc1475'};
export const KIND='qualified-selected-receiver77-native52-fields';
// Sealed-span qualification imports NumPy; system Python3.9 lacks it.
export const AUTHORITY_PYTHON='/Applications/Blender.app/Contents/Resources/5.2/python/bin/python3.13';
export const hash = async filename => {
  const h=crypto.createHash('sha256');
  for await (const chunk of (await import('node:fs')).createReadStream(filename)) h.update(chunk);
  return h.digest('hex');
};
export function adaptPrepare(source) {
  const old="assert.equal(contract.weightDerivative?.kind, 'native-regional-weight-only');";
  assert.equal(source.split(old).length,2,'Frozen single admission assertion');
  return source.replace(old,`assert.equal(contract.topologyDerivative?.kind, '${KIND}');`);
}
export function gateContract(contract,report,sourceSHA,review=false) {
  assert.equal(contract.accepted,false);
  assert.equal(contract.glbSHA256,sourceSHA);assert.equal(report.glb.sha256,sourceSHA);
  assert.deepEqual(contract.topologyDerivative,report.derivative);
  assert.equal(contract.topologyDerivative.kind,KIND);
  for(const key of ['driver','nativeRest','specification'])
    assert.deepEqual(contract[key],report.expectedRuntime[key],'Pinned native10 calibrated contract: '+key);
  for (const key of ['weightDerivative','shapeDerivative','corrective','nativeAuthoringMotion','previewClip','genericActions','diagnosticMotion'])
    assert.equal(contract[key],undefined,'Topology review cannot carry old playback: '+key);
  assert.equal(contract.qualificationState,review?'UNACCEPTED_GAMEPLAY_LEAN_REVIEW':'UNACCEPTED_RECEIVER_TOPOLOGY_TRANSPORT');
  if(review) {assert.equal(contract.gameplayLeanReview.accepted,false);
    assert.equal(contract.gameplayLeanReview.kind,'simulated-rider-com-and-torso');}
}
export function authorityCommand(exportReceipt) {
  const helper=path.join(ROOT,'assets/blender/rider-rebuild/selected-engine-receiver79/proof.py');
  return {executable:AUTHORITY_PYTHON,args:[helper,'export-gate',path.resolve(exportReceipt)]};
}
export async function authority(exportReceipt) {
  const command=authorityCommand(exportReceipt);
  const result=spawnSync(command.executable,command.args,{cwd:ROOT,encoding:'utf8',
    env:{...process.env,OPENBLAS_NUM_THREADS:'2',OMP_NUM_THREADS:'2'}});
  assert.equal(result.status,0,result.stderr||result.stdout);
  const report=JSON.parse(await fs.readFile(exportReceipt));
  const contractPath=path.join(ROOT,report.contract.path);
  assert.equal(await hash(contractPath),report.contract.sha256);
  return {...report,expectedRuntime:JSON.parse(await fs.readFile(contractPath))};
}
export function ownedOutput(filename) {
  const absolute=path.resolve(filename),base=path.join(ROOT,'harness/out/rider-rebuild/selected-engine-receiver79');
  assert(absolute.startsWith(base+path.sep),'Only fresh private71 outputs');return absolute;
}
async function main() {
  const [source,contractPath,exportReceipt,target]=process.argv.slice(2);assert(source&&contractPath&&exportReceipt&&target);
  const report=await authority(exportReceipt);const contract=JSON.parse(await fs.readFile(contractPath));
  assert.equal(path.resolve(source),path.resolve(ROOT,report.glb.path));
  assert.equal(path.resolve(contractPath),path.resolve(ROOT,report.contract.path));
  gateContract(contract,report,await hash(source));ownedOutput(target);
  const frozen=await fs.readFile(path.join(ROOT,PREPARE.path),'utf8');
  assert.equal(crypto.createHash('sha256').update(frozen).digest('hex'),PREPARE.sha256);
  process.argv=[process.argv[0],path.join(ROOT,PREPARE.path),source,contractPath,target];
  await import('data:text/javascript;base64,'+Buffer.from(adaptPrepare(frozen)).toString('base64'));
}
if(process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url)) await main();
