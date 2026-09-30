/** Silent full-App pause/resume proof, including the audio call on the input frame. */
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import { launchBrowser } from '../lib/browser';
import { startServer } from '../lib/server';

interface PauseSnapshot { appPaused: boolean; audioPaused: boolean; tick: number; hash: string; modelTime: number; updates: number }
type HeldSnapshot = Pick<PauseSnapshot, 'tick' | 'hash' | 'modelTime' | 'updates'>;
type ResumeSnapshot = Pick<PauseSnapshot, 'appPaused' | 'audioPaused' | 'tick'>;
interface AfterSnapshot { tick: number; contexts: number; updates: number }

const server = await startServer({ dev: true });
const launched = await launchBrowser({ width: 480, height: 270 });
const { page } = launched;
const errors: string[] = [];
page.on('pageerror', (error) => errors.push(error.message));
await page.addInitScript(`window.__audioContextAttempts = 0;
window.AudioContext = function () { window.__audioContextAttempts++; throw new Error('Live audio forbidden'); };
window.webkitAudioContext = window.AudioContext;
localStorage.setItem('rockhop.onboarded', '1');`);
const clock0 = Date.now();
await page.clock.install({ time: clock0 });
try {
  await page.goto(new URL('/?track=flat-test&sw=0&dev=1', server.url).toString(), { waitUntil: 'commit' });
  await page.waitForFunction(() => window.__rockhop?.app && window.__rockhop.phase() === 'countdown', undefined, { timeout: 90_000 });
  await page.clock.pauseAt(Math.max(clock0, Date.now()) + 30_000);
  await page.evaluate(`(async function () {
    var module = await import('/src/audio/graph/webAudio.ts');
    var original = module.WebAudioSystem.prototype.setPaused;
    window.__audioPauseLog = [];
    module.WebAudioSystem.prototype.setPaused = function (paused) {
      var result = original.call(this, paused);
      window.__pauseAudio = this;
      window.__audioPauseLog.push({ paused: paused, audioPaused: this.paused, tick: window.__rockhop.frame(), modelTime: this.driver.scratch.time, modelUpdates: this.driver.scratch.updates });
      return result;
    };
    window.__rockhop.setQuality('low');
    window.__rockhop.skipCountdown();
    window.__rockhop.app.frame();
  })()`);
  await page.clock.runFor(100);
  const paused = await page.evaluate<PauseSnapshot>(`(function () {
    var hook = window.__rockhop;
    hook.app.togglePause();
    hook.app.frame();
    return { appPaused: hook.app.paused(), audioPaused: window.__pauseAudio.paused, tick: hook.frame(), hash: hook.hashState(), modelTime: window.__pauseAudio.driver.scratch.time, updates: window.__pauseAudio.driver.scratch.updates };
  })()`);
  assert.equal(paused.appPaused, true);
  assert.equal(paused.audioPaused, true);
  await page.clock.runFor(150);
  const held = await page.evaluate<HeldSnapshot>(`({ tick: window.__rockhop.frame(), hash: window.__rockhop.hashState(), modelTime: window.__pauseAudio.driver.scratch.time, updates: window.__pauseAudio.driver.scratch.updates })`);
  assert.equal(held.tick, paused.tick, 'paused physics ticks must stay byte-identical');
  assert.equal(held.hash, paused.hash, 'paused physics state must stay byte-identical');
  assert.equal(held.modelTime, paused.modelTime, 'paused audio model must not advance from render-only dt');
  assert.equal(held.updates, paused.updates);
  const resumed = await page.evaluate<ResumeSnapshot>(`(function () {
    window.__rockhop.app.togglePause();
    window.__rockhop.app.frame();
    return { appPaused: window.__rockhop.app.paused(), audioPaused: window.__pauseAudio.paused, tick: window.__rockhop.frame() };
  })()`);
  assert.equal(resumed.appPaused, false);
  assert.equal(resumed.audioPaused, false);
  await page.clock.runFor(100);
  const after = await page.evaluate<AfterSnapshot>(`({tick: window.__rockhop.frame(), contexts: window.__audioContextAttempts, updates: window.__pauseAudio.driver.scratch.updates})`);
  assert.ok(after.tick > resumed.tick, 'resumed physics must advance');
  assert.ok(after.updates > held.updates, 'resumed audio model must advance');
  assert.equal(after.contexts, 0);
  assert.deepEqual(errors, []);
  const report = { at: new Date().toISOString(), renderer: launched.probe.renderer, paused, held, resumed, after, pageErrors: errors,
    limits: 'Silent headless live-App test proves same-input-frame pause notification and unchanged physics/audio model while paused. Fake graph tests prove actual audio bus gating and recorded loop continuity; physical iPhone remains unverified.' };
  const out = path.resolve('harness/out/audio-remaster/pause.json');
  await fs.mkdir(path.dirname(out), { recursive: true });
  await fs.writeFile(out, JSON.stringify(report, null, 2) + '\n');
  console.log(JSON.stringify(report, null, 2));
} finally {
  await launched.close();
  await server.close();
}
