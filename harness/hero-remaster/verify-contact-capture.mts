/** CPU-only verification of a private short contact-integration capture; no browser launch. */
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import { Game } from '../../src/game/game';
import { createBikePhysicsV2 } from '../../src/physics/v2/bike';
import { decodeJSON, expandFrames } from '../../src/core/replay';
import type { GameRenderer } from '../../src/render/index';
import { CONTACT_IDS } from './surface-contacts.mjs';

const [evidencePath, outputPath] = process.argv.slice(2);
assert(evidencePath && outputPath, 'evidence.json output.json required');
assert(!fs.existsSync(outputPath), 'verification output must be fresh');
const bytes = fs.readFileSync(evidencePath), evidence = JSON.parse(bytes.toString('utf8'));
const sha = (data: Buffer) => crypto.createHash('sha256').update(data).digest('hex');
assert.equal(evidence.physics, 'v2');
assert.equal(evidence.prefixRendered, true);
assert.equal(evidence.automationProof.webdriver, true);
assert.equal(evidence.automationProof.audioContexts, 0);
assert.equal(evidence.errors.length, 0);
assert.equal(evidence.surfaceContactProof.setup.suppliedMapping, false);
assert.equal(evidence.surfaceContactProof.mappingSHA256, null);
assert.equal(evidence.surfaceContactProof.browserBundleSHA256, sha(fs.readFileSync(path.join(path.dirname(evidencePath), 'contact-probe.js'))));
const recordingBytes = fs.readFileSync(evidence.recording);
assert.equal(sha(recordingBytes), evidence.recordingSha256);
const recording = decodeJSON(recordingBytes.toString('utf8'));
const game = new Game({ physics: createBikePhysicsV2(recording.header.physicsHz), physicsHz: recording.header.physicsHz,
  renderer: { setTrack() {}, onEvent() {}, setQuality() {}, setBikeClass() {} } as unknown as GameRenderer,
  autoSkipCountdown: true, ghostEnabled: false });
game.loadTrack(recording.header.trackId, recording.header.seed, recording.header.bike);
const inputs = expandFrames(recording), samples = new Map<number, typeof evidence.trace[number]>(evidence.trace.map((sample: typeof evidence.trace[number]) => [sample.inputTick, sample]));
let matched = 0;
for (let tick = 1; tick <= evidence.to; tick++) {
  game.setInput(inputs[tick - 1]!); game.step(1);
  const sample = samples.get(tick);
  if (!sample) continue;
  assert.equal(sample.stateHash, game.hashState(), `input tick${tick} exact physics hash`);
  assert.equal(sample.stateJson, JSON.stringify(game.getState()), `input tick${tick} exact physics state bytes`);
  assert.equal(sample.phase, game.phase());
  assert.equal(sample.runTime, game.runTime());
  assert.equal(sample.renderedTime, game.getState().time);
  assert.deepEqual(Object.keys(sample.surfaceContacts).sort(), [...CONTACT_IDS].sort());
  for (const id of CONTACT_IDS) assert.deepEqual(sample.surfaceContacts[id], { status: 'unmeasured', reason: 'mapping missing or unsupported' });
  matched++;
}
assert.equal(matched, evidence.trace.length);
for (const hero of ['rider', 'bike']) {
  const entry = evidence.surfaceContactProof.setup[hero];
  assert.equal(entry.sha256, evidence.downloads[entry.url]);
  assert.equal(entry.sha256, evidence.assetBytes[entry.url]);
}
const report = { status: 'private unmeasured capture integration verified; actual rider contacts and later gates remain unmeasured',
  evidencePath: path.resolve(evidencePath), evidenceSHA256: sha(bytes), matchedSamples: matched, playedInputTicks: evidence.to,
  allFourContactsExplicitlyUnmeasured: true, stateJSONAndHashByteEquality: true, webdriver: true, audioContexts: 0,
  missingMapping: true, helperBundleSHA256: evidence.surfaceContactProof.browserBundleSHA256,
  consumedHeroByteProof: evidence.surfaceContactProof.setup, finishTime: game.getState().finishTime,
  limitation: 'short prefix only; no track-clear finish, actual mapped surfaces or visual contact gate proven',
  verifierSHA256: sha(fs.readFileSync('harness/hero-remaster/verify-contact-capture.mts')),
  physicsSourceSHA256: sha(fs.readFileSync('src/physics/v2/bike.ts')), riderGeometrySHA256: sha(fs.readFileSync('src/core/riderGeometry.ts')) };
fs.writeFileSync(outputPath, JSON.stringify(report, null, 2)+'\n');
console.log(JSON.stringify(report));
