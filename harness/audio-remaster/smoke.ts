/** Silent live-game smoke: headless harness only; an AudioContext attempt fails loudly. */
import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import { launchBrowser } from '../lib/browser';
import { HookClient, openGame } from '../lib/hook';
import { startServer } from '../lib/server';

const server = await startServer({ dev: true });
const launched = await launchBrowser({ width: 480, height: 270 });
const { page } = launched;
const errors: string[] = [];
page.on('pageerror', (error) => errors.push(error.message));
await page.addInitScript(`window.__audioContextAttempts = 0;
window.AudioContext = function () { window.__audioContextAttempts++; throw new Error('Automation attempted live audio'); };
window.webkitAudioContext = window.AudioContext;`);
try {
  const timing = await openGame(page, server.url, { timeoutMs: 90_000 });
  const hook = new HookClient(page);
  await page.keyboard.press('Enter');
  await page.mouse.click(30, 30);
  await page.waitForTimeout(300);
  const golden = await fs.readFile('harness/inputs/flat-test/bot-3.json', 'utf8');
  const cleared = await hook.runRecording(golden);
  const finishTime = await hook.finishTime();
  assert.ok(finishTime, 'flat-test golden must clear');
  const crash = await fs.readFile('harness/inputs/flat-test/crash.json', 'utf8');
  const crashHeader = JSON.parse(crash).header as { trackId: string; seed: number };
  assert.ok(await hook.loadTrack(crashHeader.trackId, crashHeader.seed));
  const t = performance.now();
  const { crashed, restart } = await page.evaluate((json) => {
    const game = window.__rockhop!;
    const recording = JSON.parse(json) as { runs: [number, number, number, number, number][] };
    game.skipCountdown();
    let framesPlayed = 0;
    outer: for (const run of recording.runs) {
      game.setInput({ throttle: run[1] / 255, brake: run[2] / 255, lean: run[3] / 127, hop: (run[4] & 1) !== 0, restart: (run[4] & 2) !== 0 });
      for (let frame = 0; frame < run[0]; frame++) {
        game.step(1);
        framesPlayed++;
        if (game.phase() === 'crashed') break outer;
      }
    }
    const crashed = { phase: game.phase(), tick: game.frame(), faults: game.faults(), hash: game.hashState(), framesPlayed };
    if (crashed.phase !== 'crashed') throw new Error('Crash probe never reached crashed phase');
    const before = { phase: game.phase(), tick: game.frame() };
    const callStart = performance.now();
    game.restart();
    // Observe before another physics step or RAF: browser IPC/render latency is separate.
    return { crashed, restart: { before, phase: game.phase(), resetTick: game.frame(), withinPageCallMs: performance.now() - callStart } };
  }, crash);
  const restartMs = performance.now() - t;
  assert.ok(crashed.faults > 0, 'crash replay must emit a fault');
  assert.equal(restart.before.phase, 'crashed', 'manual restart must start from an actual crash');
  assert.equal(restart.phase, 'riding', 'restart must enter riding before its call returns');
  assert.equal(restart.resetTick, 0, 'restart resets the checkpoint before another physics step');
  const contexts = await page.evaluate('window.__audioContextAttempts') as number;
  assert.equal(contexts, 0);
  assert.deepEqual(errors, []);
  const report = {
    at: new Date().toISOString(), mode: 'dev', renderer: launched.probe.renderer,
    coldBootMs: timing.bootMs, contexts, pageErrors: errors,
    clear: { finishTime, hash: cleared.hash },
    crash: crashed,
    restart: { ...restart, commandMs: restartMs, commandScope: 'Crash-prefix replay plus restart in one browser call prevents an intervening RAF auto-restart.', transition: 'Synchronous within restart(), before another physics step; commandMs includes crash replay, browser IPC/render contention.' },
    limits: 'Silent browser verifies lifecycle/physics only; fake graph tests verify music, samples and mixer. Browser command latency is not phone restart latency. No physical iPhone or subjective listening verdict.',
  };
  const out = path.resolve('harness/out/audio-remaster/runtime-smoke.json');
  await fs.mkdir(path.dirname(out), { recursive: true });
  await fs.writeFile(out, JSON.stringify(report, null, 2) + '\n');
  console.log(JSON.stringify(report, null, 2));
} finally {
  await launched.close();
  await server.close();
}
