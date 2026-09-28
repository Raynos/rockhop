/** Played, silent Snowline station-lip clips on the live dev app. */
import fs from 'node:fs';
import { captureClip, describeCamera } from './capture';
import { tickAtX } from './clip';
import { loadRecording } from './lib/recording';

const outDir = 'docs/evidence/snowline-retarget';
fs.mkdirSync(outDir, { recursive: true });
const clips = [
  { name: 's1-pro-controlled', file: `${outDir}/s1-lift-line-pro-skill3.rec.json`, x: 318 },
  { name: 's1-pro-held-go', file: `${outDir}/s1-lift-line-pro-held-go.rec.json`, x: 290 },
  { name: 's2-pro-held-go', file: `${outDir}/s2-cornice-pro-held-go.rec.json`, x: 160 },
  { name: 's3-pro-held-go', file: `${outDir}/s3-whiteout-pro-held-go.rec.json`, x: 50 },
].filter((clip) => process.argv[2] === undefined || process.argv[2] === clip.name);
interface ClipRow {
  name: string;
  recording: string;
  atTick: number;
  startTick: number;
  endTick: number;
  frames: number;
  seconds: number;
  camera: string;
  mp4: string;
  sheet: string;
}
const rows: ClipRow[] = [];
for (const clip of clips) {
  const recording = loadRecording(clip.file);
  const at = await tickAtX(recording, clip.x);
  if (at === null) throw new Error(`${clip.name} did not reach x=${clip.x}`);
  const startTick = Math.max(0, at - (clip.name.startsWith('s1') ? 180 : 120));
  const endTick = Math.min(at + (clip.name.startsWith('s1') ? 480 : 300), 120 * 120);
  const result = await captureClip({
    recording, outMp4: `${outDir}/${clip.name}.mp4`,
    fps: 30, width: 852, height: 393, quality: 'low',
    startTick, endTick, dev: true, cameraCheck: true,
  });
  const sheet = `${outDir}/${clip.name}-sheet.jpg`;
  fs.copyFileSync(result.sheet, sheet);
  rows.push({ name: clip.name, recording: clip.file, atTick: at, startTick, endTick,
    frames: result.frames, seconds: result.seconds, camera: describeCamera(result.camera),
    mp4: result.mp4, sheet });
  process.stdout.write(`${clip.name}: ${result.frames} frames, ${describeCamera(result.camera)}\n`);
}
const previous = fs.existsSync(`${outDir}/played-clips.json`) ? JSON.parse(fs.readFileSync(`${outDir}/played-clips.json`, 'utf8')) as typeof rows : [];
const merged = [...previous.filter((row) => !rows.some((next) => next.name === row.name)), ...rows];
fs.writeFileSync(`${outDir}/played-clips.json`, JSON.stringify(merged, null, 2));
