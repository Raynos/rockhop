# Actual NEW white rider UniMate input

Use body-bind04, never historical production geometry or its idle motion.
prepare_input.py preserves original meshes, skins, nodes, materials, images,
textures and the entire binary prefix. It appends only animation time inputs,
retiming the actual exported clip end2.0s to59/30s. All nineteen bones remain.
Actual feature preprocessing must verify sixty frames, not assume success.

Run run_locked.py using the installed UniMate .venv Python under exactly
`lockf -k /Users/raynos/projects/localai/.model.lock`. The script does not evict
or interfere with other jobs. Admission and ongoing anonymous memory stay
below70GB. Entire batch1800s, preprocessing600s, sampling420s; timeout kills
only its own process group. Isolated Blender directories/two CPU threads,
no preprocessing preview, official50-step seed42 MPS sampler, CFG3, batch1.
Official weights remain symlinked from projects/weights/manual/Linzhan/UniMate.
Working Desktop Comfy and shared installed packages remain unchanged.

The prompt requests natural standing-to-low-bench sitting. Only foot features
are masked to GT; decoded foot/body/contact drift must still be measured.
Canonical +Z/diameter2 exports are review-only and require explicit restored
metre/bind transforms. Model inference cannot create the character weights.
No normal player asset replacement, accepted sitting/contact or game-ready
claim follows from finite sampling alone.
