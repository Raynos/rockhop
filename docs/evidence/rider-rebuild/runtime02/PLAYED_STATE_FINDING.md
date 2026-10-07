# Actual played physics states exceed the input-only contact table

Unaccepted CPU diagnosis of the source-specific engine03 pose, using all 192
physics states from the parent's played `ride-review02/report.json`. Rebuild
frames with the actual FrameBuilder at alpha 1 and compute bike placement
from the exact rookie GLB frame-origin/chassis-COM markers. Preserve every
input state byte and its existing state hash. No synthetic COM is supplied.

Validation: all 192 complete hierarchies are finite. Actual measured COM
residual is at most 0.8883 micrometers, sole-center error at most 1.0654 mm.
Hand-center error reaches 44.6867 mm at tick 1160: input lean 0.1843, actual
physical carrier 60.91 degrees and bike-local physical COM y 0.927824 m.
The input-only table selects zero spine flex there. No contact failure is hidden.

The parent's subsequent actual engine03 headless ride agrees across all 192
states: state hashes equal, maximum CPU/render socket discrepancy
0.000000000000218 m and COM-residual discrepancy 0.000000000000564 m.
This validates the CPU frame reconstruction against the actual game renderer.

Finding: a table fitted to nominal input targets cannot guarantee hand contact
for a force-displaced physical COM. Any next spine/contact rule must evaluate
the actual posed body while retaining fixed segment lengths, physical COM and
pelvis carrier. Root moving judgment remains required before selecting it.

Evidence: [measurements](combined04-played-states02.json),
[reproduction](played-state-probe.mts).
Limits: this evaluates previously played real states on CPU; it is not a new
browser replay, finish-time pass, glove-surface or moving-art qualification.
