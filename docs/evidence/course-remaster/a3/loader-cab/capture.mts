import { createHash } from 'node:crypto';
import { mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import path from 'node:path';
import { captureClip } from '../../../../../harness/capture';
import { loadRecording } from '../../../../../harness/lib/recording';

// Build the desired source first. Run once with before/, then again with after/.
const outRoot = process.argv[2];
if (!outRoot) throw new Error('capture.mts <out-dir>');
const sha = (file: string): string => createHash('sha256').update(readFileSync(file)).digest('hex');
const cases = [
  { name: 'full', input: 'harness/inputs/a3-timberline/bot-3.json', fps: 12, startTick: 0, endTick: undefined },
  { name: 'beam', input: 'harness/inputs/a3-timberline/bot-3.json', fps: 20, startTick: 1644, endTick: 2232 },
  { name: 'loader', input: 'harness/inputs/a3-timberline/bot-3.json', fps: 20, startTick: 2232, endTick: 2784 },
  { name: 'fault', input: 'harness/inputs/a3-timberline/stranger-a3-timberline-20260929-010154.json', fps: 20, startTick: 2364, endTick: 2724 },
] as const;
for (const item of cases) {
  const dir = path.resolve(outRoot, item.name);
  mkdirSync(dir, { recursive: true });
  const rec = loadRecording(item.input);
  const result = await captureClip({ recording: rec, outMp4: path.join(dir, 'clip.mp4'),
    fps: item.fps, width: 852, height: 392, quality: 'low', tailSeconds: 0,
    startTick: item.startTick, ...(item.endTick === undefined ? {} : { endTick: item.endTick }),
    cameraCheck: true });
  writeFileSync(path.join(dir, 'capture.json'), `${JSON.stringify({ input: item.input,
    inputSha256: sha(item.input), window: [item.startTick, item.endTick ?? null],
    ...result, clipSha256: sha(result.mp4) }, null, 2)}\n`);
  console.log(`${item.name}: ${result.frames} frames, ${result.finalHash}, camera=${result.camera?.pass}`);
  if (!result.camera?.pass) throw new Error(`${item.name}: camera check failed`);
}
