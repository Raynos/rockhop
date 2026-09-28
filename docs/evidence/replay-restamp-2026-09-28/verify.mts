/** Exact post-restamp node/browser hashes for flat-test and the shipped campaign. Silent headless verifier. */
import fs from 'node:fs';
import path from 'node:path';
import { expandFrames } from '../../../src/core/replay';
import { ROCKHOP_TRACKS } from '../../../src/tracks/rockhop';
import { srcFingerprint } from '../../../harness/lib/metrics';
import { loadRecording } from '../../../harness/lib/recording';
import { createSimFor } from '../../../harness/lib/sim';
import { BrowserVerifier } from '../../../harness/lib/verify';

const ids = ['flat-test', ...ROCKHOP_TRACKS.map(t => t.id)];
const files = ids.flatMap(id => ['bot-3.json', 'bot-3-pro.json'].map(name => path.join('harness', 'inputs', id, name)));
const verifier = new BrowserVerifier();
const rows: unknown[] = [];

try {
  // The verifier opens one frozen dist copy and one browser; three independent
  // pages at a time bound software-WebGL contention.
  for (let i = 0; i < files.length; i += 3) {
    const batch = await Promise.all(files.slice(i, i + 3).map(async file => {
      if (!fs.existsSync(file)) throw new Error(`missing golden: ${file}`);
      const rec = loadRecording(file);
      const sim = await createSimFor(rec);
      for (const frame of expandFrames(rec)) sim.step(frame);
      const browser = await verifier.run(rec);
      const nodeHash = sim.hash();
      const nodeFinishTime = sim.phase() === 'finished' ? sim.runTime() : null;
      return { file, src: srcFingerprint(), nodeHash, browserHash: browser.hash,
        hashEqual: nodeHash === browser.hash, nodeFinishTime, browserFinishTime: browser.finishTime,
        browserRunTime: browser.runTime, finishEqual: nodeFinishTime === browser.runTime,
        finishTickEqual: nodeFinishTime !== null && Math.round(nodeFinishTime * sim.hz) === Math.round(browser.runTime * sim.hz),
        stamp: /\bsrc=([0-9a-f]{8})\b/.exec(rec.header.note ?? '')?.[1] ?? null };
    }));
    rows.push(...batch);
  }
} finally {
  await verifier.close();
}
console.log(JSON.stringify({ sourceFingerprint: srcFingerprint(), rows }, null, 2));
if (rows.some(row => !(row as { hashEqual: boolean; finishTickEqual: boolean }).hashEqual || !(row as { hashEqual: boolean; finishTickEqual: boolean }).finishTickEqual)) process.exitCode = 1;
