# Native preservation correction207

Actual206 failed its combined finite/index assertion before saving decoder arrays.
This frozen sibling changes preservation and diagnostics ordering only. The exact
same2.1 model call, MPS adaptation, seed42, 30 steps, octree380, chunks200000,
guidance5 and reference204 are retained. The controller is byte-identical to203;
its relative sibling worker path now resolves207. The shared `lockf -k` lock,
decimal70GB anonymous limit and1790s termination rule remain unchanged.

The untouched real numeric arrays are saved before finite/index/shape validation.
Every invalid element location, affected vertex/face row ID, exact value text and
count is recorded before refusing display export. The native NPZ preserves exact
dtype and values, including NaN/Inf. Unsupported non-real/object arrays refuse
without coercion. Invalid geometry is retained evidence, not repaired geometry.

Seven CPU fixtures ran the AST-selected actual save/diagnostic/refusal block:
valid, NaN/Inf vertices, negative face, out-of-range face, fractional face, NaN face,
and empty faces. Every invalid numeric fixture retained its NPZ and diagnostic
receipt before refusal. No Torch import or GPU/model execution occurred.
The load/flashVDM/inference AST is identical to203; see `preservation-only.diff`.

`report.json` contains the exact command for the parent's one same-settings
diagnostic rerun into fresh private `tpose-shape207-01`. Parent judges admission
and actual outputs. No cosmetic polish, rig, player asset, source recipe or
installed environment changes. No appearance, motion or gameplay acceptance.
