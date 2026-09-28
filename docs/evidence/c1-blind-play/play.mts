import fs from 'node:fs';
import path from 'node:path';
import readline from 'node:readline';
import { fileURLToPath } from 'node:url';
import { startServer } from '../../../harness/lib/server';
import { launchBrowser } from '../../../harness/lib/browser';
import { openGame, HookClient } from '../../../harness/lib/hook';

const dir = path.dirname(fileURLToPath(import.meta.url));
const framesDir = path.join(dir, 'frames');
fs.mkdirSync(framesDir, { recursive: true });
const server = await startServer({ dev: true });
const launched = await launchBrowser({ width: 852, height: 392 });
const { page } = launched;
const hook = new HookClient(page);
let frames = 0;
let ticks = 0;
let attempt = 1;
let closed = false;

async function snapshot(): Promise<void> {
  await hook.render(true);
  await page.screenshot({ path: path.join(framesDir, `${String(frames++).padStart(5, '0')}.png`) });
}

try {
  await openGame(page, server.url);
  await page.evaluate(async () => {
    const { C1_CHALLENGE } = await import('/prototypes/c1-challenge/candidate.ts');
    const { registerTrack } = await import('/src/tracks/index.ts');
    registerTrack(C1_CHALLENGE);
  });
  if (!await hook.loadTrack('c1-low-tide', 341352973)) throw new Error('Candidate track did not load');
  await page.evaluate(() => window.__rockhop!.skipCountdown());
  await page.evaluate(async () => {
    const { installC1Cue } = await import('/prototypes/c1-challenge/cue.ts');
    (window as any).__c1CueUpdate = installC1Cue();
    (window as any).__c1CueUpdate(window.__rockhop!.getState().bike.pos.x);
  });
  await snapshot();
  console.log(`READY ${framesDir}`);
  const rl = readline.createInterface({ input: process.stdin, terminal: false });
  for await (const line of rl) {
    const [cmd, ...parts] = line.trim().split(/\s+/);
    if (cmd === 'go') {
      const [throttle, brake, lean, count] = parts.map(Number);
      if (![throttle, brake, lean, count].every(Number.isFinite) || count < 1 || count > 2400) {
        console.log('USAGE go THROTTLE BRAKE LEAN TICKS');
        continue;
      }
      await hook.setInput({ throttle, brake, lean });
      let left = count;
      while (left > 0) {
        const step = Math.min(12, left);
        await hook.step(step);
        ticks += step;
        await page.evaluate(() => (window as any).__c1CueUpdate(window.__rockhop!.getState().bike.pos.x));
        await snapshot();
        left -= step;
      }
      console.log(`FRAME ${frames - 1} TICKS ${ticks} ATTEMPT ${attempt}`);
    } else if (cmd === 'restart') {
      const start = performance.now();
      await hook.restart();
      await page.evaluate(() => window.__rockhop!.skipCountdown());
      await page.evaluate(() => (window as any).__c1CueUpdate(window.__rockhop!.getState().bike.pos.x));
      await snapshot();
      attempt++;
      console.log(`RESTART_MS ${(performance.now() - start).toFixed(1)} FRAME ${frames - 1} ATTEMPT ${attempt}`);
    } else if (cmd === 'status') {
      const state = await hook.getState();
      console.log(JSON.stringify({ ticks, attempt, time: state.time, finished: state.finished, failed: state.failed, finishTime: await hook.finishTime() }));
    } else if (cmd === 'quit') {
      closed = true;
      console.log('DONE');
      break;
    } else {
      console.log('COMMANDS go throttle brake lean ticks | restart | status | quit');
    }
  }
} finally {
  if (!closed) console.log('CLOSING');
  await launched.close();
  await server.close();
}
