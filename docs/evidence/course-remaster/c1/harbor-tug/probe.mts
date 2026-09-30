/** Matched Metal C1 ride probe against a frozen production build. */
import { readFileSync, writeFileSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { expandFrames } from '../../../../../src/core/replay';
import { loadRecording } from '../../../../../harness/lib/recording';
import { launchBrowser } from '../../../../../harness/lib/browser';
import { openGame } from '../../../../../harness/lib/hook';

const [outFile] = process.argv.slice(2);
const url = process.env.C1_CAPTURE_URL;
const sha = process.env.C1_CAPTURE_SHA;
if (!outFile || !url || !sha) throw new Error('C1_CAPTURE_URL=... C1_CAPTURE_SHA=... tsx probe.mts output.json');
const inputPath = 'harness/inputs/c1-low-tide/bot-3.json';
const rec = loadRecording(inputPath);
const frames = expandFrames(rec);
const inputSha256 = createHash('sha256').update(readFileSync(inputPath)).digest('hex');
const browser = await launchBrowser({ width: 852, height: 392, logConsole: false });
try {
  const page = browser.page;
  const errors: string[] = [];
  page.on('pageerror', (error) => errors.push(error.message));
  const version = await page.request.get(new URL('/version.json', url).href).then((r) => r.json()) as { sha: string };
  if (version.sha !== sha) throw new Error(`frozen build mismatch: ${version.sha} != ${sha}`);
  await openGame(page, url);
  const samples = await page.evaluate(async ([input, seed]) => {
    const game = window.__rockhop!;
    game.setQuality('low');
    game.setBike('rookie');
    await game.loadTrack('c1-low-tide', seed);
    game.resize(852, 392);
    game.skipCountdown();
    const out = [];
    for (let i = 0; i < input.length; i++) {
      game.setInput(input[i]!);
      game.step(1);
      if (i + 1 >= 160 && (i + 1) % 80 === 0) {
        const submit = game.render(false);
        const sync = game.render(true);
        out.push({ tick: i + 1, x: game.getState().bike.pos.x, submit, sync, stats: game.stats() });
      }
    }
    return { samples: out, hash: game.hashState(), finishTime: game.getState().finishTime };
  }, [frames, rec.header.seed] as const);
  const report = { url, sha, inputPath, inputSha256,
    backend: process.env.TRIALS_BROWSER_BACKEND ?? 'swiftshader', renderer: browser.probe.renderer,
    errors, ...samples };
  writeFileSync(outFile, JSON.stringify(report, null, 2) + '\n');
  console.log(outFile, samples.hash, samples.samples.length, 'samples', errors.length, 'errors');
  if (errors.length) process.exitCode = 1;
} finally {
  await browser.close();
}
