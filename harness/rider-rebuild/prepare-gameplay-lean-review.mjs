/** Pin the actual selected source and physics-driven private review. */
import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import crypto from 'node:crypto';
const [source, contractPath, target] = process.argv.slice(2);
assert(source && contractPath && target, 'SELECTED_GLB SELECTED_CONTRACT FRESH_OUTPUT_CONTRACT');
const hash = async filename => {
  const h = crypto.createHash('sha256');
  for await (const part of (await import('node:fs')).createReadStream(filename)) h.update(part);
  return h.digest('hex');
};
const contract = JSON.parse(await fs.readFile(contractPath));
assert.equal(contract.glbSHA256, await hash(source));
assert(!contract.corrective && !contract.nativeAuthoringMotion);
assert.equal(contract.weightDerivative?.kind, 'native-regional-weight-only');
contract.accepted = false; contract.qualificationState = 'UNACCEPTED_GAMEPLAY_LEAN_REVIEW';
delete contract.previewClip;
contract.gameplayLeanReview = { accepted: false, kind: 'simulated-rider-com-and-torso',
  sourcePins: await Promise.all(['src/core/riderGeometry.ts', 'src/game/game.ts', 'src/render/frame.ts',
    'harness/rider-rebuild/private-rider.mjs'].map(async name => ({ path: name, sha256: await hash(name) }))),
  selectedSource: { path: path.resolve(source), sha256: contract.glbSHA256 },
  limits: ['Actual input/physics-driven construction review only; source art, clothes and device acceptance remain open.'] };
await fs.mkdir(path.dirname(target), { recursive: true });
await fs.writeFile(target, JSON.stringify(contract, null, 2) + '\n', { flag: 'wx' });
console.log(JSON.stringify({ path: target, sha256: await hash(target), status: contract.qualificationState }));
