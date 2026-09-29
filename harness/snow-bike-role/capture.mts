/** Silent played Rookie lower-line clips to pair with the existing Pro upper-line clips. */
import fs from 'node:fs';
import path from 'node:path';
import { captureClip, describeCamera } from '../capture';
import { tickAtX } from '../clip';
import { loadRecording } from '../lib/recording';

const outDir = path.resolve('docs/evidence/snow-bike-role');
fs.mkdirSync(outDir, { recursive: true });
const cases = [
  { id: 's1-lift-line', x0: 276, x1: 303 },
  { id: 's2-cornice', x0: 147, x1: 174 },
  { id: 's3-whiteout', x0: 130, x1: 160 },
] as const;
const rows = [];
for (const { id, x0, x1 } of cases) {
  const recording = loadRecording(`harness/inputs/${id}/bot-3.json`);
  const first = await tickAtX(recording, x0);
  const last = await tickAtX(recording, x1);
  if (first === null || last === null || first >= last) throw new Error(`${id}: no lower-line window`);
  const startTick = Math.max(0, first - 24);
  const endTick = last + 24;
  const clip = await captureClip({ recording, outMp4: path.join(outDir, `${id}-rookie-lower.mp4`),
    fps: 20, width: 852, height: 393, quality: 'low', dev: true, startTick, endTick, cameraCheck: true });
  const sheet = path.join(outDir, `${id}-rookie-lower-sheet.jpg`);
  fs.copyFileSync(clip.sheet, sheet);
  if (clip.sheet !== sheet) fs.unlinkSync(clip.sheet);
  rows.push({ id, startTick, endTick, camera: describeCamera(clip.camera), frames: clip.frames,
    finalHash: clip.finalHash, mp4: path.relative(process.cwd(), clip.mp4), sheet: path.relative(process.cwd(), sheet) });
  console.log(`${id}: ${clip.frames} frames, ${describeCamera(clip.camera)}`);
}
fs.writeFileSync(path.join(outDir, 'played-clips.json'), `${JSON.stringify(rows, null, 2)}\n`);
