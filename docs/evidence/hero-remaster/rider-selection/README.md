# Rider selection — ask 216

Further art building is stopped until the user chooses a rider or requests
revert/abandonment. These five 2×2 boards contain the preserved whole-rider
appearances from this session and all five original outfit models.

- [A: original/current/fresh Blender](board-A.png)
- [B: the other four original outfits](board-B.png)
- [C: fitted neural revisions](board-C.png)
- [D: head/skin experiments](board-D.png)
- [E: raw sources and failed head topology](board-E.png)

A1 is the exact original Street full model from
`ec04192d61e39dcc8bdb80fd97842e8019ef4e55`, SHA
`11743d396b85b9e9d06f554e528886c7a093c4f30c6d958ae5750659491bc40c`.
B1–B4 are byte-identical to that revision. A2 is the current normal V6 rider.
A3 uses the reproducible V1a full, identical to rejected V1 full; its LOD
differs deterministically, but the full shown does not. No normal model changed.

All 17 engine tiles use the same current game source, Rookie bike, Garage
camera, lighting, antialiasing and 1280×720 viewport. Each capture loads all
20 catalog models, checks consumed candidate hashes and reports zero page
errors. Outfit slots serve only as private model selectors; labels identify
the actual bytes, not the original selector text. Every tile reports `bike rider`
(full detail). Native animation/rest shape differs; poses are not artificially
made identical. Raw E1–E3 are existing Blender source turntables under different
studio lighting and are unrigged, not playable candidates.

The body photo is frame 2 of a 30-frame actual Garage rotation; the front inset
is frame 7. Boards only crop, resize and label screenshots. There is no image
generation, retouching or replaced face. The [capture audit](capture-audit.json)
records exact candidate hashes. All full/LOD input pairs are in
[inventory](inventory.json). Packed/decoded and six/seven-clip duplicates are
not additional appearance choices; mobile LOD geometry is not shown separately.

The tiny Garage orbits preserve native motion for inspection; they do not
qualify riding, sustained performance, phone art or production release gates.
The fresh candidates remain rejected; the broader hero plan is unfinished.

## Tile clips

- [A1 Original before this session](A1-orbit.mp4)
- [A2 Current normal player rider (V6)](A2-orbit.mp4)
- [A3 Fresh Blender body V1](A3-orbit.mp4)
- [A4 Fresh Blender body V2](A4-orbit.mp4)
- [B1 Original Street charcoal](B1-orbit.mp4)
- [B2 Original Street open face](B2-orbit.mp4)
- [B3 Original Race blue / white](B3-orbit.mp4)
- [B4 Original Race charcoal / yellow](B4-orbit.mp4)
- [C1 First fitted Hunyuan rider (V2)](C1-orbit.mp4)
- [C2 Neural rider refinement V3](C2-orbit.mp4)
- [C3 Neural rider refinement V4](C3-orbit.mp4)
- [C4 Neural rider refinement V5](C4-orbit.mp4)
- [D1 Authored head experiment V7](D1-orbit.mp4)
- [D2 Authored head experiment V7b](D2-orbit.mp4)
- [D3 Forearm skin experiment V7](D3-orbit.mp4)
- [D4 Forearm skin experiment V7b](D4-orbit.mp4)
- [E4 V7b discarded fragmented neck](E4-orbit.mp4)

## Reproduce

Copy the mapping/inventory files here into the ignored
`harness/out/hero-remaster/rider-selection/` folder. Rebuild each A–E private
suite with `harness/hero-remaster/build.mts --out=.../A-build --models=.../A-mapping.json`
(substitute each board letter), then run `capture.py A` through `D`.
Capture E4 with the same `review.mts` options, the E build and `street-mustard`.
Run `compose.py` with the bundled Python/Pillow runtime. Source generation
recipes and archived original Git bytes supply the ignored GLB masters.
