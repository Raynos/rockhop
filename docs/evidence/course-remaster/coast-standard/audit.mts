/** CPU-only, no dist/GPU/browser. Run from repo root: pnpm exec tsx docs/evidence/course-remaster/coast-standard/audit.mts */
import { createHash } from 'node:crypto';
import { readFileSync, writeFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { getTrack, compileTrack } from '../../../../src/tracks/index.ts';
import { zoneGround } from '../../../../src/render/world/zones/zoneKit.ts';
import { MaterialLibrary } from '../../../../src/render/materials/library.ts';
import { planCoastStandard, buildCoastStandard } from '../../../../src/render/world/zones/coastStandard.ts';

const dir = fileURLToPath(new URL('.', import.meta.url));
const source = readFileSync(new URL('../../../../src/render/world/zones/coastStandard.ts', import.meta.url));
const hash = (bytes: Uint8Array): string => createHash('sha256').update(bytes).digest('hex');
const rows = [];
for (const id of ['c1-low-tide', 'c2-crane-hop', 'c3-hull-breach']) {
  const def = getTrack(id);
  if (!def) throw new Error(`${id} missing`);
  const track = compileTrack(def);
  for (const detail of ['high', 'low'] as const) {
    const plan = planCoastStandard(track, track.bounds.minX, track.bounds.maxX);
    const sample = () => {
      const lib = new MaterialLibrary(def.seed);
      const kit = buildCoastStandard(plan, { lib, detail, groundAt: (x, z) => zoneGround('coast', def.profile, x, z) });
      const state = createHash('sha256');
      const geometries = new Set([...kit.meshes.map(m => m.geometry), ...kit.batches.map(b => b.geometry)]);
      const materials = new Set([...kit.meshes.map(m => m.material), ...kit.batches.map(b => b.material)]);
      let meshTriangles = 0, placedTriangles = 0;
      for (const m of kit.meshes) {
        const g = m.geometry;
        meshTriangles += (g.index?.count ?? g.getAttribute('position').count) / 3;
        for (const attr of [g.getAttribute('position'), g.getAttribute('color'), g.getAttribute('uv')]) {
          if (!attr) throw new Error(`missing mesh attribute ${m.name}`);
          const values = attr.array as Float32Array;
          for (const v of values) if (!Number.isFinite(v)) throw new Error(`nonfinite mesh ${m.name}`);
          state.update(Buffer.from(values.buffer, values.byteOffset, values.byteLength));
        }
      }
      for (const b of kit.batches) {
        placedTriangles += ((b.geometry.index?.count ?? b.geometry.getAttribute('position').count) / 3) * b.count;
        for (const attr of [b.geometry.getAttribute('position'), b.geometry.getAttribute('color'), b.geometry.getAttribute('uv')]) {
          if (!attr) throw new Error(`missing batch attribute ${b.name}`);
          const values = attr.array as Float32Array;
          for (const v of values) if (!Number.isFinite(v)) throw new Error(`nonfinite batch ${b.name}`);
          state.update(Buffer.from(values.buffer, values.byteOffset, values.byteLength));
        }
        for (const it of b.items) state.update(Buffer.from(Float64Array.from(it.m.elements).buffer));
      }
      for (const m of materials) {
        const std = m as import('three').MeshStandardMaterial;
        if (!std.isMeshStandardMaterial || !std.map || !std.normalMap || !std.roughnessMap || !std.metalnessMap)
          throw new Error(`uncompleted material ${m.name}`);
        if (m.userData['coastStandardSurface']) {
          for (const tex of [std.map, std.normalMap, std.roughnessMap]) {
            const data = tex.image?.data as Uint8Array | undefined;
            if (!data) throw new Error(`missing manufactured map ${m.name}`);
            state.update(data);
          }
        }
      }
      const foam = kit.meshes.find(m => m.name === 'zone:coast-standard:shore-break-line');
      if (!foam || !foam.geometry.index || foam.geometry.index.count < 6) throw new Error(`${id}: absent tidal contact`);
      const digest = state.digest('hex');
      const batchCount = kit.batches.length;
      const ownedMaps = new Set<import('three').Texture>();
      for (const m of materials) if (m.userData['coastStandardSurface']) {
        const std = m as import('three').MeshStandardMaterial;
        for (const tex of [std.map, std.normalMap, std.roughnessMap]) if (tex) ownedMaps.add(tex);
      }
      let geometryDisposals = 0, mapDisposals = 0;
      for (const g of geometries) g.addEventListener('dispose', () => geometryDisposals++);
      for (const t of ownedMaps) t.addEventListener('dispose', () => mapDisposals++);
      kit.disposeMaps(); kit.disposeMaps();
      if (mapDisposals !== ownedMaps.size) throw new Error(`map ownership failed ${mapDisposals}/${ownedMaps.size}`);
      kit.dispose(); kit.dispose();
      if (geometryDisposals !== geometries.size || mapDisposals !== ownedMaps.size)
        throw new Error(`ownership failed ${geometryDisposals}/${geometries.size}, ${mapDisposals}/${ownedMaps.size}`);
      return { digest, meshTriangles, placedTriangles, textureBytes: kit.textureBytes,
        meshCount: geometries.size, batchCount, foamTriangles: foam.geometry.index.count / 3,
        landmarkCount: plan.landmarks.length, geometryDisposals, mapDisposals };
    };
    const a = sample(), b = sample();
    if (a.digest !== b.digest) throw new Error(`${id}/${detail}: candidate changed between fresh constructions`);
    rows.push({ id, detail, ...a });
  }
}
const report = { sourceSha256: hash(source), method: 'CPU-only fresh construction ×2; geometry/map/matrix digest; no renderer', rows };
writeFileSync(`${dir}audit.json`, `${JSON.stringify(report, null, 2)}\n`);
console.log(JSON.stringify(report));
