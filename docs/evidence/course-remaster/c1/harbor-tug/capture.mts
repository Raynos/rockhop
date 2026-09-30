/** Played C1 tug trial: exact same fixtures and landscape geometry before/after. */
import { createHash } from 'node:crypto';
import { mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import path from 'node:path';
import { captureClip } from '../../../../../harness/capture';
import { loadRecording } from '../../../../../harness/lib/recording';

const [outRoot] = process.argv.slice(2);
const url = process.env.C1_CAPTURE_URL;
const sha = process.env.C1_CAPTURE_SHA;
if (!outRoot || !url || !sha) throw new Error('C1_CAPTURE_URL=... C1_CAPTURE_SHA=... tsx capture.mts <out-dir>');
const output = path.resolve(outRoot);
const hash = (file: string): string => createHash('sha256').update(readFileSync(file)).digest('hex');
const cases = [
  { name: 'full', input: 'harness/inputs/c1-low-tide/bot-3.json', fps: 12, start: 0, end: undefined },
  { name: 'vessel', input: 'harness/inputs/c1-low-tide/bot-3.json', fps: 20, start: 1080, end: 1800 },
  { name: 'deck-fault', input: 'docs/evidence/c1-crash-feedback/held-go.json', fps: 20, start: 2040, end: 2460 },
] as const;
for (const c of cases) {
  const dest = path.join(output, c.name);
  mkdirSync(dest, { recursive: true });
  const result = await captureClip({ recording: loadRecording(c.input),
    outMp4: path.join(dest, 'clip.mp4'), fps: c.fps, width: 852, height: 392,
    quality: 'low', tailSeconds: 0, startTick: c.start,
    ...(c.end === undefined ? {} : { endTick: c.end }),
    url, expectSha: sha, cameraCheck: true });
  writeFileSync(path.join(dest, 'capture.json'), JSON.stringify({ input: c.input, inputSha256: hash(c.input),
    sourceVersionSha: sha, window: [c.start, c.end ?? null],
    ...result, clipSha256: hash(result.mp4) }, null, 2) + '\n');
  if (!result.camera?.pass) throw new Error(`${c.name}: camera check failed`);
  console.log(c.name, result.frames, result.seconds, result.finalHash);
}
