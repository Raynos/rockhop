/** Exactly two app modules change; replacements fail closed on a different source. */
export function overrides(sources) {
  const replace = (text, from, to) => {
    if (text.split(from).length !== 2) throw new Error(`Expected one source anchor: ${from}`);
    return text.replace(from, to);
  };
  let biome = sources['src/render/world/biomeKit.ts'];
  biome = replace(biome,
    "import { a1ForestApplicable, loadA1Forest, removeA1ForestPlaceholders } from './zones/a1Forest';",
    "import { a1ForestApplicable, loadA1Forest, removeA1ForestPlaceholders } from './zones/a1Forest';\nimport { applyAlpineSurface, calibrateAlpineCanopy } from './zones/alpineSurface';");
  biome = replace(biome,
    '      const zk = buildZoneKit({ track, biome, lib, rng, detail, keepOut, plan, x0, x1 });',
    `      const zk = buildZoneKit({ track, biome, lib, rng, detail, keepOut, plan, x0, x1 });
      if (track.def.id === 'a1-sawdust') {
        // This kit is still detached: no displaced material has been rendered/compiled.
        // The terrain clone borrows library maps; dispose only its material object.
        const displaced = zk.meshes.find(mesh => mesh.name === 'terrain')?.material;
        applyAlpineSurface(zk, lib);
        for (const material of Array.isArray(displaced) ? displaced : displaced ? [displaced] : []) material.dispose();
      }`);
  biome = replace(biome,
    'const owner = mountCourseAssets(loadA1Forest(track, {\n          completeMaterial: material => { lib.complete(material); },',
    'const owner = mountCourseAssets(loadA1Forest(track, {\n          completeMaterial: material => { lib.complete(material); calibrateAlpineCanopy(material); },');
  let deck = sources['src/render/world/zones/zoneDeck.ts'];
  deck = replace(deck, "import { lcg } from './geo';", "import { lcg } from './geo';\nimport { alpineSoil } from './alpineSurface';");
  deck = replace(deck, "  const topPaint = zonePaint(lib, id, 'top', lowTide)!;",
    "  const topPaint = track.def.id === 'a1-sawdust' ? alpineSoil(lib, 'tread') : zonePaint(lib, id, 'top', lowTide)!;");
  deck = replace(deck, "  const facePaint = zonePaint(lib, id, 'face', false, track.def.id === 'd1-dust-devil')!;",
    "  const facePaint = track.def.id === 'a1-sawdust' ? alpineSoil(lib, 'bank') : zonePaint(lib, id, 'face', false, track.def.id === 'd1-dust-devil')!;");
  return { 'src/render/world/biomeKit.ts': biome, 'src/render/world/zones/zoneDeck.ts': deck };
}
