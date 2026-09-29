/**
 * Determinism gate. Replays a recording in Node and two *fresh page loads*,
 * then compares the player-facing run clock, faults, physics attempt clock,
 * final tick and state hash. The run clock includes checkpoint retries.
 *
 *   pnpm harness:replay <input-file> [--dev] [--runs 2] [--json]
 *
 * Exit code 0 = cross-engine match, 1 = mismatch or error.
 */
import path from 'node:path';
import { encodeJSON, expandFrames } from '../src/core/replay';
import { flagBool, flagNum, parseArgs } from './lib/args';
import { launchBrowser } from './lib/browser';
import { HookClient, openGame } from './lib/hook';
import { describeRecording, loadRecording } from './lib/recording';
import { ensureOut, fail, printKV, writeJson } from './lib/report';
import { startServer } from './lib/server';
import { createSimFor } from './lib/sim';

async function main(): Promise<void> {
  const { positional, flags } = parseArgs();
  const inputFile = positional[0];
  if (!inputFile) fail('usage: harness/replay.ts <input-file> [--runs 2]');
  const runs = Math.max(2, flagNum(flags, 'runs', 2));
  const rec = loadRecording(inputFile);
  const json = encodeJSON(rec);
  console.log(`recording: ${describeRecording(rec)}`);

  // The physics state's finishTime is the current attempt's clock. The player-facing
  // result uses the run clock, which includes earlier faults and checkpoint respawns.
  const node = await createSimFor(rec);
  for (const frame of expandFrames(rec)) node.step(frame);
  const expected = { hash: node.hash(), runTime: node.runTime(), faults: node.faults(),
    finishTime: node.state().finishTime, tick: node.state().tick };

  const server = await startServer({ dev: flagBool(flags, 'dev'), forceBuild: flagBool(flags, 'build') });
  const launched = await launchBrowser({ logConsole: flagBool(flags, 'verbose') });
  try {
    const results: Array<{ hash: string; runTime: number; faults: number; finishTime: number | null; tick: number; wallMs: number; x: number }> = [];
    for (let i = 0; i < runs; i++) {
      // Fresh page per run so no in-page state can leak between attempts.
      const page = await launched.context.newPage();
      await openGame(page, server.url);
      const hook = new HookClient(page);
      const info = await hook.info();
      if (info.physicsHz !== rec.header.physicsHz) {
        fail(`recording hz ${rec.header.physicsHz} != game hz ${info.physicsHz} (pass ?hz via the page)`);
      }
      const r = await hook.runRecording(json);
      results.push({ hash: r.hash, runTime: r.runTime, faults: r.faults, finishTime: r.state.finishTime, tick: r.state.tick, wallMs: r.wallMs, x: r.state.bike.pos.x });
      await page.close();
    }
    const first = results[0]!;
    const identical = results.every((r) => r.hash === first.hash && r.runTime === first.runTime && r.faults === first.faults && r.finishTime === first.finishTime && r.tick === first.tick);
    const nodeMatch = results.every((r) => r.hash === expected.hash && r.runTime === expected.runTime && r.faults === expected.faults && r.finishTime === expected.finishTime && r.tick === expected.tick);
    const report = { input: path.resolve(inputFile), header: rec.header, node: expected, runs: results, deterministic: identical, nodeMatch };
    const outFile = path.join(ensureOut('replay'), `${path.basename(inputFile).replace(/\.[^.]+$/, '')}.json`);
    writeJson(outFile, report);
    if (flagBool(flags, 'json')) console.log(JSON.stringify(report));
    else {
      results.forEach((r, i) =>
        printKV(`run ${i + 1}`, {
          hash: r.hash,
          'result time (s)': r.runTime,
          faults: r.faults,
          'physics attempt time (s)': r.finishTime,
          ticks: r.tick,
          'final x': r.x.toFixed(4),
          'replay wall ms': r.wallMs.toFixed(1),
        }),
      );
      console.log(identical && nodeMatch ? `VERIFIED: ${runs} browser runs match Node result clock, faults and hash ${first.hash}` : `MISMATCH: browser loads ${identical ? 'agree' : 'diverge'}; Node ${nodeMatch ? 'matches' : 'differs'}`);
      console.log(`report: ${outFile}`);
    }
    if (!identical || !nodeMatch) process.exitCode = 1;
  } finally {
    await launched.close();
    await server.close();
  }
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
