/** Append-only private morph driver; physics bones and contact targets are read. */
import assert from 'node:assert/strict';
import fs from 'node:fs';
export function patchPrivateHipCorrective(source: string): string {
  const anchor = '    this.blendStage(f);';
  assert.equal(source.split(anchor).length, 2);
  const helper = fs.readFileSync(new URL('./new-rider-hip-driver.mts', import.meta.url), 'utf8')
    .replace("import * as THREE from 'three';\n", '').replaceAll('export ', '');
  return source.replace(anchor, anchor + '\n    applyPrivateHipCorrective(this.scene, !f.ragdoll?.length, 1 - this.debug.stageBlend);') + '\n' + helper;
}
