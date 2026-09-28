/** Replay the exact candidate recordings through the silent headless real-game hook. */
import { readFileSync, writeFileSync } from 'node:fs';
import { launchBrowser } from '../../harness/lib/browser';
import { HookClient, openGame } from '../../harness/lib/hook';
import { startServer } from '../../harness/lib/server';

const nodeRows = JSON.parse(readFileSync(new URL('../../docs/evidence/c2-challenge/skilled.json', import.meta.url), 'utf8'));
const server = await startServer({ dev: true });
const browser = await launchBrowser({ width: 852, height: 392 });
const rows = [];
try {
  await openGame(browser.page, server.url);
  await browser.page.evaluate(async () => {
    const [{ C2_CHALLENGE }, { registerTrack }] = await Promise.all([
      import('/prototypes/c2-challenge/candidate.ts'), import('/src/tracks/index.ts'),
    ]);
    registerTrack(C2_CHALLENGE);
  });
  const hook = new HookClient(browser.page);
  for (const bike of ['rookie', 'pro'] as const) {
    const json = readFileSync(new URL(`../../docs/evidence/c2-challenge/${bike}-skilled.json`, import.meta.url), 'utf8');
    const run = await hook.runRecording(json);
    const browserRunTime = await hook.finishTime();
    const expected = nodeRows.find((row: { bike: string; seed: number }) => row.bike === bike && row.seed === 3733111498);
    const nodeFinishTick = expected.finishTick;
    const browserFinishTick = Math.round((browserRunTime ?? run.state.finishTime) * 120);
    const row = { bike, nodeFinishTick, browserFinishTick, nodeHash: expected.hash, browserHash: run.hash, exact: nodeFinishTick === browserFinishTick && expected.hash === run.hash, browserWallMs: run.wallMs };
    rows.push(row);
    process.stdout.write(`${bike} ${JSON.stringify(row)}\n`);
    if (!row.exact) throw new Error(`${bike} browser replay differs`);
  }
} finally {
  await browser.close();
  await server.close();
}
writeFileSync(new URL('../../docs/evidence/c2-challenge/browser-verify.json', import.meta.url), `${JSON.stringify(rows, null, 2)}\n`);
