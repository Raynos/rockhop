/** Silent FFmpeg reference PCM with explicit mono duplication; preserve stereo L/R. */
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';

export function decodeStereoReference(local: string): { pcm: Buffer; sourceChannels: number; channelMapping: string } {
  const probe = spawnSync('ffprobe', ['-v', 'error', '-select_streams', 'a:0', '-show_entries', 'stream=channels', '-of', 'csv=p=0', local], { encoding: 'utf8' });
  assert.equal(probe.status, 0, `ffprobe reference channels: ${local}`);
  const sourceChannels = Number(probe.stdout.trim());
  assert.ok(sourceChannels === 1 || sourceChannels === 2, `reference expects mono/stereo: ${local} has ${sourceChannels} channels`);
  const args = ['-v', 'error', '-i', local];
  // Default -ac2 attenuates mono by sqrt(0.5). Native mono PCM retains its original amplitude.
  if (sourceChannels === 1) args.push('-af', 'pan=stereo|c0=c0|c1=c0');
  args.push('-f', 'f32le', '-ac', '2', '-ar', '48000', 'pipe:1');
  const decoded = spawnSync('ffmpeg', args, { maxBuffer: 128 * 1024 * 1024 });
  assert.equal(decoded.status, 0, `ffmpeg reference decode: ${local}`);
  return { pcm: decoded.stdout, sourceChannels, channelMapping: sourceChannels === 1 ? 'mono duplicated equally into L/R at unity gain' : 'stereo L/R preserved' };
}
