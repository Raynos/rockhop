import { createHash } from 'node:crypto';
import { mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import path from 'node:path';
import { captureClip } from '../../../../../harness/capture';
import { loadRecording } from '../../../../../harness/lib/recording';

const [inputsRoot, outputRoot] = process.argv.slice(2);
if (!inputsRoot || !outputRoot) throw new Error('capture.mts <inputs-repo> <output-dir>');
const root = path.resolve(inputsRoot);
const output = path.resolve(outputRoot);
const sha256 = (file: string): string => createHash('sha256').update(readFileSync(file)).digest('hex');
const cases = [
  { name: 'full', file: 'harness/inputs/c1-low-tide/bot-3.json', fps: 12, startTick: 0, endTick: undefined },
  { name: 'ramp', file: 'harness/inputs/c1-low-tide/bot-3.json', fps: 20, startTick: 1698, endTick: 2364 },
  { name: 'deck-fault', file: 'docs/evidence/c1-crash-feedback/held-go.json', fps: 20, startTick: 2040, endTick: 2460 },
] as const;
for (const item of cases) {
  const file = path.join(root, item.file);
  const dir = path.join(output, item.name);
  mkdirSync(dir, { recursive: true });
  const recording = loadRecording(file);
  const result = await captureClip({ recording, outMp4: path.join(dir, 'clip.mp4'),
    fps: item.fps, width: 852, height: 392, quality: 'low', tailSeconds: 0,
    startTick: item.startTick, ...(item.endTick === undefined ? {} : { endTick: item.endTick }),
    cameraCheck: true });
  const report = { input: item.file, inputSha256: sha256(file), window: [item.startTick, item.endTick ?? null],
    ...result, clipSha256: sha256(result.mp4) };
  writeFileSync(path.join(dir, 'capture.json'), `${JSON.stringify(report, null, 2)}\n`);
  console.log(`${item.name}: ${result.frames} frames, ${result.finalHash}, camera=${result.camera?.pass}`);
  if (!result.camera?.pass) throw new Error(`${item.name}: camera check failed`);
}
