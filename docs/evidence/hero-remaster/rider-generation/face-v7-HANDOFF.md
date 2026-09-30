# Frozen, unaccepted head experiments — 2026-09-30

Stop reason: parent relayed the user's rejection of the whole rider/body and
request for a complete rebuild from scratch. Neither V7 nor V7b is approved for
public promotion. Builder has stopped geometry generation and makes no art
quality or plan-completion claim.

## Stable owned paths

- `assets/blender/hero-remaster/rider/face-v7-build.py`, `face-v7-graft.mjs`,
  `face-v7-render.py`, `face-v7-rebuild.sh`: rejected first authored head.
- `face-v7-b-build.py`, `face-v7-b-graft.mjs`, `face-v7-b-pack.mjs`,
  `face-v7-b-neck-gate.mts`: final coherent head / inner collar experiment.
- Local ignored masters and candidate GLBs use these same `face-v7-*` prefixes.
  Original V6 masters, original 19 bones, four sockets and seven clips were not
  modified. Builder made no public/src changes and no commit.
- Evidence: `face-v7-{full,lod}-contract.json`,
  `face-v7-b-{full,lod}-contract.json`, `face-v7-b-neck-gate.json`,
  `face-v7-b-fragmented-neck-gate.json`, both `*-builder-sequence.jpg` files,
  `face-v7-builder-full.mp4`, `face-v7-b-builder-full.mp4`, and
  `face-v7-b-fan-reject.mp4`. Movies are local ignored files; parent must select
  and explicitly stage portable evidence if retaining it in a commit.

## Frozen packed hashes and outcomes

| Candidate | SHA-256 | Triangles / draws | Outcome |
| --- | --- | --- | --- |
| `face-v7-full-packed.glb` | `cbbaa485422b7a4e10551104e8ab23ec09ed476266074a0a14062a0150c5f277` | 54,842 / 4 | Parent rejected actual Garage orbit: neck hole, wedge face, unreadable eyes/mouth, plate hair. |
| `face-v7-lod-packed.glb` | `2b84ca8ab4520c83f4945905c17890f93a2ae77f058202fda8fad7039265ae29` | 7,765 / 4 | Same unaccepted design. |
| `face-v7-b-fragmented-full-packed.glb` | `a4d07e7bcbacb031ed6ac41218acb21c248006e8a7bede61f195288bfa4119d6` | local rejected iteration | Neck gate FAIL: two source nonmanifold edges and inconsistent contour winding. |
| `face-v7-b-fragmented-lod-packed.glb` | `810dbd551c8fae22d4f2e57b519fd982a6657d6789e435c515405c364c254fa3` | local rejected iteration | Neck gate FAIL: inconsistent contour winding. |
| `face-v7-b-full-packed.glb` | `1c35a15b3116b6416b783ccc353f3785b52527d3e90b2ec4b718865e207edb7a` | 56,775 / 4 | Contracts and declared neck contour gate PASS; art unaccepted. |
| `face-v7-b-lod-packed.glb` | `ca2a2999247c2815c612977ea0135c00e2b4a3d88a45e89b9704c7dcea23e093` | 7,991 / 4 | Contracts and declared neck contour gate PASS; art unaccepted. |

Final V7b geometric head/inner-collar cut produces one closed source cycle per
level: 136 full / 58 LOD edges. Every declared edge has one retained-source and
one graft triangle with opposite winding. Source/graft positions, raw and
normalized named weights, bind-aware coefficients, live bone identity and world
motion agree through actual `prepareHero` and `GltfRider` Garage, back lean,
neutral, forward lean, compression, extension and landing frame conditions.
Those CPU samples do not replace played engine evidence. The gate proves the
declared attachment contours; it is not a general whole-head manifold, facial
anatomy, full motion-quality or mockup-parity approval. No LOD diagnostic movie
was completed before the stop instruction.

## Rebuild commands retained for forensic reproducibility

First rejected V7: `bash assets/blender/hero-remaster/rider/face-v7-rebuild.sh`
was run and its two pinned packed SHA checks passed.

Final V7b was built sequentially with these commands for `TIER=full` (source
`candidate-v6.glb`, no `--lod`) and `TIER=lod` (source
`candidate-v6-lod.glb`, `--lod`):

```sh
/Applications/Blender.app/Contents/MacOS/Blender -b --python-exit-code 1 \
  --python assets/blender/hero-remaster/rider/face-v7-b-build.py -- \
  --input assets/blender/hero-remaster/rider/SOURCE.glb \
  --out assets/blender/hero-remaster/rider/face-v7-b-TIER-donor.glb [--lod]
node assets/blender/hero-remaster/rider/face-v7-b-graft.mjs \
  assets/blender/hero-remaster/rider/SOURCE.glb \
  assets/blender/hero-remaster/rider/face-v7-b-TIER-donor.glb \
  assets/blender/hero-remaster/rider/face-v7-b-TIER.glb
node assets/blender/hero-remaster/rider/face-v7-b-pack.mjs \
  assets/blender/hero-remaster/rider/face-v7-b-TIER.glb \
  assets/blender/hero-remaster/rider/face-v7-b-TIER-packed.glb
pnpm exec tsx assets/blender/hero-remaster/rider/face-v7-b-neck-gate.mts
```

`SOURCE`, `TIER`, and `[--lod]` above are explanatory substitutions, not literal
shell arguments. Final V7b full/LOD contracts were also run with `verifyRider`,
60k/8k triangle limits, eight draw limit and `allowGarageIdle:true`.

Local prerequisites: ignored original V6 masters and seam maps, Blender 5.2.1,
installed Node/Three/Meshopt, original baseline GLB, retained UniMate GT/donor
run in `~/projects/localai/runtime/unimate/runs/mps-seed42`. No neural rerun or
new weights were used. Approximate remaining response capacity at retirement:
20–30; parent should use a fresh builder for the user-requested whole-body
restart rather than resume this rejected head-only direction.
