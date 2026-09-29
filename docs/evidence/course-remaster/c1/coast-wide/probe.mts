/** Silent, deterministic C1 moving-frame sample at landscape phone geometry. Run after building dist. */
import { expandFrames } from '../../../../../src/core/replay';
import { loadRecording } from '../../../../../harness/lib/recording';
import { launchBrowser } from '../../../../../harness/lib/browser';
import { openGame } from '../../../../../harness/lib/hook';
import { startServer } from '../../../../../harness/lib/server';

const rec = loadRecording('harness/inputs/c1-low-tide/bot-3.json');
const frames = expandFrames(rec);
const server = await startServer({ freeze: true });
const browser = await launchBrowser({ width: 852, height: 392, logConsole: false });
try {
  const page = browser.page;
  await openGame(page, server.url);
  const samples = await page.evaluate(([input, seed]) => {
    const game = window.__rockhop!;
    game.setQuality('low');
    game.setBike('rookie');
    game.loadTrack('c1-low-tide', seed);
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
  console.log(JSON.stringify({ backend: process.env.TRIALS_BROWSER_BACKEND ?? 'swiftshader', renderer: browser.probe.renderer,
    source: process.env.C1_SOURCE_LABEL ?? 'unlabeled', ...samples }, null, 2));
} finally {
  await browser.close();
  await server.close();
}
