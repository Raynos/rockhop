/** Silent headless browser cross-check for two constant-throttle clears. */
import { readFileSync, writeFileSync } from 'node:fs';
import { launchBrowser } from '../../../harness/lib/browser';
import { HookClient, openGame } from '../../../harness/lib/hook';
import { startServer } from '../../../harness/lib/server';

const probe = JSON.parse(readFileSync(new URL('./throttle-only.json', import.meta.url), 'utf8')) as {
  rows: { id: string; bike: 'rookie' | 'pro'; seed: number; simulatedS: number; timeS: number | null; hash: string }[];
};
const cases = [
  probe.rows.find((r) => r.id === 'c1-low-tide' && r.bike === 'rookie')!,
  probe.rows.find((r) => r.id === 's1-lift-line' && r.bike === 'pro')!,
];
const server = await startServer({ dev: true });
const browser = await launchBrowser({ width: 932, height: 430 });
const rows = [];
const uiResults = [];
try {
  await openGame(browser.page, server.url);
  const hook = new HookClient(browser.page);
  for (const row of cases) {
    const ticks = Math.round(row.simulatedS * 120);
    const recording = {
      magic: 'TRIN',
      header: { version: 1, trackId: row.id, seed: row.seed, physicsHz: 120, bike: row.bike, physics: 'v2', note: 'gameplay-audit constant throttle=1' },
      runs: [[ticks, 255, 0, 0, 0]],
    };
    const result = await hook.runRecording(JSON.stringify(recording));
    const out = { id: row.id, bike: row.bike, ticks, nodeHash: row.hash, browserHash: result.hash, sameHash: row.hash === result.hash, nodeFinishS: row.timeS, browserFinishS: result.state.finishTime, browserWallMs: +result.wallMs.toFixed(1) };
    rows.push(out);
    process.stdout.write(`${row.id} ${row.bike}: ${out.sameHash ? 'HASH MATCH' : 'HASH MISMATCH'} finish=${out.browserFinishS}\n`);
    if (!out.sameHash || out.browserFinishS === null) throw new Error(`browser replay mismatch on ${row.id} ${row.bike}`);
    if (row.id === 'c1-low-tide') {
      await hook.step(140); // results reveal after the finish tick
      await hook.render();
      await browser.page.screenshot({ path: new URL('./c1-throttle-results.png', import.meta.url).pathname });
      const replay = browser.page.locator('.results .tile[data-id="replay"]');
      const initial = { replayPresent: await replay.count() === 1, replayDisabled: await replay.isDisabled(), replayLabel: await replay.textContent(), resultsClass: await browser.page.locator('.results').getAttribute('class') };
      if (!initial.replayDisabled) {
        await replay.click();
        const viewerPresent = await browser.page.locator('.replay').count() === 1;
        const viewerVisible = viewerPresent && await browser.page.locator('.replay').isVisible();
        const exitPresent = await browser.page.locator('.rp-exit').count() === 1;
        if (exitPresent) await browser.page.locator('.rp-exit').click();
        uiResults.push({ ...initial, viewerPresent, viewerVisible, exitPresent, returnedToResults: await browser.page.locator('.results').isVisible() });
      } else uiResults.push(initial);
    }
  }
} finally {
  await browser.close();
  await server.close();
}
writeFileSync(new URL('./browser-verify.json', import.meta.url), `${JSON.stringify({ browser: browser.probe.renderer, rows, uiResults }, null, 2)}\n`);
