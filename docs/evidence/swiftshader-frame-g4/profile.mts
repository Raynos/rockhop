/** Silent, frozen-dist profile of the gate's real harness render path. */
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { preview } from 'vite';
import { launchBrowser } from '../../../harness/lib/browser';
import { openGame } from '../../../harness/lib/hook';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../../..');
const outDir = process.env['FRAME_DIST'] ?? path.join(root, 'dist');
const width = Number(process.env['FRAME_WIDTH'] ?? '1280');
const height = Number(process.env['FRAME_HEIGHT'] ?? '720');
const server = await preview({ root, configFile: path.join(root, 'vite.config.ts'), logLevel: 'error', build: { outDir }, preview: { host: '127.0.0.1', port: 0 } });
const url = server.resolvedUrls?.local[0];
if (!url) throw new Error('preview URL unavailable');
const launched = await launchBrowser();

async function page() {
  const context = await launched.browser.newContext({ viewport: { width, height }, deviceScaleFactor: 1 });
  const page = await context.newPage();
  await openGame(page, url!);
  return { page, context };
}

const install = `(() => {
  const r = window.__render;
  const rows = [];
  const wrap = (object, key, name) => {
    if (!object || typeof object[key] !== 'function') return;
    const original = object[key];
    object[key] = function (...args) {
      const t0 = performance.now();
      try { return original.apply(this, args); }
      finally { rows.push({ name, ms: performance.now() - t0 }); }
    };
  };
  wrap(r, 'renderInner', 'renderInner');
  wrap(r, 'ensureHero', 'ensureHero');
  wrap(r, 'ensureLighting', 'ensureLighting');
  wrap(r.lib, 'generateTextures', 'generateTextures');
  wrap(r.post, 'render', 'post.render');
  wrap(r.renderer, 'render', 'renderer.render');
  wrap(r, 'finish', 'readPixels sync');
  window.__frameProfile = { rows, clear: () => { rows.length = 0; } };
})()`;

try {
  const boot = await page();
  await boot.page.evaluate(install);
  const first = await boot.page.evaluate(() => {
    const t = window.__rockhop!;
    const ms = t.render(true);
    const r = (window as typeof window & { __render: { debugInfo(): Record<string, unknown> }; __frameProfile: { rows: unknown[] } });
    return { ms, breakdown: t.info().lastRender, rows: r.__frameProfile.rows,
      render: r.__render.debugInfo(), hash: t.hashState(), finishTime: t.finishTime() };
  });
  console.log(JSON.stringify({ kind: 'first', backend: launched.probe.renderer, width, height, ...first }));
  await boot.context.close();

  const restart = await page();
  await restart.page.evaluate(install);
  const out = await restart.page.evaluate(() => {
    const t = window.__rockhop!;
    const p = (window as typeof window & { __frameProfile: { rows: { name: string; ms: number }[]; clear(): void }; __render: { debugInfo(): Record<string, unknown> } }).__frameProfile;
    void t.loadTrack('flat-test');
    t.skipCountdown();
    t.setInput({ throttle: 1 });
    t.step(360);
    const warmMs = t.render(true);
    const warmRows = [...p.rows];
    p.clear();
    const frames = [];
    for (let rep = 0; rep < 20; rep++) {
      t.setInput({ throttle: 1 });
      t.step(120);
      const a = performance.now();
      t.setInput({ restart: true });
      t.step(1);
      t.setInput({ restart: false });
      const b = performance.now();
      const ms = t.render(true);
      frames.push({ rep, wallMs: b - a, frameMs: performance.now() - a, renderMs: ms,
        breakdown: { ...t.info().lastRender }, rows: [...p.rows], stateHash: t.hashState() });
      p.clear();
      t.setInput({ throttle: 1 });
      t.step(1);
      while (!(t.getState().bike.vel.x > 0)) t.step(1);
    }
    return { warmMs, warmRows, frames, render: (window as typeof window & { __render: { debugInfo(): Record<string, unknown> } }).__render.debugInfo() };
  });
  console.log(JSON.stringify({ kind: 'restart', backend: launched.probe.renderer, width, height, ...out }));
  await restart.context.close();
} finally {
  await launched.close();
  await new Promise<void>((resolve, reject) => server.httpServer.close(error => error ? reject(error) : resolve()));
}
