# D1 authored quarry integration, private before/after candidate

Status: **source frozen; private before builds pass, after builds fail the unchanged player JS cap; unplayed and not accepted as course art**. This prototype changes no production source or public model bank. The parent judges any later compact candidate.

## Frozen pair

- Pair: `/private/tmp/rockhop-quarry-d1-pair-v5/`
- Provenance, exact source and model table: `/private/tmp/rockhop-quarry-d1-pair-v5/pair.json`
- Source head at freeze: `17115c8ee8baa7b38acebcb51a250d20c75579cc`
- Original v5 prepared patch SHA-256: `59780237282bd27f7ac488074766ed226f61a5123a9a405b1ec0833aa6a26cbc`
- Current equivalent zero-context patch SHA-256: `edaabe71a9612e14f3f86062de5b07f7aad540cd9db50d347ecc0531c687cbf7`
- Current-source snapshot SHA-256: `7520778ff4c74c1ce1d2809132c422e4cfbc2b674796c2f95ac9ba3d8a58e419`
- Frozen input snapshot SHA-256 (with candidate bank): `b0b00be96bc5d89a3f8629762e718d12ca644fd855e9e8c4328f6afa14023687`
- Before/after source differences: only `src/render/world/biomeKit.ts` and `src/render/world/zones/quarryStandard.ts`.

The freeze copies the complete `src`, `public`, `assets/worldmap` and typecheck support from `harness/lib`, plus the root HTML, build and TypeScript config. The four delivered machine models and four low-detail counterparts are copied into the **same private bank** for both phases. The after phase alone applies `runtime.patch`. The output path is resolved to `/private/tmp` before phase creation so Vite's `c.root` and Rollup's module IDs share one physical path on macOS.

The current patch is a zero-context unified diff applied with `git apply --unidiff-zero`. Its formatting removes blank context lines that fail the staged whitespace gate. Reapplying it to the frozen v5 before files reproduced the exact frozen v5 after SHA-256 values for both changed files (`a8c3357a7284680ed00f7ec43b4d1fa96bcb4dd9c31cbd1d0469afec2ceb8c2e`, `1e6db50fa71157f77fcb57faa438ad1d8b49259e6f385e5fbce8669feaf765bd`). The build recipe accepts the original v5 patch hash only with its exact recorded head; new freezes use the current pinned patch hash.

The delivery's `quarry-<kind>-lod-packed.glb` names are copied as `quarry-<kind>-packed-lod.glb` in the private bank because the model catalog pairs `foo.glb` with `foo-lod.glb`. The after leaf's URL is patched to request the normalized name. The eight bytes and SHA-256 values remain those in the delivery manifest. `pair.json` records each source and private logical name; `readModelCatalog` and `readModelResources` passed with 28 models and 17 resources in the same before/after bank.

## Integration behavior

The D1 switch runs only for an authored `d1-dust-devil` course entry, after the original ZoneKit finishes its seeded RNG generation. It replaces the named generic quarry terrain, pit floor, pool, two bench batches and three generic machinery batches with collider-following bank/terrain surfaces and the authored crusher, drill, gantry and haul models. It retains the ridden road, all colliders, edge/witness cues, other rock and hazard batches, and every later RNG consumer.

The original meshes, batches and quarry plate remain a visible fallback while all four GLBs load. An empty or failed delivery leaves the original complete scene visible; a successful attached delivery reveals the authored group and hides the fallback and plate. The course owner disposes the authored model geometry/material/maps and the procedural quarry maps at world retirement. The hidden fallback stays allocated until retirement so an inaccessible old material is not disposed during the switch. This preservation may cost frame or memory budget and must be measured.

The candidate is a whole D1 scene experiment, not a claim that the quarry graphics are finished. A played full/fault/retry review must confirm that the ledges read at tire scale, machine silhouettes and strata have useful near/mid/far depth, obstacle visibility survives, and no flat plate or empty pit dominates. Parent should reject it if the view regresses, even if exact replays and budgets pass.

## Reproduce and qualify

Source freeze (new empty output path only):

```sh
pnpm exec tsx prototypes/quarry-authored-integration-v1/prepare.mts prepare /tmp/rockhop-quarry-d1-pair-NEW
```

The frozen v5 after phase passed `tsc -p tsconfig.json --noEmit`; the script passed `oxlint`, and `runtime.patch` passed `git apply --check --whitespace=error --unidiff-zero` against frozen v5 before. No browser, GPU capture, iPhone check or replay was run here.

Parent-only private build, with no shared `dist` mutation:

```sh
pnpm exec tsx prototypes/quarry-authored-integration-v1/prepare.mts build /private/tmp/rockhop-quarry-d1-pair-v5
```

The build command refuses modified phase inputs, builds each phase once, checks the emitted model catalog and records entry JS hashes, generated boot/model table hashes, full postbuild source digests, and output paths in `before-build.json` and `after-build.json`. It does **not** change the 700 KiB compressed JS limit. If either phase exceeds that or fails an existing build check, keep the failure as evidence rather than filtering or raising a gate.

### Real private build result, unchanged 716,800 B player JS cap

| Pair | Frozen source head | Before | After | Candidate increase | Outcome |
| --- | --- | ---: | ---: | ---: | --- |
| v5 | `17115c8` | 714,882 B | 719,419 B | 4,537 B | After exceeds cap by 2,619 B. |
| v6, after resident-decoder refactor | `f2f737c` | 714,679 B | 719,193 B | 4,514 B | After exceeds cap by 2,393 B. |

The v5 and v6 before phases built successfully; each after phase stopped at `rockhop:bundle-budget` before a qualifying output or visual run. The v6 full build log is `/private/tmp/rockhop-quarry-d1-pair-v6/build.log`; the two frozen reports and `before-build.json` files remain under their respective `/private/tmp/rockhop-quarry-d1-pair-v{5,6}/` directories. Reusing the resident decoder recovered roughly 0.2 KiB of baseline, too little to close the candidate gap. Do not infer that the art or gameplay passes from these source/build checks.

For the played comparison, use the two built outputs on distinct local ports and the same D1 replay, tier, camera and browser backend. Check normal resource delivery, delayed model completion, missing-model fallback, full/fault/retry exact hashes, frame/texture budget, and decoded full-motion frames. The parent owns any production integration and acceptance decision.
