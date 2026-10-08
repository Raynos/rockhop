# Motion11 — separate native controls and action construction

Source ready, native run pending. Parent owns the serial CPU2 guard and judges
the selected dressed result. No master, mesh, field, material or rest edit.

Run from repository root into a fresh output:

```sh
blender -b -t 2 --python-exit-code 1 --python assets/blender/rider-rebuild/selected-authoring-motion11/build.py -- assets/blender/rider-rebuild/selected-authoring-motion11/source.json harness/out/rider-rebuild/selected-authoring-motion11/native01
```

The source reads only `RiderSkeleton` from pinned engine05. It adds native
hips/spine/head FK, palm/sole targets, elbow/knee poles and ten digit curl
properties; ordinary IK and builtin drivers work without trusted Python handlers.
Existing75 rest bones stay exact. Pelvis wings follow the root; each thigh pair
shares its swing. Every sample checks actual skin-operator equivalence over a
conservative2m radius before the regional palette can be reused.

Six named actions: Idle, Walk, Jog, Turn90, JumpLand, RangeOfMotion. The latter
contains held A/T, overhead/forward reach, asymmetric bend,40cm crouch and head
turn/nod. Travelling walk/jog have stationary stance targets and explicit.70/.95m
root displacement per cycle. Play them once or accumulate root offsets; a raw
LoopRepeat reset would visibly teleport. Turn lifts feet before rotation; jump
uses a.5s ballistic air phase and continuous takeoff/landing root velocity.

Output: editable control blend, separate baked75 blend, rig-only GLB and sampled
native matrices. Saved source controls and visual bake are independently
compared. The master owner appends/transfers these actions and controls to the
complete selected textured derivative before parent playback. Rig-only output
is not a garment or artistic deliverable. Actual bike action authoring follows
the supported, corrected master; rejected seated keys are not relabelled final.

Validation so far: five pure trajectory tests pass, including1001subsamples
per travelling score/side against actual source limb lengths; Python AST checks
pass. An initial score exceeded leg reach by7–10mm; lowering authored walk/jog
pelvis arcs before native execution restores positive reach margin. No Blender,
export, film, collision, GPU or device pass is claimed.
