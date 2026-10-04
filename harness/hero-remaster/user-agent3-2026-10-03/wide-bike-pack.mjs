/** Pack existing captured pixels with an explicit constant30fps input clock. */
import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import { spawnSync } from 'node:child_process';
const out = path.resolve('harness/out/user-agent3-2026-10-03/presentation50');
const report = JSON.parse(fs.readFileSync(path.join(out, 'report.json')));
const sha = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
const source = fs.readFileSync('harness/hero-remaster/user-agent3-2026-10-03/wide-bike-presentation.mjs');
assert.equal(sha(source), report.captureSHA256);
fs.writeFileSync(path.join(out, 'executed-capture.mjs'), source, { flag: 'wx' });
const run = args => { const result = spawnSync('ffmpeg', ['-v', 'error', '-n', ...args], { encoding: 'utf8' }); assert.equal(result.status, 0, result.stderr); };
for (const c of report.cases) {
  assert(c.everyPhysicsTickMatchesPrior && c.inputTicks === 703 && c.samples.every(s => s.matrices.length === 51));
  run(['-r', '30', '-f', 'concat', '-safe', '0', '-i', path.join(out, c.mode, 'frames.txt'),
    '-vf', 'scale=960:720:flags=lanczos', '-r', '30', '-frames:v', String(c.frames),
    '-c:v', 'libx264', '-threads', '2', '-crf', '18', '-pix_fmt', 'yuv420p', '-an', '-movflags', '+faststart', path.join(out, c.mode, 'constant-clock.mp4')]);
}
const film = path.join(out, 'wide-slow-final.mp4');
run(['-i', path.join(out, 'off/constant-clock.mp4'), '-i', path.join(out, 'on/constant-clock.mp4'),
  '-filter_complex', '[0:v][1:v]hstack=inputs=2[v]', '-map', '[v]', '-c:v', 'libx264', '-threads', '2',
  '-crf', '18', '-pix_fmt', 'yuv420p', '-an', '-movflags', '+faststart', film]);
const probe = spawnSync('ffprobe', ['-v', 'error', '-count_frames', '-show_entries', 'stream=codec_type,r_frame_rate,avg_frame_rate,nb_read_frames,duration,width,height', '-of', 'json', film], { encoding: 'utf8' });
assert.equal(probe.status, 0, probe.stderr);
const stream = JSON.parse(probe.stdout).streams;
assert.equal(stream.length, 1); assert.equal(stream[0].codec_type, 'video');
assert.equal(stream[0].nb_read_frames, String(report.cases[0].frames));
assert.equal(stream[0].r_frame_rate, '30/1'); assert.equal(stream[0].width, 1920); assert.equal(stream[0].height, 720);
const receipt = { status: 'SINGLE_CAMERA_REPLACEMENT_CONSTANT_CLOCK_PACKED_UNACCEPTED',
  reportSHA256: sha(fs.readFileSync(path.join(out, 'report.json'))), packRecipeSHA256: sha(fs.readFileSync(new URL(import.meta.url))),
  captureRecipeSHA256: report.captureSHA256, final: { path: film, sha256: sha(fs.readFileSync(film)), ...stream[0] },
  inputTicks: 703, physicsHz: 120, ridingFrames: 176, ridingFilmSeconds: 176 / 30,
  actualRidingSeconds: 703 / 120, finalRidingFramePaddingSeconds: 176 / 30 - 703 / 120,
  originalLimitErratum: 'Initial capture report incorrectly says25ms padding; actual final partial riding frame padding is8.333333ms.',
  cameraOnlyPausedSeconds: 25, geometryMaterialRigPhysicsChanged: false,
  limits: ['Reuses exactly the same captured pixels. First pack retained privately; only this final single replacement is delivered.',
    'Read-only CPU framing and silent decode do not certify art, closed-solid seating, GPU output or iOS performance.'] };
fs.writeFileSync(path.join(out, 'pack.json'), JSON.stringify(receipt, null, 2) + '\n', { flag: 'wx' });
console.log(JSON.stringify(receipt));
