# UniMate feasibility — 2026-09-30, ask 190

Finding: promising offline rider-animation experiment; no geometry/material improvement or bike-physics replacement established.

The [linked post](https://x.com/Stefan_3D_AI/status/2104981826888675532) was recovered through the public FxTwitter endpoint after X returned 403. It points to [UniMate](https://github.com/Friedrich-M/UniMate), not a mesh generator. The [author project](https://linzhanmou.com/unimate/) describes text-conditioned motion, joint editing, in-betweening and expansion.

Checked upstream code at `5d6aabedd947297b5ba6706d8e9113e68c0c3e4f` and [official model card](https://huggingface.co/Linzhan/UniMate/blob/387a344c3031299bc25fcbef35d36bd186d5afe7/README.md). The recommended `unimate_uniml3d_f60_v2` checkpoint exists; cached search results saying checkpoints are unreleased are stale. Official samples are 60 frames at 30 fps; longer actions require expansion. Code and checkpoints declare MIT; source datasets retain their own terms, so this does not establish blanket source-asset redistribution rights.

Rockhop's rider has 19 joints and six existing clips. That fits the documented v2 joint range and the preprocessing requirement for at least one animation. Custom-rig import is not a drag-and-drop inference path: `run_preprocess_char.sh` creates canonical assets, conditioning and motion features; sampler integration and mapping back to our rig still need verification. Upstream canonical facing is +Z, Rockhop's is +X.

`src/render/hero/clipAliases.ts` records `sit_cruise` as a static hold with no breathing source. A two-second subtle seated idle is the best initial probe; restrained head motion or a finish celebration are later candidates. In-ride lean/landing improvements need the existing physics pose, grip/peg IK and reachable-motion limits in `gltfRider.ts`. Pinning joint features in UniMate does not prove world-space hand/foot contacts with a moving bike.

`gltfBike.ts` already drives the rigid chassis, fork, swingarm, shock, chain and wheels from physics endpoints. UniMate is not a substitute for those mechanical constraints. Bike silhouette, materials and detail remain Blender art work.

Upstream requirements pin PyTorch CUDA 12.4 wheels; the recommended checkpoint config selects `cuda`. This host is arm64 with 128 GiB RAM. Local MPS/CPU compatibility, speed and required GPU memory are unmeasured; an external NVIDIA inference machine is the straightforward supported-environment route. No installation, model download, paid compute or inference was performed.

Proposed trial: preprocess one clean runtime rider, generate seeded seated-idle candidates offline, restore the Rockhop coordinate/rig/socket contract and review silent before/after motion in the headless Garage. Only accepted baked animation enters the game; verify all five outfits/full and LOD models, contacts, repeat-input finish bytes, startup/swap cost and physical iPhone pacing before release. No neural model is needed on the phone.

Validation: live author README, model card/API, preprocessing script, requirements, sampler and checkpoint config inspected against local rider/bike drivers. Limits: no generated Rockhop clip, moving visual comparison or device performance claim; existing release/course gates remain open.
