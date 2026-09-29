/** Inventory and capture representative Rookie fault → checkpoint retry windows.
 *
 * `pnpm exec tsx harness/e2e/course-fault-retry.mts inventory`
 * `pnpm exec tsx harness/e2e/course-fault-retry.mts capture [course-id ...]`
 * The capture command uses the existing silent, headless production-game harness.
 */
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { execFileSync } from 'node:child_process';
import { build } from 'vite';
import { expandFrames, InputRecorder, quantizeInput } from '../../src/core/replay';
import type { InputFrame } from '../../src/core/types';
import { captureClip } from '../capture';
import { createSimFor } from '../lib/sim';
import { loadRecording, saveRecording } from '../lib/recording';

const courseIds = [
  'c1-low-tide', 'c2-crane-hop', 'c3-hull-breach',
  'a1-sawdust', 'a2-log-jam', 'a3-timberline',
  'd1-dust-devil', 'd2-conveyor', 'd3-rope-walk',
  's1-lift-line', 's2-cornice', 's3-whiteout',
] as const;
const root = process.cwd();
const out = path.join(root, 'docs/evidence/course-remaster/fault-retry');
const sha = (bytes: Buffer | string): string => crypto.createHash('sha256').update(bytes).digest('hex');
const head = execFileSync('git', ['rev-parse', 'HEAD'], { encoding: 'utf8' }).trim();
function sourceTreeSha256(): string {
  const digest = crypto.createHash('sha256');
  const visit = (dir: string): void => {
    for (const entry of fs.readdirSync(dir, { withFileTypes: true }).sort((a, b) => a.name.localeCompare(b.name))) {
      const full = path.join(dir, entry.name);
      if (entry.isDirectory()) visit(full);
      else if (entry.isFile()) { digest.update(path.relative(root, full)); digest.update(fs.readFileSync(full)); }
    }
  };
  visit(path.join(root, 'src'));
  return digest.digest('hex');
}
type EventRow = { tick: number; type: string; reason?: string; x: number; checkpoint: number; phase: string; hash: string };
type Candidate = { id: string; file: string; sha256: string; events: EventRow[]; faults: number; finished: boolean; finalHash: string; firstFault: EventRow | null; retry: EventRow | null; correctionTick: number | null };

function representativePair(row: Candidate): { fault: EventRow; retry: EventRow; firstActiveTick: number | null; before: InputFrame; after: InputFrame | null } | null {
  const faults = row.events.filter(e => e.type === 'fault' && e.reason !== 'restart');
  // D1's first terrace is the measured blind-readability fault. For the other
  // multi-fault riders, the last bail leads into the successful next attempt.
  const fault = row.id === 'd1-dust-devil' ? faults[0] : faults.at(-1);
  if (!fault) return null;
  const retry = row.events.find(e => e.type === 'restart' && e.tick > fault.tick);
  if (!retry) return null;
  const frames = expandFrames(loadRecording(path.join(root, row.file)));
  const before = frames[fault.tick - 1]!;
  let firstActiveTick: number | null = null;
  for (let i = retry.tick; i < frames.length; i++) {
    const f = frames[i]!;
    if (f.throttle > 0 || f.brake > 0 || f.lean !== 0) { firstActiveTick = i + 1; break; }
  }
  return { fault, retry, firstActiveTick, before, after: firstActiveTick ? frames[firstActiveTick - 1]! : null };
}

async function hashAtTick(file: string, tick: number): Promise<string> {
  const rec = loadRecording(file);
  const sim = await createSimFor(rec);
  for (const input of expandFrames(rec).slice(0, tick)) sim.step(input);
  return sim.hash();
}

async function inspect(id: string, file: string): Promise<Candidate> {
  const rec = loadRecording(file);
  if (rec.header.trackId !== id || (rec.header.bike ?? 'rookie') !== 'rookie') throw new Error(`Wrong course/bike: ${file}`);
  const sim = await createSimFor(rec);
  const events: EventRow[] = [];
  const frames = expandFrames(rec);
  for (let i = 0; i < frames.length; i++) {
    for (const event of sim.step(frames[i]!)) {
      if (event.type === 'fault' || event.type === 'restart') {
        const state = sim.state();
        events.push({ tick: i + 1, type: event.type, ...('reason' in event ? { reason: event.reason } : {}),
          x: state.bike.pos.x, checkpoint: state.checkpoint, phase: sim.phase(), hash: sim.hash() });
      }
    }
  }
  const firstFault = events.find(e => e.type === 'fault' && e.reason !== 'restart') ?? null;
  const retry = firstFault ? events.find(e => e.type === 'restart' && e.tick > firstFault.tick) ?? null : null;
  let correctionTick: number | null = null;
  if (retry) {
    for (let i = retry.tick; i < frames.length; i++) {
      const f = frames[i]!;
      if (f.throttle > 0 || f.brake > 0 || f.lean !== 0) { correctionTick = i + 1; break; }
    }
  }
  return { id, file: path.relative(root, file), sha256: sha(fs.readFileSync(file)), events,
    faults: sim.faults(), finished: sim.phase() === 'finished', finalHash: sim.hash(), firstFault, retry, correctionTick };
}

async function candidates(id: string): Promise<Candidate[]> {
  const dir = path.join(root, 'harness/inputs', id);
  const names = fs.readdirSync(dir).filter(name => /^stranger-.*\.json$/.test(name)).sort().reverse();
  const results: Candidate[] = [];
  for (const name of names) {
    try { results.push(await inspect(id, path.join(dir, name))); }
    catch (error) { console.error(`skip ${id}/${name}: ${String(error)}`); }
  }
  return results;
}

async function scriptedSnowline(id: string): Promise<Candidate> {
  if (!id.startsWith('s')) throw new Error(`${id} is not a Snowline course`);
  const clean = loadRecording(path.join(root, 'harness/inputs', id, 'bot-3.json'));
  const cleanInputs = expandFrames(clean);
  const reference = await createSimFor(clean);
  let cpOffset = 0;
  if (id === 's2-cornice') {
    for (let i = 0; i < cleanInputs.length; i++) {
      reference.step(cleanInputs[i]!);
      if (reference.state().checkpoint >= 2) { cpOffset = i + 1; break; }
    }
    if (!cpOffset) throw new Error('S2 clean reference never reaches checkpoint 2');
  }
  const go = quantizeInput({ throttle: 1 });
  const restart = quantizeInput({ restart: true });
  // Keep three 20-fps crash frames visible before the manual retry. A genuine
  // next-tick restart would vanish inside one rendered frame at this cadence.
  const crashHold = 18;
  const tailOptions = [
    { label: 'ease-go-24-ticks-then-clean', frames: [
      ...(Array(24).fill(quantizeInput({ throttle: 0.5 })) as InputFrame[]),
      ...cleanInputs.slice(cpOffset, cpOffset + 336),
    ] },
    { label: 'clean-reference', frames: cleanInputs.slice(cpOffset, cpOffset + 360) },
    { label: 'steady-half-go', frames: Array(360).fill(quantizeInput({ throttle: 0.5 })) as InputFrame[] },
    { label: 'steady-third-go', frames: Array(360).fill(quantizeInput({ throttle: 0.33 })) as InputFrame[] },
  ];
  for (const option of tailOptions) {
    const sim = await createSimFor(clean);
    const recorder = new InputRecorder({ ...clean.header, note: `scripted held-GO Rookie fault, ${crashHold}-tick visible crash hold, manual restart, ${option.label} 3 s tail; source ${head}` });
    let faultTick = 0;
    for (let tick = 1; tick <= 30 * clean.header.physicsHz; tick++) {
      recorder.push(go);
      const events = sim.step(go);
      if (events.some(event => event.type === 'fault')) { faultTick = tick; break; }
    }
    if (!faultTick) throw new Error(`${id}: held GO did not fault within 30 seconds`);
    for (let i = 0; i < crashHold; i++) { const neutral = quantizeInput({}); recorder.push(neutral); sim.step(neutral); }
    recorder.push(restart);
    const restartEvents = sim.step(restart);
    if (sim.phase() !== 'riding' || !restartEvents.some(event => event.type === 'restart')) throw new Error(`${id}: next-tick manual restart did not restore riding`);
    const restartX = sim.state().bike.pos.x;
    const faults = sim.faults();
    for (const input of option.frames) { recorder.push(input); sim.step(input); }
    const progressed = sim.state().bike.pos.x > restartX + 2;
    if (sim.faults() === faults && progressed) {
      const file = path.join(out, id, 'scripted-input.json');
      saveRecording(file, recorder.toRecording());
      console.log(`${id}: scripted from ${option.label}, fault t${faultTick}, visible ${crashHold}-tick hold then manual restart, moved ${(sim.state().bike.pos.x - restartX).toFixed(1)} m with no second fault`);
      return inspect(id, file);
    }
  }
  throw new Error(`${id}: no scripted 3-second post-retry input progressed without a second fault`);
}

function choose(rows: Candidate[]): Candidate | null {
  const valid = rows.filter(row => row.firstFault && row.retry && row.correctionTick);
  // The last fault/retry/clear recording is strongest; otherwise keep a played
  // failed retry, accurately labelled in metadata.
  return valid.sort((a, b) => Number(b.finished) - Number(a.finished) || a.faults - b.faults || b.file.localeCompare(a.file))[0] ?? null;
}

const [command, ...requested] = process.argv.slice(2);
if (command !== 'inventory' && command !== 'prepare' && command !== 'capture') throw new Error('Use inventory, prepare or capture [course-id ...]');
const selected = requested.length ? requested : [...courseIds];
for (const id of selected) if (!(courseIds as readonly string[]).includes(id)) throw new Error(`Unknown course ID ${id}`);

const sourceTree = sourceTreeSha256();
if (command === 'capture') {
  await build({ root, configFile: path.join(root, 'vite.config.ts'), logLevel: 'error' });
  if (sourceTreeSha256() !== sourceTree) throw new Error('Source changed during production build');
}
const buildIndexSha256 = command === 'capture' ? sha(fs.readFileSync(path.join(root, 'dist/index.html'))) : null;
for (const id of selected) {
  if (command === 'prepare') {
    if (id.startsWith('s')) await scriptedSnowline(id);
    continue;
  }
  const found = await candidates(id);
  const chosen = choose(found) ?? (command === 'capture' && id.startsWith('s') ? await scriptedSnowline(id) : null);
  if (!chosen) {
    console.log(`${id}: no stranger recording with fault, retry and corrective input`);
    if (command === 'inventory') {
      const clean = loadRecording(path.join(root, 'harness/inputs', id, 'bot-3.json'));
      const sim = await createSimFor(clean);
      const go: InputFrame = { throttle: 1, brake: 0, lean: 0, hop: false, restart: false };
      for (let tick = 1; tick <= 30 * clean.header.physicsHz; tick++) {
        const events = sim.step(go);
        if (events.some(event => event.type === 'fault')) {
          console.log(`  held GO Rookie fault t${tick} x${sim.state().bike.pos.x.toFixed(1)} checkpoint ${sim.state().checkpoint}`);
          break;
        }
      }
    }
    continue;
  }
  const pair = representativePair(chosen);
  if (!pair) { console.log(`${id}: selected input lost representative fault/retry`); continue; }
  const { fault, retry } = pair;
  const hz = loadRecording(path.join(root, chosen.file)).header.physicsHz;
  console.log(`${id}: ${chosen.file} fault t${fault.tick} x${fault.x.toFixed(1)} → retry t${retry.tick} (${((retry.tick - fault.tick) * 1000 / hz).toFixed(0)} ms), active input t${pair.firstActiveTick}; ${chosen.finished ? 'finished' : 'not finished'}`);
  if (command === 'inventory') {
    console.log(`  events: ${chosen.events.map(event => `${event.type}@${event.tick}/x${event.x.toFixed(1)}`).join(' ')}`);
    continue;
  }
  const dir = path.join(out, id);
  fs.mkdirSync(dir, { recursive: true });
  const totalInputTicks = expandFrames(loadRecording(path.join(root, chosen.file))).length;
  const startTick = Math.max(0, fault.tick - Math.round(1.5 * hz));
  const endTick = Math.min(totalInputTicks, (pair.firstActiveTick ?? retry.tick) + Math.round(2.5 * hz));
  const result = await captureClip({ recording: loadRecording(path.join(root, chosen.file)), outMp4: path.join(dir, 'played.mp4'),
    fps: 20, width: 852, height: 392, quality: 'high', tailSeconds: 0,
    startTick, endTick, build: false, cameraCheck: true });
  if (sourceTreeSha256() !== sourceTree) throw new Error(`${id}: source changed during browser capture`);
  const endInputTick = Math.min(totalInputTicks, Math.floor(startTick / (hz / 20)) * (hz / 20) + result.frames * (hz / 20));
  const expectedEndHash = await hashAtTick(path.join(root, chosen.file), endInputTick);
  if (result.finalHash !== expectedEndHash) throw new Error(`${id}: browser clip hash ${result.finalHash} != Node ${expectedEndHash} at input tick ${endInputTick}`);
  const report = { courseId: id, sourceHead: head, sourceTreeSha256: sourceTree, buildIndexSha256,
    origin: chosen.file.includes('scripted-input') ? 'scripted Rookie held-GO + manual restart' : 'briefed CLI Rookie recording',
    recording: chosen.file, recordingSha256: chosen.sha256,
    recordingFinished: chosen.finished, recordingFinalHash: chosen.finalHash,
    window: { startTick, endTick, fps: 20, width: 852, height: 392 },
    fault, retry, allFaultRestartEvents: chosen.events,
    faultToRestartTicks: retry.tick - fault.tick,
    faultToRestartMsSim: (retry.tick - fault.tick) * 1000 / hz,
    firstActiveInputTick: pair.firstActiveTick,
    faultToActiveInputMsSim: pair.firstActiveTick ? (pair.firstActiveTick - fault.tick) * 1000 / hz : null,
    inputAtFault: pair.before, firstActiveInputAfterRetry: pair.after,
    firstActiveInputChanged: pair.after ? JSON.stringify(pair.before) !== JSON.stringify(pair.after) : null,
    browserClip: { frames: result.frames, seconds: result.seconds, finalHash: result.finalHash,
      expectedNodeHash: expectedEndHash, endInputTick, physicsStateTick: result.ticksSimulated,
      mp4Sha256: sha(fs.readFileSync(result.mp4)), camera: result.camera, wallMs: result.wallMs },
    limitations: 'Silent headless browser at landscape phone geometry. Latencies are simulation time from recorded fault to automatic checkpoint restart and the first subsequent non-neutral input, not physical touch or rendered wall-clock latency. A non-neutral input need not be an effective correction. The prior prefix is stepped without frames; the window itself is played.' };
  fs.writeFileSync(path.join(dir, 'capture.json'), JSON.stringify(report, null, 2) + '\n');
  console.log(`  captured ${result.frames} frames / ${result.seconds.toFixed(2)} s → ${path.relative(root, result.mp4)}`);
}
