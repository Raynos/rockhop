# Hero remaster — round 1 concept choice

Ask 191 · 2026-09-30 · [implementation plan](../../../../project/archive/sol-6.1-2026-09-30-HERO_REMASTER.md).

The rider and bike must read as one complete, convincing hero in the existing dusk Garage. Keep five outfits and two bike classes, human-scale anatomy, a lightweight trials-machine silhouette and grounded mechanical/contact detail. The tools contribute different things: Hunyuan3D/TRELLIS generate static candidates, Blender produces the final mesh/material/rig, and UniMate supplies offline motion candidates. They are one workflow, not three rival product features.

| Direction | Visual intent | Main risk to prove in actual 3D |
|---|---|---|
| [A — Street remaster](A-street-remaster.png) | Familiar mustard/curls/denim identity, richer sculpting and coherent blue/white Rookie machinery | Real anatomy and cloth, believable contacts, face/hair cost |
| [B — Race remaster](B-race-remaster.png) | Blue/white technical outfit and helmet, sharper gunmetal/yellow Pro | Shoulder/collar continuity, boot/peg fit, tiny hardware texture/detail cost |
| [C — Sculpted remaster](C-sculpted-remaster.png) | Charcoal open-face rider, confident simplified forms and restrained PBR | Keeping adult identity and material richness without a toy silhouette |

Initial recommendation: A's identity, with C's clean form hierarchy when it improves phone readability; B guides the Race family. Ask 195 subsequently authorises pursuit of the mockups and tomorrow's engine comparison: start with A Street/Rookie and B Race/Pro, each versus its mockup; C stays a study. No additional pick blocks the first candidates. Human final visual approval remains open. No target changes bike power, unlocks or physics.

Each PNG is a newly generated imagegen concept, using the current clean-runtime Garage board and the older Street target as visual references. Neither local geometry generator nor UniMate was run to produce these PNGs. The images are desired appearance studies; meshes, animation, performance and in-game fidelity remain unproven. Prompt provenance is in `prompts.json`; output hashes are in `files.json`.

Review the full rider/bike first: proportions, frame/engine shape, wheel/tyre character and body/material separation. Ignore generator lettering and compare the design, not fake performance. The next evidence is a whole candidate in the actual Garage with silent rotating/moving clips, followed by normal gameplay. No detail still accepts a hero.
