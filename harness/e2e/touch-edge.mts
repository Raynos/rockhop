/** Silent headless layout/input regression; no game or AudioContext boots.
 * pnpm exec tsx harness/e2e/touch-edge.mts
 * Browser emulation proves boundary handling, not the iOS Siri gesture.
 */
import assert from 'node:assert/strict';
import { chromium, webkit } from 'playwright';
import { startServer } from '../lib/server';

const server = await startServer({ dev: true });
const rows: unknown[] = [];
try {
  for (const engine of [chromium, webkit]) {
    const browser = await engine.launch({ headless: true });
    try {
      const page = await browser.newPage({ viewport: { width: 844, height: 390 }, hasTouch: true });
      // tsx preserves names in nested functions serialized by Playwright.
      await page.addInitScript('window.__name = (fn) => fn;');
      await page.route(new URL(server.url).href, (route) => route.fulfill({
        contentType: 'text/html',
        body: `<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
          <div id="ui" style="position:fixed;inset:0"></div><script type="module">
          import { TOKENS_CSS, HUD_CSS } from '/src/ui/styles.ts';
          import { TouchInput } from '/src/game/input/touch.ts';
          const style = document.createElement('style'); style.textContent = TOKENS_CSS + HUD_CSS; document.head.append(style);
          window.edgeInput = new TouchInput(document.querySelector('#ui'));
          edgeInput.setEnabled(true); edgeInput.setVisible(true);
          </script>`,
      }));
      await page.goto(server.url);
      await page.waitForFunction('!!window.edgeInput');
      for (const [width, height] of [[667, 375], [844, 390], [932, 430], [390, 844]] as const) {
        await page.setViewportSize({ width, height });
        for (const safeArea of [0, 21, 34]) {
          const row = await page.evaluate((safe) => {
            document.documentElement.style.setProperty('--sab', `${safe}px`);
            const t = (window as unknown as { edgeInput: {
              root: HTMLElement; read(out: Record<string, unknown>): void;
              setEnabled(on: boolean): void;
            } }).edgeInput;
            t.setEnabled(false); t.setEnabled(true);
            const root = t.root, rect = root.getBoundingClientRect();
            const read = (): Record<string, unknown> => { const out = {}; t.read(out); return out; };
            const event = (target: Element, type: string, id: number, x: number, y: number): void => {
              target.dispatchEvent(new PointerEvent(type, { bubbles: true, cancelable: true,
                pointerId: id, pointerType: 'touch', clientX: x, clientY: y, buttons: 1 }));
            };
            const keys = [...root.querySelectorAll('.tz-key')].map((key, i) => {
              const r = key.getBoundingClientRect(), x = (r.left + r.right) / 2, y = (r.top + r.bottom) / 2;
              const target = document.elementFromPoint(x, y)!;
              event(target, 'pointerdown', i + 1, x, y);
              const frame = read();
              event(root, 'pointerup', i + 1, x, y);
              return { bottom: r.bottom, hitsRoot: target === root, frame };
            });
            const edgeTarget = document.elementFromPoint(innerWidth * .9, innerHeight - 5)!;
            event(edgeTarget, 'pointerdown', 10, innerWidth * .9, innerHeight - 5);
            const edgeFrame = read();
            event(edgeTarget, 'pointerup', 10, innerWidth * .9, innerHeight - 5);
            event(root, 'pointerdown', 11, innerWidth * .9, rect.bottom - 10);
            const held = read();
            event(root, 'pointermove', 11, innerWidth * .9, innerHeight - 5);
            const slidToEdge = read();
            event(root, 'pointermove', 11, innerWidth * .9, rect.bottom - 10);
            const slidBack = read();
            event(root, 'pointerup', 11, innerWidth * .9, rect.bottom - 10);
            event(root, 'pointerdown', 12, innerWidth * .9, rect.bottom - 10);
            event(root, 'pointerdown', 13, innerWidth * .1, rect.bottom - 10);
            const both = read();
            event(root, 'pointercancel', 12, 0, 0); event(root, 'pointercancel', 13, 0, 0);
            return { safe, gap: innerHeight - rect.bottom, keys,
              edgeHitsRoot: root.contains(edgeTarget), edgeFrame, held, slidToEdge, slidBack, both, released: read() };
          }, safeArea);
          assert.equal(row.gap, safeArea + 20);
          assert(row.keys.every((k) => k.hitsRoot && k.bottom <= height - safeArea - 20));
          assert.deepEqual(row.keys.map((k) => [k.frame.lean, k.frame.brake, k.frame.throttle]),
            [[-1, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1]]);
          assert.equal(row.edgeHitsRoot, false);
          for (const f of [row.edgeFrame, row.slidToEdge, row.slidBack, row.released]) {
            assert.equal(f.throttle, 0); assert.equal(f.brake, 0); assert.equal(f.lean, 0);
          }
          assert.equal(row.held.throttle, 1);
          assert.equal(row.both.throttle, 1); assert.equal(row.both.lean, -1);
          rows.push({ engine: engine.name(), width, height, ...row });
        }
      }
      await page.close();
    } finally { await browser.close(); }
  }
  console.log(JSON.stringify({ pass: true, cases: rows.length, rows }, null, 2));
} finally { await server.close(); }
