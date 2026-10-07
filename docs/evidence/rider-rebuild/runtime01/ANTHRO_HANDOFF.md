# Runtime continuation handoff

Frozen first adapter source checkpoint is `9da258bb`; bounded near-similarity
helper checkpoint is `d25665c4`. Actual-engine01 and actual-engine02 already build
and retain the original Garage/game/menu/bike flows. Engine02 uses appearance02
SHA `291da1cad6d5ea03b71e2ff0c5ae12f1a7a675e6f71437b575d3b2239690e174`.
No browser, Blender or model jobs were run by the runtime owner. Root owns all
moving visual judgment and coordinates the heavy lease.

New independent, uncommitted files are `anthropometric-inverse.mjs`, its two
passing Node tests, and `anthropometric-probe.json`. The source helper calibrates
actual native/export head and toe/finger tail correspondence in loaded rest,
then measures an explicitly approximate adult male segment COM from the posed
real shoulder/elbow/wrist, hip/knee/ankle and rigid head/toe/finger extents.
`invertAnthropometricCOM` solves hips against the supplied physical COM with
fixed torso articulation. It never interprets COM as hips or changes inputs.

Probe on frozen combined01 converges in 2–3 Newton iterations below .5µm COM
residual. It reduces maximum back hand gap from116mm to65mm, but contacts still
fail. Neutral gap28.6mm, forward57.7mm; full forward sole gap20.6mm. No source
stretch or fabricated contact flag is involved. This is diagnosis, not acceptance.

Native author is preparing native04 correcting measured source joint fit:
shoulder native(.184,.010,1.340), elbow(.286,.006,1.10), wrist(.374,-.063,.88),
actual arm chain .53464m. Do not force the old generic profile's .59m. Recalibrate
and rerun the anthropometric inverse against that exact new exported source.

Smallest integration: import the new helper into `private-rider.mjs`; call
`calibrateAnthropometry(this, metadata)` after capturing placed rest Q/P and
before attaching to the bike. Save requested physical COM in `physicsTarget`.
Extract the current pose operation so it accepts an explicit candidate hip
position; reset the complete hierarchy before each numerical evaluation.
Evaluate the real posed mass proxy, transform it into bike coordinates, solve,
and finally pose the winning hips. Keep actual grip/sole/COM residuals visible.
The old profile inverse can remain initial guess only. Runtime cost needs a
bounded measurement; repeated full hierarchy evaluations may need analytic
endpoint evaluation or a carefully measured smaller iteration bound later.

If corrected native04 still cannot close all contacts at fixed carrier angle,
test explicit spine flex relative to the fixed physical pelvis carrier. Preserve
pelvis orientation; remove the pelvis ID from the trunk group before applying
that extra articulation. Do not simply rotate the whole body or modify physics
COM. The native shoulder/arm/leg lengths and all rest/FOUR fields stay fixed.
Root judges bounded articulation and the moving result; no unreported draw clamp.

The private class's debug contains explicit source SHA/semantic IDs/author object
roles/observed primitive names, finite status, reset count and real contacts.
For root material QA a next private build can expose the instance/material map,
factor, texture image dimensions and loaded state. Existing `setLivery` is a
no-op; it never recolors outfits. `lib.complete` retains an existing albedo map;
normal Garage stage lift and lighting/grade are still applied. Wardrobe owns
palette changes, and currently awaits actual engine material evidence.
