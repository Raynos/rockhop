/** Reproduce the C3 breach motion clip from the qualified input recording on the live dev app. */
import { captureClip, describeCamera } from './capture';
import { loadRecording } from './lib/recording';

const recording = loadRecording('harness/inputs/c3-hull-breach/bot-3.json');
const first = process.argv[2] === 'first';
const suffix = process.argv[3] === 'overhead' ? '-overhead' : '';
const result = await captureClip({
  recording,
  outMp4: `docs/evidence/coast-retarget/c3-breach-${first ? 'fail' : 'clear'}${suffix}.mp4`,
  fps: 30, width: 852, height: 393, quality: 'low',
  startTick: first ? 2265 : 3036, endTick: first ? 2865 : 3636,
  dev: true,
  cameraCheck: true,
});
process.stdout.write(`${JSON.stringify({ frames: result.frames, camera: describeCamera(result.camera) }, null, 2)}\n`);
