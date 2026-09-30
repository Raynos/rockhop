# Pin actual maneuvers before changing the rider rig

Finding: existing inputs exercise both full physical leans, exclusive front
and rear landings with a riding recovery second, crash/instant restart and a
clear for both bikes. Pin12 matched cases and exact prefixes for future old/new
rider captures. The old Pro B1 inputs fail today; keep that outcome visible
and use the verified current Pro C1 clear rather than pretending B1 cleared.

Validation:16 recordings played twice through actual Game,65,978 input steps;
every tick trace/event/sample and final finish Float64 bytes match independently.
All physical states finite; source hashes fixed. Twelve cases, no missing
categories. Typecheck and targeted oxlint pass. Input copies retain exact SHAs.

Limits: CPU input preparation only; E2 Pro has16 prior faults and is an impact
diagnostic, not a clear. No visible contact, rig, moving art, browser or phone
acceptance. The body choice and bounded stage1 refinement remain open.

Finding: a concurrent Game restart edit changed the source after the original
scan. Preserve that scan and revalidate rather than rewriting its provenance.
Validation: another32 independent plays/65,978 steps yield identical whole
traces/events and all12 cases/samples; current source hashes verified.
Limits: this matrix does not exercise the changed finish-publication path.
