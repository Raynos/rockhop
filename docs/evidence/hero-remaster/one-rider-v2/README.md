# One coherent rider — approval package

Status: reference mockups and read-only donor review complete; direction
approved in asks233–234, autonomous execution delegated. New bust reference
and bounded generation recipe ready; no new3D generation or assembly yet.
Ask232 supersedes the preceding P3-only head-preservation proposal.

## Hair target

[Three full characters](hair/full-character-options.jpg) and
[face/hair closeups](hair/hair-closeups.jpg): 1 buzz cut,2 short crop,3 swept back.
Same reference identity, clothes, adult proportions, neutral pose and studio
light. Built-in imagegen edited each separately; exact prompts and corrections
are [saved](../../../../assets/design/hero-remaster/one-rider-v2/hair/prompts.json).
The first buzz/crop outputs retained too much curl; each received one targeted
correction. Final silhouettes are compact; crop retains shallow waviness,
swept hair has shallow grooves. Do not present that crop as perfectly straight.

[Verification](hair/verification.json) records hashes and small image-detail
drift outside the scalp: these are visually consistent concepts, not a
pixel-identical controlled photograph or proof of generated topology.
All final1024×1536 assets are in assets/design/hero-remaster/one-rider-v2/hair/.
Simple hair is a hypothesis to test with saved pre-cleanup geometry.

## Body recommendation

[Matched native PBR front/back](body-review/front-back-pbr.jpg) and
[matched gray front/back](body-review/front-back-gray.jpg) compare five NEW
preserved bodies. All use the same CPU renderer, four exact yaws0/45/90/180,
camera/light/display height. PBR is preserved, without the older metallic0
override. Uniform display normalization is not an anatomical fit. Renderer,
commands, source SHAs and40 frames are in [verification](body-review/verification.json).
Profile/three-quarter frames remain in the recorded ignored runtime folders.
None is skinned or accepted; source bytes are unchanged.

| Donor | Visible reason to choose or reject |
|---|---|
| H21-4 | Recommended body: continuous hood/back, useful garment volume and denim detail. Fused/coarse glove fingers, shoe/knee detail and old head remain defects. Replace head deliberately; body still needs cleanup. |
| Original P3 | Readable existing face and useful proportions, but ankle/shoe breaks and topology issues. Two global repairs failed; no further automated repairs. Original remains a comparison alternative. |
| COMP-A Pixal | Visible back hole in both PBR and gray; not merely a dark texture patch. Folds/shoes require cleanup. |
| COMP-B Hunyuan2.1 | Coherent alternative body, close to H21-4; broad knee/foot forms and coarse hands. Existing bust slabs cannot be called decoder failures without the missing dense shape. |
| COMP-C TRELLIS.2 | Extensive hoodie and hand breaks in gray as well as PBR. Higher repair burden for this task. |

Approved direction: **H21-4 body + NEW detailed Pixal head/neck + hairstyle1
buzz cut**. The prior detailed Pixal bust has the more readable face among
the task-2 busts, but porous hair/patchy beard remain defects; it is evidence
for testing a new simpler-hair bust, not a final asset or a quality guarantee.
Actual Hunyuan3D2.1 supplied the body; no2.0 substitution. Historical production
rider is comparison-only. Asks233–234 authorize this route and subsequent visual decisions.

## Approved execution

Generate one new head/neck using the approved identity/hair, preserving the
decoded high-resolution shape before processing and keeping reproducible
settings. Use the canonical GPU lock across sampling AND native Metal exports;
no eviction, memory<70GB, batches<=30minutes. Working Desktop Comfy stays
separate; wrapper dispatch is not native linked tensor nodes. Use the working
CPU rendering/baking for actual Hunyuan2.1, whose large Metal bake failed.

Clean the chosen body/head deliberately, retain untouched sources and bake
detail/PBR onto the clean derivative. Preserve the garment/hood silhouette.
Retopologize a continuous skin neck transition using anatomical boundaries,
rather than overlapping bust/body shells or a horizontal hood cut. Test
front/profile/rear/three-quarter, normals/materials and later turn/bend.

First deliver one actual textured whole rider, face and neck closeups, matched
gray and a complete orbit with defects stated. Local neck deformation clips
are temporary join diagnostics, not runtime proof. Full rigging requires
recorded parent appearance acceptance under delegated ask233 decisions; then explicit19-bone adapter/weights and the existing
ordered sitting and Garage/riding checkpoints. Preserve physics-driven lean,
COM/IK/contacts and blending; validate seated/max-lean/landings in motion.
All stage bounds and twice-failed-technique stop rules persist.

## Imported findings and provenance

Sources: /Users/raynos/Documents/Codex/2026-09-30/task-2/comparison/README.md
and bust/final-report.json. [Source snapshot](source-findings.json) records
hashes and the relevant final settings/report.

The shared sawtooth neck edge comes from the cutting procedure. Planar cuts
removed it but clipped the hood and left visible normal/material seams.
Those three assemblies are feasibility failures, not three independent
generator neck failures. The retained Hunyuan hair slabs exist pre-paint,
but that saved mesh is post-decimation; dense decoder versus reducer origin
remains unisolated. Do not revive either failed assembly technique silently.

Unfinished: new head generation, cleanup/join, actual character appearance
judgment, sitting, riding contacts and physical devices.

## New bust reference and bounded worker

[Reference](../../../../assets/design/hero-remaster/one-rider-v2/head/buzz-bust-reference.png)
derives the approved face with a compact buzz silhouette and visible neck/
clavicle base. Fine stubble remains in the raster; no topology benefit claimed.
Built-in imagegen [prompt](../../../../assets/design/hero-remaster/one-rider-v2/head/prompt.json)
and untouched source are retained.

`generate_bust.py` uses the installed Pixal worker in its existing environment,
without editing shared port files. `lockf -k` encloses sampling and native Metal
export; queue time is outside the <=30-minute batch. Memory is polled at most
every10 seconds and work stops at anonymous70GiB or the batch deadline.
Dense `raw.npz` is saved before asset_to_glb remeshing/decimation; native export
is separately retained. Worker source HEAD is dirty: relevant file hashes and
status are recorded before/after, never represented as a clean commit.
Read-only preflight passes at anonymous24.3GiB; generation has not started.
No static output is promoted into player assets.

## Required baseline round check

[Fresh silent WebKit baseline](player-baseline-round-check.json) on the
[recorded private build](player-baseline-build-version.json) passes low/high
cold entry, Rookie B1 clear40.083333333333336s, exact Node state/Float64 finish
bytes, crash and one-tick restart, with zero page errors. Restart render
submission is1/2ms, not phone frame latency. [Process record](player-baseline-process.json)
shows canonical GPU lock and memory check. Production rider only: this does
not pass the proposed new character, neck, sitting or riding contact gates.
