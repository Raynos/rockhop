/** Diagnostic-only driver on the frozen current11 renderer, not a release build. */
import fs from 'node:fs';
import { transformWithEsbuild } from 'vite';
import type { Page } from 'playwright';

export async function installPrivateSleeveReviewDriver(page: Page): Promise<void> {
  const source = fs.readFileSync('harness/hero-remaster/new-rider-sleeve-driver.mts', 'utf8')
    .replace("import * as THREE from 'three';", 'const THREE = window.__render.debug.THREE;')
    .replace('export function applyPrivateSleeveCorrective', 'function applyPrivateSleeveCorrective');
  const installer = `
const rider = window.__render.debug.rider;
let targets = 0;
rider.scene.traverse(o => { if (o.isSkinnedMesh && o.morphTargetDictionary?.['sleeveCorrective.sample114'] !== undefined) targets++; });
if (targets !== 3) throw new Error('Review overlay did not load the candidate sleeve targets');
const original = rider.update;
rider.update = function(frame) {
  original.call(this, frame);
  applyPrivateSleeveCorrective(this.scene, !frame.ragdoll?.length, 1-this.debug.stageBlend);
};
window.__privateSleeveReviewDriverInstalled = true;
`;
  const compiled = await transformWithEsbuild(source + installer, 'sleeve-review-driver.ts', { target: 'es2022' });
  await page.addScriptTag({ content: compiled.code });
}
