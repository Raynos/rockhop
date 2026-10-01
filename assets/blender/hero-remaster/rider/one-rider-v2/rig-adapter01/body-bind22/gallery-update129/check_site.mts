import { webkit } from 'playwright';
import { writeFile } from 'node:fs/promises';

// Local-only, silent headless verification; caller owns the shared Metal lock.
const browser = await webkit.launch({ headless: true });
const results = [];
try {
  for (const width of [390, 1200]) {
    const page = await browser.newPage({ viewport: { width, height: 844 } });
    const errors: string[] = [];
    page.on('pageerror', error => errors.push(error.message));
    await page.goto(process.argv[3]!, { waitUntil: 'networkidle' });
    const movies = await page.evaluate(async () => {
      const rows = [];
      for (const video of document.querySelectorAll('video')) {
        video.muted = true;
        await video.play();
        await new Promise(resolve => setTimeout(resolve, 200));
        rows.push({ source: video.getAttribute('src'), seconds: video.duration,
          currentTime: video.currentTime, width: video.videoWidth,
          height: video.videoHeight, error: video.error?.message ?? null });
        video.pause();
      }
      return rows;
    });
    await page.evaluate(async () => {
      for (const image of document.images) {
        image.loading = 'eager';
        await image.decode();
      }
    });
    const layout = await page.evaluate(() => ({
      viewport: innerWidth, pageWidth: document.documentElement.scrollWidth,
      imageCount: document.images.length,
      images: [...document.images].map(i => ({src:i.getAttribute('src'), complete:i.complete, width:i.naturalWidth}))
    }));
    if (errors.length || layout.pageWidth > width || movies.length !== 21 ||
        movies.some(v => v.error || !(v.currentTime > 0) || !v.width) ||
        layout.images.some(i => !i.complete || !i.width)) {
      throw new Error(JSON.stringify({ width, errors, movies, layout }));
    }
    await page.screenshot({ path: `${process.argv[2]}/local-${width}.png`, fullPage: true });
    results.push({ width, errors, movies, layout });
    await page.close();
  }
} finally { await browser.close(); }
await writeFile(`${process.argv[2]}/local-site-check.json`, JSON.stringify(results, null, 2) + '\n');
console.log(JSON.stringify(results));
