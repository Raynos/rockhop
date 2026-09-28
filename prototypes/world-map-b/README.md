# World map B — handcrafted tabletop prototype

Independent Three.js study based on `assets/design/worldmap-3d/mockups/map-styles/B/board-3x3.jpg`. This is a standalone scene and is not loaded by the game.

Run from the repository root:

```bash
pnpm exec vite prototypes/world-map-b --host 127.0.0.1 --port 5187 --strictPort
node prototypes/world-map-b/capture.mjs
node prototypes/world-map-b/capture-terrain-compare.mjs
```

Open `http://127.0.0.1:5187/` to inspect. Drag to orbit, scroll to zoom, click the 3D roadside flag towers, or use the rotation buttons. In portrait, a landscape rotation message appears.

The default view loads [`assets/sculpted-terrain.glb`](assets/sculpted-terrain.glb), a Blender-built displaced terrain tray with UV-mapped biome surfaces, eroded front cliffs, and six cut quarry walls. Regenerate it with:

```bash
/opt/homebrew/bin/blender --background --python prototypes/world-map-b/blender/build_terrain.py
```

Add `?proceduralTerrain=1` to see the previous Three.js terrain at the same camera and layout. The remaining ships, trees, road, structures, and rally towers are standalone Three.js geometry. The GLB embeds six [Poly Haven CC0](textures/SOURCES.md) diffuse maps; it is 8.0 MB with 13 meshes and about 132,000 triangles. This is an exploration asset, not a mobile shipping budget.

The terrain, forest, snowline, water, winding road, bridges, quarry benches, wooden base, scenery, and twelve flag towers are actual 3D geometry. There is no painted world-map backdrop. The CSS is limited to the interface around the 3D scene.

The scene was iterated through thirteen captured visual passes against B's concept board. The final pass has photo-sourced CC0 surface maps, carved cliff geometry, quarry benches, a lofted ship hull, harbor crane, distinct conifers and broadleaf trees, a visible coast-to-snow route, and a closer mobile camera. Selecting a tower focuses the actual 3D model and local terrain; closing the card restores the atlas view. See [`docs/evidence/world-map-b/orbit-showcase.mp4`](../../docs/evidence/world-map-b/orbit-showcase.mp4) for a played view.

This reaches the **functional mockup** bar but remains below the concept board's photographic miniature fidelity. The foliage, ship details, water movement, rock faces, and quarry still read as stylized procedural assets, especially at close range. An authored asset pass, stronger materials, shadow and light tuning, and mobile performance work would be needed before production integration.

Stage names in this isolated visual prototype are placeholders. A production map must use the actual C1 Low Tide through S3 Whiteout stage identifiers and real lock and medal state.
