/** One explicit guarded stage: private sixth-rider build or recorded review. */
import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import { pathToFileURL } from 'node:url';
import { ROOT,hash,authority,gateContract,ownedOutput } from './gameplay-source.mjs';

const arg=name=>process.argv.find(v=>v.startsWith(`--${name}=`))?.slice(name.length+3);
const mode=arg('mode'),source=arg('source'),contractPath=arg('contract'),receipt=arg('export-receipt'),out=arg('out');
assert(['build','garage','comparison'].includes(mode));assert(source&&contractPath&&receipt&&out);
ownedOutput(out);
const report=await authority(receipt),contract=JSON.parse(await fs.readFile(contractPath));
assert.equal(path.resolve(source),path.resolve(ROOT,report.glb.path));
gateContract(contract,report,await hash(source),contract.qualificationState==='UNACCEPTED_GAMEPLAY_LEAN_REVIEW');
for(const flag of ['clip','garage-clip','dev-source','pose-calibration','near-similarity'])
  assert.equal(arg(flag),undefined,'Review preserves calibrated physical driver and actual Garage seating');
assert(!process.argv.includes('--allow-failed-diagnostic'));

const recipes={
  build:{path:'harness/rider-rebuild/build-private-engine.mjs',sha256:'6c637b02ecc4847a4980f86498fa2b6ac235e28b60a0a5c0d4f0eb0328595e70'},
  garage:{path:'harness/rider-rebuild/garage60-capture.mjs',sha256:'36db056ebd803d521d6c078060f552ae9fa026a894fbd9faa80d3bf16ab2111b'},
  comparison:{path:'harness/rider-rebuild/garage-comparison-review.mjs',sha256:'de2ef889324cde7e32cde11ed265623dac8048cb9594ecd8f077ac4abc45a90c'}
};
const recipe=recipes[mode],script=path.join(ROOT,recipe.path);
assert.equal(await hash(script),recipe.sha256);
let args=[`--source=${path.resolve(source)}`,`--contract=${path.resolve(contractPath)}`,`--out=${path.resolve(out)}`];
if(mode==='build')args.push('--comparison');
else {
  const build=arg('build');assert(build);ownedOutput(build);
  const input=JSON.parse(await fs.readFile(path.join(build,'rider-rebuild-inputs.json')));
  assert.equal(input.releaseBuild,false);assert.equal(input.comparison.id,'street-remastered');
  assert.equal(input.sourceSHA256,report.glb.sha256);
  assert.equal(input.metadataSHA256,await hash(contractPath));
  args.push(`--build=${path.resolve(build)}`,`--bike=${arg('bike')??'rookie'}`);
  if(mode==='garage') {
    assert.equal(process.env.TRIALS_BROWSER_BACKEND,'metal');
    args.push(`--seconds=${arg('seconds')??'18'}`);
  }
}
process.argv=[process.argv[0],script,...args];
const module=await import(pathToFileURL(script).href);
if(mode==='garage')await module.main(args);
