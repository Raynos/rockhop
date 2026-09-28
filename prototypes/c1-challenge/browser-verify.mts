/** Check candidate skilled recordings against the real browser game and renderer. */
import { writeFileSync, readFileSync } from 'node:fs';
import { launchBrowser } from '../../harness/lib/browser';
import { HookClient, openGame } from '../../harness/lib/hook';
import { startServer } from '../../harness/lib/server';

const nodeRows = JSON.parse(readFileSync(new URL('../../docs/evidence/c1-challenge/skilled.json', import.meta.url), 'utf8'));
const server = await startServer({ dev: true });
const browser = await launchBrowser({ width: 852, height: 392 });
const rows = [];
try {
  await openGame(browser.page, server.url);
  await browser.page.evaluate(async () => {
    const [{ C1_CHALLENGE }, { registerTrack }] = await Promise.all([
      import('/prototypes/c1-challenge/candidate.ts'), import('/src/tracks/index.ts'),
    ]);
    registerTrack(C1_CHALLENGE);
  });
  const hook = new HookClient(browser.page);
  for (const bike of ['rookie', 'pro'] as const) {
    const json = readFileSync(new URL(`../../docs/evidence/c1-challenge/${bike}-skilled.json`, import.meta.url), 'utf8');
    const r = await hook.runRecording(json);
    const browserRunTime = await hook.finishTime();
    const expected = nodeRows.find((row: { bike: string; seed: number }) => row.bike === bike && row.seed === 341352973);
    const nodeFinishTick = Math.round(expected.finishTime * 120);
    const browserFinishTick = Math.round((browserRunTime ?? r.state.finishTime) * 120);
    const row = { bike, nodeFinishTime: expected.finishTime, browserRunTime, browserPhysicsFinishTime: r.state.finishTime, nodeFinishTick, browserFinishTick, nodeHash: expected.hash, browserHash: r.hash, exact: nodeFinishTick === browserFinishTick && expected.hash === r.hash, browserWallMs: r.wallMs };
    rows.push(row);
    process.stdout.write(`${bike} ${JSON.stringify(row)}\n`);
    if (!row.exact) throw new Error(`${bike} browser replay differs`);
  }
} finally {
  await browser.close();
  await server.close();
}
writeFileSync(new URL('../../docs/evidence/c1-challenge/browser-verify.json', import.meta.url), `${JSON.stringify(rows, null, 2)}\n`);
