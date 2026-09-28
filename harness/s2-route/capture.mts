/** Silent, played landscape comparison of S2's upper and lower lines. */
import fs from 'node:fs';
import path from 'node:path';
import { captureClip, describeCamera } from '../capture';
import { tickAtX } from '../clip';
import { loadRecording } from '../lib/recording';

const outDir = path.resolve('docs/evidence/s2-wind-shelf');
const cases = [
  { name: 's2-rookie-lower', file: 'harness/inputs/s2-cornice/bot-3.json' },
  { name: 's2-pro-upper', file: path.join(outDir, 's2-pro-upper.rec.json') },
].filter(c => process.argv[2] === undefined || c.name === process.argv[2]);
const rows = [];
for (const c of cases) {
  const recording = loadRecording(c.file);
  const xStart = await tickAtX(recording, 139);
  const xEnd = await tickAtX(recording, 204);
  if (xStart === null || xEnd === null) throw new Error(`${c.name} misses cornice window`);
  const startTick = Math.max(0, xStart - 100);
  const endTick = xEnd + 100;
  const result = await captureClip({ recording, outMp4: path.join(outDir, `${c.name}.mp4`),
    fps: 30, width: 852, height: 393, quality: 'low', startTick, endTick, dev: true, cameraCheck: true });
  const sheet = path.join(outDir, `${c.name}-sheet.jpg`);
  fs.copyFileSync(result.sheet, sheet);
  rows.push({ name: c.name, recording: c.file, startTick, endTick, frames: result.frames,
    camera: describeCamera(result.camera), mp4: result.mp4, sheet });
  console.log(`${c.name}: ${result.frames} frames, ${describeCamera(result.camera)}`);
}
fs.writeFileSync(path.join(outDir, 'played-clips.json'), `${JSON.stringify(rows, null, 2)}\n`);
