/** Silent played Pro upper-line windows through all four optional Diamond cues. */
import fs from 'node:fs';
import path from 'node:path';
import { captureClip, describeCamera } from '../capture';
import { tickAtX } from '../clip';
import { loadRecording } from '../lib/recording';
import { getTrack } from '../../src/tracks';
import { diamondRouteCue } from '../../src/ui/diamondRouteCue';

const outDir = path.resolve('docs/evidence/diamond-route-cues');
fs.mkdirSync(outDir, { recursive: true });
const ids = ['d3-rope-walk', 's1-lift-line', 's2-cornice', 's3-whiteout'];
const rows = [];
for (const [index, id] of ids.entries()) {
  const track = getTrack(id)!;
  const cue = diamondRouteCue(track)!;
  if (!cue) throw new Error(`Missing Diamond cue for ${id}`);
  const file = path.resolve(`harness/inputs/${id}/bot-3-pro.json`);
  const recording = loadRecording(file);
  const first = await tickAtX(recording, cue.x0 - 5);
  const last = await tickAtX(recording, cue.x1 + 4);
  if (first === null || last === null || first >= last) throw new Error(`${id} misses cue window`);
  const startTick = Math.max(0, first - 48);
  const endTick = last + 48;
  const clip = await captureClip({ recording, outMp4: path.join(outDir, `${id}-pro.mp4`),
    fps: 20, width: 852, height: 393, quality: 'low', build: index === 0,
    startTick, endTick, cameraCheck: true });
  const sheet = path.join(outDir, `${id}-pro-sheet.jpg`);
  fs.copyFileSync(clip.sheet, sheet);
  if (clip.sheet !== sheet) fs.unlinkSync(clip.sheet);
  rows.push({ id, goal: cue.goalId, title: cue.title, action: cue.action, startTick, endTick,
    frames: clip.frames, finalHash: clip.finalHash, camera: describeCamera(clip.camera),
    clip: path.relative(process.cwd(), clip.mp4), sheet: path.relative(process.cwd(), sheet) });
  console.log(`${id}: ${clip.frames} frames, ${describeCamera(clip.camera)}`);
}
fs.writeFileSync(path.join(outDir, 'report.json'), `${JSON.stringify(rows, null, 2)}\n`);
