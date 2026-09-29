/** Silent, played S1 Pro bridge approach with the production HUD. */
import fs from 'node:fs';
import path from 'node:path';
import { captureClip, describeCamera } from '../capture';
import { tickAtX } from '../clip';
import { loadRecording } from '../lib/recording';
import { getTrack } from '../../src/tracks';
import { diamondRouteCue } from '../../src/ui/diamondRouteCue';

const outDir = path.resolve('docs/evidence/s1-lift-bridge');
const track = getTrack('s1-lift-line')!;
const cue = diamondRouteCue(track)!;
const recording = loadRecording(path.resolve('harness/inputs/s1-lift-line/bot-3-pro.json'));
const first = await tickAtX(recording, cue.x0 - 5);
const last = await tickAtX(recording, cue.x1 + 4);
if (first === null || last === null || first >= last) throw new Error('S1 recording misses bridge cue window');
const clip = await captureClip({
  recording,
  outMp4: path.join(outDir, 's1-pro-bridge-cue.mp4'),
  fps: 20,
  width: 852,
  height: 393,
  quality: 'low',
  build: true,
  startTick: Math.max(0, first - 48),
  endTick: last + 48,
  cameraCheck: true,
});
const sheet = path.join(outDir, 's1-pro-bridge-cue-sheet.jpg');
fs.copyFileSync(clip.sheet, sheet);
if (clip.sheet !== sheet) fs.unlinkSync(clip.sheet);
const report = {
  title: cue.title,
  action: cue.action,
  frames: clip.frames,
  finalHash: clip.finalHash,
  camera: describeCamera(clip.camera),
  startTick: Math.max(0, first - 48),
  endTick: last + 48,
};
fs.writeFileSync(path.join(outDir, 'cue-report.json'), `${JSON.stringify(report, null, 2)}\n`);
console.log(report);
