/** Native MP3/AAC decoding and loop-window measurements. Never constructs a live AudioContext. */
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import fs from 'node:fs/promises';
import path from 'node:path';
import { webkit, type Page } from 'playwright';
import { MUSIC_CUES } from '../../src/audio/music/cues';
import type { SampleManifest } from '../../src/audio/samples/player';
import { launchBrowser } from '../lib/browser';
import { startServer } from '../lib/server';
import { decodeStereoReference } from './decode-reference';

interface WindowSpec { name: string; start: number; duration: number; loop: boolean }
interface AlignmentProbe { name: string; startSample: number; stride: number; samples: number[] }
interface DecodeJob { file: string; bytes: number; sha256: string; windows: WindowSpec[]; alignment?: AlignmentProbe[]; referenceSourceChannels?: number; referenceChannelMapping?: string }
interface CodecProbe { aac: string; wav: string; wavDecode: 'pass' | string; aacControlDecode?: 'pass' | string; aacAdtsControlDecode?: 'pass' | string; mp3ControlDecode?: 'pass' | string }
interface Measurement {
  file: string; sampleRate: number; channels: number; duration: number; frames: number;
  peak: number; peakDbfs: number;
  alignment: { name: string; nativeOffsetSamples: number; nativeOffsetSeconds: number; correlation: number; nativeRmsGainDb: number }[];
  windows: { name: string; inBounds: boolean; startSample: number; endSample: number; seamDerivativeRatio: number | null; energyStepDb50ms: number | null; maxAbsEnergyStepDb50ms: number | null }[];
}

// A plain JS evaluator avoids tsx keepNames injecting unavailable helpers in the browser.
const decodeSource = String.raw`async function(job) {
  var context = new OfflineAudioContext(2, 48000, 48000);
  var response = await fetch(job.file);
  if (!response.ok) throw new Error(job.file + ': HTTP ' + response.status);
  var bytes = await response.arrayBuffer();
  if (bytes.byteLength !== job.bytes) throw new Error(job.file + ': file changed during verification');
  var buffer = await new Promise(function(resolve, reject) {
    var failed = function(error) { reject(new Error('decodeAudioData rejected: ' + (error && error.name ? error.name + ': ' + error.message : String(error)))); };
    var promise = context.decodeAudioData(bytes, resolve, failed);
    if (promise && typeof promise.then === 'function') promise.then(resolve, failed);
  });
  var peak = 0;
  var windows = [];
  var rate = buffer.sampleRate;
  for (var channel = 0; channel < buffer.numberOfChannels; channel++) {
    var samples = buffer.getChannelData(channel);
    for (var i = 0; i < samples.length; i++) {
      if (!Number.isFinite(samples[i])) throw new Error(job.file + ': nonfinite PCM');
      peak = Math.max(peak, Math.abs(samples[i]));
    }
  }
  for (var window of job.windows) {
    var start = Math.round(window.start * rate);
    var end = Math.round((window.start + window.duration) * rate);
    var inBounds = start >= 0 && end > start && end <= buffer.length;
    var derivativeRatio = 0;
    var energyStep = 0;
    var maxAbsEnergyStep = 0;
    if (inBounds && window.loop) {
      var width = Math.min(Math.round(rate * 0.05), Math.floor((end - start) / 2));
      for (var channel = 0; channel < buffer.numberOfChannels; channel++) {
        var samples = buffer.getChannelData(channel);
        var before = 0;
        var after = 0;
        var derivativeEnergy = 0;
        var derivativeCount = 0;
        for (var i = 0; i < width; i++) {
          before += samples[end - width + i] ** 2;
          after += samples[start + i] ** 2;
          if (i > 0) {
            derivativeEnergy += (samples[end - width + i] - samples[end - width + i - 1]) ** 2;
            derivativeEnergy += (samples[start + i] - samples[start + i - 1]) ** 2;
            derivativeCount += 2;
          }
        }
        var seam = Math.abs(samples[start] - samples[end - 1]);
        var rmsDerivative = Math.sqrt(derivativeEnergy / Math.max(1, derivativeCount));
        derivativeRatio = Math.max(derivativeRatio, seam / Math.max(1e-9, rmsDerivative));
        var step = 10 * Math.log10(Math.max(after, 1e-20) / Math.max(before, 1e-20));
        if (Math.abs(step) > maxAbsEnergyStep) { maxAbsEnergyStep = Math.abs(step); energyStep = step; }
      }
    }
    windows.push({ name: window.name, inBounds: inBounds, startSample: start, endSample: end,
      seamDerivativeRatio: window.loop && inBounds ? derivativeRatio : null,
      energyStepDb50ms: window.loop && inBounds ? energyStep : null,
      maxAbsEnergyStepDb50ms: window.loop && inBounds ? maxAbsEnergyStep : null });
  }
  var alignment = [];
  for (var probe of job.alignment || []) {
    var reference = probe.samples;
    var mean = 0;
    for (var value of reference) mean += value;
    mean /= reference.length;
    var variance = 0;
    for (var value of reference) variance += (value - mean) ** 2;
    if (variance < 1e-12) continue;
    var best = -2;
    var bestOffset = 0;
    var bestVariance = 0;
    var maxOffset = Math.round(rate * 0.1);
    var phases = [[-maxOffset, maxOffset, 8], [0, 0, 1]];
    for (var phase = 0; phase < phases.length; phase++) {
      var lower = phase === 0 ? -maxOffset : bestOffset - 8;
      var upper = phase === 0 ? maxOffset : bestOffset + 8;
      var step = phases[phase][2];
      for (var offset = lower; offset <= upper; offset += step) {
        var first = probe.startSample + offset;
        if (first < 0 || first + (reference.length - 1) * probe.stride >= buffer.length) continue;
        var sum = 0;
        var squared = 0;
        var product = 0;
        for (var i = 0; i < reference.length; i++) {
          var position = first + i * probe.stride;
          var sample = 0;
          for (var channel = 0; channel < buffer.numberOfChannels; channel++) sample += buffer.getChannelData(channel)[position];
          sample /= buffer.numberOfChannels;
          sum += sample;
          squared += sample * sample;
          product += (reference[i] - mean) * sample;
        }
        var nativeVariance = squared - sum * sum / reference.length;
        var correlation = product / Math.sqrt(Math.max(1e-20, variance * nativeVariance));
        if (correlation > best) { best = correlation; bestOffset = offset; bestVariance = nativeVariance; }
      }
    }
    alignment.push({ name: probe.name, nativeOffsetSamples: bestOffset, nativeOffsetSeconds: bestOffset / rate, correlation: best,
      nativeRmsGainDb: 10 * Math.log10(Math.max(1e-20, bestVariance) / variance) });
  }
  return { file: job.file, sampleRate: rate, channels: buffer.numberOfChannels, duration: buffer.duration,
    frames: buffer.length, alignment: alignment, peak: peak, peakDbfs: 20 * Math.log10(Math.max(peak, 1e-20)), windows: windows };
}`;

const controlFrames = 48000;
const control = new Uint8Array(44 + controlFrames * 2);
const controlView = new DataView(control.buffer);
for (const [offset, label] of [[0, 'RIFF'], [8, 'WAVE'], [12, 'fmt '], [36, 'data']] as const) {
  for (let i = 0; i < label.length; i++) control[offset + i] = label.charCodeAt(i);
}
controlView.setUint32(4, control.length - 8, true);
controlView.setUint32(16, 16, true);
controlView.setUint16(20, 1, true);
controlView.setUint16(22, 1, true);
controlView.setUint32(24, 48000, true);
controlView.setUint32(28, 96000, true);
controlView.setUint16(32, 2, true);
controlView.setUint16(34, 16, true);
controlView.setUint32(40, controlFrames * 2, true);
for (let i = 0; i < controlFrames; i++) controlView.setInt16(44 + i * 2, Math.sin(i * 2 * Math.PI * 440 / 48000) * 8192, true);
const controlsDir = path.resolve('harness/out/audio-remaster/codec-control');
await fs.mkdir(controlsDir, { recursive: true });
await fs.writeFile(path.join(controlsDir, 'control.wav'), control);
const encodedControls = new Map<string, Uint8Array>();
for (const [extension, codec] of [['m4a', 'aac'], ['aac', 'aac'], ['mp3', 'libmp3lame']] as const) {
  const result = spawnSync('ffmpeg', ['-v', 'error', '-y', '-i', path.join(controlsDir, 'control.wav'), '-c:a', codec, '-b:a', '128k', path.join(controlsDir, 'control.' + extension)]);
  if (result.status === 0) encodedControls.set(extension, await fs.readFile(path.join(controlsDir, 'control.' + extension)));
}
const probes = new Map<Page, CodecProbe>();

const jobs = new Map<string, DecodeJob>();
async function add(file: string, spec: WindowSpec, expectedBytes?: number): Promise<void> {
  const local = path.join('public', file);
  const stat = await fs.stat(local);
  if (expectedBytes !== undefined) assert.equal(stat.size, expectedBytes, `${local} manifest byte count`);
  let job = jobs.get(file);
  if (!job) { job = { file: '/' + file, bytes: stat.size, sha256: createHash('sha256').update(await fs.readFile(local)).digest('hex'), windows: [] }; jobs.set(file, job); }
  job.windows.push(spec);
}
for (const [name, cue] of Object.entries(MUSIC_CUES)) {
  await add('audio/' + cue!.file, { name: 'music:' + name, start: cue!.pre, duration: cue!.len, loop: cue!.loop }, cue!.bytes);
}
const manifest = JSON.parse(await fs.readFile('src/audio/samples/manifest.json', 'utf8')) as SampleManifest;
for (const [family, clips] of Object.entries(manifest.oneshots)) {
  for (let i = 0; i < (clips?.length ?? 0); i++) {
    const clip = clips![i]!;
    await add('audio/sfx/' + clip.file, { name: `${family}:${i}`, start: clip.start, duration: clip.duration, loop: false });
  }
}
for (const [zone, clip] of Object.entries(manifest.beds)) {
  await add('audio/sfx/' + clip!.file, { name: 'bed:' + zone, start: clip!.start, duration: clip!.duration, loop: true });
}
// Compare music, atlas clips and beds against FFmpeg's stereo gapless decode; no speakers.
for (const [file, job] of jobs) {
  const reference = decodeStereoReference(path.join('public', file));
  job.referenceSourceChannels = reference.sourceChannels;
  job.referenceChannelMapping = reference.channelMapping;
  const data = reference.pcm;
  job.alignment = [];
  for (const window of job.windows.slice(0, 6)) {
    const start = Math.round((window.start + Math.min(0.04, window.duration * 0.15)) * 48000);
    const count = Math.floor(Math.min(0.16, window.duration * 0.6) * 48000 / 6);
    const samples: number[] = [];
    for (let i = 0; i < count; i++) {
      const offset = (start + i * 6) * 8;
      if (offset + 8 > data.length) break;
      // Explicit (L+R)/2; unity mono duplication matches a native mono buffer's mean too.
      samples.push((data.readFloatLE(offset) + data.readFloatLE(offset + 4)) / 2);
    }
    if (samples.length > 20) job.alignment.push({ name: window.name, startSample: start, stride: 6, samples });
  }
}
assert.ok(jobs.size > 0, 'at least one delivered audio file');

const server = await startServer({ dev: true });
const engines: { engine: string; version: string; userAgent: string; codecs: CodecProbe; sampleRate: number; liveAudioContextAttempts: number; decoded: Measurement[] }[] = [];
const failures: string[] = [];
const protection = `window.__audioContextAttempts = 0;
window.AudioContext = function () { window.__audioContextAttempts++; throw new Error('Live audio forbidden in decode verification'); };
window.webkitAudioContext = window.AudioContext;`;
async function decodeAll(page: Page, engine: string): Promise<Measurement[]> {
  await page.addInitScript(protection);
  await page.route('**/audio-remaster-decode', (route) => route.fulfill({ contentType: 'text/html', body: '<!doctype html><title>Silent offline codec check</title>' }));
  await page.route('**/audio-remaster-control.wav', (route) => route.fulfill({ contentType: 'audio/wav', body: Buffer.from(control) }));
  for (const [extension, bytes] of encodedControls) {
    await page.route('**/audio-remaster-control.' + extension, (route) => route.fulfill({ contentType: extension === 'm4a' ? 'audio/mp4' : extension === 'aac' ? 'audio/aac' : 'audio/mpeg', body: Buffer.from(bytes) }));
  }
  await page.goto(new URL('/audio-remaster-decode', server.url).toString());
  const codec = await page.evaluate(`({aac: document.createElement('audio').canPlayType('audio/mp4; codecs="mp4a.40.2"'), wav: document.createElement('audio').canPlayType('audio/wav'), wavDecode: 'not-run'})`) as CodecProbe;
  try {
    await page.evaluate(`(${decodeSource})(${JSON.stringify({ file: '/audio-remaster-control.wav', bytes: control.length, windows: [] })})`);
    codec.wavDecode = 'pass';
  } catch (error) { codec.wavDecode = String(error); }
  for (const [extension, bytes] of encodedControls) {
    const key = extension === 'm4a' ? 'aacControlDecode' : extension === 'aac' ? 'aacAdtsControlDecode' : 'mp3ControlDecode';
    try {
      await page.evaluate(`(${decodeSource})(${JSON.stringify({ file: '/audio-remaster-control.' + extension, bytes: bytes.length, windows: [] })})`);
      codec[key] = 'pass';
    } catch (error) { codec[key] = String(error); }
  }
  probes.set(page, codec);
  const decoded: Measurement[] = [];
  for (const job of jobs.values()) {
    try {
      const measured = await page.evaluate(`(${decodeSource})(${JSON.stringify(job)})`) as Measurement;
      decoded.push(measured);
      for (const window of measured.windows) {
        if (!window.inBounds) failures.push(`${engine}: ${job.file} ${window.name}: window outside native decoder output`);
      }
      if (!(measured.peak > 0 && measured.peak <= 1.01)) failures.push(`${engine}: ${job.file}: invalid/silent decoded peak ${measured.peak}`);
    } catch (error) { failures.push(`${engine}: ${job.file}: ${String(error)}`); }
  }
  return decoded;
}
try {
  const chromium = await launchBrowser({ width: 480, height: 270 });
  try {
    const decoded = await decodeAll(chromium.page, 'chromium');
    engines.push({ engine: 'chromium', version: chromium.browser.version(), userAgent: await chromium.page.evaluate(() => navigator.userAgent), codecs: probes.get(chromium.page)!, sampleRate: 48000,
      liveAudioContextAttempts: await chromium.page.evaluate('window.__audioContextAttempts') as number, decoded });
  } finally { await chromium.close(); }
  const browser = await webkit.launch({ headless: true });
  try {
    const page = await browser.newPage();
    const decoded = await decodeAll(page, 'webkit');
    engines.push({ engine: 'webkit', version: browser.version(), userAgent: await page.evaluate(() => navigator.userAgent), codecs: probes.get(page)!, sampleRate: 48000,
      liveAudioContextAttempts: await page.evaluate('window.__audioContextAttempts') as number, decoded });
  } finally { await browser.close(); }
  for (const engine of engines) if (engine.liveAudioContextAttempts !== 0) failures.push(`${engine.engine}: live AudioContext attempted`);
  const report = {
    declarations: [...jobs.values()].map(({ alignment, ...job }) => ({ ...job, alignmentProbeWindows: alignment?.map(({ samples, ...probe }) => ({ ...probe, sampleCount: samples.length })) })),
    at: new Date().toISOString(), pass: failures.length === 0, files: jobs.size, engines, failures,
    measurements: { seamDerivativeRatio: 'Absolute wrap sample delta divided by RMS adjacent-sample derivative in both 50 ms windows; maximum across channels.', energyStepDb50ms: '10 log10(after RMS energy / before RMS energy), channel with greatest absolute change.', referenceChannelMapping: 'FFprobe source channels first. Mono uses explicit pan=stereo|c0=c0|c1=c0 at unity gain; stereo L/R remains unchanged. FFmpeg f32le -ac2 -ar48000, reference=(L+R)/2; native PCM uses its channel mean.', nativeAlignment: 'Positive nativeOffsetSamples means the native waveform starts later than FFmpeg. Search +/-100ms, coarse8samples then1sample refinement, 8kHz sampled probes; correlation1 is identical alignment.', nativeRmsGainDb: 'At the best matched offset, 10 log10(native centered energy / FFmpeg centered energy). DC is removed from each probe; positive dB means the native decoder is louder. Correlation is insensitive to this gain.', thresholds: 'File bytes, native decode, finite nonzero PCM <=1.01 peak, all declared windows in bounds are asserted. Seam, alignment and gain metrics are measured for the parent to judge against mastering requirements.' },
    limits: 'Playwright WebKit on macOS verifies the delivered codec through native WebKit decoding at 48kHz, not a physical iPhone pass. Only OfflineAudioContext is used; no playback/rendering context, source start or audible override.',
  };
  const out = path.resolve(process.argv[2] ?? 'harness/out/audio-remaster/native-decode.json');
  await fs.mkdir(path.dirname(out), { recursive: true });
  await fs.writeFile(out, JSON.stringify(report, null, 2) + '\n');
  console.log(JSON.stringify({ pass: report.pass, files: jobs.size, engines: engines.map((e) => ({ engine: e.engine, version: e.version, codecs: e.codecs, decoded: e.decoded.length, contexts: e.liveAudioContextAttempts,
    loops: e.decoded.flatMap((d) => d.windows.filter((w) => w.seamDerivativeRatio !== null).map((w) => ({ name: w.name, derivativeRatio: w.seamDerivativeRatio, energyStepDb: w.energyStepDb50ms }))) })), failures, report: out }, null, 2));
  assert.equal(failures.length, 0, failures.join('\n'));
} finally { await server.close(); }
