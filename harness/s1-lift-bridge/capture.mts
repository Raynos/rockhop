/** Silent, played before/after station route evidence at phone-landscape dimensions. */
import fs from 'node:fs';
import path from 'node:path';
import { captureClip, describeCamera } from '../capture';
import { tickAtX } from '../clip';
import { loadRecording } from '../lib/recording';

const root = path.resolve('docs/evidence/s1-lift-bridge');
fs.mkdirSync(root, { recursive: true });
const rows = [];
for (const bike of ['pro', 'rookie'] as const) {
  const recording = loadRecording(`harness/inputs/s1-lift-line/bot-3${bike === 'pro' ? '-pro' : ''}.json`);
  const first = await tickAtX(recording, 277);
  const last = await tickAtX(recording, 311);
  if (first === null || last === null || first >= last) throw new Error(`${bike}: missing station window`);
  const dir = path.join(root, bike);
  fs.mkdirSync(dir, { recursive: true });
  const clip = await captureClip({ recording, outMp4: path.join(dir, 'clip.mp4'),
    fps: 20, width: 852, height: 393, quality: 'low', dev: true,
    startTick: first - 12, endTick: last + 12, cameraCheck: true });
  const sheet = path.join(dir, 'sheet.jpg');
  fs.copyFileSync(clip.sheet, sheet);
  if (clip.sheet !== sheet) fs.unlinkSync(clip.sheet);
  rows.push({ bike, first, last, frames: clip.frames, finalHash: clip.finalHash,
    camera: describeCamera(clip.camera), clip: path.relative(process.cwd(), clip.mp4),
    sheet: path.relative(process.cwd(), sheet) });
  console.log(`${bike}: ${clip.frames} frames, ${describeCamera(clip.camera)}`);
}
fs.writeFileSync(path.join(root, 'played-clips.json'), `${JSON.stringify(rows, null, 2)}\n`);
