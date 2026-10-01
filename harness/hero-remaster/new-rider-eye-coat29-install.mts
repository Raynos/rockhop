/* oxlint-disable typescript/no-explicit-any -- isolated browser material diagnostics. */
/** One reversible native-cornea material diagnostic, isolated from release code. */
import fs from 'node:fs';
import assert from 'node:assert/strict';
import { transformWithEsbuild } from 'vite';
import type { Page } from 'playwright';

export async function installPrivateEyeCoat29(page: Page, sourceSHA256: string): Promise<unknown> {
  assert.equal(sourceSHA256, 'cc20ab813669b628c8e5d21596b655188d7188770adc374377cebf40769232ff');
  const geometrySHA256 = await page.evaluate(async () => {
    const win = window as unknown as { __render: { debug: { rider: { scene: { traverse: (fn: (mesh: any) => void) => void } } } } }; // isolated diagnostic
    const candidates: any[] = [];
    win.__render.debug.rider.scene.traverse(mesh => {
      if (mesh.isMesh && !Array.isArray(mesh.material) && mesh.material.name === 'CC0 brown iris and sclera') candidates.push(mesh);
    });
    if (candidates.length !== 1) throw new Error('Opaque-eye census differs');
    const geometry = candidates[0].geometry, chunks: Uint8Array[] = [], encoder = new TextEncoder();
    for (const [name, attr] of Object.entries(geometry.attributes).sort(([a], [b]) => a.localeCompare(b)) as [string, any][]) {
      chunks.push(encoder.encode(name + '/' + attr.itemSize + '/' + attr.count + '/' + attr.normalized));
      const values = new Float64Array(attr.count * attr.itemSize);
      for (let i = 0; i < attr.count; i++) for (let c = 0; c < attr.itemSize; c++) values[i * attr.itemSize + c] = attr.getComponent(i, c);
      chunks.push(new Uint8Array(values.buffer));
    }
    if (geometry.index) chunks.push(new Uint8Array(Uint32Array.from(geometry.index.array).buffer));
    const bytes = new Uint8Array(chunks.reduce((n, c) => n + c.length, 0));
    let offset = 0;
    for (const chunk of chunks) { bytes.set(chunk, offset); offset += chunk.length; }
    return Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256', bytes))).map(n => n.toString(16).padStart(2, '0')).join('');
  });
  assert.equal(geometrySHA256, 'a6ba58aa72d3da5fd0b31cb9e1c9af5cd3faa6055400f8647f74cf0ce9320f4a');
  const source = fs.readFileSync('assets/blender/hero-remaster/rider/one-rider-v2/rig-adapter01/body-bind29/private_eye_coat.ts', 'utf8')
    .replace("import * as THREE from 'three';", 'const THREE = window.__render.debug.THREE;').replace(/^export /gm, '');
  const installer = `
const trial = coatOpaqueEyesForPrivateTrial(window.__render.debug.rider.scene, ${JSON.stringify({ sourceSHA256, geometrySHA256 })});
window.__render.debug.rider.scene.userData.privateEyeCoat29 = {
  sourceSHA256: SOURCE22_SHA256, geometrySHA256: EXPECTED_EYE_GEOMETRY,
  meshes: [trial.mesh.name], settings: {type:trial.material.type,transmission:trial.material.transmission,
  thickness:trial.material.thickness,ior:trial.material.ior,opacity:trial.material.opacity,
  alphaTest:trial.material.alphaTest,transparent:trial.material.transparent,depthWrite:trial.material.depthWrite,
  roughness:trial.material.roughness,side:trial.material.side,clearcoat:trial.material.clearcoat,clearcoatRoughness:trial.material.clearcoatRoughness}
};
`;
  const compiled = await transformWithEsbuild(source + installer, 'private-eye-coat29.ts', { target: 'es2022' });
  await page.addScriptTag({ content: compiled.code });
  return page.evaluate(() => (window as unknown as { __render: { debug: { rider: { scene: { userData: { privateEyeCoat29: unknown } } } } } }).__render.debug.rider.scene.userData.privateEyeCoat29);
}
